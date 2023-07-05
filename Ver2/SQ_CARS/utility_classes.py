#Class defination for various utility functions

import numpy 
import xrfdc
import xrfclk
#from pynq import Xlnk
from pynq import Overlay
from pynq.lib import AxiGPIO
from pynq import allocate
import numpy as np
import socket
import time
import sys
from pynq import Clocks
from time import sleep
import multiprocessing, time
import logging, sys
from pynq import MMIO
import matplotlib.pyplot as plt
import threading 
import config
class utility_functions():
    def __init__(self, hw_config, thisConfig):
        #self._config = config
        self._hw_config = hw_config
        self._loopback = 0;
        self._start_gaussian = 0;
        self._wakeup = 0 
        self._no_of_pulses = 1
        self.init_exp_user_params()
        self.thisConfig = thisConfig
        #print('executing inint for utility')
    @property  
    def loopback(self):
        return self._loopback
    @loopback.setter
    def loopback(self, val):
        if(val !=0 or val !=1):
            logging.error("This property only takes either 1 or 0")
        self._loopback = val
        logging.info('loopback value set')
        #self._gaussian_width_for_trigger = 0 if(self._loopback==1) else self._wave_len
    @property  
    def exp_type(self):
        return self._exp_type
#     @loopback.setter
#     def exp_type(self, val):
        
