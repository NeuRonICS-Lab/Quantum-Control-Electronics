#Class defination for DACs 

from utility_classes import *
import xrfdc
import xrfclk
import numpy
from pynq import MMIO
import logging, sys
from pynq import MMIO
import matplotlib.pyplot as plt
import threading

class dac_populate_exp_config():
    def __init__(self,u_obj, ch, exp_config, dac_conf, conf, hw_config ):
        #super().__init__(hw_config)
        #self._config = []
        self.u_obj = u_obj
        self._config = {"sleep_time" : {'addr' : 0, 'val' : u_obj.ns_to_cycles(exp_config["data_fetch_time"])}}
        self._config["time_between_pulses"] = {'addr' : 4, 'val' : u_obj._start_time_bw_pulses}
        self._config["trigger_time"] = {'addr' : 8, 'val' : conf.trigger_time}
        self._config["inner_loop_step"] = {'addr' : 12, 'val' : u_obj.ns_to_cycles(exp_config["inner_loop_step"])}
        #self._config["inner_loop_count"] = {'addr': 16, 'val' : self.ns_to_cycles(exp_config["inner_loop_count"])}
        self._config["inner_loop_count"] = {'addr': 16, 'val' : u_obj._num_of_averages}
        self._config["repetition_rate"] = {'addr': 20, 'val' : u_obj.ns_to_cycles(exp_config["repetition_rate"])}
        self._config["outer_loop_count"] = {'addr' : 24, 'val' : exp_config["outer_loop_count"]}
        self._config["amplitude_factor"] = {'addr' : 28, 'val' : round(exp_config["amplitude_factor"] * ((numpy.power(2, 15) - 1) / 100))}
        #self._config["n_s_4"] = {'addr': 32, 'val' : self.cal_n_s(4*self.ns_to_cycles(exp_config["gaussian_pulse_duration"]), exp_config['mode'])}
        self._config["n_s_4"] = {'addr': 32, 'val' : u_obj._wave_len-1}
        self._config["gaussian_width"] = {'addr': 36, 'val': 0 if(u_obj._loopback == 1) else u_obj._wave_len-1}
        self._config["adc_dac_lat"] = {'addr' : 40, 'val' : conf.adc_dac_lat}
        self._config["trigger_delay"] = {'addr' : 44, 'val' : u_obj.ns_to_cycles(conf.trigger_delay)}
        self._config["trigger_width"] = {'addr' : 48, 'val' : u_obj.ns_to_cycles(conf.trigger_width)}
        self._config["amplitude_factor_direct"] = {'addr' : 52 , 'val' : round(u_obj._control_amplitude_list[int(ch%4)] * ((numpy.power(2, 15) - 1) / 100)), 'bit_offset': 0,  'bit_width': 16 }
        self._config["mode"] = {'addr' : 52, 'val' : u_obj._mode, 'bit_offset': 16,  'bit_width': 2 } # required to be made 3 in future ver
        
        
        self._config["trigger_rst"] = {'addr' : 52, 'val' : 0 , 'bit_offset': 18,  'bit_width': 1 } 
        self._config["continuous"] = {'addr' : 52, 'val' : u_obj._continuous, 'bit_offset': 19,  'bit_width': 1  }
        self._config["power_rabi"] = {'addr' : 52, 'val' : exp_config["power_rabi"], 'bit_offset': 20,  'bit_width': 1 }
        self._config["gaussian_arb_bar"] = {'addr' : 52, 'val' : 0 if (self._config["mode"]['val'] >=3) else 1 , 'bit_offset': 21,  'bit_width': 1}
        
        
        
        #self._config['sel_cont_rst'] = {'addr' : 100, 'val': round((self._config["power_rabi"]['val'] * 4) + (self._config["continuous"]['val'] * 2 + 1))}
        #self._config["dac_parameters4"] = {'addr' : 52, 'val' : self.cal_dac_param4()}
        self._config["gaussian_pulse_duration"] = {'addr' : 104, 'val' : u_obj._wave_len-1}
        self._config["gaussian_sigma"] = {'addr' : None, 'val' : u_obj._sigma}
        self._config["rst"] = {'addr' : 56, 'val' : 0}
        self._config['update'] = {'addr': 56, 'val' : 0}
        self._config['rst_update'] = {'addr' : 56, 'val' : 0}
        self._config['trigger_src'] = {'addr': 60, 'val': dac_conf["trigger_src"]} 
        self._config['half_time'] = {'addr' : 64, 'val' : round(u_obj._wave_len/2)}
        self._config['trigger_delay_inc_in'] = {'addr' : 68, 'val' : round(u_obj._trigger_delay_inc_in)}
        self._config['wave_addr_0_1'] = {'addr': 72, 'val' : ((2**13)*u_obj._wave_addr[1]+ u_obj._wave_addr[0])}
        self._config['wave_addr_2_3'] = {'addr': 76, 'val' : ((2**13)*u_obj._wave_addr[3]+ u_obj._wave_addr[2])}
        self._config['trigger_scaled_value'] = {'addr': 80, 'val': round(u_obj._readout_amplitude_list[int(ch%4)] * ((numpy.power(2, 15) - 1) / 100)), 'bit_width': 16, 'bit_offset': 8 }
        self._config['start_gaussian'] = {'addr': 80, 'val': u_obj._start_gaussian, 'bit_offset': 0, 'bit_width': 1 }
        self._config['wakeup'] = {'addr': 80, 'val': u_obj._wakeup, 'bit_offset': 1, 'bit_width': 1 }
        self._config['num_of_pulses'] = {'addr': 80, 'val': u_obj._no_of_pulses, 'bit_offset': 2,  'bit_width': 5 }
        self._config['loopback'] = {'addr': 108, 'val': u_obj._loopback}        

        
        #print(self._config)
    


