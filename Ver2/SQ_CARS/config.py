#This file contains top level configuration which control the number of DAC channels and ADC channels used, experiment parameters, DMA buffer parametrs, UDP streaming parameters
#config: top level config, defines verious experiment parameters

#dac_exp_config: experiment config pertaining to DAC like waveform shape, width etc.
#dac_config: LO (NCO freq), nyquist zone of operation, phase etc.
#dac_mem_config: User dont need to change
#adc_config : parameters pertaining to Readout pipeline






#2. RFDC_config: automatically populated
import numpy as np
import logging, sys
num_desc_glbl = 6

logging.basicConfig(filename='output.log', filemode='w', level=logging.INFO)
config = {"bitfile": "./bitstreams/design_1_wrapper_jun18.bit" ,
          "dac_channels": [0, 1, 2, 3, 4,5,6,7], "adc_channels": [0],
          "exp_list": [1],
          "freq_scale": "G",
          "freq_start": 4400,
          "freq_steps": 100,
          "freq_end": 4600,
          "amp_start": 6.123456,
          "amp_steps": 100,
          "amp_end": 6.323456,
          "remote_host": "192.168.1.1",
          "remote_port": {0: 503, 1: 504, 2: 505, 3: 506,}, # 4:507, 5:508, 6:509, 7:510},
          "tcp_server" : '192.168.1.99',
          "tcp_port" : 8000,
          #"adc_config": adc_config,
          #"dac_config": dac_config,
          "loopback": 0,
          "adc_dac_lat": 35, #cycles
          "trigger_delay": 0, #ns
          "trigger_width" : 4000, #4686 , #2343, #nano seconds
          "trigger_time": 0,
          "readout_dtype" : np.int64
          }

dac_mem_config = {0: {"DAC_BRAM_SIZE": 8192,
                      "DAC_CONF_ADDR": 0x00B00D0000,
                      "DAC_BRAM_I_LSB": 0x00B0000000,
                      "DAC_BRAM_I_MSB": 0x00B0100000,
                      "DAC_BRAM_Q_LSB": 0x00B0200000,
                      "DAC_BRAM_Q_MSB": 0x00B0300000},
                  1: {"DAC_BRAM_SIZE": 8192,
                      "DAC_CONF_ADDR": 0x00B0190000,
                      "DAC_BRAM_I_LSB": 0x00A0000000,
                      "DAC_BRAM_I_MSB": 0x00A0100000,
                      "DAC_BRAM_Q_LSB": 0x00A0200000,
                      "DAC_BRAM_Q_MSB": 0x00A0300000},
                  2: {"DAC_BRAM_SIZE": 8192,
                      "DAC_CONF_ADDR": 0x00B00F0000,
                      "DAC_BRAM_I_LSB": 0x00A0080000,
                      "DAC_BRAM_I_MSB": 0x00A0082000,
                      "DAC_BRAM_Q_LSB": 0x00A0084000,
                      "DAC_BRAM_Q_MSB": 0x00A0086000},
                  3: {"DAC_BRAM_SIZE": 8192,
                      "DAC_CONF_ADDR": 0x00B0180000,
                      "DAC_BRAM_I_LSB": 0x00A0088000,
                      "DAC_BRAM_I_MSB": 0x00A008A000,
                      "DAC_BRAM_Q_LSB": 0x00A008C000,
                      "DAC_BRAM_Q_MSB": 0x00A008E000},
                  }

dac_exp_config = {"power_rabi": 0,
                  "continuous": 1,  # boolean (infinite pulses or in loop mode)
                  "mode": 0,  # integer (T1=0,T2=1,Rabbi=2)
                  "repetition_rate": 300000,  # nano seconds
                  "time_between_pulses": 1000,  #in cycle now
                  #"initial_amp": 10,  # percentage of maximum
                  "trigger_delay": 0,  # nano seconds
                  "amplitude_factor": 100, # this is the initial amplitude for Power Rabi experiment
                  "amplitude_factor_direct": 100,
                  "gaussian_sigma": 768,  # in cycles now
                  "gaussian_pulse_duration": 300 , # in cycles now#1566,  # nano seconds(gaussian_pulse) 10000, #
                  "outer_loop_count": 1,  # integer
                  #"inner_loop_count": 20000,  # integer
                  "inner_loop_step": 0, # for amp incerement
                  "data_fetch_time":300000 ,#1000000000, #30 sec # in ns
                  "loopback": 1,
                  "READOUT_CHANNEL_CONF_ADDR" : dac_mem_config[0]['DAC_CONF_ADDR']+60 ,
                  "wave_type" : "gaussian"



                  }
