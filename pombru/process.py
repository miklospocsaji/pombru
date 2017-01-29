"Module contains classes which manage the brewing process."
import functools
import logging
import threading
from time import sleep

class BrewTask(object):
    "Describes a task during brewing."
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

    def __init__(self, event, param=None):
        self.event = event
        self.param = param

    def __str__(self):
        return "BrewTask(" + self.event + ", " + str(self.param) + ")"

class BrewProcess(object):
    "Manages a process of the whole brewing."
    _PUMP_SECONDS_PER_LITER = 10
    _SPARGING_TEMP = 74

    # Nothing has been done to the sparging water in the boiling kettle
    _SPARGE_INIT = 1
    # Sparging water is heating up
    _SPARGE_HEATING = 2
    # Sparging water is ready
    _SPARGE_READY = 3

    def __init__(self, recipe, actor):
        self.recipe = recipe
        self._timers = []
        self._current_mashing_step = -1
        self.actor = actor
        self._sparging_stage = BrewProcess._SPARGE_INIT
        self._mashing_done = False
        self._lock = threading.RLock()

    def start(self):
        # First, heat up the mashing tun
        self._current_mashing_step = 0
        temp, _ = self.recipe.mash_stages[0]
        self.actor.task(BrewTask(BrewTask.SET_MASH_VALVE_TARGET_MASH))
        self.actor.task(BrewTask(BrewTask.MASH_TARGET_TEMP, temp))
        self.actor.task(BrewTask(BrewTask.START_MASH_PUMP))
        # Set up timer to start heating the sparging water
        total_mash_time = functools.reduce(lambda sum, (_, y): sum + y, self.recipe.mash_stages, 0)
        logging.debug("Total mash time: %d minutes", total_mash_time)
        sparge_heat_delay = total_mash_time - 50
        if sparge_heat_delay <= 0:
            self._start_sparge_heat()
        else:
            timer = threading.Timer(sparge_heat_delay * 60, self._start_sparge_heat)
            self._timers.append(timer)
            timer.start()

    def _start_sparge_heat(self):
        with self._lock:
            self.actor.task(BrewTask(BrewTask.BOIL_TARGET_TEMP, BrewProcess._SPARGING_TEMP))
            self._sparging_stage = BrewProcess._SPARGE_HEATING

    def mash_target_reached(self, temp):
        with self._lock:
            _, minutes = self.recipe.mash_stages[self._current_mashing_step]
            timer = threading.Timer(minutes * 60, self._mash_stage_done)
            timer.start()
            self._timers.append(timer)

    def boil_target_reached(self, temp):
        with self._lock:
            if self._sparging_stage == BrewProcess._SPARGE_HEATING:
                # Sparging water ready
                self._sparging_stage = BrewProcess._SPARGE_READY
                if self._mashing_done:
                    # Mashing already done, start sparging now
                    self._sparge_start()
            if temp == 100:
                # Boiling
                # TODO: hops
                timer = threading.Timer(self.recipe.boiling_time * 60, self._boil_finished)
                self._timers.append(timer)
                timer.start()

    def _mash_stage_done(self):
        with self._lock:
            stepcount = len(self.recipe.mash_stages)
            if self._current_mashing_step == stepcount - 1:
                # Mashing finished!
                # If the sparging water is ready, then sparge
                self._mashing_done = True
                if self._sparging_stage == BrewProcess._SPARGE_READY:
                    self._sparge_start()
            else:
                # There are more mashing steps
                self._current_mashing_step += 1
                temp, _ = self.recipe.mash_stages[self._current_mashing_step]
                self.actor.task(BrewTask(BrewTask.MASH_TARGET_TEMP, temp))

    #########################################
    ## SPARGING
    #########################################

    def _sparge_start(self):
        # Switch off mash tun and pump
        self.actor.task(BrewTask(BrewTask.STOP_MASHING_TUN))
        self.actor.task(BrewTask(BrewTask.STOP_MASH_PUMP))
        # Set valves
        self.actor.task(BrewTask(BrewTask.SET_BOIL_VALVE_TARGET_MASH))
        self.actor.task(BrewTask(BrewTask.SET_MASH_VALVE_TARGET_TEMP))
        # Wait for valves to settle
        sleep(2)
        # Start pump from mash to temp
        self.actor.task(BrewTask(BrewTask.START_MASH_PUMP))
        time = self.recipe.mash_water * BrewProcess._PUMP_SECONDS_PER_LITER
        timer = threading.Timer(time, self._sparge_from_boil_to_mash)
        self._timers.append(timer)
        timer.start()

    def _sparge_from_boil_to_mash(self):
        """Situation:
        * Mashing tun is empty
        * Temporary kettle contains first wort
        * Boiling kettle is filled with hot sparging water
        This sparging water needs to be transferred to mash tun"""
        self.actor.task(BrewTask(BrewTask.STOP_MASH_PUMP))
        self.actor.task(BrewTask(BrewTask.START_BOIL_PUMP))
        time = self.recipe.sparge_water * BrewProcess._PUMP_SECONDS_PER_LITER
        timer = threading.Timer(time, self._sparge_from_mash_to_temp)
        self._timers.append(timer)
        timer.start()

    def _sparge_from_mash_to_temp(self):
        """Situation:
        * Mashing tun contains sparging water
        * Temporary tun contains first wort
        * Boiling kettle is empty
        Wort from mashing tun needs to be transferred to temporary"""
        self.actor.task(BrewTask(BrewTask.STOP_BOIL_PUMP))
        self.actor.task(BrewTask(BrewTask.START_MASH_PUMP))
        time = self.recipe.sparge_water * BrewProcess._PUMP_SECONDS_PER_LITER
        timer = threading.Timer(time, self._sparge_from_temp_to_boil)
        self._timers.append(timer)
        timer.start()

    def _sparge_from_temp_to_boil(self):
        """Situation:
        * Mashing tun is empty
        * Temporary kettle contains all wort
        * Boiling kettle is empty
        Wort from temporary needs to be transferred to boiling kettle."""
        self.actor.task(BrewTask(BrewTask.STOP_MASH_PUMP))
        self.actor.task(BrewTask(BrewTask.START_TEMP_PUMP))
        time = (self.recipe.mash_water + self.recipe.sparge_water) * BrewProcess._PUMP_SECONDS_PER_LITER
        timer = threading.Timer(time, self._sparge_finish)
        self._timers.append(timer)
        timer.start()

    def _sparge_finish(self):
        self.actor.task(BrewTask(BrewTask.STOP_TEMP_PUMP))
        self.actor.task(BrewTask(BrewTask.BOIL_TARGET_TEMP, 100))

    ################################################
    ## Boiling
    ################################################

    def _boil_finished(self):
        self.actor.task(BrewTask(BrewTask.STOP_BOIL_KETTLE))
