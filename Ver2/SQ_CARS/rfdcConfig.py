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
import ipywidgets as widgets
from IPython.display import display, clear_output
from tqdm import tqdm

from dacConfig import *
from adcConfig import *
from utility_classes import *
import config
class mainConfig():
    def __init__(self, config):
        self.bitfile = config["bitfile"]

        

        self.remote_host = config["remote_host"]
        self.remote_port = config["remote_port"]

        ######## Few parameters , need to find fitting location for them letter

        ## Readout params
        self.trigger_delay = config["trigger_delay"]
        self.trigger_width = config["trigger_width"]
        self.trigger_time = config["trigger_time"]
        self.adc_dac_lat = config["adc_dac_lat"]
        

        # Streaming params
        self.remote_port = []
        k=0
        for i in range(4):
            #logging.debug('val of i is %d', i)
            self.remote_port.append(config["remote_port"][i])
            #logging.debug('Port added %d for adc channel %d', self.remote_port[k], i)
            k = k + 1

        try:
            self.o1 = Overlay(self.bitfile)
            logging.info('Loading Bitstream %s ', self.bitfile )
        except:
            logging.error('Bitfile %s Ovelay could not be loaded',self.bitfile  )


class rfdcConfig():
    def __init__(self, u_obj, rfdc_config = config.rfdc_config, hw_config=config.hw_config):
        ## assign BRAM address
        # self.dac_bram_addr[] = dac_mem_config
        
        self.u_obj = u_obj
        self.top_config = self.u_obj.thisConfig #(config.config) #top_config
#         if (u_obj._load_bitstream==0):
#             logging.info(' Bitstream %s already loaded, not reloading', self.top_config.bitfile )
#             #print("Hi")
#         else:
#             try:
#                 self.o1 = Overlay(self.top_config.bitfile)
#                 logging.info('Loading Bitstream %s ', self.top_config.bitfile )
#             except:
#                 logging.error('Bitfile %s Ovelay could not be loaded',self.top_config.bitfile  )
        
            #logging.debug('to reload the bitstream, either restart the kernel or delete self.o1')
        self.o1 = self.top_config.o1
        self.rf = self.o1.usp_rf_data_converter_0
        self.board = 'zcu111'
        self.dac_channels = rfdc_config["dac_channels"]
        self.adc_channels = rfdc_config["adc_channels"]
        self.dac_tiles = rfdc_config[self.board]['dac_tiles']
        self.adc_tiles = rfdc_config[self.board]['adc_tiles']
        self.dac_id = []
        self.adc_id = []
        self.dac = []
        self.readout = []
        self._stop_task = False
        self._stop_lock = threading.Lock()

# Global flag to indicate whether the task should stop



        for i in range(len(self.dac_channels)):
            self.dac_id.append(self.dac_channels[i])
            ch_t = self.dac_channels[i]
            self.dac.append(dac(self.rf, ch_t, rfdc_config["dac_config"][ch_t], rfdc_config["dac_mem_config"][int(ch_t%4)], self.top_config, hw_config, self.u_obj))
        for i in range(len(self.adc_channels)):
            self.adc_id.append(self.adc_channels[i])
            ch_t = self.adc_channels[i]
            self.readout.append(Readout(self.rf, ch_t, rfdc_config["adc_config"][ch_t], rfdc_config["adc_mem_config"], self.top_config, self.o1, hw_config, self.u_obj))
        try:
            self.init_MTS()
        except:
            logging.info("Unable to complete MTS sucessfully");
            logging.info("Re-running the MTS")
            try:
                self.init_MTS()
            except:
                logging.error("Unable to complete MTS sucessfully in even 2nd Run, Please check and reprogramm clocks")
        self.find_common_freq()
        self.dac[0].set_param('update', 1, "None")
        self.gauss_the_boss = self.o1.ip_dict['gaussian_block_control']
        self.gauss_the_boss_reset = AxiGPIO(self.gauss_the_boss).channel1
        self.gauss_the_boss_curr_state = AxiGPIO(self.gauss_the_boss).channel2
        self.readout[0].set_readout_update(1)
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
    def update_all(self):
        self.update_freq()
        self.update_phase()
        self.update_mode()
        self.update_amplitude()
        self.update_readout_amplitude()
        self.update_readout_channel()
        self.update_loopback()
        self.update_inner_loop_count()
        
    def set_readout_rotation(self, ch):
        #for i in (self.adc_channels):
        quad = int(self.u_obj._readout_rotation_angle/90)
        theta = self.u_obj._readout_rotation_angle//4
        self.readout[ch].set_adc_quad(quad)
        self.readout[ch].set_adc_theta(theta)
        
    def update_freq(self):
        for i in(self.dac_channels):
            self.dac[i].set_nco_freq(self.u_obj._freq_list[i][0])
            self.dac[i]._nyquist_zone= 2 if(self.dac[i]._nco_freq[0] > (self.dac[i]._fs/2)) else 1
            self.dac[i].set_nyquist_zone(self.dac[i]._nyquist_zone)
        for i in (self.adc_channels):
            self.readout[i].set_nco_freq(self.u_obj._readout_freq[0])
            self.readout[i]._nyquist_zone = 2 if(self.readout[i]._nco_freq[0] > (self.readout[i]._fs/2)) else 1
            self.readout[i].set_nyquist_zone(self.readout[i]._nyquist_zone)
            
        self.run_MTS()
    def update_phase(self):
        for i in(self.dac_channels):
            self.dac[i].set_nco_phase(self.u_obj._phase_list[i])