adc_mem_config = {"IIR_CONF_MEM_SIZE": 8096,
                      "IIR_CONF_BASE_ADDR": 0x0080000000,

                  }

iir_filter_config = {"f_cutoff": 0.530, # cutoff freq in MHz
    "filter_order" : 1 , # filter order
    #"iir_mem_config" : iir_mem_config ,


}
adc_pipeline_config = { "adc_input_sel" : 0,  # 0 for diffrential, 1 for single-ended
                        "filter_bypass" : 0, # make 1 for bypassing filters
                        "theta" : 0, # 0-360 angle in degrees

}
adc_config_0 = {"fs": 3840,
                "LO freq": 10,
                "phase": 0,
                "nyquist_zone" : 1,
                #   "bram_addr": 0x00000000,
                "filter_pipeline": 1,
                "gain": 1,
                "data_type": config["readout_dtype"],
                "num_desc" : num_desc_glbl , #num of desc per channel
                "number_of_xfr" : 1, #int(dac_exp_config['outer_loop_count'] /1), #int(dac_exp_config['inner_loop_count']/num_desc_glbl), # number of outer transfer (total will be number_of_xfr * num_desc) dac_exp_config['inner_loop_count'], #
                "readout_trigger_src" : 3 , # 2 bit value to select trigger source for each adc readout pipeline
                "adc_input_sel" : 1,  # 0 for diffrential, 1 for single-ended
                "filter_bypass" : 0, # make 1 for bypassing filters
                "theta" : 0, # 0-360 angle in degrees
                "filter_config" : iir_filter_config , #IIR filter config

                }
adc_config_1 = {"fs": 3840,
                "LO freq": 10,
                "phase": 0,
                "nyquist_zone" : 1,
                #  "bram_addr": 0x00000000,
                "filter_pipeline": 1,
                "gain": 1,
                "data_type": config["readout_dtype"],
                "num_desc" : num_desc_glbl ,#num of desc per channel
                "number_of_xfr" :  int(dac_exp_config['outer_loop_count'] /1), # int(dac_exp_config['inner_loop_count']/num_desc_glbl) ,# num_desc_glbl #int (dac_exp_config['outer_loop_count']), # number of outer transfer (total will be number_of_xfr * num_desc)
                "readout_trigger_src" : 3,
                "adc_input_sel": 1,  # 0 for diffrential, 1 for single-ended
                "filter_bypass": 0,  # make 1 for bypassing filters
                "readout_rotation_angle": 0,  # 0-360 angle in degrees
                "adc_input_sel" : 0,  # 0 for diffrential, 1 for single-ended
                "filter_config" : iir_filter_config , #IIR filter config
                }
dac_mem_config = {0: {"DAC_BRAM_SIZE": 8192,
                      "DAC_CONF_ADDR": 0x00B00D0000,
                      "DAC_BRAM_I_LSB": 0x00B0000000,
                      "DAC_BRAM_I_MSB": 0x00B0100000,
                      "DAC_BRAM_Q_LSB": 0x00B0200000,
                      "DAC_BRAM_Q_MSB": 0x00B0300000},
                  1: {"DAC_BRAM_SIZE": 8192,
                      "DAC_CONF_ADDR": 0x00B0190000,
                      "DAC_BRAM_I_LSB": 0x00A0000000,
                      "DAC_BRAM_I_MSB": 0x00A0100000,
                      "DAC_BRAM_Q_LSB": 0x00A0200000,
                      "DAC_BRAM_Q_MSB": 0x00A0300000},
                  2: {"DAC_BRAM_SIZE": 8192,
                      "DAC_CONF_ADDR": 0x00B00F0000,
                      "DAC_BRAM_I_LSB": 0x00A0080000,
                      "DAC_BRAM_I_MSB": 0x00A0082000,
                      "DAC_BRAM_Q_LSB": 0x00A0084000,
                      "DAC_BRAM_Q_MSB": 0x00A0086000},
                  3: {"DAC_BRAM_SIZE": 8192,
                      "DAC_CONF_ADDR": 0x00B0180000,
                      "DAC_BRAM_I_LSB": 0x00A0088000,
                      "DAC_BRAM_I_MSB": 0x00A008A000,
                      "DAC_BRAM_Q_LSB": 0x00A008C000,
                      "DAC_BRAM_Q_MSB": 0x00A008E000},
                  }

