import logging
import threading

import devices
import recipes
import process

class Mock(object):
    def __init__(self):
        self.mashtun = devices.JamMaker(0, 2, self.mash_temp_reached)
        self.boiler = devices.JamMaker(1, 3, self.boil_temp_reached)
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
        logging.info("%s", task)
        if task.event == process.BrewTask.MASH_TARGET_TEMP:
            self.mashtun.set_temperature(task.param)
        elif task.event == process.BrewTask.BOIL_TARGET_TEMP:
            self.boiler.set_temperature(task.param)

    def print_status(self):
        threading.Timer(5, self.print_status).start()
        logging.debug("mashing temp: %.1f C", self.mashtun.get_temperature())
        logging.debug("boiler temp: %.1f C", self.boiler.get_temperature())

logging.basicConfig(filename="mock.log", level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
Mock().start()