#         for i in range(self.adc_channels):
#             self.readout[i].set_nco_phase(u_obj.phase_list[i])
        self.run_MTS()
    def update_mode(self):
        for i in(self.dac_channels):
            self.dac[i].set_param('mode',self.u_obj._mode_list[int(i%4)], 'None')
    def update_amplitude(self):
        for i in(self.dac_channels):
            self.dac[i].set_param('amplitude_factor_direct', self.u_obj._control_amplitude_list[int(i%4)], 'scale')
    def update_readout_amplitude(self):
        for i in(self.dac_channels):
            self.dac[i].set_param('trigger_scaled_value', self.u_obj._readout_amplitude_list[int(i%4)], 'scale')
    def update_readout_channel(self):
        for i in(self.dac_channels):
            self.dac[i].set_readout_channel(self.u_obj._readout_channel_list[i])
    def update_loopback(self):
        for i in(self.dac_channels):
            if(self.u_obj._loopback[i%4] ==1):
                self.dac[i].set_param('gaussian_width', 0 ,'None')
            else:
                self.dac[i].set_param('gaussian_width', (self.u_obj._num_of_pulses*self.u_obj._wave_len)+ self.u_obj._start_time_bw_pulses, 'None')
    def update_inner_loop_count(self):
        for i in (self.adc_channels):
            self.dac[i].set_param('inner_loop_count', self._num_of_averages[0], 'None')
            
    def find_common_freq(self):
        rdout_dac_idx = self.u_obj._readout_channel_list.index(1)
        self._ff = self.u_obj._readout_freq[0]
        logging.info("in find_common_freq and inital readout freq is %d", self._ff)
        itrs =0;
        self.freq_nums = []
        self.diff = []
        while(True):
            self.dac[rdout_dac_idx].set_nco_freq(self._ff)
            self.readout[0].set_nco_freq(self._ff)
            b=self.readout[0]._adc_handle.MixerSettings['Freq']
            a=self.dac[rdout_dac_idx]._dac_handle.MixerSettings['Freq']
            logging.debug("current iteration for common freq search is %d and %.15f, %.15f", itrs, a, b)
            self.freq_nums.append(self._ff)
            self.diff.append(a-b)
            if((a-b)==0):
                logging.info("found common freq to be %.15f and the diff from original freq is %.15f ", self._ff, self._ff - self.u_obj._readout_freq[0])
                self.u_obj._readout_freq[0] = a
                break;
            self._ff+=0.00000000007
            itrs+=1
        print('freq_list', self.u_obj._readout_freq[0], self.u_obj._freq_list)
        self.update_freq()
        #self.run_MTS()
        
                
    def disable_gaussian(self):
        for i in(self.dac_channels):
            self.dac[i].set_param('start_gaussian', 0, "None")
            self.dac[i].set_param('wakeup', 0, "None")
    def enable_gaussian(self):
        for i in(self.dac_channels):
            self.dac[i].set_param('start_gaussian', 1, "None")
            self.dac[i].set_param('wakeup', 1, "None")
   

    
        
    def change_time_bw_pulses(self, t_b_p, d):    
        #print(t_b_p)
        #for i in(self.dac_channels):
        self.dac[d].set_param("time_between_pulses", t_b_p, 'None') #_exp_config._config[key]['val']
            
        if(self.u_obj._loopback[0] ==1):
            self.dac[d].set_param('gaussian_width', 0 ,'None')
        else:
            self.dac[d].set_param('gaussian_width', (self.u_obj._num_of_pulses*self.u_obj._wave_len)+ t_b_p, 'None')
               
    def update_param_exp(self, val) :
        experiment_type= self.u_obj._exp_type[0]
        w1_I = 0
        if(experiment_type == 'power_rabi'):
            for d in (self.dac_channels):
                self.dac[d].set_param('amplitude_factor_direct', val, "scale")
                #print('changed control dac (all T0) power to', val)
        elif(experiment_type == 'T1'):
            for d in (self.dac_channels):
                self.dac[d].set_param('trigger_delay', val, 'None')
                #print('changed trigger delay to ', val)
        elif(experiment_type == 'T2'):
             for d in (self.dac_channels):
                self.change_time_bw_pulses(val, d) # 2 gaussian pulses
                #print('changed time between pulses to for T2 ', val, 'cycles')
        elif(experiment_type== 'time_rabi'):
            for d in (self.dac_channels):
                self.change_time_bw_pulses(val, d) # only 1 gaussian pulse
                #print('changed time between pulses to ', val, 'cycles')
        elif(experiment_type== 'power_rabi_2pulses'):
            for d in (self.dac_channels):
                self.dac[d].set_param('amplitude_factor_direct', val, "scale")
               
        elif(experiment_type== 'spectroscopy'):
            self.u_obj._readout_freq[0] = val;
            self.find_common_freq()
        
        return w1_I
    def stop_task_execution(self):
    #global stop_task
        with self._stop_lock:
            self._stop_task = True
    def run_exp(self):
