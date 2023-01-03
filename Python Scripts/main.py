config = {"bitfile": "./design_1_wrapper_2Jan.bit",
          "dac_channels": [0, 1, 2], "adc_channels": [0],
          "exp_list": [1],
          "freq_scale": "G",
          "freq_start": 6.123456,
          "freq_steps": 100,
          "freq_end": 6.323456,
          "amp_start": 6.123456,
          "amp_steps": 100,
          "amp_end": 6.323456,
          "remote_host": "192.168.1.1",
          "remote_port": {0: 503, 1: 504, 2: 505, 3: 506},
          # "adc_config": adc_config,
          # "dac_config": dac_config,
          "loopback": 1,
          "adc_dac_lat": 0,
          "trigger_delay": 0,
          "trigger_width": 600,
          "trigger_time": 0,
          "readout_dtype": np.uint64
          }

if __name__ == '__main__':
    thisConfig = mainConfig(config)
    rfdc_handle = rfdcConfig(thisConfig, rfdc_config, hw_config)
    u_obj = utility_functions(hw_config)
    for i in (rfdc_handle.dac_channels):
        print(i)
        w1_I = u_obj.gen_wave(config, dac_exp_config["wave_type"], dac_exp_config["gaussian_pulse_duration"],
                              dac_exp_config["gaussian_sigma"], 1)
        w1_Q = u_obj.gen_wave(config, "zero", dac_exp_config["gaussian_pulse_duration"],
                              dac_exp_config["gaussian_sigma"], 1)
        rfdc_handle.dac[i].load_wave(w1_I, w1_Q)
    rfdc_handle.dac[0].set_param('rst', 1, "None")
    rfdc_handle.dac[0].set_param('update', 1, "None")
    rfdc_handle.dac[0].set_param('rst', 0, "None")
    rfdc_handle.dac[0].set_param('update', 1, "None")


