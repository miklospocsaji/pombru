"The module representing a brewery."
import logging

import devices
import lowlevel
import process

class Brewery(object):
    def __init__(self, recipe):
        self.mashtun = devices.JamMaker(0, 27, self.mash_temp_reached)
        self.boiler = devices.JamMaker(1, 22, self.boil_temp_reached)
        self.mashpump = lowlevel.Relay(2)
        self.temppump = lowlevel.Relay(3)
        self.boilerpump = lowlevel.Relay(4)
        self.mashvalve = devices.TwoWayValve(14, 15, "mash", "temp", 2)
        self.boilvalve = devices.TwoWayValve(17, 18, "mash", "boil", 2)
        self.recipe = recipe
        self.process = process.BrewProcess(recipe, self)

    ##############################
    # Jam maker callbacks
    ##############################

    def mash_temp_reached(self, temp):
        logging.info("mash temperature reached: %dC", temp)
        self.process.mash_target_reached(temp)

    def boil_temp_reached(self, temp):
        logging.info("boil temperature reached: %dC", temp)
        self.process.boil_target_reached(temp)

    #################################
    # Process callback
    #################################
    def task(self, task):
        "This method is called by the BrewProcess object."
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
            self.boilerpump.on()
        elif task.event == process.BrewTask.STOP_BOIL_PUMP:
            self.boilerpump.off()
        elif task.event == process.BrewTask.SET_BOIL_VALVE_TARGET_MASH:
            self.boilvalve.mash()
        elif task.event == process.BrewTask.SET_BOIL_VALVE_TARGET_TEMP:
            self.boilvalve.temp()
        elif task.event == process.BrewTask.ENGAGE_COOLING_VALVE:
            #TODO
            pass
        elif task.event == process.BrewTask.STOP_COOLING_VALVE:
            #TODO
            pass
        elif task.event == process.BrewTask.RELEASE_ARM:
            # TODO
            pass
