import configparser

class PombruConfig:

    CONFIG_FILE = "pombru.ini"

    SECTION_PUMPS = "pumps"
    PROPERTY_SECONDS_PER_LITER_MASH_TO_TEMP = "SecondsPerLiterMashToTemp"
    PROPERTY_SECONDS_PER_LITER_TEMP_TO_BOIL = "SecondsPerLiterTempToBoil"
    PROPERTY_SECONDS_PER_LITER_BOIL_TO_TEMP = "SecondsPerLiterBoilToTemp"
    PROPERTY_SECONDS_PER_LITER_BOIL_TO_MASH = "SecondsPerLiterBoilToMash"
    PROPERTY_MASH_CIRCULATE_DISTRIBUTION_WORK = "MashCirculateDistributionWork"
    PROPERTY_MASH_CIRCULATE_DISTRIBUTION_IDLE = "MashCirculateDistributionIdle"
    PROPERTY_SPARGE_CIRCULATE_DISTRIBUTION_WORK = "SpargeCirculateDistributionWork"
    PROPERTY_SPARGE_CIRCULATE_DISTRIBUTION_IDLE = "SpargeCirculateDistributionIdle"

    SECTION_PID = "pid"
    PROPERTY_PROPORTIONAL = "Proportional"
    PROPERTY_INTEGRAL = "Integral"
    PROPERTY_DERIVATIVE = "Derivative"

    SECTION_PROCESS = "process"
    PROPERTY_SPARGING_TEMPERATURE = "SpargingTemperature"
    PROPERTY_SPARGING_CIRCULATE_SECS = "SpargingCirculateSecs"
    PROPERTY_SPARGING_DELAY_BETWEEN_MASH_TO_TEMP_STAGES = "SpargingDelayBetweenMashToTempStages"
    PROPERTY_PAUSE = "Pause"
    PROPERTY_PREBOIL_MASH_TO_TEMP_CYCLE = "PreBoilMashToTempCycle"
    PROPERTY_PREBOIL_MASH_TO_TEMP_PERIOD = "PreBoilMashToTempPeriod"

    SECTION_VALVES = "valves"
    PROPERTY_VALVE_SETTLE_TIME_SECS = "SettleTimeSecs"

    def __init__(self):
        self.reload()

    def reload(self):
        self.cp = configparser.ConfigParser()
        self.cp.read(PombruConfig.CONFIG_FILE)

        # Section "pumps"
        self.pump_seconds_per_liter_mash_to_temp = float(self.cp[PombruConfig.SECTION_PUMPS][PombruConfig.PROPERTY_SECONDS_PER_LITER_MASH_TO_TEMP])
        self.pump_seconds_per_liter_temp_to_boil = float(self.cp[PombruConfig.SECTION_PUMPS][PombruConfig.PROPERTY_SECONDS_PER_LITER_TEMP_TO_BOIL])
        self.pump_seconds_per_liter_boil_to_temp = float(self.cp[PombruConfig.SECTION_PUMPS][PombruConfig.PROPERTY_SECONDS_PER_LITER_BOIL_TO_TEMP])
        self.pump_seconds_per_liter_boil_to_mash = float(self.cp[PombruConfig.SECTION_PUMPS][PombruConfig.PROPERTY_SECONDS_PER_LITER_BOIL_TO_MASH])
        self.mash_circulate_distribution_work = int(self.cp[PombruConfig.SECTION_PUMPS][PombruConfig.PROPERTY_MASH_CIRCULATE_DISTRIBUTION_WORK])
        self.mash_circulate_distribution_idle = int(self.cp[PombruConfig.SECTION_PUMPS][PombruConfig.PROPERTY_MASH_CIRCULATE_DISTRIBUTION_IDLE])
        self.sparge_circulate_distribution_work = int(self.cp[PombruConfig.SECTION_PUMPS][PombruConfig.PROPERTY_SPARGE_CIRCULATE_DISTRIBUTION_WORK])
        self.sparge_circulate_distribution_idle = int(self.cp[PombruConfig.SECTION_PUMPS][PombruConfig.PROPERTY_SPARGE_CIRCULATE_DISTRIBUTION_IDLE])

        # Section "process"
        self.sparging_temperature = int(self.cp[PombruConfig.SECTION_PROCESS][PombruConfig.PROPERTY_SPARGING_TEMPERATURE])
        self.sparging_circulate_secs = int(self.cp[PombruConfig.SECTION_PROCESS][PombruConfig.PROPERTY_SPARGING_CIRCULATE_SECS])
        self.sparging_delay_between_mash_to_temp_stages = int(self.cp[PombruConfig.SECTION_PROCESS][PombruConfig.PROPERTY_SPARGING_DELAY_BETWEEN_MASH_TO_TEMP_STAGES])
        self.pause = bool(self.cp[PombruConfig.SECTION_PROCESS][PombruConfig.PROPERTY_PAUSE].lower() == 'true')
        self.preboil_mash_to_temp_cycle = int(self.cp[PombruConfig.SECTION_PROCESS][PombruConfig.PROPERTY_PREBOIL_MASH_TO_TEMP_CYCLE])
        self.preboil_mash_to_temp_period = int(self.cp[PombruConfig.SECTION_PROCESS][PombruConfig.PROPERTY_PREBOIL_MASH_TO_TEMP_PERIOD])

        # Section "pid"
        self.pid_proportional = float(self.cp[PombruConfig.SECTION_PID][PombruConfig.PROPERTY_PROPORTIONAL])
        self.pid_integral = float(self.cp[PombruConfig.SECTION_PID][PombruConfig.PROPERTY_INTEGRAL])
        self.pid_derivative = float(self.cp[PombruConfig.SECTION_PID][PombruConfig.PROPERTY_DERIVATIVE])

        # Section "valves"
        self.valve_settle_time_secs = int(self.cp[PombruConfig.SECTION_VALVES][PombruConfig.PROPERTY_VALVE_SETTLE_TIME_SECS])

config = PombruConfig()
