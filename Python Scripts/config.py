"""
Configuration file for Quantum Control Electronics.
This script defines various configuration dictionaries for DAC, ADC, and RFDC components, 
as well as experimental and hardware settings. These configurations are used to control 
and manage the behavior of the quantum control system.
Configurations:
---------------
1. dac_mem_config:
    - Memory configuration for DAC channels.
    - Contains details such as BRAM size, configuration address, and BRAM addresses for I/Q data.
2. dac_exp_config:
    - Experimental configuration for DAC.
    - Includes parameters like mode, repetition rate, pulse duration, amplitude, and waveform type.
3. adc_mem_config:
    - Memory configuration for ADC.
    - Defines the size and base address for IIR configuration memory.
4. iir_filter_config:
    - Configuration for IIR filters.
    - Includes cutoff frequency and filter order.
5. adc_pipeline_config:
    - Configuration for ADC pipeline.
    - Specifies input selection, filter bypass, and phase angle.
6. adc_config_0, adc_config_1:
    - ADC channel-specific configurations.
    - Includes sampling frequency, LO frequency, phase, gain, and filter settings.
7. dac_config_0 to dac_config_4:
    - DAC channel-specific configurations.
    - Includes sampling frequency, LO frequency, phase, gain, and experimental settings.
8. adc_config:
    - Aggregated configuration for all ADC channels.
9. dac_config:
    - Aggregated configuration for all DAC channels.
10. rfdc_config:
        - RFDC configuration combining DAC and ADC settings.
        - Includes channel counts, memory configurations, and individual channel configurations.
11. hw_config:
        - Hardware configuration.
        - Defines fabric clock frequency and samples per cycle.
Logging:
--------
- Configures logging to output debug information to standard error.
Note:
-----
- Some configurations reference undefined variables (e.g., `config["readout_dtype"]`, `config["dac_channels"]`).
    Ensure these variables are defined elsewhere in the codebase.
"""


dac_mem_config = {0: {"DAC_BRAM_SIZE": 8096,
                      "DAC_CONF_ADDR": 0x00B00D0000,
                      "DAC_BRAM_I_LSB": 0x00B0000000,
                      "DAC_BRAM_I_MSB": 0x00B0100000,
                      "DAC_BRAM_Q_LSB": 0x00B0200000,
                      "DAC_BRAM_Q_MSB": 0x00B0300000},
                  1: {"DAC_BRAM_SIZE": 8096,
                      "DAC_CONF_ADDR": 0x00B0190000,
                      "DAC_BRAM_I_LSB": 0x00A0000000,
                      "DAC_BRAM_I_MSB": 0x00A0100000,
                      "DAC_BRAM_Q_LSB": 0x00A0200000,
                      "DAC_BRAM_Q_MSB": 0x00A0300000},
                  2: {"DAC_BRAM_SIZE": 8096,
                      "DAC_CONF_ADDR": 0x00B00F0000,
                      "DAC_BRAM_I_LSB": 0x00A0080000,
                      "DAC_BRAM_I_MSB": 0x00A0082000,
                      "DAC_BRAM_Q_LSB": 0x00A0084000,
                      "DAC_BRAM_Q_MSB": 0x00A0086000},
                  3: {"DAC_BRAM_SIZE": 8096,
                      "DAC_CONF_ADDR": 0x00B0180000,
                      "DAC_BRAM_I_LSB": 0x00A0088000,
                      "DAC_BRAM_I_MSB": 0x00A008A000,
                      "DAC_BRAM_Q_LSB": 0x00A008C000,
                      "DAC_BRAM_Q_MSB": 0x00A008E000},
                  }

dac_exp_config = {"power_rabi": 0,
                  "continuous": 1,  # boolean (infinite pulses or in loop mode)
                  "mode": 2,  # integer (T1=0,T2=1,Rabbi=2)
                  "repetition_rate": 10000,  # nano seconds
                  "time_between_pulses": 120,  # nano seconds
                  "initial_amp": 100,  # percentage of maximum
                  "trigger_delay": 0,  # nano seconds
                  "amplitude_factor": 100,
                  "amplitude_factor_direct": 100,
                  "gaussian_sigma": 500,  # nano seconds
                  "gaussian_pulse_duration": 5000,  # nano seconds(gaussian_pulse)
                  "outer_loop_count": 50,  # integer
                  "inner_loop_count": 10,  # integer
                  "inner_loop_step": 7.8125,
                  "data_fetch_time": 0,  # in ms
                  "loopback": 0,
                  "READOUT_CHANNEL_CONF_ADDR": dac_mem_config[0]['DAC_CONF_ADDR'] + 60
                  "wave_type" : "gaussian"
                  }
adc_mem_config = {"IIR_CONF_MEM_SIZE": 8096,
                  "IIR_CONF_BASE_ADDR": 0x0080000000,

                  }

iir_filter_config = {"f_cutoff": 1,  # cutoff freq in MHz
                     "filter_order": 3,  # filter order
                     # "iir_mem_config" : iir_mem_config ,

                     }
adc_pipeline_config = {"adc_input_sel": 0,  # 0 for diffrential, 1 for single-ended
                       "filter_bypass": 0,  # make 1 for bypassing filters
                       "theta": 0,  # 0-360 angle in degrees

                       }
