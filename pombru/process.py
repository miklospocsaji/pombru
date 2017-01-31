"Module contains classes which manage the brewing process."
import functools
import logging
import threading
from time import sleep

import utils

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

class BrewStages(object):
    "(Name, mash stage, next stage) tuples."
    BOIL = ("Boiling wort", 0, None)
    TEMP_TO_BOIL = ("Transferring wort to boiling kettle", 0, BOIL)
    SPARGE_MASH_TO_TEMP_3 = ("Sparging - transferring wort to temporary III.", 0, TEMP_TO_BOIL)
    SPARGE_CIRCULATE_IN_MASH_2 = ("Sparging - circulating in mash tun II.", 0, SPARGE_MASH_TO_TEMP_3)
    SPARGE_BOIL_TO_MASH_2 = ("Sparging - transferring water to mashing tun II.", 0, SPARGE_CIRCULATE_IN_MASH_2)
    SPARGE_MASH_TO_TEMP_2 = ("Sparging - transferring wort to temporary II.", 0, SPARGE_BOIL_TO_MASH_2)
    SPARGE_CIRCULATE_IN_MASH_1 = ("Sparging - circulating in mash tun I.", 0, SPARGE_MASH_TO_TEMP_2)
    SPARGE_BOIL_TO_MASH_1 = ("Sparging - transferring water to mashing tun I.", 0, SPARGE_CIRCULATE_IN_MASH_1)
    SPARGE_MASH_TO_TEMP_1 = ("Sparging - transferring wort to temporary I.", 0, SPARGE_BOIL_TO_MASH_1)
    MASHING_4 = ("Mashing - step IV.", 4, SPARGE_MASH_TO_TEMP_1)
    MASHING_3 = ("Mashing - step III.", 3, MASHING_4)
    MASHING_2 = ("Mashing - step II.", 2, MASHING_3)
    MASHING_1 = ("Mashing - step I.", 1, MASHING_2)
    INITIAL = ("Initial stage", 0, MASHING_1)


    # next = {
    #     INITIAL: MASHING_1,
    #     MASHING_1: MASHING_2,
    #     MASHING_2: MASHING_3,
    #     MASHING_3: MASHING_4,
    #     MASHING_4: SPARGE_MASH_TO_TEMP_1,
    #     SPARGE_MASH_TO_TEMP_1: SPARGE_BOIL_TO_MASH_1,
    #     SPARGE_BOIL_TO_MASH_1: SPARGE_CIRCULATE_IN_MASH_1,
    #     SPARGE_CIRCULATE_IN_MASH_1: SPARGE_MASH_TO_TEMP_2,
    #     SPARGE_MASH_TO_TEMP_2: SPARGE_BOIL_TO_MASH_2,
    #     SPARGE_BOIL_TO_MASH_2: SPARGE_CIRCULATE_IN_MASH_2,
    #     SPARGE_CIRCULATE_IN_MASH_2: SPARGE_MASH_TO_TEMP_3,
    #     SPARGE_MASH_TO_TEMP_3: TEMP_TO_BOIL,
    #     TEMP_TO_BOIL: BOIL
    # }

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
        self._brewing_stage = BrewStages.INITIAL

    _MASH_VALVE_TO_MASH = "_MASH_VALVE_TO_MASH"
    _MASH_VALVE_TO_TEMP = "_MASH_VALVE_TO_TEMP"
    _BOIL_VALVE_TO_MASH = "_BOIL_VALVE_TO_MASH"
    _BOIL_VALVE_TO_TEMP = "_BOIL_VALVE_TO_TEMP"

    def _set_valves_and_pumps(self, mash_pump=False, temp_pump=False, boil_pump=False, mash_valve=_MASH_VALVE_TO_MASH, boil_valve=_BOIL_VALVE_TO_MASH):
        events = []
        if mash_pump:
            events.append(BrewTask(BrewTask.START_MASH_PUMP))
        else:
            events.append(BrewTask(BrewTask.STOP_MASH_PUMP))

        if temp_pump:
            events.append(BrewTask(BrewTask.START_TEMP_PUMP))
        else:
            events.append(BrewTask(BrewTask.STOP_TEMP_PUMP))

        if boil_pump:
            events.append(BrewTask(BrewTask.START_BOIL_PUMP))
        else:
            events.append(BrewTask(BrewTask.STOP_BOIL_PUMP))

        if mash_valve == BrewProcess._MASH_VALVE_TO_MASH:
            events.append(BrewTask(BrewTask.SET_MASH_VALVE_TARGET_MASH))
        elif mash_valve == BrewProcess._MASH_VALVE_TO_TEMP:
            events.append(BrewTask(BrewTask.SET_MASH_VALVE_TARGET_TEMP))
        else:
            raise ValueError("Invalid value for mash_valve: " + str(mash_valve))

        if boil_valve == BrewProcess._BOIL_VALVE_TO_MASH:
            events.append(BrewTask(BrewTask.SET_BOIL_VALVE_TARGET_MASH))
        elif boil_valve == BrewProcess._BOIL_VALVE_TO_TEMP:
            events.append(BrewTask(BrewTask.SET_BOIL_VALVE_TARGET_TEMP))
        else:
            raise ValueError("Invalid value for boil_valve: " + str(boil_valve))

        for event in events:
            self.actor.task(event)

    def _stop_all(self):
        self.actor.task(BrewTask(BrewTask.STOP_COOLING_VALVE))
        self.actor.task(BrewTask(BrewTask.STOP_MASHING_TUN))
        self.actor.task(BrewTask(BrewTask.STOP_BOIL_KETTLE))
        self._set_valves_and_pumps() # Without parameters it switches off all pumps

    def _reset(self):
        self._stop_all()
        self._brewing_stage = BrewStages.INITIAL
        self._sparging_stage = BrewProcess._SPARGE_INIT

    def _next_stage(self, stage):
        _, _, next_stage = stage
        _, mashstage, _ = next_stage
        if mashstage > len(self.recipe.mash_stages):
            # This mash stage is not defined in the recipe
            return BrewStages.MASHING_4[2]
        return next_stage

    def _enter_stage(self, stage):
        _, mashstage, _ = stage
        if stage == BrewStages.INITIAL:
            raise ValueError("Initial is not a valid stage to resume to.")
        elif mashstage > 0:
            self._mash(mashstage)

        self._brewing_stage = stage

    def _mash(self, step):
        if step > len(self.recipe.mash_stages):
            raise ValueError("Mashing step " + str(step) + " is not defined in recipe!")
        temp, _ = self.recipe.mash_stages[step - 1]
        self.actor.task(BrewTask(BrewTask.MASH_TARGET_TEMP, temp))
        self._set_valves_and_pumps(mash_pump=True)

    def start(self):
        "Starts the brewing process."
        self._enter_stage(BrewStages.MASHING_1)
        # Set up timer to start heating the sparging water
        total_mash_time = functools.reduce(lambda sum, (_, y): sum + y, self.recipe.mash_stages, 0)
        logging.debug("Total mash time: %d minutes", total_mash_time)
        sparge_heat_delay = total_mash_time - 50
        if sparge_heat_delay <= 0:
            self._start_sparge_heat(None)
        else:
            timer = utils.PausableTimer(sparge_heat_delay * 60, self._start_sparge_heat)
            self._timers.append(timer)
            timer.start()

    def _start_sparge_heat(self, timer):
        with self._lock:
            self.actor.task(BrewTask(BrewTask.BOIL_TARGET_TEMP, BrewProcess._SPARGING_TEMP))
            self._sparging_stage = BrewProcess._SPARGE_HEATING
            if timer is not None:
                self._timers.remove(timer)

    ####################################################
    ## Callbacks from jam makers
    ####################################################
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

    ########################################################
    ## Mashing
    ########################################################
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

if __name__ == "__main__":
    print BrewStages.INITIAL