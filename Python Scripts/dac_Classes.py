
class dac_populate_exp_config(utility_functions):
    def __init__(self, exp_config, conf, hw_config):
        super().__init__(hw_config)
        # self._config = []

        self._config = {"sleep_time": {'addr': 0, 'val': self.ns_to_cycles(exp_config["data_fetch_time"])}}
        self._config["time_between_pulses"] = {'addr': 4, 'val': self.ns_to_cycles(exp_config["time_between_pulses"])}
        self._config["trigger_time"] = {'addr': 8, 'val': conf.trigger_time}
        self._config["inner_loop_step"] = {'addr': 12, 'val': self.ns_to_cycles(exp_config["inner_loop_step"])}
        self._config["inner_loop_count"] = {'addr': 16, 'val': exp_config["inner_loop_count"]}
        self._config["repetition_rate"] = {'addr': 20, 'val': self.ns_to_cycles(exp_config["repetition_rate"])}
        self._config["outer_loop_count"] = {'addr': 24, 'val': exp_config["outer_loop_count"]}
        self._config["amplitude_factor"] = {'addr': 28, 'val': round(
            exp_config["amplitude_factor"] * ((np.power(2, 15) - 1) / 100))}
        self._config["n_s_4"] = {'addr': 32,
                                 'val': self.cal_n_s(self.ns_to_cycles(exp_config["gaussian_pulse_duration"]),
                                                     exp_config['mode'])}
        self._config["gaussian_width"] = {'addr': 36, 'val': 0 if (exp_config["loopback"] == 1) else self.ns_to_cycles(
            exp_config["gaussian_pulse_duration"])}
        self._config["adc_dac_lat"] = {'addr': 40, 'val': conf.adc_dac_lat}
        self._config["trigger_delay"] = {'addr': 44, 'val': conf.trigger_delay}
        self._config["trigger_width"] = {'addr': 48, 'val': conf.trigger_width}
        self._config["power_rabi"] = {'addr': 100, 'val': exp_config["power_rabi"]}
        self._config["mode"] = {'addr': 100, 'val': exp_config["mode"]}
        self._config["continuous"] = {'addr': 100, 'val': exp_config["continuous"]}
        self._config["gaussian_arb_bar"] = {'addr': 100, 'val': 0 if (self._config["mode"]['val'] >= 3) else 1}
        self._config["amplitude_factor_direct"] = {'addr': None, 'val': round(
            exp_config["amplitude_factor_direct"] * ((np.power(2, 15) - 1) / 100))}
        # self._config['sel_cont_rst'] = {'addr' : 100, 'val': round((self._config["power_rabi"]['val'] * 4) + (self._config["continuous"]['val'] * 2 + 1))}
        self._config["dac_parameters4"] = {'addr': 52, 'val': self.cal_dac_param4()}
        self._config["gaussian_pulse_duration"] = {'addr': None,
                                                   'val': self.ns_to_cycles(exp_config["gaussian_pulse_duration"])}
        self._config["gaussian_sigma"] = {'addr': None, 'val': self.ns_to_cycles(exp_config["gaussian_sigma"])}
        # print(self._config)

    def cal_dac_param4(self):
        val1 = self._config['gaussian_arb_bar']['val']
        val2 = (round((self._config["power_rabi"]['val'] * 4) + (self._config["continuous"]['val'] * 2 + 1)))
        val3 = (self._config['mode']['val'])
        val4 = (self._config['amplitude_factor_direct']['val'])
        return (((2 ** 21) * val1) + ((2 ** 18) * val2) + ((2 ** 16) * val3) + val4)

    def cal_n_s(self, n_s, mode):
        if ((n_s % 4) == 0):
            n_s = n_s
        elif ((n_s % 4) == 1):
            n_s = n_s + 3
        elif ((n_s % 4) == 2):
            n_s = n_s + 2
        else:
            n_s = n_s + 1
        if (mode == 3):
            n_s_4 = round(n_s / 4) - 1
        else:
            n_s_4 = round(n_s / 4)
        return n_s_4


