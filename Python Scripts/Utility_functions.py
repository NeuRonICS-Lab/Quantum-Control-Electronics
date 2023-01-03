class utility_functions():
    def __init__(self, hw_config):
        # self._config = config
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
        return 1 / (np.sqrt(2 * np.pi) * sig) * np.exp(-np.power((x - mu) / sig, 2) / 2)

    def der_gaussian(self, x, mu, sig):
        return (-1 / (np.sqrt(2 * np.pi) * sig)) * (np.exp(-np.power((x - mu) / sig, 2) / 2)) * (
                (x - mu) / np.power(sig, 2))

    def sine(self, x):
        return np.sin(x)

    def to_hex_scale(self, x, amp_scale):
        if (np.max(x) != 0):
            x = x / (np.max(x))
        return ((x * amp_scale * ((2 ** 15) - 4)).astype(np.int16))

    def gen_wave(self, config, wav_type, on_time, sigma, amp_scale):
        number_samples = self.ns_to_cycles(on_time)
        mu = on_time / 2
        a = np.linspace(0, on_time, number_samples)
        print("wave params on_time, number_samples", on_time, number_samples)
        if (wav_type == "gaussian"):
            samples = self.gaussian(a, mu, sigma)
            samples = self.to_hex_scale(samples, amp_scale)
            for i in range(len(samples)):
                print("samples in gen wave", samples[i])
            plt.plot(samples)
            return samples
        elif (wav_type == "der"):
            samples = self.der_gaussian(a, mu, sigma)
            samples = self.to_hex_scale(samples, amp_scale)
            return samples
        elif (wav_type == "sine"):
            time = np.linspace(0, 2 * np.pi, number_samples)
            samples = self.sine(time)
            samples = self.to_hex_scale(samples, amp_scale)
            return samples
        elif (wav_type == "cw"):
            # time = np.linspace(0,2*np.pi,number_samples)
            samples = np.ones((number_samples,))
            samples = samples * round((2 ** 15 - 1))
            samples = self.to_hex_scale(samples, amp_scale)
            return samples
        elif (wav_type == "zero"):
            # time = np.linspace(0,2*np.pi,number_samples)
            samples = np.zeros((number_samples,))
            # samples = samples * round((2**15-1))
            samples = self.to_hex_scale(samples, amp_scale)
            return samples
        else:
            logging.error('Unknown waveform type %s, please check', wav_type)

    def set_bitfield(self, field_base_addr, field_offset, field_width, ch_num, new_val):
        m = 3 if (field_width == 2) else 1
        rd_val = field_base_addr.mmio.read(0)
        mask = (m << field_offset) << ch_num
        wr_val = (rd_val ^ mask) | new_val
        field_base_addr.mmio.read(0, wr_val)

    def get_bitfield(self, field_base_addr, field_offset, field_width, ch_num):
        m = 0x0000000c if (field_width == 2) else 0x0000000e
        rd_val = field_base_addr.mmio.read(0)
        rd_val = (rd_val >> field_offset) >> ch_num
        return (rd_val & m)

    def find_quad(self, theta_deg_0):
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
        return (quadr_0, theta_deg_0)

