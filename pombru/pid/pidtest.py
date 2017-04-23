"""
PID testing
"""
import datetime
import sys
import threading
import time
#from ... import lowlevel
import lowlevel
import devices
import pid.PID
#import PID as MYPID

SAMPLE_INTERVAL_SECS = 10

class pidtest:

    def main(self):
        self.thermistor = lowlevel.Thermistor(7)
        self.heater = devices.Heater(22)
        self.heater.start()
        self.pid = pid.PID.PID(P=1, I=2, D=0.2)
        self.pid.SetPoint = 70

        self.timeout()

    def timeout(self):
        temperature = round(self.thermistor.get_temp())
        self.pid.update(temperature)
        power = self.pid.output
        power = max(power, 0)
        power = min(power, 100)
        print("temp:", temperature, "power:", power)
        self.heater.set_power(power)

        timer = threading.Timer(SAMPLE_INTERVAL_SECS, self.timeout)
        timer.start()


class calibrator:
    """
    Calculates P, I and D values for a PID controller using the 
    Cohen-Coon method.
    See http://www.chem.mtu.edu/~tbco/cm416/tuning_methods.pdf for details
    """
    def __init__(self):
        self.thermistor = lowlevel.Thermistor(6)
        self.heater = devices.Heater(27)

    def start(self):
        self.heater.start()
        self.heater.set_power(40)
        self.timeout()

    def stop(self):
        self.heater.stop()

    def timeout(self):
        temperature = self.thermistor.get_temp()
        print("temp:", temperature, "power:", self.heater.get_power(), "time:", datetime.datetime.now().time())

        timer = threading.Timer(SAMPLE_INTERVAL_SECS, self.timeout)
        timer.start()
        
    
if __name__ == "__main__":

    if len(sys.argv) == 2:
        print "calibrating"
        c = calibrator()
        c.start()
    else:
        pt = pidtest()
        pt.main()
