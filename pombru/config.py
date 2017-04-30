import configparser

class PombruConfig:

    CONFIG_FILE = "pombru.ini"

    SECTION_PUMPS = "pumps"
    PROPERTY_SECONDS_PER_LITER = "SecondsPerLiter"
    PROPERTY_MASH_PUMP_CIRCULATE_DISTRIBUTION_WORK = "CirculateDistributionWork"
    PROPERTY_MASH_PUMP_CIRCULATE_DISTRIBUTION_IDLE = "CirculateDistributionIdle"

    SECTION_PROCESS = "process"
    PROPERTY_SPARGING_TEMPERATURE = "SpargingTemperature"
    PROPERTY_SPARGING_CIRCULATE_SECS = "SpargingCirculateSecs"

    def __init__(self):
        self.reload()

    def reload(self):
        self.cp = configparser.ConfigParser()
        self.cp.read(PombruConfig.CONFIG_FILE)
        self.pump_seconds_per_liter = int(self.cp[PombruConfig.SECTION_PUMPS][PombruConfig.PROPERTY_SECONDS_PER_LITER])
        self.mash_pump_circulate_distribution_work = int(self.cp[PombruConfig.SECTION_PUMPS][PombruConfig.PROPERTY_MASH_PUMP_CIRCULATE_DISTRIBUTION_WORK])
        self.mash_pump_circulate_distribution_idle = int(self.cp[PombruConfig.SECTION_PUMPS][PombruConfig.PROPERTY_MASH_PUMP_CIRCULATE_DISTRIBUTION_IDLE])
        self.sparging_temperature = int(self.cp[PombruConfig.SECTION_PROCESS][PombruConfig.PROPERTY_SPARGING_TEMPERATURE])
        self.sparging_circulate_secs = int(self.cp[PombruConfig.SECTION_PROCESS][PombruConfig.PROPERTY_SPARGING_CIRCULATE_SECS])

config = PombruConfig()

if __name__ == '__main__':
    print PombruConfig.PROPERTY_SECONDS_PER_LITER, config.pump_seconds_per_liter
