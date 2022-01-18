import universal_usbtmc
import time


class PPS:
    def __init__(self, address, pause_after_change=0.2, pause_between_write_read=0.02):
        kernel_tmc = universal_usbtmc.import_backend("linux_kernel")
        self._inst = kernel_tmc.Instrument(address)
        self.pause_after_change = pause_after_change
        self.pause_between_write_read = pause_between_write_read


    def measure_ch_volt(self, channel):
        data = self._query(f"MEAsure:VOLTage? CH{channel}")
        return float(data)

    def measure_ch_amp(self, channel):
        data = self._query(f"MEASure:CURRent? CH{channel}")
        return float(data)

    def get_ch_volt(self, channel):
        data = self._query(f"CH{channel}:VOLTage?")
        return float(data)

    def get_ch_amp(self, channel):
        data = self._query(f"CH{channel}:CURRent?")
        return float(data)

    def set_ch_volt(self, channel, value: float):
        self._inst.write(f"CH{channel}:VOLTage {value}")
        # Sleep because it takes a moment to update the state
        time.sleep(self.pause_after_change)

        # Confirm the change has been made:
        new = float(self.get_ch_volt(channel))
        if not new == value:
            self.set_ch_volt(mode)

    def set_ch_amp(self, channel, value: float):
        self._inst.write(f"CH{channel}:CURRent {value}")
        # Sleep because it takes a moment to update the state
        time.sleep(self.pause_after_change)

        # Confirm the change has been made:
        new = float(self.get_ch_amps(channel))
        if not new == value:
            self.set_ch_amps(mode)

    def set_ch_active(self, channel, state):
        if state == False:
            new_state = "OFF"
        elif state == True:
            new_state = "ON"

        self._inst.write(f"OUTPut CH{channel}, {new_state}")
        # print (f"OUTPut CH{channel}, {new_state}")

        # Sleep because it takes a moment to update the state
        time.sleep(self.pause_after_change)

        # Confirm the change has been made:
        self.get_state()
        if not self.ch_state[channel] == state:
            self.set_channel(channel, state)

    def set_mode(self, mode):
        self._inst.write(f"OUTPut:TRACk {mode}")
        # print(f"OUTPut:TRACk {mode}")

        # Sleep because it takes a moment to update the state
        time.sleep(self.pause_after_change)

        # Confirm the change has been made:
        self.get_state()
        if not self.mode == mode:
            self.set_mode(mode)

    def _query(self, query):
        # Keep trying if the query fails
        while True:
            self._inst.write(query)
            time.sleep(self.pause_between_write_read)
            try:
                data = self._inst.read_raw(-1, timeout=0.1).decode().rstrip("\n")
                return data
            except(universal_usbtmc.exceptions.UsbtmcReadTimeoutError):
                pass

    def get_state(self):
        data = self._query("SYSTem:STATus?")

        # Raw state
        self._state = int(data[2:], 16)

        # Check channel on / off
        self.ch_state = [None, self._check_bit(5), self._check_bit(6)]

        # Check channel constant current or constant voltage
        self.ch_cc = [None, self._check_bit(1), self._check_bit(1)]

        # Check mode
        if self._check_bit(4) == False and self._check_bit(3) == True:
            self.mode = 0 # Independent mode
        elif self._check_bit(4) == True and self._check_bit(3) == True:
            self.mode = 1 # Parallel mode
        elif self._check_bit(4) == True and self._check_bit(3) == False:
            self.mode = 2 # Series mode

        # print(f"{format(self._state, '0>6b')} CH1: {self.ch_state[1]} - CH2: {self.ch_state[2]} - mode: {self.mode}")

    def _check_bit(self, k):
        if self._state & (1 << (k - 1)):
            return True
        else:
            return False



inst = PPS("/dev/usbtmc1")

while True:
    volts = inst.measure_ch_volt(1)
    amps = inst.measure_ch_amp(1)
    inst.get_state()
    print (f"{volts:2.2}v / {amps:2.2} CC: {inst.ch_cc[1]}")