#         self._exp_type = val
#         define_mode()
#         logging.info('exp_type value set')
        #self._gaussian_width_for_trigger = 0 if(self._loopback==1) else self._wave_len
    def init_exp_user_params(self):
        
        self._qubit_freq = config.qubit_freq
        self._readout_freq = config.readout_freq
        self._freq_list = config.freq_list
        self._phase_list = config.phase_list
        self._readout_channel_list = config.readout_channel_list
        self._control_amplitude_list = config.control_amplitude_list
        self._readout_amplitude_list = config.readout_amplitude_list
        
        self._exp_type = config.exp_type
        self._exp_steps = config.exp_steps
        
        #calculate the experiment params depending on exp type
        
        self._exp_inc_val = 0
        self._exp_start_val = 0
        #Params for Power rabi
        self._start_power = 100 #config.start_power
        self._end_power = 100 #config.end_power

        self._power_inc = 0 #(self._end_power[0] - self._start_power[0])/(self._exp_steps-1)
        
        
        ## trigger params for T1
        self._start_trigger_delay = 0 #self.ns_to_cycles(config.start_trigger_delay[0])
        self._end_trigger_delay = 0 #self.ns_to_cycles(config.end_trigger_delay[0]) # in us
        self._trigger_delay_inc_in = 0 #(self._end_trigger_delay - self._start_trigger_delay ) / (self._exp_steps-1)
        
        #logging.info('trigger inc is %d in cycles and %f in ns', self._trigger_delay_inc_in, ((self._trigger_delay_inc_in* pow(10, -6))/self._hw_config["fabric_clock"])) 
        
        ## time bw pulses param for T2
        self._start_time_bw_pulses = 0 #self.ns_to_cycles(config.start_time_bw_pulses[0]) #2*5.20833
        self._end_time_bw_pulses = 0 #self.ns_to_cycles(config.end_time_bw_pulses[0]) # in ns
        self._time_bw_pulse_inc_in = 0 #(self._end_time_bw_pulses - self._start_time_bw_pulses ) / (self._exp_steps-1)
        
        self._start_freq = 0
        self._end_freq = 0
        self._freq_inc =  0
        #logging.info('time_bw_pulse_inc inc is %d in cycles and %d in ns', self._time_bw_pulse_inc_in, ((self._time_bw_pulse_inc_in* pow(10, -6))/self._hw_config["fabric_clock"]))
        ## power factos for both readout and control

        #self._readout_amp_fac = config.readout_amp_fac[0]
        #self._control_amp_fac = config.control_amp_fac[0]
        
        self._readout_rotation_angle = config.readout_rotation_angle[0]
        self._loopback = config.loopback[0]
        
        self._num_of_averages = config.num_of_averages[0]
        
        self._sample_file = None if (config.sample_file == '') else config.sample_file
        
        if(config.wave_type != None):
            self._wave_type = config.wave_type
        
        
        self.gen_wave_sample()
        self.cal_exp_params()
        self.cal_wave_addr()
        self._loopback = config.loopback
        self._continuous = config.continuous
        
    def cal_wave_addr(self):
        #calculating wave address from text file can be implemented here
        self._wave_addr = []
        self._wave_addr.append(0x0) #wave 0
        self._wave_addr.append(0x0) #wave 0
        self._wave_addr.append(0x0) #wave 0
        self._wave_addr.append(0x0) #wave 0
        

    def cal_exp_params(self):
        print('start num in u class', config.start_num)
        if(self._exp_type[0]=='power_rabi'):
            m = 0
            num_of_pulses = 1
            if(config.end_num[0] > 100):
                logging.error("Maximum power can only be 100, but given %d. Assigning Max power", config.end_num[0])
               
            self._start_power = config.start_num[0]
            self._end_power = config.end_num[0]
            self._power_inc = (self._end_power - self._start_power ) / (self._exp_steps[0]-1)
            self._exp_inc_val = self._power_inc
            self._exp_start_val = self._start_power
            
        elif(self._exp_type[0]=='T2'):
            m = 1
            num_of_pulses = 2
            self._start_time_bw_pulses = int(self.ns_to_cycles(config.start_num[0])) #in ns
            self._end_time_bw_pulses = int(self.ns_to_cycles(config.end_num[0])) # in ns
            self._time_bw_pulse_inc_in = int((self._end_time_bw_pulses - self._start_time_bw_pulses ) / (self._exp_steps[0]-1))
            self._exp_inc_val = self._time_bw_pulse_inc_in 
            self._exp_start_val = self._start_time_bw_pulses
        elif(self._exp_type[0]=='time_rabi'):
            m=2
            num_of_pulses = 1
            self._start_time_bw_pulses = int(self.ns_to_cycles(config.start_num[0])) #in ns
            self._end_time_bw_pulses = int(self.ns_to_cycles(config.end_num[0])) # in ns
            self._time_bw_pulse_inc_in = int((self._end_time_bw_pulses - self._start_time_bw_pulses ) / (self._exp_steps[0]-1))
            self._exp_inc_val = self._time_bw_pulse_inc_in
            self._exp_start_val = self._start_time_bw_pulses
        elif(self._exp_type[0]=='power_rabi_2pulses'):
            m=1
            num_of_pulses = 2
            if(config.end_num[0] > 100):
                logging.error("Maximum power can only be 100, but given %d. Please check and rerun", config.end_num[0])
                return
            self._start_power = config.start_num[0]
            self._end_power = config.end_num[0]
            self._power_inc = (self._end_power - self._start_power ) / (self._exp_steps[0]-1)
            self._exp_inc_val = self._power_inc
            self._exp_start_val = self._start_power
        elif(self._exp_type[0]=='T1'):
            m=0
            num_of_pulses = 1
            self._start_trigger_delay = int(self.ns_to_cycles(config.start_num[0]))
            self._end_trigger_delay = int(self.ns_to_cycles(config.end_num[0])) # in us
            self._trigger_delay_inc_in = int((self._end_trigger_delay - self._start_trigger_delay ) / (self._exp_steps[0]-1))
            self._exp_inc_val = self._trigger_delay_inc_in 
            self._exp_start_val = self._start_trigger_delay
        elif(self._exp_type[0] == 'cw'):
            m=3
            num_of_pulses = 1
        elif(self._exp_type[0] == 'spectroscopy'):
            m= 0
            num_of_pulses = 1
            self._start_freq = config.start_num[0]
            self._end_freq = config.end_num[0]
            self._freq_inc =  (self._end_freq - self._start_freq ) / (self._exp_steps[0]-1)
            self._exp_start_val = self._start_freq
            self._exp_inc_val = self._freq_inc
        else:
            logging.error("Given Experiment type %s is not supported, assigning default mode 0",self._exp_type[0] )
            m=0
            num_of_pulses = 1
        self._mode = m
        self._mode_list = [m,m,m,m]
        self._num_of_pulses = num_of_pulses
        logging.debug("Given Experiment type is %s , assigned mode is %d, start_val is %f, inc val is %f",self._exp_type[0], self._mode, self._exp_start_val, self._exp_inc_val )
        
    def gen_wave_sample(self):
        self._sigma  = 0
        if(self._sample_file != None):
            arr = np.loadtxt(self._sample_file)
            self._debug_w_I = arr[:, 0]
            self._debug_w_Q = arr[:, 1]
            self._w_I = self.to_hex_scale(arr[:, 0], 1)
            self._w_Q = self.to_hex_scale(arr[:, 1], 1)            
            self._wave_len = self._w_I.shape[0]
            logging.debug("reading pregenerated wave from file %s wave type in utility function", self._sample_file)
            logging.debug("length of the wave from file is %d", self._wave_len)
        else:
            logging.debug("generating %s wave type in utility function", self._wave_type)
            #self._wave_type = config.wave_type
            self._wave_len = self.ns_to_cycles(config.wave_duration)
            self._sigma = self.ns_to_cycles(config.sigma_gauss)
            
            self._w_I = self.gen_wave(self._wave_type, self._wave_len, self._sigma, 1,0,  const_val = 0x7fff)
            self._w_Q = self.gen_wave(self._wave_type, self._wave_len, self._sigma, 0,0,  const_val = 0x7fff)
            
    def ns_to_cycles(self, time):
        cycles = round((time * pow(10, -9) * (self._hw_config["fabric_clock"] * pow(10, 6))))
        return cycles

    def us_to_cycles(self, time):
        cycles = round((time * pow(10, -6) * (self._hw_config["fabric_clock"] * pow(10, 6))))
        return cycles

    def ms_to_cycles(self, time):
        cycles = round((time * pow(10, -3) * (self._hw_config["fabric_clock"] * pow(10, 6))))
        return cycles

    # Gaussian and Derivate of Gaussian
    def gaussian(self, x, mu, sig):
        #1 / (numpy.sqrt(2 * numpy.pi) * sig) * numpy.exp(-numpy.power((x - mu) / sig, 2) / 2)
        return numpy.exp(-numpy.power((x - mu) / sig, 2) / 2)
    
    def der_gaussian(self, x, mu, sig):
        return (-1 / (numpy.sqrt(2 * numpy.pi) * sig)) * (numpy.exp(-numpy.power((x - mu) / sig, 2) / 2)) * (
                    (x - mu) / numpy.power(sig, 2))

    def sine(self, x):
        return numpy.sin(x)

    def to_hex_scale(self, x, amp_scale):
        if (numpy.max(x) != 0):
            x = x / (numpy.max(x))
        return ((x * amp_scale * ((2 ** 15) - 4)).astype(numpy.int16))

    def gen_wave(self,  wav_type, on_time,  sigma, amp_scale,time_bw_pulses, const_val = 0x7fff):
        #number_samples = 4*self.ns_to_cycles(on_time)
        #clocks_bw_pulses=4*self.ns_to_cycles(time_bw_pulses)
        #print("number_samples",number_samples)
        number_samples = on_time
        logging.debug("number of samples in utility fun genwav %d",number_samples)
        clocks_bw_pulses=time_bw_pulses
        mu = on_time / 2
        a = numpy.linspace(0, on_time, number_samples)
        #a = numpy.linspace(0, on_time, number_samples)
        #print("wave params on_time, number_samples", on_time, number_samples)
        if (wav_type == "gaussian"):
            samples = self.gaussian(a, mu, sigma)
            samples = self.to_hex_scale(samples, amp_scale)
            
        elif (wav_type == "der"):
            samples = self.der_gaussian(a, mu, sigma)
            samples = self.to_hex_scale(samples, amp_scale)
            #return samples
        elif (wav_type == "sine"):
            time = numpy.linspace(0, 2 * numpy.pi, number_samples)
            samples = self.sine(time)
            samples = self.to_hex_scale(samples, amp_scale)
            return samples
        elif (wav_type == "cw"):
            # time = np.linspace(0,2*np.pi,number_samples)
            samples = numpy.ones((number_samples,))
            samples = samples * round((2**15-1))
            samples = self.to_hex_scale(samples, amp_scale)
            #return samples
        elif (wav_type == "zero"):
            # time = np.linspace(0,2*np.pi,number_samples)
            samples = numpy.zeros((number_samples,))
            # samples = samples * round((2**15-1))
            samples = self.to_hex_scale(samples, amp_scale)
            #return samples
        elif (wav_type == "const"):
            samples = numpy.empty((number_samples,))
            samples[:] = const_val
            #samples = numpy.zeros((number_samples,))
            # samples = samples * round((2**15-1))
            #samples = self.to_hex_scale(samples, amp_scale)
            samples = samples.astype(numpy.int16)
            #return samples
        elif (wav_type == "alternating"):
            samples = numpy.empty((number_samples,))
            quarter_len = round(len(samples)/4)
            start = 0
            end = quarter_len 
            for i in range(4):
                samples[start:end] = const_val[i]
                start += quarter_len
                end += quarter_len
                #print("start, end , quarter_len", start, end, quarter_len )
            
            #samples = numpy.zeros((number_samples,))
            # samples = samples * round((2**15-1))
            samples = samples.astype(numpy.int16) #self.to_hex_scale(samples, amp_scale)
            #return samples
        elif (wav_type == "double_gauss"):
            samples_1=self.gaussian(a, mu, sigma)
            zeros_1=np.zeros(clocks_bw_pulses)
            samples = np.concatenate((samples_1,zeros_1,samples_1))
            samples = self.to_hex_scale(samples, amp_scale)
            #print(len(samples_1))
            #return samples
        else:
            logging.error('Unknown waveform type %s, please check', wav_type)
        plt.plot(samples)
        return samples
    def set_bitfield(self, field_base_addr, field_offset, field_width, ch_num, new_val):
        #print(field_base_addr,field_offset, field_width, ch_num,  new_val)
        if(field_base_addr == None):
            logging.error('Error in programming the set_bitfield as addr is None')
            return
        m = ((2**field_width)-1) #3 if(field_width==2) else 1
        mmio_handle = MMIO(field_base_addr, 8)
        #print("m", m)
        rd_val = mmio_handle.read(0)
        #print("rd_val", hex(rd_val))
        #print("base addrs channel offset and channel", field_base_addr, field_offset, ch_num)
        mask = (m << field_offset) << (ch_num*field_width)
        wr_val = (rd_val & (~mask)) | ((new_val << field_offset) << (ch_num*field_width))
        #wr_val = (rd_val ^ mask) | mask
        #print("wr_val and mask", hex(wr_val), hex(mask))
        mmio_handle.write(0, wr_val)
        del mmio_handle
    def get_bitfield(self, field_base_addr, field_offset, field_width, ch_num):
        if(field_base_addr == None):
            logging.error('Error in the get_bitfield as addr is None')
            return
        m = 0x00000003 if (field_width == 2) else 0x00000001
        mmio_handle = MMIO(field_base_addr, 8)
        rd_val = mmio_handle.read(0)
        #print("rd_val full", rd_val)
        #print("base addre channel offset and channel", field_base_addr, field_offset, ch_num)
        rd_val = (rd_val >> field_offset) >> (ch_num*field_width)
        return (rd_val & m)
    def find_quad_angle(self, theta_deg_0):
        if ((theta_deg_0 >= 0) and (theta_deg_0 < 90)):
            quadr_0 = 0;
        elif ((theta_deg_0 >= 90) and (theta_deg_0 < 180)):
            quadr_0 = 1;
            theta_deg_0 = theta_deg_0 - 90;
        elif ((theta_deg_0 >= 180) and (theta_deg_0 < 270)):
            quadr_0 = 2;
            theta_deg_0 = theta_deg_0 - 180;
        elif ((theta_deg_0 >= 270) and (theta_deg_0 < 360)):
            quadr_0 = 3;
            theta_deg_0 = theta_deg_0 - 270;
        
        theta_deg_0=round((theta_deg_0*(np.pi/180))*(2**21))
        return (quadr_0, theta_deg_0)
    
    def make_connect_tcp(self, host, port):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind the socket to a specific host and port
        self.server_socket.bind((host, port))

        # Listen for incoming connections
        self.server_socket.listen(1)

        # Set the server socket to non-blocking mode
        self.server_socket.setblocking(False)

        # Accept a new connection
        self.client_socket = None
        while not self.client_socket:
            try:
                self.client_socket, self.client_address = self.server_socket.accept()
                print('Connection established with', self.client_address)

            except socket.error:
                #print('Waiting for client connection...')
                time.sleep(1)

        # Set the client socket to non-blocking mode
        self.client_socket.setblocking(False)
        self.state = 'WAITING_FOR_40K_ACK'
        #return (server_socket, client_socket)
    def run_server_sync(self): #server_socket, client_socket, state):
        self.client_socket.setblocking(False)
        self.server_socket.setblocking(False)
        while True:
            try:
                # Receive data from the client socket
                self.server_socket.setblocking(False)
                data = self.client_socket.recv(1024).decode()
                if(self.state == 'WAITING_FOR_40K_ACK'):
                    if data:
                        # Process the received data
                        print('Received data:', data, 'in state', self.state)

                        # Send a response to the client
                        response = 'ACK_RCVD'

                        if(data == '40K_RCVD'):
                            self.client_socket.send(response.encode())
                            self.state = 'ACK_SENT'
                            print('RT-1')
                            return self.state;
                        else:
                            print('RT-2')
                            return self.state;
                elif(self.state == 'ACK_SENT'):
                    if data:
                        # Process the received data
                        print('Received data:', data, 'in state', self.state)

                        # Send a response to the client
                        response = 'ACK_RCVD'

                        if(data == 'START_AGAIN_NOW'):
                            #client_socket.send(response.encode())
                            self.state = 'DONE'
                            print('RT-1')
                            return self.state;
                        else:
                            print('RT-2')
                            continue;
                            #return self.state;
                    else:
                        continue;
                elif(self.state == 'DONE'):
                    return self.state
                else:
                    return self.state



            except socket.error:
                    #print('no message, coming out ', self.state)
                    if(self.state == 'ACK_SENT' ):
                        sleep(0)
                        continue
                    else:
                        return self.state;
                #break;


        
        
