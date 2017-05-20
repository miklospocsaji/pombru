"The module representing a brewery."
import logging

import config
import devices
import lowlevel
import process

class Brewery(object):
    def __init__(self):
        self.mashtun = devices.JamMaker(6, 27, self.mash_temp_reached)
        self.boiler = devices.JamMaker(7, 22, self.boil_temp_reached)
        self.mashtunpump = devices.Pump(2)
        self.temppump = devices.Pump(4)
        self.boilerpump = devices.Pump(3)
        self.mashtunvalve = devices.TwoWayValve(17, 18, "mashtun", "temporary")
        self.boilervalve = devices.TwoWayValve(14, 15, "mashtun", "temporary")
        self.process = None

    def reload_config(self):
        self.mashtun.reload_config()
        self.boiler.reload_config()

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
            self.mashtunvalve.mashtun()
        elif task.event == process.BrewTask.SET_MASH_VALVE_TARGET_TEMP:
            self.mashtunvalve.temporary()
        elif task.event == process.BrewTask.START_MASH_PUMP:
            if task.param == 'MASH_DISTRIBUTION':
                self.mashtunpump.start(config.config.mash_circulate_distribution_work, config.config.mash_circulate_distribution_idle)
            elif task.param == 'SPARGE_DISTRIBUTION':
                self.mashtunpump.start(config.config.sparge_circulate_distribution_work, config.config.sparge_circulate_distribution_idle)
            else:
                self.mashtunpump.start()
        elif task.event == process.BrewTask.STOP_MASH_PUMP:
            self.mashtunpump.stop()
        elif task.event == process.BrewTask.MASH_TARGET_TEMP:
            self.mashtun.set_temperature(task.param)
        elif task.event == process.BrewTask.BOIL_TARGET_TEMP:
            self.boiler.set_temperature(task.param)
        elif task.event == process.BrewTask.STOP_MASHING_TUN:
            self.mashtun.off()
        elif task.event == process.BrewTask.STOP_BOIL_KETTLE:
            self.boiler.off()
        elif task.event == process.BrewTask.START_TEMP_PUMP:
            self.temppump.start()
        elif task.event == process.BrewTask.STOP_TEMP_PUMP:
            self.temppump.stop()
        elif task.event == process.BrewTask.START_BOIL_PUMP:
            self.boilerpump.start()
        elif task.event == process.BrewTask.STOP_BOIL_PUMP:
            self.boilerpump.stop()
        elif task.event == process.BrewTask.SET_BOIL_VALVE_TARGET_MASH:
            self.boilervalve.mashtun()
        elif task.event == process.BrewTask.SET_BOIL_VALVE_TARGET_TEMP:
            self.boilervalve.temporary()
        elif task.event == process.BrewTask.ENGAGE_COOLING_VALVE:
            #TODO
            pass
        elif task.event == process.BrewTask.STOP_COOLING_VALVE:
            #TODO
            pass
        elif task.event == process.BrewTask.RELEASE_ARM:
            # TODO
            pass
