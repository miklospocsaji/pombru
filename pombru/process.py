"Module contains classes which manage the brewing process."
import datetime
import functools
import logging
import threading
from time import sleep
import traceback

import config
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
    SPARGE_PAUSE_2 = {KEY_NAME: "Second pause while sparging", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: SPARGE_MASH_TO_TEMP_3}
    SPARGE_CIRCULATE_IN_MASH_2 = {KEY_NAME: "Sparging - circulating in mash tun II.", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: SPARGE_PAUSE_2}
    SPARGE_BOIL_TO_MASH_2 = {KEY_NAME: "Sparging - transferring water to mashing tun II.", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: SPARGE_CIRCULATE_IN_MASH_2}
    SPARGE_MASH_TO_TEMP_2 = {KEY_NAME: "Sparging - transferring wort to temporary II.", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: SPARGE_BOIL_TO_MASH_2}
    SPARGE_PAUSE_1 = {KEY_NAME: "First pause while sparging", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: SPARGE_MASH_TO_TEMP_2}
    SPARGE_CIRCULATE_IN_MASH_1 = {KEY_NAME: "Sparging - circulating in mash tun I.", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: SPARGE_PAUSE_1}
    SPARGE_BOIL_TO_MASH_1 = {KEY_NAME: "Sparging - transferring water to mashing tun I.", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: SPARGE_CIRCULATE_IN_MASH_1}
    SPARGE_MASH_TO_TEMP_1 = {KEY_NAME: "Sparging - transferring wort to temporary I.", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: SPARGE_BOIL_TO_MASH_1}
    WAIT_FOR_SPARGING_WATER = {KEY_NAME: "Waiting for the sparging water to heat up", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: SPARGE_MASH_TO_TEMP_1}
    MASHING_PAUSE = {KEY_NAME: "Paused after mashing. Please take a iodine test and continue", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: WAIT_FOR_SPARGING_WATER}
    MASHING_4 = {KEY_NAME: "Mashing - step IV.", KEY_MASH_STAGE_NUM: 4, KEY_NEXT_STAGE: MASHING_PAUSE}
    MASHING_3 = {KEY_NAME: "Mashing - step III.", KEY_MASH_STAGE_NUM: 3, KEY_NEXT_STAGE: MASHING_4}
    MASHING_2 = {KEY_NAME: "Mashing - step II.", KEY_MASH_STAGE_NUM: 2, KEY_NEXT_STAGE: MASHING_3}
    MASHING_1 = {KEY_NAME: "Mashing - step I.", KEY_MASH_STAGE_NUM: 1, KEY_NEXT_STAGE: MASHING_2}
    MASHING_TEMP_TO_BOIL = {KEY_NAME: "Prepare for mashing - transferring from temp to boil", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: MASHING_1}
    MASHING_BOIL_TO_MASH = {KEY_NAME: "Prepare for mashing - transferring from boil to mash", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: MASHING_TEMP_TO_BOIL}
    MASHING_PREPARE = {KEY_NAME: "Prepare for mashing - heat up for first step", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: MASHING_BOIL_TO_MASH}
    INITIAL = {KEY_NAME: "Initial stage", KEY_MASH_STAGE_NUM: 0, KEY_NEXT_STAGE: MASHING_PREPARE}