#         self.output = []
        #self._progress_bar = tqdm(total=self.u_obj._exp_steps)
    
        self.disable_gaussian()
        exp_prog_val=self.u_obj._exp_start_val
        for e in range(self.u_obj._exp_steps[0]): #exp_steps):
            #print('Enter to contiue')
            #input("press to continue")
            if(self._stop_task ==1):
                logging.info('Existing the run_exp task on stop request')
                sys.exit();
            itrs = 1; 
            self.update_param_exp(exp_prog_val)
            while(itrs >0):
                #print('experimental parameter', exp_prog_val, 'in itr', e)
                for k in (self.adc_channels):
                    self.readout[k]._dma.init_dma()
                    self.readout[k].init_streamer(self.dac[k]._exp_config._config['mode']['val'], self.dac[k].get_param('power_rabi'))
                self.enable_gaussian()

                for k in (self.adc_channels):
                    self.readout[k].dma_streamer_thread(e)
                logging.debug("closed sucessfully DMA for channel %d", k)
                #message = "closed sucessfully DMA for channel {k}"
                #self.output.append(message)
                self.disable_gaussian()
                
                while((self.gauss_the_boss_curr_state.read() & 0x1f) != 0x7):
                    time.sleep(0)
                itrs-=1;
            time.sleep(1)

            #self._progress_bar.update(1)
            #self._progress_bar.set_postfix({'Progress': f'{item+1}/{len(data)}'})
            logging.info("Comleted %d / %d  iteration and the value of param is %.4f for experiment %s", e, self.u_obj._exp_steps[0], exp_prog_val, self.u_obj._exp_type)
            #message= f"Comleted {e} iteration and the value of param is {exp_prog_val} for experiment {self.u_obj._exp_type}"
            #self.output.append(message)
            exp_prog_val += self.u_obj._exp_inc_val
        logging.info('Completed the experiment')
        print("Experiment ", self.u_obj._exp_type,  "Completed")
# class gen_waveform(top_config):
#     def __init__(self, config):
#         self.fabric_clock = self.pl_freq
#         self.sample_per_clock = self.

    def create_slider_widget(self):