class dac():
    def __init__(self, rf, ch, config, mem_config, top_config, hw_config, u_obj):  # ch, fs, mixer_freq, phase, bram_addr):
        #super().__init__(hw_config)
        self._rf = rf
        self._ch = ch
        self.u_obj = u_obj
        self._exp_config = dac_populate_exp_config(u_obj, self._ch, config["dac_exp_config"],config, top_config,  hw_config)
        self._fs = config["fs"]
        self._nco_freq = u_obj._freq_list[ch] #config["LO freq"]
        self._nco_phase = u_obj._phase_list[ch] #config["phase"]
        self._nyquist_zone = 2 if(self._nco_freq[0] > (self._fs/2)) else 1 #config["nyquist_zone"]
        self._readout_channel = u_obj._readout_channel_list[ch] #config['readout_channel']
        self._bram_size = mem_config["DAC_BRAM_SIZE"]
        self._conf_mem_base_addr  = mem_config["DAC_CONF_ADDR"]
        self._bram_mmio_conf_mem = MMIO(mem_config["DAC_CONF_ADDR"], self._bram_size)  # mem_config["DAC_BRAM_I_LSB"] #
        self._bram_mmio_I_lsb = MMIO(mem_config["DAC_BRAM_I_LSB"], self._bram_size)  # mem_config["DAC_BRAM_I_LSB"] #
        #print('dac channel and I mem address', self._ch,hex(mem_config["DAC_CONF_ADDR"]) )
        self._bram_mmio_I_msb = MMIO(mem_config["DAC_BRAM_I_MSB"], self._bram_size)  # mem_config["DAC_BRAM_I_MSB"] #
        self._bram_mmio_Q_lsb = MMIO(mem_config["DAC_BRAM_Q_LSB"], self._bram_size)  # mem_config["DAC_BRAM_Q_LSB"] #
        self._bram_mmio_Q_msb = MMIO(mem_config["DAC_BRAM_Q_MSB"], self._bram_size)  # mem_config["DAC_BRAM_Q_MSB"] #
        self._control_or_readout_sel_addr = config["dac_exp_config"]["READOUT_CHANNEL_CONF_ADDR"]
        self._dac_handle = self._rf.dac_tiles[int(ch // 4)].blocks[ch % 4]
        self.init_conf_mem(self._bram_mmio_conf_mem)
        self.set_nco_freq(self._nco_freq[0])
        self.set_nco_phase(self._nco_phase)
        self.set_nyquist_zone(self._nyquist_zone)
        
        #set readout channel config for the channel
        self.set_readout_channel(self._readout_channel)
        self.load_wave(u_obj)
    
    def concat_samples(self, samples_l, samples_m):
        return int((samples_l) + (samples_m * (2 ** 16)))
    def prog_param(self, addr, val):
        #print('addr and val', addr, val)
        self._bram_mmio_conf_mem.write(addr, val)
    def set_param(self, key, val, unit):
        #print('channel no', self._ch)
        addr = self._exp_config._config[key]['addr']
        if(self._ch>3):
            logging.debug("PARAM set  ERROR, Cant set exp program param for for Dac %d as it is CH >4", self._ch)
            if(self._exp_config._config[key]['addr'] == 60):
                self.u_obj.set_bitfield(self._conf_mem_base_addr+addr, 0, 1, 0, val)
            return;
        if(unit == 'time'):
            self._exp_config._config[key]['val'] = self.u_obj.ns_to_cycles(val)
        elif(unit=='scale'):
            self._exp_config._config[key]['val'] = round(val * ((numpy.power(2, 15) - 1) / 100))
        else:
            self._exp_config._config[key]['val'] = val
        addr = self._exp_config._config[key]['addr']
        if(addr == None):
            logging.debug('Error in the dac param programming as addr is None')
            return
        if(addr==52 or addr == 80):
            self.u_obj.set_bitfield(self._conf_mem_base_addr+addr, self._exp_config._config[key]['bit_offset'], self._exp_config._config[key]['bit_width'], 0, self._exp_config._config[key]['val'])
            return
        elif(addr==56):
            self._exp_config._config['rst_update']['val'] = (2**25)*self._exp_config._config['rst']['val']+(2**24)*self._exp_config._config['update']['val']
            key = 'rst_update'    
        elif(addr== 104): # gaussian pulse duration
            self._exp_config._config['n_s_4']['val'] = (self._exp_config._config[key]['val'])
            key = 'n_s_4'
            self.prog_param(self._exp_config._config[key]['addr'], self._exp_config._config[key]['val'])
            self._exp_config._config['gaussian_width']['val'] = 0 if (self._exp_config._config["loopback"] == 1) else self._exp_config._config['gaussian_pulse_duration']['val']
            key = 'gaussian_width'
            self.prog_param(self._exp_config._config[key]['addr'], self._exp_config._config[key]['val'])
            return
        elif(addr==108):
            self._exp_config._config['gaussian_width']['val'] = 0 if ( val == 1) else self._exp_config._config['n_s_4']['val']
            key = 'gaussian_width'
            self.prog_param(self._exp_config._config[key]['addr'], self._exp_config._config[key]['val'])
            return
        self.prog_param(addr, self._exp_config._config[key]['val'])
        logging.debug('Programmed Dac experimental param %s with val %x at addr %x and channel %x', key, (int(self._exp_config._config[key]['val'])), self._exp_config._config[key]['addr'], self._ch)
    def get_param(self, key):
        return self._exp_config._config[key]['val']
    def init_conf_mem(self, mmio_handle):
        paramList = list(self._exp_config._config.items())
        #print(paramList)
        #print('len of param list', len(paramList))
        for i in range(len(paramList)):
            key = paramList[i][0]
            #print('key', key)
            val = paramList[i][1]['val']
            self.set_param(key, val, 'None')
        
  


    def set_readout_channel(self, val):
        self.u_obj.set_bitfield(self._control_or_readout_sel_addr, 8, 1, self._ch, val)
    def get_readout_channel(self):
        self.u_obj.get_bitfield(self._control_or_readout_sel_addr, 8, 1, self._ch)

    def load_wave(self, u_obj):
        # First load I Samples
        I_samples =  u_obj._w_I
        Q_samples =  u_obj._w_Q
        self.addr_off = 0

        s_len = u_obj._wave_len
        #print("s_len",s_len)
        
        zero_len = (int(self._bram_size/4) - (s_len )) 
        #print('zero_len', zero_len)
        
        for x in range(0, s_len, 1):
            self._bram_mmio_I_lsb.write(self.addr_off, self.concat_samples(I_samples[x], I_samples[x]))
            self._bram_mmio_I_msb.write(self.addr_off, self.concat_samples(I_samples[x], I_samples[x]))
            self.addr_off = self.addr_off + 4
        for x in range(zero_len):
            self._bram_mmio_I_lsb.write(self.addr_off, 0)
            self._bram_mmio_I_msb.write(self.addr_off, 0)
            self.addr_off = self.addr_off + 4
            #print(x, self.addr_off)
            
        ## Load Q_samples
        self.addr_off = 0
        s_len = len(Q_samples)
        zero_len = (int(self._bram_size/4) - (s_len )) 
        #print("Q-addr", self.addr_off)
        for x in range(0, s_len, 1):
            self._bram_mmio_Q_lsb.write(self.addr_off, self.concat_samples(Q_samples[x], Q_samples[x]))
            self._bram_mmio_Q_msb.write(self.addr_off, self.concat_samples(Q_samples[x], Q_samples[x ]))
            self.addr_off = self.addr_off + 4
        for x in range(zero_len):
            self._bram_mmio_Q_lsb.write(self.addr_off, 0)
            self._bram_mmio_Q_msb.write(self.addr_off, 0)
            self.addr_off = self.addr_off + 4
        logging.info('Wave loading completed for channel %d', self._ch)
        
    
    def set_nco_freq(self, freq, event=xrfdc.EVNT_SRC_SYSREF):
        self._dac_handle.MixerSettings['EventSource'] = event
        self._dac_handle.MixerSettings['Freq'] = freq

    def set_nco_phase(self, phase, event=xrfdc.EVNT_SRC_SYSREF):
        self._dac_handle.MixerSettings['EventSource'] = event
        self._dac_handle.MixerSettings['PhaseOffset'] = phase

    def set_nyquist_zone(self, nyq_zone, event=xrfdc.EVNT_SRC_SYSREF):
        self._dac_handle.MixerSettings['EventSource'] = event
        self._dac_handle.NyquistZone = nyq_zone

    def reset_nco_phase(self, event=xrfdc.EVNT_SRC_SYSREF):
        self._dac_handle.MixerSettings['EventSource'] = event
        self._dac_handle.ResetNCOPhase()

