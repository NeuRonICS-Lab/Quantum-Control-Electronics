# Classes for ADC Readout pipeline. The pipeline consists of ADC->FilterBlock->Rotation Block -> DMA -> UDP Streamer
# Configurable parameters
# Help commands

from pynq.lib import AxiGPIO
from utility_classes import *
import xrfdc
import xrfclk
import xrfdc
import xrfclk
import numpy
from pynq import MMIO
import logging, sys
from pynq import MMIO
import matplotlib.pyplot as plt
import threading
import time
import sys

ADC_CONF_MEM_SIZE = 4096
ADC_PIPELINE_PARAM_OFFSET = 48 #  IIR paramers (num_ch * param_no * 4 bytes = 4*3*4=48) go first in conf mem, other params start afterwards
ADC_SRC_SEL_BIT_OFFSET = 0
ADC_FIL_BYPASS_BIT_OFFSET = 4
ADC_IIR_ORDER_BIT_OFFSET = 8
ADC_QUAD_BIT_OFFSET = 16
ADC_THETA_OFFSET = 4 #(after 4 32-bit words from IIR params
ADC_ILA_SEL_OFFSET = 20 #(after 20 32-bit words from IIR params)
ADC_UPDATE_OFFSET = 24
MA_BYP_BASE_ADDR = 80
#ADC_IIR_ORDER_OFFSET = 
class Readout():
    def __init__(self, rf, ch, rdout_config, rdout_mem_config, top_config, o1, hw_config, u_obj):
        logging.debug('RT-4')
        #super().__init__(hw_config)
        #return 
        self._rf = rf
        self._ch = ch
        self._top_config = top_config
        self.u_obj = u_obj
        self._fs = rdout_config["fs"]
        self._start_reg = o1.start_fifo_cap #AxiGPIO(o1.ip_dict['start_fifo_cap']).channel1
        self._nco_freq = u_obj._readout_freq #rdout_config["LO freq"]
        self._nco_phase = rdout_config["phase"]
        self._nyquist_zone = 2 if(self._nco_freq[0] > (self._fs/2)) else 1
        #self._readout_trigger_src = rdout_config["readout_trigger_src"]
        self._adc_input_sel = rdout_config["adc_input_sel"]
        self._adc_fil_bypass = rdout_config["filter_bypass"]
        self._readout_xfr_count = rdout_config["number_of_xfr"]
        self._adc_theta = u_obj._readout_rotation_angle #rdout_config["readout_rotation_angle"]
        self._trigger_width = u_obj.ns_to_cycles(top_config.trigger_width)
        self._trigger_delay = u_obj._start_trigger_delay
        self._adc_dac_lat = top_config.adc_dac_lat
        self._conf_mem_base_addr = rdout_mem_config["IIR_CONF_BASE_ADDR"] + 12 * ch
        self._conf_param_base_addr = rdout_mem_config["IIR_CONF_BASE_ADDR"] + ADC_PIPELINE_PARAM_OFFSET # 3 iir params per channel (4 channels)
        self._start_fifo_reg_addr = o1.ip_dict['start_fifo_cap']['phys_addr']
        self._adc_handle = self._rf.adc_tiles[int(ch // 2)].blocks[ch % 2]        
        self._adc_pipeline = AdcPipeline((ch%4),   rdout_config, self._conf_mem_base_addr, hw_config, u_obj)
        self._dma = Dma(o1, ch%4, rdout_config, top_config,hw_config, u_obj)
        self._streamer = Streamer(top_config.remote_host, top_config.remote_port[ch%4])
        self._streamer_process = 'None'
        self.init_all_params()
        logging.debug('Readout init completed')

    def init_all_params(self):
        self.u_obj.set_bitfield(self._start_fifo_reg_addr, 0, 1, (self._ch%4), 1)
        self.set_adc_src_sel(self._adc_input_sel)
        self.set_filter_bypass(self._adc_fil_bypass)
        self.set_adc_theta(self._adc_theta)
        self.set_ma_bypass(1)
        self.set_nco_freq(self._nco_freq[0])
        self.set_nco_phase(self._nco_phase)
        self.set_nyquist_zone(self._nyquist_zone)
        #xrfdc.EVNT_SRC_SYSREF
    def set_nco_freq(self, freq, event=xrfdc.EVNT_SRC_SYSREF):
        self._adc_handle.MixerSettings['EventSource'] = event
        self._adc_handle.MixerSettings['Freq'] = freq

    def set_nco_phase(self, phase, event=xrfdc.EVNT_SRC_SYSREF):
        self._adc_handle.MixerSettings['EventSource'] = event
        self._adc_handle.MixerSettings['PhaseOffset'] = phase

    def set_nyquist_zone(self, nyq_zone, event=xrfdc.EVNT_SRC_SYSREF):
        self._adc_handle.MixerSettings['EventSource'] = event
        self._adc_handle.NyquistZone = nyq_zone

    def reset_nco_phase(self, event=xrfdc.EVNT_SRC_SYSREF):
        self._adc_handle.MixerSettings['EventSource'] = event
        self._adc_handle.ResetNCOPhase()
    def init_streamer(self, mode, power_rabi):
        self.u_obj.set_bitfield(self._start_fifo_reg_addr, 0, 1, (self._ch%4), 1)
        self._dma._xfr_completed_outer = 0;
        self._mode = mode
        self._power_rabi = power_rabi
        #f_name = 'output-26-05-001.csv'
        #self._csv_file_handle = open(f_name, 'w') 

        self._streamer_process = threading.Thread(target=self.dma_streamer_thread)
    def start_readout(self):
        self._streamer_process.start()
    def stop_readout(self):
        #self._start_reg.mmio.write(0x0, 0) # mmio.write(addr , value)
        #multiprocessing.Process(target=self.dma_streamer_thread).stop()
        #threading.Thread(target=self.dma_streamer_thread).stop()
        self._streamer_process.terminate()
    def set_adc_src_sel(self, val):
        self.u_obj.set_bitfield(self._conf_param_base_addr, ADC_SRC_SEL_BIT_OFFSET, 1, self._ch, val)
    def get_adc_src(self):
        return self.u_obj.get_bitfield(self._conf_param_base_addr, ADC_SRC_SEL_BIT_OFFSET, 1, self._ch)
    def set_filter_bypass(self, val):
        self.u_obj.set_bitfield( self._conf_param_base_addr, ADC_FIL_BYPASS_BIT_OFFSET, 1, self._ch, val)
    def get_filter_bypass(self):
        return self.u_obj.get_bitfield( self._conf_param_base_addr, ADC_FIL_BYPASS_BIT_OFFSET, 1, self._ch)
    def set_adc_quad(self, val):
        self.u_obj.set_bitfield(self._conf_param_base_addr, ADC_QUAD_BIT_OFFSET, 2, self._ch, val)
    def set_adc_theta(self, val):
        theta_addr_offset = ADC_THETA_OFFSET + (self._ch%4)*4
        (quad , theta)= self.u_obj.find_quad_angle(val)
        self.u_obj.set_bitfield(self._conf_param_base_addr, ADC_QUAD_BIT_OFFSET, 2, (self._ch%4),quad )
        mmio_handle = MMIO((self._conf_param_base_addr + theta_addr_offset), 8)
        mmio_handle.write(0, theta)
        del(mmio_handle)
    def get_adc_theta(self):
        theta_addr_offset = ADC_THETA_OFFSET + (self._ch%4)*4;
        mmio_handle = MMIO((self._conf_param_base_addr + theta_addr_offset), 8)
        return mmio_handle.read(0)
    def set_ila_sel(self, val): #This is for debuggng only and same for all the readout channels:: Should find a better place to call it to avoid redundancy
        self.u_obj.set_bitfield((self._conf_param_base_addr + ADC_ILA_SEL_OFFSET), 0, 2, 0, val) #channel value is passed as 0, as these are a single param for all channels
    def set_readout_update(self, val):
        self.u_obj.set_bitfield((self._conf_param_base_addr + ADC_UPDATE_OFFSET), 0, 1, 0, val) #channel value is passed as 0, as these are a single param for all channels
    def get_readout_update(self, val):
        self.u_obj.get_bitfield((self._conf_param_base_addr + ADC_UPDATE_OFFSET), 0, 1, 0)    #channel value is passed as 0, as these are a single param for all channels
    def set_ma_bypass(self, val):
        self.u_obj.set_bitfield( (self._conf_param_base_addr+MA_BYP_BASE_ADDR), 0, 1, self._ch, val)
    def dma_streamer_thread(self, exp_prog_val):
        #self._start_reg.mmio.write(0x0, 1)
        #self.set_bitfield(self._start_fifo_reg_addr, 0, 1, (self._ch%4), 1)
        
        i=0
        
        #self._dma._xfr_completed_outer =0
        #self._dma._avg_buffer[:] = 0
        j=0
        kk=0
        junk=0;
        while True:
            #self._dma._avg_buffer[:] = 0
            #print(self._dma._avg_buffer)
            
            while True:
                # print("Hello, i")
                #if(self._dma._dma_handle.mmio.read(0x34) == 0x11008):
                if(self._dma._desc_buffer[i][7] != 0x0):
                    #self._start = time.time()
                    #self._dma._dma_handle.mmio.write(0x34, 0x1000)
                    self._dma._desc_buffer[i][7] = 0x0
                    #self._dma._verification_buffer[0][j] = self._i
                    j+=1
                    
                    #self._dma._data_buffer[i][0] = numpy.int64(exp_prog_val)
                    self._streamer._sock.sendto(self._dma._data_buffer[i], (self._streamer._host, self._streamer._port))
                    #numpy.savetxt(self._csv_file_handle, self._dma._data_buffer[i], delimiter=',')
                    
                    break;
                    i=i+1
                    if (i == self._dma._num_desc-1): 
                    #if (j == self._dma._num_desc-1):
                        #self._i = 0;
                        i=0
                        break;
            
            kk+=1;
            sleep(0)
            self._dma._xfr_completed_outer = kk
            #break;
        
            #if(self._dma._xfr_completed_outer == self._readout_xfr_count-1):
            if(kk == self._readout_xfr_count):
                break
        #sys.exit(0)   
        #break
class AdcPipeline():
    def __init__(self, ch ,rdout_config,  conf_mem_base_addr , hw_config, u_obj):
        #super().__init__(hw_config)
        #logging.debug('>>>>>>>>>Complete the reg bank work for ADC pipeline')
        self._filter = IIRFilter(ch, rdout_config["filter_config"], conf_mem_base_addr, hw_config, u_obj)
        #self._dac_addr_sel_trigen_0 = o1.
class IIRFilter():
    def __init__(self, ch , filter_config, conf_mem_base_addr,  hw_config, u_obj):
        #super().__init__(hw_config)
        self._ch = ch
        self.u_obj = u_obj
        self._f_cutoff = filter_config["f_cutoff"]
        self._f_order = filter_config["filter_order"]
        self._fs = hw_config["fabric_clock"]
        self._conf_mem_base_addr = conf_mem_base_addr #filter_config["IIR_CONF_BASE_ADDR"] + ch*16 # 2 word for each iir
        self._conf_mem_size = ADC_CONF_MEM_SIZE #filter_config[IIR_CONF_MEM_SIZE]
        self._conf_param_base_addr = (self._conf_mem_base_addr - (12*ch)) + ADC_PIPELINE_PARAM_OFFSET
        logging.debug('IIR Param init in init fun completed')
        self._conf_mem_mmio_handle = MMIO(self._conf_mem_base_addr, self._conf_mem_size)
        self._Ts = 1/(self._fs)

        self.set_iir_params(self._f_cutoff)  #prog params at init
        self.set_iir_order(self._f_order)

    def scale(self, val, bits):
        return round(val * (2**bits)) #check th
    def concat_samples(self, samples_l, samples_m):
        return int((samples_l) + (samples_m * (2 ** 16))) # yes this is ok. 
    def gen_iir_params(self, f_cutoff):
        self._Tau = 0.1592 / (f_cutoff)
        self._a = numpy.exp(-(self._Ts) / self._Tau)
        b = 1 - self._a
        self._b = self.scale(b, 15) # these we changed.
        self._ab = self.scale((self._a * b), 15)
        self._a2b = self.scale(numpy.power(self._a, 2) * b, 15)
        self._a3b = self.scale(numpy.power(self._a, 3) * b, 15)
        self._a4 = self.scale(numpy.power(self._a, 4), 15)
    def set_iir_params(self, f_cutoff):
        self.gen_iir_params(f_cutoff)
        #logging.debug('programmed IIR params with value %x, %x, %x', hex(self.concat_samples(self._b, self._ab)), hex(self.concat_samples(self._a2b, self._a3b)), hex(self.concat_samples(self._a4, 0x0)))
        self._conf_mem_mmio_handle.write(0, self.concat_samples(self._b, self._ab))
        self._conf_mem_mmio_handle.write(4, self.concat_samples(self._a2b, self._a3b))
        self._conf_mem_mmio_handle.write(8, self.concat_samples(self._a4, 0x0))
    def get_iir_params(self):
        return (self._conf_mem_mmio_handle.read(0),
        self._conf_mem_mmio_handle.read(4),
        self._conf_mem_mmio_handle.read(8)
                )
    def set_iir_order(self, order):
        self.u_obj.set_bitfield(self._conf_param_base_addr, ADC_IIR_ORDER_BIT_OFFSET , 2, self._ch, order)
    def get_iir_order(self):
        return self.u_obj.get_bitfield(self._conf_param_base_addr, ADC_IIR_ORDER_BIT_OFFSET , 2, self._ch)


class Dma():
    def __init__(self, o1, ch, rdout_config, top_config,hw_config, u_obj):
        
        #super().__init__(hw_config)
        self._hw_config = hw_config
        self.u_obj= u_obj
        #self._dma_handle = o1.Readout_DMA_0.axi_dma_0 (if ch==0) else (o1.Readout_DMA_1.axi_dma_0)
        if(ch ==0):
            self._dma_handle = o1.Readout_DMA_0.axi_dma_0
        elif(ch==1):
            self._dma_handle = o1.Readout_DMA_1.axi_dma_0
        elif(ch==2): 
            self._dma_handle = o1.Readout_DMA_2.axi_dma_0
        elif(ch==3):
            self._dma_handle = o1.Readout_DMA_3.axi_dma_0
        else:
            self._dma_handle = o1.Readout_DMA_0.axi_dma_0
                
        self._dma_reg_addr = MMIO(o1.ip_dict['Readout_DMA_%d/axi_dma_0' %(ch)]['phys_addr'], 65536) ## Using MMIO for fast writing to regs
        self._data_len = self.u_obj.ns_to_cycles(top_config.trigger_width)
        self._num_desc = rdout_config["num_desc"]
        self._desc_data_size = 16
        self._data_type = rdout_config["data_type"]
        self._desc_buffer = allocate(shape=(self._num_desc, self._desc_data_size,), dtype=numpy.uint32, cacheable=False)
        self._data_buffer = allocate(shape=(self._num_desc,(self._data_len*2),), dtype=self._data_type, cacheable=False) #self._data_len*2 bcus, both I and Q samples
        self._avg_buffer = allocate(shape=(1,(self._data_len*2),), dtype=self._data_type, cacheable=False) #self._data_len*2 
        self._verification_buffer = allocate(shape=(1,(100*self._num_desc)), dtype=self._data_type, cacheable=False) #self._data_len*2 
        self._xfr_completed_outer = 0;
        self.init_desc_buff()
    def ns_to_cycles(self, time):
        cycles = round((time * pow(10, -9) * (self._hw_config["fabric_clock"] * pow(10, 6))))
        return cycles
    def init_desc_buff(self):
        for i in range(self._num_desc - 1):
            # print(i, hex(desc_buffer[i].device_address))
            self._desc_buffer[i][0] = self._desc_buffer[i + 1].device_address
            self._desc_buffer[i][2] = self._data_buffer[i].device_address
            self._desc_buffer[i][6] = (self._data_buffer[0].size * 8) #data_size_bytes  # 0x00000000 | data_size*4;# 0x00004000
            self._desc_buffer[i][7] = 0
        self._desc_buffer[self._num_desc - 1][0] = self._desc_buffer[0].device_address
        self._desc_buffer[self._num_desc - 1][2] = self._data_buffer[self._num_desc - 1].device_address
        self._desc_buffer[self._num_desc - 1][6] =  (self._data_buffer[0].size * 8)   # data_size*4;#0x00004000
        self._desc_buffer[self._num_desc - 1][7] =0
    def init_dma(self):
        self._dma_reg_addr.write(0x30, 0x1004)
        self._dma_reg_addr.write(0x30, 0x0010)
        self._dma_reg_addr.write(0x38, self._desc_buffer[0].device_address)
        self._dma_reg_addr.write(0x30, 0x0011)
        self._dma_reg_addr.write(0x40, 0x50)
        #self.set_bitfield(self._start_fifo_reg_addr, 0, 1, (self._ch%4), 1)
    def soft_reset_dma(self):
        self._dma_reg_addr.write(0x30, 0x1004)
#     def start_dma_thread(self):
#         self._sock.sendto(self._dma.)



class Streamer():
    def __init__(self, host, port):
        self._host = host
        self._port = port
        self.stream_init()
        #self._proto = proto
    def stream_init(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


