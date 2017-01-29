"Represents Pombru devices: Pumps, Valves and JamMakers."

import threading
from lowlevel import Relay, Thermistor

class TwoWayValve(object):
    "Class represents a valve which can flow liquid in two directions."

    def __init__(self, pin, direction_when_off, direction_when_on):
        self._relay = Relay(pin)
        self._off_name = direction_when_off
        self._on_name = direction_when_on
        def off_func():
            self._relay.off()
        self._off_func = off_func
        def on_func():
            self._relay.on()
        self._on_func = on_func

    def __getattr__(self, attr):
        if attr == self._off_name:
            return self._off_func
        elif attr == self._on_name:
            return self._on_func
        else:
            return super.__getattr__(attr)

class Heater(object):
    """Class represents a heater.

    This heater is backed by a Relay. The heater can be set a power in 10 percentages.
    E.g. when the heater is told to work 30% then it is on for 3 seconds every 10 seconds.
    """

    def __init__(self, pin, initial_power=0):
        "Only the pin is needed."
        self.__relay = Relay(pin)
        self.__lock = threading.RLock()
        self.__power = initial_power / 10
        self.__cycle = 0
        self.__timer = None
        self.__lock = threading.RLock()

    def start(self):
        "Starts the heater."
        with self.__lock:
            if self.__timer is not None:
                return
            self.__timer = threading.Timer(1, self.__timeout)
            self.__timer.start()

    def stop(self):
        "Stops the heater."
        with self.__lock:
            self.__power = 0
            self.__timer.cancel()
            self.__relay.off()
            self.__timer = None

    def set_power(self, power):
        """Sets the current power.

        Argument must be between 0 and 100 (inclusive)."""
        with self.__lock:
            self.__power = power / 10

    def is_panel_on(self):
        "Returns true if the heating panel is currently on."
        with self.__lock:
            return self.__relay.get_value()

    def __timeout(self):
        self.__cycle += 1
        if self.__cycle == 11:
            self.__cycle = 1
        with self.__lock:
            if self.__timer is None:
                return
            if self.__cycle <= self.__power:
                self.__relay.on()
            else:
                self.__relay.off()
            self.__timer = threading.Timer(1, self.__timeout)
            self.__timer.start()

class JamMaker(object):
    """Represents a controller jam maker.
    * thermistor_channel: The channel number on the MCP3208 A/D converter which reads the temperature
    * heater_panel_gpio_pin: The RPi GPIO PIN number to which the heater panel's relay is wired
    * listener: a function to call when the preset temperature is reached it is passed the set temperature
    * thermistor_spi_args: SPI GPIO PIN settings for the MCP3208"""
    MODE_MANUAL_ON = 1
    MODE_MANUAL_OFF = 2
    MODE_CONTROLLED = 3

    _STATUS_HEATING = 1
    _STATUS_HOLDING = 2

    def __init__(self, thermistor_channel, heater_panel_gpio_pin, listener=None, **thermistor_spi_args):
        self._thermistor = Thermistor(thermistor_channel, sample_count=5, sample_delay=0.1, spi_args=thermistor_spi_args)
        self._heater = Heater(heater_panel_gpio_pin)
        self._mode = JamMaker.MODE_MANUAL_OFF
        self._listener = listener
        self._target_temperature = 0
        self._status = JamMaker._STATUS_HEATING
        self._heater.start()
        self._timer = None
        self._set_timer()

    def manual_on(self):
        "Switch on the heater."
        self._mode = JamMaker.MODE_MANUAL_ON
        self._heater.set_power(100)

    def manual_off(self):
        "Switch off the heater."
        self._mode = JamMaker.MODE_MANUAL_OFF
        self._heater.set_power(0)

    def set_temperature(self, target_temp):
        """Set the target temperature for the heater.

        If the specified temperature is reached, the listener is called.
        """
        self._target_temperature = target_temp
        self._status = JamMaker._STATUS_HEATING
        self._mode = JamMaker.MODE_CONTROLLED

    def get_mode(self):
        "Return the current mode operation of the jam maker."
        return self._mode

    def get_temperature(self):
        "Returns the jam maker's inside temperature in Celsius."
        return self._thermistor.get_temp()

    def _timeout(self):
        self._set_timer()
        if self._mode != JamMaker.MODE_CONTROLLED:
            return
        self._calc_heater_power()

    def _calc_heater_power(self):
        curr_temp = self._thermistor.get_temp()
        if self._target_temperature >= 100:
            # Boiling
            self._heater.set_power(100)
            if self._status == JamMaker._STATUS_HEATING and curr_temp >= 100:
                self._status = JamMaker._STATUS_HOLDING
                self._listener(self._target_temperature)
            return

        if self._status == JamMaker._STATUS_HEATING and curr_temp >= self._target_temperature + 0.5:
            self._status = JamMaker._STATUS_HOLDING
            self._listener(self._target_temperature)

        if curr_temp >= self._target_temperature + 0.5:
            self._heater.set_power(0)
        elif curr_temp >= self._target_temperature:
            self._heater.set_power(30)
        else:
            diff = self._target_temperature - curr_temp + 3
            diff = min(10, diff)
            self._heater.set_power(diff * 10)

    def _set_timer(self):
        self._timer = threading.Timer(1, self._timeout)
        self._timer.start()
