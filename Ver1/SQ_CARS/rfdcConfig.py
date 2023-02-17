#Class defination for the main configuration and the board (RF Data converter)

import numpy 
import xrfdc
import xrfclk
#from pynq import Xlnk
from pynq import Overlay
from pynq.lib import AxiGPIO
from pynq import allocate
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
from dacConfig import *
from adcConfig import *
from utility_classes import *
class mainConfig():
    def __init__(self, config):
        self.bitfile = config["bitfile"]

        self.exp_list = config["exp_list"]
        if (config["freq_scale"] == "G"):  # Giga Hz
            self.freq_scale = numpy.power(10, 9)
        elif (config["freq_scale"] == "M"):  # Mega Hz
            self.freq_scale = numpy.power(10, 6)
        elif (config["freq_scale"] == "K"):  # Kilo Hz
            self.freq_scale = numpy.power(10, 3)
        else:  # Hz
            self.freq_scale = 1

        self.freq_start = config["freq_start"]
        self.freq_steps = config["freq_steps"]
        self.freq_stop = config["freq_end"]
        self.freq_inc = self.freq_stop - self.freq_start / self.freq_steps

        self.amp_start = config["amp_start"]
        self.amp_steps = config["amp_steps"]
        self.amp_stop = config["amp_end"]

        self.remote_host = config["remote_host"]
        self.remote_port = config["remote_port"]

        ######## Few parameters , need to find fitting location for them letter

        ## Readout params
        self.trigger_delay = config["trigger_delay"]
        self.trigger_width = config["trigger_width"]
        self.trigger_time = config["trigger_time"]
        self.adc_dac_lat = config["adc_dac_lat"]
        self.dma_trf_done_flag = [0, 0, 0, 0, 0, 0, 0, 0]

        # Streaming params
        self.remote_port = []
        k=0
        for i in range(4):
            logging.debug('val of i is %d', i)
            self.remote_port.append(config["remote_port"][i])
            logging.debug('Port added %d for adc channel %d', self.remote_port[k], i)
            k = k + 1




class rfdcConfig():
    def __init__(self, top_config, rfdc_config, hw_config):
        ## assign BRAM address
        # self.dac_bram_addr[] = dac_mem_config
        self.top_config = top_config
        self.o1 = Overlay(top_config.bitfile)
        self.rf = self.o1.usp_rf_data_converter_0
        self.board = 'zcu111'
        self.dac_channels = rfdc_config["dac_channels"]
        self.adc_channels = rfdc_config["adc_channels"]
        self.dac_tiles = 2 #rfdc_config[self.board][dac_tiles]
        self.adc_tiles = 4 #rfdc_config[self.board][adc_tiles]
        self.dac_id = []
        self.adc_id = []
        self.dac = []
        self.readout = []
        for i in range(len(self.dac_channels)):
            self.dac_id.append(self.dac_channels[i])
            ch_t = self.dac_channels[i]
            self.dac.append(dac(self.rf, ch_t, rfdc_config["dac_config"][ch_t], rfdc_config["dac_mem_config"][int(ch_t%4)], self.top_config, hw_config))
        for i in range(len(self.adc_channels)):
            self.adc_id.append(self.adc_channels[i])
            ch_t = self.adc_channels[i]
            self.readout.append(Readout(self.rf, ch_t, rfdc_config["adc_config"][ch_t], rfdc_config["adc_mem_config"], self.top_config, self.o1, hw_config))
        try:
            self.init_MTS()
        except:
            print("Unable to complete MTS sucessfully");
            print("Re-running the MTS")
            try:
                self.init_MTS()
            except:
                print("Unable to complete MTS sucessfully in even 2nd Run, Please check and reprogramm clocks")
    def init_MTS(self):
        (lat_dac_t0, lat_dac_t1) = self.rf.dac_tiles[0].dacMTS(3)
        (lat_adc_t0, lat_adc_t1, lat_adc_t2, lat_adc_t3) = self.rf.adc_tiles[0].adcMTS(0x1f)
        max_dac_lat = max(lat_dac_t0, lat_dac_t1) + (16)
        max_adc_lat = max(lat_adc_t0, lat_adc_t1, lat_adc_t2, lat_adc_t3) + (16)
        for i in range(self.dac_tiles):
            self.rf.dac_tiles[i].dacMTSwl(3,max_dac_lat)
        for i in range(self.adc_tiles):
            self.rf.adc_tiles[i].adcMTSwl(0x1f,max_adc_lat)
    def run_MTS(self):
        for i in range(self.dac_tiles):
            self.rf.dac_tiles[i].sysref_enable(0)
        for i in range(self.adc_tiles):
            self.rf.adc_tiles[i].sysref_enable(0)
        sleep(0.2)
        for i in range(self.dac_tiles):
            self.rf.dac_tiles[i].sysref_enable(1)
        for i in range(self.adc_tiles):
            self.rf.adc_tiles[i].sysref_enable(1)
        sleep(0.2)
        for i in range(self.dac_tiles):
            self.rf.dac_tiles[i].sysref_enable(0)
        for i in range(self.adc_tiles):
            self.rf.adc_tiles[i].sysref_enable(0)


# class gen_waveform(top_config):
#     def __init__(self, config):
#         self.fabric_clock = self.pl_freq
#         self.sample_per_clock = self.


