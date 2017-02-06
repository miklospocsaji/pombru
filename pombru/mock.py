import gpiozero
import logging
import threading

import devices
import recipes
import process

class Mock(object):
    def __init__(self):
        self.mashtun = devices.JamMaker(0, 27, self.mash_temp_reached)
        self.boiler = devices.JamMaker(1, 22, self.boil_temp_reached)
        self.mashpump = gpiozero.LED(2)
        self.temppump = gpiozero.LED(3)
        self.boilpump = gpiozero.LED(4)
        self.mashvalve = devices.TwoWayValve(14, 15, "mash", "temp", 2)
        self.boilvalve = devices.TwoWayValve(17, 18, "mash", "boil", 2)
        testrecipe = recipes.Recipe(mash_stages=[(50, 1), (64, 1), (68, 1), (74, 1)], boiling_time=1, mash_water=1, sparge_water=1)
        self.process = process.BrewProcess(testrecipe, self)
        threading.Timer(5, self.print_status).start()

    def start(self):
        self.process.start()

    def mash_temp_reached(self, temp):
        logging.info("mash temperature reached: %dC", temp)
        self.process.mash_target_reached(temp)

    def boil_temp_reached(self, temp):
        logging.info("boil temperature reached: %dC", temp)
        self.process.boil_target_reached(temp)

    def task(self, task):
        """
        SET_MASH_VALVE_TARGET_MASH = "SET_MASH_VALVE_TARGET_MASH"
        SET_MASH_VALVE_TARGET_TEMP = "SET_MASH_VALVE_TARGET_TEMP"
        START_MASH_PUMP = "START_MASH_PUMP"
        STOP_MASH_PUMP = "STOP_MASH_PUMP"
        MASH_TARGET_TEMP = "MASH_TARGET_TEMP"
        BOIL_TARGET_TEMP = "BOIL_TARGET_TEMP"
        STOP_MASHING_TUN = "STOP_MASHING_TUN"
        STOP_BOIL_KETTLE = "STOP_BOIL_KETTLE"
        START_TEMP_PUMP = "START_TEMP_PUMP"
        STOP_TEMP_PUMP = "STOP_TEMP_PUMP"
        START_BOIL_PUMP = "START_BOIL_PUMP"
        STOP_BOIL_PUMP = "STOP_BOIL_PUMP"
        SET_BOIL_VALVE_TARGET_MASH = "SET_BOIL_VALVE_TARGET_MASH"
        SET_BOIL_VALVE_TARGET_TEMP = "SET_BOIL_VALVE_TARGET_TEMP"
        ENGAGE_COOLING_VALVE = "ENGAGE_COOLING_VALVE"
        STOP_COOLING_VALVE = "STOP_COOLING_VALVE"
        RELEASE_ARM = "RELEASE_ARM"
        """
        logging.info("%s", task)
        if task.event == process.BrewTask.SET_MASH_VALVE_TARGET_MASH:
            self.mashvalve.mash()
        elif task.event == process.BrewTask.SET_MASH_VALVE_TARGET_TEMP:
            self.mashvalve.temp()
        elif task.event == process.BrewTask.START_MASH_PUMP:
            self.mashpump.on()
        elif task.event == process.BrewTask.STOP_MASH_PUMP:
            self.mashpump.off()
        elif task.event == process.BrewTask.MASH_TARGET_TEMP:
            self.mashtun.set_temperature(task.param)
        elif task.event == process.BrewTask.BOIL_TARGET_TEMP:
            self.boiler.set_temperature(task.param)
        elif task.event == process.BrewTask.STOP_MASHING_TUN:
            self.mashtun.off()
        elif task.event == process.BrewTask.STOP_BOIL_KETTLE:
            self.boiler.off()
        elif task.event == process.BrewTask.START_TEMP_PUMP:
            self.temppump.on()
        elif task.event == process.BrewTask.STOP_TEMP_PUMP:
            self.temppump.off()
        elif task.event == process.BrewTask.START_BOIL_PUMP:
            self.boilpump.on()
        elif task.event == process.BrewTask.STOP_BOIL_PUMP:
            self.boilpump.off()
        elif task.event == process.BrewTask.SET_BOIL_VALVE_TARGET_MASH:
            self.boilvalve.mash()
        elif task.event == process.BrewTask.SET_BOIL_VALVE_TARGET_TEMP:
            self.boilvalve.temp()
        elif task.event == process.BrewTask.ENGAGE_COOLING_VALVE:
            pass
        elif task.event == process.BrewTask.STOP_COOLING_VALVE:
            pass
        elif task.event == process.BrewTask.RELEASE_ARM:
            pass

    def print_status(self):
        threading.Timer(5, self.print_status).start()
        logging.debug("mashing temp: %.1f C", self.mashtun.get_temperature())
        logging.debug("boiler temp: %.1f C", self.boiler.get_temperature())

logging.basicConfig(filename="mock.log", level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
Mock().start()