dac_config_0 = {"fs": 6144,
                "LO freq": 10,
                "phase": 0,
                "nyquist_zone" : 1,
                #  "bram_addr": 0x00000000,
                # "filter_pipeline": 1 ,
                "gain": 1,
                "readout_channel" : 0,
                "dac_exp_config": dac_exp_config,
                "trigger_src" : 0 # onlu useful for Dac channel >3
                }
dac_config_1 = {"fs": 6144,
                "LO freq": 10,
                "phase": 0,
                "nyquist_zone" : 1,
                # "bram_addr": 0x00000000,
                # "filter_pipeline": 1,
                "gain": 1,
                "readout_channel" : 0,
                "dac_exp_config": dac_exp_config,
                "trigger_src" : 0 # onlu useful for Dac channel >3

                }
dac_config_2 = {"fs": 6144,
                "LO freq": 10,
                "phase": 0,
                "nyquist_zone" : 1,
                # "bram_addr": 0x00000000,
                # "filter_pipeline": 1,
                "gain": 1,
                "readout_channel" : 0,
                "dac_exp_config": dac_exp_config,
                "trigger_src" : 0 # onlu useful for Dac channel >3
                }
dac_config_3 = {"fs": 6144,
                "LO freq": 10,
                "phase": 0,
                "nyquist_zone" : 1,
                # "bram_addr": 0x00000000,
                # "filter_pipeline": 1,
                "gain": 1,
                "readout_channel" : 0,
                "dac_exp_config": dac_exp_config,
                "trigger_src" : 0 # onlu useful for Dac channel >3
                }
dac_config_4 = {"fs": 6144,
                "LO freq": 10,
                "phase": 0,
                "nyquist_zone" : 1,
                # "bram_addr": 0x00000000,
                # "filter_pipeline": 1,
                "gain": 1,
                "readout_channel" : 1,
                "dac_exp_config": dac_exp_config,
                "trigger_src" : 0 # onlu useful for Dac channel >3
                }

dac_config_5 = {"fs": 6144,
                "LO freq": 10,
                "phase": 0,
                "nyquist_zone" : 1,
                # "bram_addr": 0x00000000,
                # "filter_pipeline": 1,
                "gain": 1,
                "readout_channel" : 1,
                "dac_exp_config": dac_exp_config,
                "trigger_src" : 1 # onlu useful for Dac channel >3
                }
dac_config_6 = {"fs": 6144,
                "LO freq": 10,
                "phase": 0,
                "nyquist_zone" : 1,
                # "bram_addr": 0x00000000,
                # "filter_pipeline": 1,
                "gain": 1,
                "readout_channel" : 1,
                "dac_exp_config": dac_exp_config,
                "trigger_src" : 2 # onlu useful for Dac channel >3
                }
dac_config_7 = {"fs": 6144,
                "LO freq": 10,
                "phase": 0,
                "nyquist_zone" : 1,
                # "bram_addr": 0x00000000,
                # "filter_pipeline": 1,
                "gain": 1,
                "readout_channel" : 1,
                "dac_exp_config": dac_exp_config,
                "trigger_src" : 3 # onlu useful for Dac channel >3
                }

adc_config = {0: adc_config_0, 1: adc_config_1, 2: adc_config_0, 3: adc_config_1, 4: adc_config_0, 5: adc_config_1, 6: adc_config_0, 7: adc_config_1}
dac_config = {0: dac_config_0, 1: dac_config_1, 2:dac_config_2,  3:dac_config_3,4: dac_config_4, 5: dac_config_5, 6:dac_config_6,  7:dac_config_7 }

zcu111 = {'dac_tiles' : 2
          ,'adc_tiles' : 4
         }
rfdc_config = {"dac_channels": config["dac_channels"],
               "adc_channels": config["adc_channels"],
               "dac_config": dac_config,
               "adc_config": adc_config,
               "dac_mem_config": dac_mem_config,
               "adc_mem_config" : adc_mem_config,
               "zcu111" : zcu111 , 
               }

   
hw_config = {"fabric_clock": 192,  # always in MHz
             "sample per cycles": 4

             }


