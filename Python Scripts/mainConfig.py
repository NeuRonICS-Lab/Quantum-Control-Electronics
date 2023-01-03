
class mainConfig():
    def __init__(self, config):
        self.bitfile = config["bitfile"]

        self.exp_list = config["exp_list"]
        if (config["freq_scale"] == "G"):  # Giga Hz
            self.freq_scale = np.power(10, 9)
        elif (config["freq_scale"] == "M"):  # Mega Hz
            self.freq_scale = np.power(10, 6)
        elif (config["freq_scale"] == "K"):  # Kilo Hz
            self.freq_scale = np.power(10, 3)
        else:  # Hz
            self.freq_scale = 1

        self.freq_start = config["freq_start"]
        self.freq_steps = config["freq_steps"]
        self.freq_stop = config["freq_end"]

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
        self.dac_channels = rfdc_config["dac_channels"]
        self.adc_channels = rfdc_config["adc_channels"]
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
        self.init_MTS()
    def init_MTS(self):
        (lat_dac_t0, lat_dac_t1) = self.rf.dac_tiles[0].dacMTS(3)
        if(lat_dac_t0>lat_dac_t1):
            dac_tar_lat = lat_dac_t0+16
        else:
            dac_tar_lat = lat_dac_t1+16
        self.rf.dac_tiles[0].dacMTSwl(3,dac_tar_lat)
        self.rf.dac_tiles[1].dacMTSwl(3,dac_tar_lat)
    def run_MTS(self):
        self.rf.dac_tiles[0].sysref_enable(0)
        self.rf.dac_tiles[1].sysref_enable(0)
        sleep(2)
        for i in range(len(self.dac_channels)):
            ch_t = self.dac_channels[i]
            #self.dac[i].set_nco_freq(100, xrfdc.EVNT_SRC_SYSREF)
            logging.debug('setting nco freq for dac channel %d', ch_t)
        sleep(2)
        self.rf.dac_tiles[0].sysref_enable(1)
        self.rf.dac_tiles[1].sysref_enable(1)
        sleep(2)
        self.rf.dac_tiles[0].sysref_enable(0)
        self.rf.dac_tiles[1].sysref_enable(0)


# class gen_waveform(top_config):
#     def __init__(self, config):
#         self.fabric_clock = self.pl_freq
#         self.sample_per_clock = self.