class BrewProcess(object):
    "Manages a process of the whole brewing."

    def __init__(self, recipe):
        self.recipe = recipe
        self._timers = []
        self.actor = None
        self._lock = threading.RLock()
        self._brewing_stage = BrewStages.INITIAL
        self._sparging_water_ready = False
        self._stage_minutes = {}
        self._brewing_stage_started_at = None
        self._paused_at = None
        self.reload_config()
        self._calculate_stage_minutes()

    def reload_config(self):
        self._pump_seconds_per_liter = config.config.pump_seconds_per_liter
        self._sparging_temperature = config.config.sparging_temperature
        self._sparging_circulate_secs = config.config.sparging_circulate_secs

    def _calculate_stage_minutes(self):
        self._stage_minutes[BrewStages.INITIAL["name"]] = 0
        def mashtime(recipe, mashstage):
            if mashstage > len(recipe.mash_stages):
                return 0
            start = 20
            if mashstage > 1:
                start = recipe.mash_stages[mashstage - 2][0]
            # Assumption: 30 seconds per degrees celsius
            return ((recipe.mash_stages[mashstage - 1][0] - start) / 2.0 + recipe.mash_stages[mashstage - 1][1]) * 60
        self._stage_minutes[BrewStages.MASHING_PREPARE["name"]] = (self.recipe.mash_stages[0][0] - 20) / 2.0
        self._stage_minutes[BrewStages.MASHING_BOIL_TO_MASH["name"]] = (self.recipe.mash_water - 1) * self._pump_seconds_per_liter + 60
        self._stage_minutes[BrewStages.MASHING_TEMP_TO_BOIL["name"]] = (self.recipe.sparge_water - 1) * self._pump_seconds_per_liter + 60
        self._stage_minutes[BrewStages.MASHING_1["name"]] = self.recipe.mash_stages[0][1] * 60
        self._stage_minutes[BrewStages.MASHING_2["name"]] = mashtime(self.recipe, 2)
        self._stage_minutes[BrewStages.MASHING_3["name"]] = mashtime(self.recipe, 3)
        self._stage_minutes[BrewStages.MASHING_4["name"]] = mashtime(self.recipe, 4)
        self._stage_minutes[BrewStages.MASHING_PAUSE["name"]] = 0
        self._stage_minutes[BrewStages.WAIT_FOR_SPARGING_WATER["name"]] = 0
        self._stage_minutes[BrewStages.SPARGE_MASH_TO_TEMP_1["name"]] = (self.recipe.mash_water - 1) * self._pump_seconds_per_liter + 60
        self._stage_minutes[BrewStages.SPARGE_BOIL_TO_MASH_1["name"]] = (self.recipe.sparge_water / 2.0 - 1) * self._pump_seconds_per_liter + 60
        self._stage_minutes[BrewStages.SPARGE_CIRCULATE_IN_MASH_1["name"]] = self._sparging_circulate_secs
        self._stage_minutes[BrewStages.SPARGE_PAUSE_1["name"]] = 0
        self._stage_minutes[BrewStages.SPARGE_MASH_TO_TEMP_2["name"]] = self._stage_minutes[BrewStages.SPARGE_BOIL_TO_MASH_1["name"]]
        self._stage_minutes[BrewStages.SPARGE_BOIL_TO_MASH_2["name"]] = self._stage_minutes[BrewStages.SPARGE_BOIL_TO_MASH_1["name"]]
        self._stage_minutes[BrewStages.SPARGE_CIRCULATE_IN_MASH_2["name"]] = self._stage_minutes[BrewStages.SPARGE_CIRCULATE_IN_MASH_1["name"]]
        self._stage_minutes[BrewStages.SPARGE_PAUSE_2["name"]] = 0
        self._stage_minutes[BrewStages.SPARGE_MASH_TO_TEMP_3["name"]] = self._stage_minutes[BrewStages.SPARGE_BOIL_TO_MASH_1["name"]]
        self._stage_minutes[BrewStages.SPARGE_TEMP_TO_BOIL["name"]] = (self.recipe.mash_water + self.recipe.sparge_water - 1) * self._pump_seconds_per_liter + 60
        self._stage_minutes[BrewStages.BOIL["name"]] = ((100 - self._sparging_temperature) / 2.0 + self.recipe.boiling_time) * 60
        logging.info("Stage minutes: " + str(self._stage_minutes))

    _MASH_VALVE_TO_MASH = "_MASH_VALVE_TO_MASH"
    _MASH_VALVE_TO_TEMP = "_MASH_VALVE_TO_TEMP"
    _BOIL_VALVE_TO_MASH = "_BOIL_VALVE_TO_MASH"
    _BOIL_VALVE_TO_TEMP = "_BOIL_VALVE_TO_TEMP"

    _TIMER_START_SPARGE_HEAT = "_TIMER_START_SPARGE_HEAT"
    _TIMER_MASH = "_TIMER_MASH"
    _TIMER_BOIL = "_TIMER_BOIL"
    _TIMER_SPARGING = "_TIMER_SPARGING"

    def start(self):
        "Starts the brewing process."
        self._enter_stage(BrewStages.INITIAL["next"])
        # Set up timer to start heating the sparging water
        total_mash_time = functools.reduce(lambda sum, (_, y): sum + y, self.recipe.mash_stages, 0)
        logging.debug("Total mash time: %d minutes", total_mash_time)

    def stop(self):
        self._reset()

    def pause(self):
        "Pauses the brewing."
        # TODO
        pass

    def cont(self):
        pass

    def cont_with(self, stage):
        with self._lock:
            for timer in self._timers:
                timer.cancel()
            self._timers = []
            self._stop_all()
        self._enter_stage(stage)

    def next(self):
        for timer in self._timers:
            timer.cancel()
        self._enter_stage(self._next_stage(self._brewing_stage))

    def get_status(self):
        """Returns a tuple with:
        - stopped|running|paused
        - the brewing stage
        - remaining time to complmeting the brewing stage in seconds
        - remaining time to complete the brewing in seconds
        """
        status = 'stopped' if self._brewing_stage is BrewStages.INITIAL else 'running'
        stage_remaining = self._stage_minutes[self._brewing_stage["name"]]
        stage_elapsed = 0
        if self._brewing_stage_started_at:
            stage_elapsed = datetime.datetime.utcnow() - self._brewing_stage_started_at
            stage_elapsed = stage_elapsed.seconds
        return status, self._brewing_stage, stage_remaining - stage_elapsed, self._get_all_process_remaining_time()

    def _get_all_process_remaining_time(self):
        # TODO handle paused state
        ret = self._get_time_remaining(self._brewing_stage)
        now = datetime.datetime.utcnow()
        if self._brewing_stage_started_at:
            elapsed = now - self._brewing_stage_started_at
            return ret - elapsed.seconds
        else:
            return ret

    def _get_time_remaining(self, stage):
        # TODO handle paused state
        if stage[BrewStages.KEY_NEXT_STAGE] is None:
            return self._stage_minutes[stage["name"]]
        else:
            return self._stage_minutes[stage["name"]] + self._get_time_remaining(stage[BrewStages.KEY_NEXT_STAGE])

    def _set_valves_and_pumps(self, mash_pump=False, temp_pump=False, boil_pump=False, mash_valve=_MASH_VALVE_TO_MASH, boil_valve=_BOIL_VALVE_TO_MASH, param=None):
        logging.debug("set_valves_and_pumps: " + str(locals()))
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

        if boil_valve == BrewProcess._BOIL_VALVE_TO_MASH:
            events.append(BrewTask(BrewTask.SET_BOIL_VALVE_TARGET_MASH))
        elif boil_valve == BrewProcess._BOIL_VALVE_TO_TEMP:
            events.append(BrewTask(BrewTask.SET_BOIL_VALVE_TARGET_TEMP))

        # Set pumps
        if mash_pump:
            events.append(BrewTask(BrewTask.START_MASH_PUMP, param))
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
        with self._lock:
            self._stop_all()
            self._calculate_stage_minutes()
            self._brewing_stage = BrewStages.INITIAL
            self._brewing_stage_started_at = None
            self._sparging_water_ready = False

    def _next_stage(self, stage):
        next_stage = stage["next"]
        mashstage = next_stage["mash"]
        if mashstage > len(self.recipe.mash_stages):
            # This mash stage is not defined in the recipe
            return BrewStages.MASHING_4["next"]
        return next_stage


    def _get_pump_time(self, liters, to_empty):
        if to_empty:
            return (liters - 1) * self._pump_seconds_per_liter + 60
        else:
            return liters * self._pump_seconds_per_liter

    #################################################
    ## State machine
    #################################################
    def _enter_stage(self, stage):
        logging.info("enter stage: " + stage["name"])
        self.log_call_stack()
        pause_stage = stage in [BrewStages.SPARGE_PAUSE_1, BrewStages.SPARGE_PAUSE_2, BrewStages.MASHING_PAUSE]
        if not config.config.pause and pause_stage:
            logging.info("Pausing not enabled by config, skipping automatically to next stage")
            self._enter_stage(stage[BrewStages.KEY_NEXT_STAGE])
        # Time multiplier when the mash tun pump operates in sparging mode
        sparge_pump_multiplier = float(config.config.sparge_circulate_distribution_work + config.config.sparge_circulate_distribution_idle) / float(config.config.sparge_circulate_distribution_work)
        mashstage = stage["mash"]
        first_mash_temp = self.recipe.mash_stages[0][0]
        self._brewing_stage_started_at = datetime.datetime.utcnow()
        if stage == BrewStages.INITIAL:
            raise ValueError("Initial is not a valid stage to resume to.")
        elif stage == BrewStages.MASHING_PREPARE:
            self.actor.task(BrewTask(BrewTask.BOIL_TARGET_TEMP, first_mash_temp))
        elif stage == BrewStages.MASHING_BOIL_TO_MASH:
            self._set_valves_and_pumps(boil_valve=BrewProcess._BOIL_VALVE_TO_MASH, boil_pump=True)
            timer = utils.PausableTimer(self._get_pump_time(self.recipe.mash_water, True), self._enter_next_stage_on_timer, name='timer: mash water from boil to mash')
            self._timers.append(timer)
            timer.start()
            #self.actor.task(BrewTask(BrewTask.MASH_TARGET_TEMP, first_mash_temp))
        elif stage == BrewStages.MASHING_TEMP_TO_BOIL:
            self._set_valves_and_pumps(temp_pump=True)
            timer = utils.PausableTimer(self._get_pump_time(self.recipe.sparge_water, True), self._enter_next_stage_on_timer, name='timer: sparging water from temp to boil')
            self._timers.append(timer)
            timer.start()
        elif mashstage > 0:
            if mashstage == 1:
                self.actor.task(BrewTask(BrewTask.BOIL_TARGET_TEMP, self._sparging_temperature))
            self._mash(mashstage)
        elif stage == BrewStages.WAIT_FOR_SPARGING_WATER:
            # It is possible that sparging water is already hot enough
            if self._sparging_water_ready:
                self._enter_stage(stage["next"])
                return # to avoid setting the brewing stage at the end...
        elif stage == BrewStages.SPARGE_MASH_TO_TEMP_1:
            self._sparge(self._get_pump_time(self.recipe.mash_water, True) * sparge_pump_multiplier, mash_pump=True, mash_valve=BrewProcess._MASH_VALVE_TO_TEMP, param='SPARGE_DISTRIBUTION')
        elif stage == BrewStages.SPARGE_BOIL_TO_MASH_1:
            self._sparge(self._get_pump_time(self.recipe.sparge_water / 2.0, False), boil_pump=True, boil_valve=BrewProcess._BOIL_VALVE_TO_MASH)
            self.actor.task(BrewTask(BrewTask.MASH_TARGET_TEMP, config.config.sparging_temperature))
        elif stage == BrewStages.SPARGE_CIRCULATE_IN_MASH_1:
            self._sparge(config.config.sparging_circulate_secs, mash_pump=True, mash_valve=BrewProcess._MASH_VALVE_TO_MASH, param='SPARGE_DISTRIBUTION')
        elif stage == BrewStages.SPARGE_PAUSE_1 or stage == BrewStages.SPARGE_PAUSE_2:
            self._set_valves_and_pumps(mash_valve=None, boil_valve=None)
        elif stage == BrewStages.SPARGE_MASH_TO_TEMP_2:
            self._sparge(self._get_pump_time(self.recipe.sparge_water / 2.0, True) * sparge_pump_multiplier, mash_pump=True, mash_valve=BrewProcess._MASH_VALVE_TO_TEMP, param='SPARGE_DISTRIBUTION')
        elif stage == BrewStages.SPARGE_BOIL_TO_MASH_2:
            self._sparge(self._get_pump_time(self.recipe.sparge_water / 2.0, True), boil_pump=True, boil_valve=BrewProcess._BOIL_VALVE_TO_MASH)
            self.actor.task(BrewTask(BrewTask.STOP_BOIL_KETTLE))
        elif stage == BrewStages.SPARGE_CIRCULATE_IN_MASH_2:
            self._sparge(config.config.sparging_circulate_secs, mash_pump=True, mash_valve=BrewProcess._MASH_VALVE_TO_MASH, param='SPARGE_DISTRIBUTION')
        elif stage == BrewStages.SPARGE_MASH_TO_TEMP_3:
            self.actor.task(BrewTask(BrewTask.STOP_MASHING_TUN))
            self._sparge(self._get_pump_time(self.recipe.sparge_water / 2.0, True) * sparge_pump_multiplier, mash_pump=True, mash_valve=BrewProcess._MASH_VALVE_TO_TEMP, param='SPARGE_DISTRIBUTION')
        elif stage == BrewStages.SPARGE_TEMP_TO_BOIL:
            self._sparge(self._get_pump_time(self.recipe.mash_water + self.recipe.sparge_water, True), temp_pump=True)
        elif stage == BrewStages.BOIL:
            self._stop_all()
            self.actor.task(BrewTask(BrewTask.BOIL_TARGET_TEMP, 100))
        elif pause_stage:
            pass
        else:
            raise ValueError("Unhandled target stage:" + stage["name"])
        self._brewing_stage_started_at = datetime.datetime.utcnow()
        self._brewing_stage = stage

    ####################################################
    ## Callbacks from jam makers
    ####################################################
    def mash_target_reached(self, temp):
        with self._lock:
            logging.info("mashtun target reached: " + str(temp))
            if self._brewing_stage == BrewStages.INITIAL:
                return
            _, minutes = self.recipe.mash_stages[self._brewing_stage["mash"] - 1]
            timer = utils.PausableTimer(minutes * 60, self._enter_next_stage_on_timer, name=BrewProcess._TIMER_MASH)
            timer.start()
            self._timers.append(timer)
            # Update to reflect correct remaining time
            self._stage_minutes[self._brewing_stage["name"]] = 60 * minutes
            self._brewing_stage_started_at = datetime.datetime.utcnow()

    def boil_target_reached(self, temp):
        with self._lock:
            logging.info("boiler target reached: " + str(temp) + " stage: " + self._brewing_stage["name"])
            if self._brewing_stage == BrewStages.INITIAL:
                return
            if temp == self._sparging_temperature:
                self._sparging_water_ready = True
            if self._brewing_stage == BrewStages.WAIT_FOR_SPARGING_WATER:
                # Process waited for sparging water
                self._enter_stage(BrewStages.WAIT_FOR_SPARGING_WATER["next"])
            elif self._brewing_stage == BrewStages.BOIL:
                # Boiling
                # TODO: hops
                timer = utils.PausableTimer(self.recipe.boiling_time * 60, self._boil_finished, name=BrewProcess._TIMER_BOIL)
                self._timers.append(timer)
                timer.start()
                # Update remaining time
                self._stage_minutes[self._brewing_stage["name"]] = self.recipe.boiling_time * 60
            elif self._brewing_stage == BrewStages.MASHING_PREPARE:
                self._enter_stage(self._brewing_stage["next"])

    def _enter_next_stage_on_timer(self, timer, *_, **__):
        with self._lock:
            logging.debug("args: " + str(_) + ", kwargs: " + str(__))
            logging.debug("_enter_next_stage_on_timer: " + timer.name)
            self._timers.remove(timer)
            if self._brewing_stage == BrewStages.INITIAL:
                return
            self._enter_stage(self._next_stage(self._brewing_stage))

    ########################################################
    ## Mashing
    ########################################################
    def _mash(self, step):
        if step > len(self.recipe.mash_stages):
            raise ValueError("Mashing step " + str(step) + " is not defined in recipe!")
        temp, _ = self.recipe.mash_stages[step - 1]
        self.actor.task(BrewTask(BrewTask.MASH_TARGET_TEMP, temp))
        self._set_valves_and_pumps(mash_pump=True, param='MASH_DISTRIBUTION')

    #########################################
    ## SPARGING
    #########################################

    def _sparge(self, waittime, **kwargs):
        with self._lock:
            self._set_valves_and_pumps(**kwargs)
            timer = utils.PausableTimer(waittime, self._enter_next_stage_on_timer, BrewProcess._TIMER_SPARGING)
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

    def log_call_stack(self):
        for line in traceback.format_stack():
            logging.debug(line)
        logging.debug("timers: " + str(self._timers))

if __name__ == "__main__":
    print BrewStages.INITIAL