class dac(utility_functions):
    def __init__(self, rf, ch, config, mem_config, top_config, hw_config):  # ch, fs, mixer_freq, phase, bram_addr):
        super().__init__(hw_config)
        self._rf = rf
        self._ch = ch
        self._exp_config = dac_populate_exp_config(config["dac_exp_config"], top_config, hw_config)
        self._fs = config["fs"]
        self._nco_freq = config["LO freq"]
        self._nco_phase = config["phase"]
        self._readout_channel = config['readout_channel']
        self._bram_size = mem_config["DAC_BRAM_SIZE"]
        self._bram_mmio_conf_mem = MMIO(mem_config["DAC_CONF_ADDR"], self._bram_size)  # mem_config["DAC_BRAM_I_LSB"] #
        self._bram_mmio_I_lsb = MMIO(mem_config["DAC_BRAM_I_LSB"], self._bram_size)  # mem_config["DAC_BRAM_I_LSB"] #
        self._bram_mmio_I_msb = MMIO(mem_config["DAC_BRAM_I_MSB"], self._bram_size)  # mem_config["DAC_BRAM_I_MSB"] #
        self._bram_mmio_Q_lsb = MMIO(mem_config["DAC_BRAM_Q_LSB"], self._bram_size)  # mem_config["DAC_BRAM_Q_LSB"] #
        self._bram_mmio_Q_msb = MMIO(mem_config["DAC_BRAM_Q_MSB"], self._bram_size)  # mem_config["DAC_BRAM_Q_MSB"] #
        self._control_or_readout_sel_addr = MMIO(config["dac_exp_config"]["READOUT_CHANNEL_CONF_ADDR"], 16)
        self._dac_handle = self._rf.dac_tiles[int(ch // 4)].blocks[ch % 4]
        self.init_conf_mem(self._bram_mmio_conf_mem)
        logging.debug('Dac descriptor called for channel number %d', ch)
        print('Super Class rf object is descriptor called for channel number', rf)
        # logging.debug('Dac Mem Addr is %x for channel number %d', self._bram_mmio_I_lsb, ch)

    def concat_samples(self, samples_l, samples_m):
        return int((samples_l) + (samples_m * (2 ** 16)))

    def prog_param(self, addr, val):
        self._bram_mmio_conf_mem.write(addr, val)

    def set_param(self, key, val, unit):
        if (unit == 'time'):
            self._exp_config._config[key]['val'] = self.ns_to_cycles(val)
        elif (unit == 'scale'):
            self._exp_config._config[key]['val'] = round(exp_config["amplitude_factor"] * ((np.power(2, 15) - 1) / 100))
        else:
            self._exp_config._config[key]['val'] = val
        addr = self._exp_config._config[key]['addr']
        if (addr == 100):
            self._exp_config._config['dac_parameters4']['val'] = self._exp_config.cal_dac_param4()
            addr = self._exp_config._config['dac_parameters4']['addr']
            key = 'dac_parameters4'
        self.prog_param(addr, self._exp_config._config[key]['val'])
        logging.debug('Programmed Dac experimental param %s with val %d', key, val)

    def init_conf_mem(self, mmio_handle):
        paramList = list(self._exp_config._config.items())
        # print("full param", paramList)
        for i in range(12):
            key = paramList[i][0]
            # addr = paramList[i][1]['addr']
            val = paramList[i][1]['val']
            self.set_param(key, val, 'None')
        mmio_handle.write(52, self._exp_config._config["dac_parameters4"]['val'])

    def set_readout_channel(self, val):
        val = (val << 4) << self._ch
        self._control_or_readout_sel_addr.write(0x0, val)

    def load_wave(self, I_samples, Q_samples):
        # First load I Samples
        addr_off = 0

        s_len = len(I_samples)  # if(self._exp_config._config['mode']['val']<3) else self._bram_size
        zero_len = (self._bram_size) - (s_len >> 2)
        const_val = 0x7fff7fff if (self._exp_config._config['mode']['val'] < 3) else 0
        print("sample_length=", s_len)
        for x in range(0, s_len, 4):
            self._bram_mmio_I_lsb.write(addr_off, self.concat_samples(I_samples[x], I_samples[x + 1]))
            self._bram_mmio_I_msb.write(addr_off, self.concat_samples(I_samples[x + 2], I_samples[x + 3]))
            #             print("samples", hex(addr_off), hex(self.concat_samples(I_samples[x], I_samples[x + 1])), hex(self.concat_samples(I_samples[x + 2], I_samples[x + 3])))
            #             print("I samples 0 and 1", hex(addr_off), hex(I_samples[x]),  hex(I_samples[x + 1]))
            addr_off = addr_off + 4
        for x in range(zero_len):
            self._bram_mmio_I_lsb.write(addr_off, const_val)
            self._bram_mmio_I_msb.write(addr_off, const_val)
        ## Load Q_samples
        addr_off = 0
        s_len = len(Q_samples)
        zero_len = (self._bram_size) - (s_len >> 2)
        for x in range(0, s_len, 4):
            self._bram_mmio_Q_lsb.write(addr_off, self.concat_samples(Q_samples[x], Q_samples[x + 1]))
            self._bram_mmio_Q_msb.write(addr_off, self.concat_samples(Q_samples[x + 2], Q_samples[x + 3]))
            addr_off = addr_off + 4
        for x in range(zero_len):
            self._bram_mmio_Q_lsb.write(addr_off, 0x00000000)
            self._bram_mmio_Q_msb.write(addr_off, 0x00000000)

    def set_nco_freq(self, freq, event):
        self._dac_handle.MixerSettings['EventSource'] = event
        self._dac_handle.MixerSettings['Freq'] = freq

    def set_nco_phase(self, phase, event):
        self._dac_handle.MixerSettings['EventSource'] = event
        self._dac_handle.MixerSettings['PhaseOffset'] = phase

    def set_nyquist(self, nyq_zone, event):
        self._dac_handle.MixerSettings['EventSource'] = event
        self._dac_handle.NyquistZone = nyq_zone

    def reset_nco_phase(self, event):
        self._dac_handle.MixerSettings['EventSource'] = event
        self._dac_handle.ResetNCOPhase()

