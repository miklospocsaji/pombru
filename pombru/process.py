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
    "Name, mash stage, next stage."
    KEY_NAME = "name"
    KEY_MASH_STAGE_NUM = "mash"
    KEY_NEXT_STAGE = "next"
    BOIL = {KEY_NAME: "Boiling wort", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: None}
    SPARGE_TEMP_TO_BOIL = {KEY_NAME: "Transferring wort to boiling kettle", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: BOIL}
    SPARGE_MASH_TO_TEMP_3 = {KEY_NAME: "Sparging - transferring wort to temporary III.", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: SPARGE_TEMP_TO_BOIL}
    SPARGE_CIRCULATE_IN_MASH_2 = {KEY_NAME: "Sparging - circulating in mash tun II.", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: SPARGE_MASH_TO_TEMP_3}
    SPARGE_BOIL_TO_MASH_2 = {KEY_NAME: "Sparging - transferring water to mashing tun II.", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: SPARGE_CIRCULATE_IN_MASH_2}
    SPARGE_MASH_TO_TEMP_2 = {KEY_NAME: "Sparging - transferring wort to temporary II.", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: SPARGE_BOIL_TO_MASH_2}
    SPARGE_CIRCULATE_IN_MASH_1 = {KEY_NAME: "Sparging - circulating in mash tun I.", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: SPARGE_MASH_TO_TEMP_2}
    SPARGE_BOIL_TO_MASH_1 = {KEY_NAME: "Sparging - transferring water to mashing tun I.", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: SPARGE_CIRCULATE_IN_MASH_1}
    SPARGE_MASH_TO_TEMP_1 = {KEY_NAME: "Sparging - transferring wort to temporary I.", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: SPARGE_BOIL_TO_MASH_1}
    WAIT_FOR_SPARGING_WATER = {KEY_NAME: "Waiting for the sparging water to heat up", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: SPARGE_MASH_TO_TEMP_1}
    MASHING_4 = {KEY_NAME: "Mashing - step IV.", KEY_MASH_STAGE_NUM: 4, KEY_NEXT_STAGE: WAIT_FOR_SPARGING_WATER}
    MASHING_3 = {KEY_NAME: "Mashing - step III.", KEY_MASH_STAGE_NUM: 3, KEY_NEXT_STAGE: MASHING_4}
    MASHING_2 = {KEY_NAME: "Mashing - step II.", KEY_MASH_STAGE_NUM: 2, KEY_NEXT_STAGE: MASHING_3}
    MASHING_1 = {KEY_NAME: "Mashing - step I.", KEY_MASH_STAGE_NUM: 1, KEY_NEXT_STAGE: MASHING_2}
    INITIAL = {KEY_NAME: "Initial stage", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: MASHING_1}