adc_config_0 = {"fs": 4.096,
                "LO freq": 100,
                "phase": 0,
                #   "bram_addr": 0x00000000,
                "filter_pipeline": 1,
                "gain": 1,
                "data_type": config["readout_dtype"],
                "num_desc": 16,  # num of desc per channel
                "readout_trigger_src": 0,  # 2 bit value to select trigger source for each adc readout pipeline
                "adc_input_sel": 0,  # 0 for diffrential, 1 for single-ended
                "filter_bypass": 0,  # make 1 for bypassing filters
                "theta": 0,  # 0-360 angle in degrees
                "filter_config": iir_filter_config,  # IIR filter config
                }
adc_config_1 = {"fs": 4.096,
                "LO freq": 100,
                "phase": 0,
                #  "bram_addr": 0x00000000,
                "filter_pipeline": 1,
                "gain": 1,
                "data_type": config["readout_dtype"],
                "num_desc": 16,  # num of desc per channel
                "readout_trigger_src": 1,
                "adc_input_sel": 0,  # 0 for diffrential, 1 for single-ended
                "filter_bypass": 0,  # make 1 for bypassing filters
                "theta": 0,  # 0-360 angle in degrees
                "adc_input_sel": 0,  # 0 for diffrential, 1 for single-ended
                "filter_config": iir_filter_config,  # IIR filter config
                }
dac_mem_config = {0: {"DAC_BRAM_SIZE": 8096,
                      "DAC_CONF_ADDR": 0x00B00D0000,
                      "DAC_BRAM_I_LSB": 0x00B0000000,
                      "DAC_BRAM_I_MSB": 0x00B0100000,
                      "DAC_BRAM_Q_LSB": 0x00B0200000,
                      "DAC_BRAM_Q_MSB": 0x00B0300000},
                  1: {"DAC_BRAM_SIZE": 8096,
                      "DAC_CONF_ADDR": 0x00B0190000,
                      "DAC_BRAM_I_LSB": 0x00A0000000,
                      "DAC_BRAM_I_MSB": 0x00A0100000,
                      "DAC_BRAM_Q_LSB": 0x00A0200000,
                      "DAC_BRAM_Q_MSB": 0x00A0300000},
                  2: {"DAC_BRAM_SIZE": 8096,
                      "DAC_CONF_ADDR": 0x00B00F0000,
                      "DAC_BRAM_I_LSB": 0x00A0080000,
                      "DAC_BRAM_I_MSB": 0x00A0082000,
                      "DAC_BRAM_Q_LSB": 0x00A0084000,
                      "DAC_BRAM_Q_MSB": 0x00A0086000},
                  3: {"DAC_BRAM_SIZE": 8096,
                      "DAC_CONF_ADDR": 0x00B0180000,
                      "DAC_BRAM_I_LSB": 0x00A0088000,
                      "DAC_BRAM_I_MSB": 0x00A008A000,
                      "DAC_BRAM_Q_LSB": 0x00A008C000,
                      "DAC_BRAM_Q_MSB": 0x00A008E000},
                  }

dac_config_0 = {"fs": 4.096,
                "LO freq": 200,
                "phase": 0,
                #  "bram_addr": 0x00000000,
                # "filter_pipeline": 1 ,
                "gain": 1,
                "readout_channel": 0,
                "dac_exp_config": dac_exp_config
                }
dac_config_1 = {"fs": 4.096,
                "LO freq": 200,
                "phase": 0,
                # "bram_addr": 0x00000000,
                # "filter_pipeline": 1,
                "gain": 1,
                "readout_channel": 0,
                "dac_exp_config": dac_exp_config
                }
dac_config_2 = {"fs": 4.096,
                "LO freq": 200,
                "phase": 0,
                # "bram_addr": 0x00000000,
                # "filter_pipeline": 1,
                "gain": 1,
                "readout_channel": 0,
                "dac_exp_config": dac_exp_config
                }
dac_config_3 = {"fs": 4.096,
                "LO freq": 200,
                "phase": 0,
                # "bram_addr": 0x00000000,
                # "filter_pipeline": 1,
                "gain": 1,
                "readout_channel": 0,
                "dac_exp_config": dac_exp_config
                }
dac_config_4 = {"fs": 4.096,
                "LO freq": 200,
                "phase": 0,
                # "bram_addr": 0x00000000,
                # "filter_pipeline": 1,
                "gain": 1,
                "readout_channel": 1,
                "dac_exp_config": dac_exp_config
                }

adc_config = {0: adc_config_0, 1: adc_config_1}
dac_config = {0: dac_config_0, 1: dac_config_1, 2: dac_config_2, 3: dac_config_3}

rfdc_config = {"dac_channels": config["dac_channels"],
               "adc_channels": config["adc_channels"],
               "dac_config": dac_config,
               "adc_config": adc_config,
               "dac_mem_config": dac_mem_config,
               "adc_mem_config": adc_mem_config,
               }
hw_config = {"fabric_clock": 128,  # always in MHz
             "sample per cycles": 4

             }

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)