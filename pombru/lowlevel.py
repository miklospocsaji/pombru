""" Low-level classes and functions for Pombru Python Brewing System"""
import math
import os
import random
import threading
from gpiozero import OutputDevice
from gpiozero import MCP3208

class Relay(object):
    "Simple Relay class which is a gpiozero OutputDevice wrapper."

    def __init__(self, pin):
        """ Relay constructor takes a pin argument only"""
        self.__mock = os.getenv('GPIOZERO_PIN_FACTORY') == 'mock'
        try:
            if not self.__mock:
                self.__device = OutputDevice(pin=pin, active_high=False, initial_value=False)
            else:
                self.__is_on = False
        except IOError as _:
            self.__mock = True
            self.__is_on = False

    def on(self):
        "Turns on the relay."
        if self.__mock:
            self.__is_on = True
        else:
            self.__device.on()

    def off(self):
        "Turns off the relay."
        if self.__mock:
            self.__is_on = False
        else:
            self.__device.off()

    def toggle(self):
        "Toggles the state."
        if self.__mock:
            self.__is_on = not self.__is_on
        else:
            self.__device.toggle()

    def get_value(self):
        "Gets the relay value."
        if self.__mock:
            return self.__is_on
        else:
            return self.__device.value

def create_spi_args(clock_pin=11, mosi_pin=10, miso_pin=9, select_pin=8):
    """ Creates a dictionary from the arguments. """
    return {'clock_pin':clock_pin, 'mosi_pin':mosi_pin, 'miso_pin':miso_pin, 'select_pin':select_pin}

class Thermistor(object):
    """ Class representing a thermistor. The class assumes that
        the termistor is a variable resistor with impedance of 100 kOhm at
        25 Celsius. This variable resistor is then connected to an appropriate channel
        of an MCP3208 integrated circuit
    """

    __DEFAULT_SPI_ARGS = create_spi_args()

    def __init__(self, channel, sample_count=5, sample_delay=0.1, spi_args=None):
        if spi_args is None:
            spi_args = Thermistor.__DEFAULT_SPI_ARGS
        try:
            if os.getenv('GPIOZERO_PIN_FACTORY') != 'mock':
                self.__ic = MCP3208(channel=channel, differential=False, **spi_args)
            else:
                self.__ic = None
        except IOError as _:
            self.__ic = None
        self.__sample_count = sample_count
        self.__sample_delay = sample_delay

    def get_temp(self):
        """ Reads the 3208 value n times and counts an average.

            From this, it counts the resistance of the termistor.
            The actual temperature is then calculated by the
            Steinhart-Hart equation, see:
            https://www.thermistor.com/calculators
        """
        if self.__ic is None:
            return random.randrange(25, 110)
        const_a = 0.000607906373979
        const_b = 0.000229555466739
        const_c = 0.000000067688324
        val = 0.0
        for _ in range(self.__sample_count):
            val += self.__ic.value
        val /= self.__sample_count
        resistance = ((1-val) * 100000)/val
        logrest = math.log(resistance)
        temp_steinhart_hart = const_a + const_b * logrest + const_c * math.pow(logrest, 3)
        temp_steinhart_hart = 1 / temp_steinhart_hart - 273.15
        return temp_steinhart_hart