class BrewProcess(object):
    "Manages a process of the whole brewing."
    _PUMP_SECONDS_PER_LITER = 10
    _SPARGING_TEMP = 74

    def __init__(self, recipe, actor):
        self.recipe = recipe
        self._timers = []
        self.actor = actor
        self._lock = threading.RLock()
        self._brewing_stage = BrewStages.INITIAL
        self._sparging_water_ready = False

    _MASH_VALVE_TO_MASH = "_MASH_VALVE_TO_MASH"
    _MASH_VALVE_TO_TEMP = "_MASH_VALVE_TO_TEMP"
    _BOIL_VALVE_TO_MASH = "_BOIL_VALVE_TO_MASH"
    _BOIL_VALVE_TO_TEMP = "_BOIL_VALVE_TO_TEMP"

    _TIMER_START_SPARGE_HEAT = "_TIMER_START_SPARGE_HEAT"
    _TIMER_MASH = "_TIMER_MASH"
    _TIMER_BOIL = "_TIMER_BOIL"
    _TIMER_SPARGING = "_TIMER_SPARGING"

    def _set_valves_and_pumps(self, mash_pump=False, temp_pump=False, boil_pump=False, mash_valve=_MASH_VALVE_TO_MASH, boil_valve=_BOIL_VALVE_TO_MASH):
        events = []
        # Stop all pumps
        events.append(BrewTask(BrewTask.STOP_MASH_PUMP))
        events.append(BrewTask(BrewTask.STOP_TEMP_PUMP))
        events.append(BrewTask(BrewTask.STOP_BOIL_PUMP))

        # Set valves
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

        # Set pumps
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
        self._sparging_water_ready = False

    def _next_stage(self, stage):
        next_stage = stage["next"]
        mashstage = next_stage["mash"]
        if mashstage > len(self.recipe.mash_stages):
            # This mash stage is not defined in the recipe
            return BrewStages.MASHING_4["next"]
        return next_stage

    #################################################
    ## State machine
    #################################################
    def _enter_stage(self, stage):
        halfsparge_pump_time = self.recipe.sparge_water / 2.0 * BrewProcess._PUMP_SECONDS_PER_LITER
        mash_pump_time = self.recipe.mash_water * BrewProcess._PUMP_SECONDS_PER_LITER
        mashstage = stage["mash"]
        if stage == BrewStages.INITIAL:
            raise ValueError("Initial is not a valid stage to resume to.")
        elif mashstage > 0:
            self._mash(mashstage)
        elif stage == BrewStages.WAIT_FOR_SPARGING_WATER:
            # It is possible that sparging water is already hot enough
            if self._sparging_water_ready:
                self._enter_stage(stage["next"])
                return # to avoid setting the brewing stage at the end...
        elif stage == BrewStages.SPARGE_MASH_TO_TEMP_1:
            self._sparge(mash_pump_time, mash_pump=True, mash_valve=BrewProcess._MASH_VALVE_TO_TEMP)
        elif stage == BrewStages.SPARGE_BOIL_TO_MASH_1:
            self._sparge(halfsparge_pump_time, boil_pump=True, boil_valve=BrewProcess._BOIL_VALVE_TO_MASH)
        elif stage == BrewStages.SPARGE_CIRCULATE_IN_MASH_1:
            self._sparge(60, mash_pump=True, mash_valve=BrewProcess._MASH_VALVE_TO_MASH)
        elif stage == BrewStages.SPARGE_MASH_TO_TEMP_2:
            self._sparge(halfsparge_pump_time, mash_pump=True, mash_valve=BrewProcess._MASH_VALVE_TO_TEMP)
        elif stage == BrewStages.SPARGE_BOIL_TO_MASH_2:
            self._sparge(halfsparge_pump_time, boil_pump=True, boil_valve=BrewProcess._BOIL_VALVE_TO_MASH)
        elif stage == BrewStages.SPARGE_CIRCULATE_IN_MASH_2:
            self._sparge(60, mash_pump=True, mash_valve=BrewProcess._MASH_VALVE_TO_MASH)
        elif stage == BrewStages.SPARGE_MASH_TO_TEMP_3:
            self._sparge(halfsparge_pump_time, mash_pump=True, mash_valve=BrewProcess._MASH_VALVE_TO_TEMP)
        elif stage == BrewStages.SPARGE_TEMP_TO_BOIL:
            self._sparge(2 * halfsparge_pump_time + mash_pump_time, temp_pump=True)
        elif stage == BrewStages.BOIL:
            self._stop_all()
            self.actor.task(BrewTask(BrewTask.BOIL_TARGET_TEMP, 100))
        else:
            raise ValueError("Unhandled target stage:" + stage["name"])
        self._brewing_stage = stage

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
            timer = utils.PausableTimer(sparge_heat_delay * 60, self._start_sparge_heat, name=BrewProcess._TIMER_START_SPARGE_HEAT)
            self._timers.append(timer)
            timer.start()

    def _start_sparge_heat(self, timer):
        with self._lock:
            self.actor.task(BrewTask(BrewTask.BOIL_TARGET_TEMP, BrewProcess._SPARGING_TEMP))
            if timer is not None:
                self._timers.remove(timer)

    ####################################################
    ## Callbacks from jam makers
    ####################################################
    def mash_target_reached(self, temp):
        with self._lock:
            _, minutes = self.recipe.mash_stages[self._brewing_stage["mash"] - 1]
            timer = utils.PausableTimer(minutes * 60, self._mash_stage_done, name=BrewProcess._TIMER_MASH)
            timer.start()
            self._timers.append(timer)

    def boil_target_reached(self, temp):
        with self._lock:
            if temp == BrewProcess._SPARGING_TEMP:
                self._sparging_water_ready = True
            if self._brewing_stage == BrewStages.WAIT_FOR_SPARGING_WATER:
                # Process waited for sparging water
                self._enter_stage(BrewStages.WAIT_FOR_SPARGING_WATER[2])
            elif self._brewing_stage == BrewStages.BOIL:
                # Boiling
                # TODO: hops
                timer = utils.PausableTimer(self.recipe.boiling_time * 60, self._boil_finished, name=BrewProcess._TIMER_BOIL)
                self._timers.append(timer)
                timer.start()

    ########################################################
    ## Mashing
    ########################################################
    def _mash_stage_done(self, timer, *_, **__):
        with self._lock:
            self._timers.remove(timer)
            self._enter_stage(self._next_stage(self._brewing_stage))

    def _mash(self, step):
        if step > len(self.recipe.mash_stages):
            raise ValueError("Mashing step " + str(step) + " is not defined in recipe!")
        temp, _ = self.recipe.mash_stages[step - 1]
        self.actor.task(BrewTask(BrewTask.MASH_TARGET_TEMP, temp))
        self._set_valves_and_pumps(mash_pump=True)

    #########################################
    ## SPARGING
    #########################################

    def _sparging_stage_done(self, timer, *_, **__):
        with self._lock:
            self._timers.remove(timer)
            self._enter_stage(self._next_stage(self._brewing_stage))

    def _sparge(self, waittime, **kwargs):
        with self._lock:
            self._set_valves_and_pumps(**kwargs)
            timer = utils.PausableTimer(waittime, self._sparging_stage_done, BrewProcess._TIMER_SPARGING)
            self._timers.append(timer)
            timer.start()

    ################################################
    ## Boiling
    ################################################

    def _boil_finished(self, timer, *_, **__):
        with self._lock:
            self._reset()
            self._timers.remove(timer)
            # TODO cooling

if __name__ == "__main__":
    print BrewStages.INITIAL