# Define the callback functions for each slider


        self._slider_ch_num = 0
        def slider1_callback(value):
            with slider1_output:
                clear_output(wait=True)
                new_value = value['new']
                print(f"Amplitude: {new_value} for channel {self._slider_ch_num}")
                self.dac[self._slider_ch_num].set_param('amplitude_factor_direct', new_value, 'scale')

        def slider2_callback(value):
            with slider2_output:
                clear_output(wait=True)
                new_value = value['new']
                print(f"Phase: {new_value}")
                self.dac[self._slider_ch_num].set_nco_phase(new_value)
                self.run_MTS()

        def slider3_callback(value):
            with slider3_output:
                clear_output(wait=True)
                new_value = value['new']
                quad = int(new_value/90)
                theta = new_value//4
                print(f"Rotation: {new_value}")
                self.readout[0].set_adc_quad(quad)
                self.readout[0].set_adc_theta(theta)

        def slider4_callback(value):
            with slider4_output:
                clear_output(wait=True)
                new_value = value['new']
                print(f"Readout Amplitude: {new_value}")
                self.dac[self._slider_ch_num].set_param('amplitude_factor_direct', new_value, 'scale')
                self.dac[self._slider_ch_num].set_param('trigger_scaled_value', new_value, 'scale')

        #         # Define the callback function for the button
        #         def button_callback(button):
        #             input_number = int(number_input.value)
        #             if 0 <= input_number <= 7:  # Define the desired number limit
        #                 with number_output:
        #                     clear_output(wait=True)
        #                     self._slider_ch_num = input_number
        #                     print("Channel number: ", input_number)
        #             else:
        #                 with number_output:
        #                     clear_output(wait=True)
        #                     print("Invalid input. Please enter a number between 0 and 7")
        def number_dropdown_callback(button):
            input_number = int(number_dropdown.value)
            if 0 <= input_number <= 7:  # Define the desired number limit
                with number_output:
                    clear_output(wait=True)
                    self._slider_ch_num = input_number
                    print("Channel Number:", input_number)
            else:
                with number_output:
                    clear_output(wait=True)
                    print("Invalid input. Please select a number between 0 and 7")

        # Define the callback function for the string button
        def string_dropdown_callback(button):
            input_string = str(string_dropdown.value)
            with string_output:
                clear_output(wait=True)
                print("Experiment Type: (Mode/Exp Type Changes for all channels)", input_string)
                self.u_obj._exp_type[0] = input_string
                self.u_obj.cal_exp_params()
                self.update_mode()
        def number1_dropdown_callback(button):
            input_number = int(number1_dropdown.value)
            with number1_output:
                clear_output(wait=True)
                self.dac[self._slider_ch_num].set_readout_channel(input_number)
                ss = 'Readout Ch' if (input_number ==1) else 'Control Ch'
                print("Channel Number:", self._slider_ch_num, " is" , ss, "now")
        def loopback_dropdown_callback(button):
            input_number = int(number1_dropdown.value)
            with loopback_output:
                clear_output(wait=True)
                #self.dac[self._slider_ch_num].set_readout_channel(input_number)
                if(self._slider_ch_num>3):
                    ss = f'Given channel no is {self._slider_ch_num} but this will update channel no {self._slider_ch_num%4} '


                else:
                    ss = 'in loopback' if (input_number ==1) else 'not in loopback'
                print("Loopback Channel Number:", self._slider_ch_num,  ss)

                self.u_obj._loopback[self._slider_ch_num%4] = input_number
                self.update_loopback()
        def input_number1_callback(value):
                with input_number1_output:
                    clear_output(wait=True)
                    new_value = value['new']
                    config.start_num[0] = new_value
                    self.u_obj.cal_exp_params()
                    print(f"Start number for exp is: {new_value}")
                    # Perform desired actions with new_value

        def input_number2_callback(value):
            with input_number2_output:
                clear_output(wait=True)
                new_value = value['new']
                config.end_num[0] = new_value
                self.u_obj.cal_exp_params()
                print(f"End number for exp is: {new_value}")
                    # Perform desired actions with new_value
        def input_exp_steps_callback(value):
            with input_exp_steps_output:
                clear_output(wait=True)
                new_value = value['new']
                config.exp_steps[0] = new_value
                self.u_obj.cal_exp_params()
                print(f"Experment Steps are : {new_value}")

        # Create the slider descriptions with long names
        slider1_label = widgets.Label(value='Control Ch Amplitude Scale:')
        slider2_label = widgets.Label(value='Control Ch Phase Scale2 (in Degrees):')
        slider3_label = widgets.Label(value='Readout Rotation angle (in Degrees):')
        slider4_label = widgets.Label(value='Readout Ch Amplitude Scale:')

        # Create the sliders
        slider1 = widgets.FloatSlider(min=0, max=100, step=0.1, value = self.dac[self._slider_ch_num].get_param('amplitude_factor_direct') )
        slider2 = widgets.FloatSlider(min=0, max=179, step=1, value = self.dac[self._slider_ch_num]._nco_phase)
        slider3 = widgets.FloatSlider(min=0, max=360, step=1, value = self.readout[0].get_adc_theta() )
        slider4 = widgets.FloatSlider(min=0, max=100, step=0.1, value = self.dac[self._slider_ch_num].get_param('trigger_scaled_value'))


        # Register the callbacks to the slider events
        slider1.observe(slider1_callback, 'value')
        slider2.observe(slider2_callback, 'value')
        slider3.observe(slider3_callback, 'value')
        slider4.observe(slider4_callback, 'value')

        # Create the number input field and button
        #         number_input = widgets.IntText(description='Number:', min=0, max=100)  # Set the desired number limits
        #         button = widgets.Button(description='Submit')
        #         button.on_click(button_callback)

        # Create the number dropdown menu
        number_values = list(range(8))  # Define the range of numbers
        number_dropdown = widgets.Dropdown(options=number_values, description='Channel Number:')
        number_dropdown.observe(number_dropdown_callback, 'value')
        # Create the string dropdown menu
        string_values = ['power_rabi', 'time_rabi', 'T1', 'T2', 'cw', 'power_rabi_2pulses', 'spectroscopy']  # Define the predefined string values
        string_dropdown = widgets.Dropdown(options=string_values, description='Exp Type:', value = self.u_obj._exp_type[0])
        string_dropdown.observe(string_dropdown_callback, 'value')
         # Create the string dropdown menu for readout channel
        number1_values = list(range(2))  # Define the range of numbers
        number1_dropdown = widgets.Dropdown(options=number1_values, description='Is Readout ?', value = self.u_obj._readout_channel_list[self._slider_ch_num])
        number1_dropdown.observe(number1_dropdown_callback, 'value')
        #Create loopback dropdown
        loopback_values = list(range(2))  # Define the range of numbers
        loopback_dropdown = widgets.Dropdown(options=loopback_values, description='Is Loopback ?', value = self.u_obj._readout_channel_list[self._slider_ch_num])
        loopback_dropdown.observe(loopback_dropdown_callback, 'value')

        input_number1 = widgets.IntText(description='start_num:', value = config.start_num[0])
        input_number2 = widgets.IntText(description='end_num:', value = config.end_num[0])
        input_exp_steps = widgets.IntText(description='exp_steps:', value = config.exp_steps[0])

        input_number1.observe(input_number1_callback, 'value')
        input_number2.observe(input_number2_callback, 'value')
        input_exp_steps.observe(input_exp_steps_callback, 'value')
        # Create output widgets
        slider1_output = widgets.Output()
        slider2_output = widgets.Output()
        slider3_output = widgets.Output()
        slider4_output = widgets.Output()
        number_output = widgets.Output()
        string_output = widgets.Output()
        number1_output = widgets.Output()
        loopback_output  = widgets.Output()
        input_number1_output=widgets.Output()
        input_number2_output=widgets.Output()
        input_exp_steps_output=widgets.Output()


        # Create layout containers
        slider_box = widgets.VBox([slider1_label, slider1, slider2_label, slider2, slider3_label, slider3, slider4_label, slider4])
        output_box = widgets.VBox()
        input_box = widgets.VBox([ number_dropdown, loopback_dropdown, string_dropdown, number1_dropdown, input_number1, input_number2, input_exp_steps])
        #output_area = widgets.VBox()
        output_area = widgets.VBox([slider1_output, slider2_output, slider3_output, slider4_output])




        # Display the layout containers and output widgets
        display(widgets.HBox([input_box, widgets.VBox([number_output, string_output, number1_output, loopback_output, input_number1_output, input_number2_output,input_exp_steps_output ])]), output_box, slider_box, output_area)
