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
class utility_functions():
    def __init__(self, hw_config):
        #self._config = config
        self._hw_config = hw_config

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
        return 1 / (numpy.sqrt(2 * numpy.pi) * sig) * numpy.exp(-numpy.power((x - mu) / sig, 2) / 2)

    def der_gaussian(self, x, mu, sig):
        return (-1 / (numpy.sqrt(2 * numpy.pi) * sig)) * (numpy.exp(-numpy.power((x - mu) / sig, 2) / 2)) * (
                    (x - mu) / numpy.power(sig, 2))

    def sine(self, x):
        return numpy.sin(x)

    def to_hex_scale(self, x, amp_scale):
        if (numpy.max(x) != 0):
            x = x / (numpy.max(x))
        return ((x * amp_scale * ((2 ** 15) - 4)).astype(numpy.int16))

    def gen_wave(self, config, wav_type, on_time,  sigma, amp_scale, const_val = 0x7fff):
        number_samples = 4*self.ns_to_cycles(on_time)
        #print("number_samples",number_samples)
        mu = on_time / 2
        a = numpy.linspace(0, on_time, number_samples)
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
            end = quarter_len -1
            for i in range(4):
                samples[start:end] = const_val[i]
                start += quarter_len
                end += quarter_len
            
            #samples = numpy.zeros((number_samples,))
            # samples = samples * round((2**15-1))
            samples = samples.astype(numpy.int16) #self.to_hex_scale(samples, amp_scale)
            #return samples
        else:
            logging.error('Unknown waveform type %s, please check', wav_type)
        plt.plot(samples)
        return samples
    def set_bitfield(self, field_base_addr, field_offset, field_width, ch_num, new_val):
        m = 3 if(field_width==2) else 1
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
    def get_bitfield(self, field_base_addr, field_offset, field_width, ch_num):
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
