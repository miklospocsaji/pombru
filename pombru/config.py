import configparser

class PombruConfig:

    CONFIG_FILE = "pombru.ini"

    SECTION_PUMPS = "pumps"
    PROPERTY_SECONDS_PER_LITER = "SecondsPerLiter"
    PROPERTY_MASH_PUMP_CIRCULATE_DISTRIBUTION_WORK = "CirculateDistributionWork"
    PROPERTY_MASH_PUMP_CIRCULATE_DISTRIBUTION_IDLE = "CirculateDistributionIdle"

    SECTION_PID = "pid"
    PROPERTY_PROPORTIONAL = "Proportional"
    PROPERTY_INTEGRAL = "Integral"
    PROPERTY_DERIVATIVE = "Derivative"

    SECTION_PROCESS = "process"
    PROPERTY_SPARGING_TEMPERATURE = "SpargingTemperature"
    PROPERTY_SPARGING_CIRCULATE_SECS = "SpargingCirculateSecs"

    def __init__(self):
        self.reload()

    def reload(self):
        self.cp = configparser.ConfigParser()
        self.cp.read(PombruConfig.CONFIG_FILE)

        # Section "pumps"
        self.pump_seconds_per_liter = int(self.cp[PombruConfig.SECTION_PUMPS][PombruConfig.PROPERTY_SECONDS_PER_LITER])
        self.mash_pump_circulate_distribution_work = int(self.cp[PombruConfig.SECTION_PUMPS][PombruConfig.PROPERTY_MASH_PUMP_CIRCULATE_DISTRIBUTION_WORK])
        self.mash_pump_circulate_distribution_idle = int(self.cp[PombruConfig.SECTION_PUMPS][PombruConfig.PROPERTY_MASH_PUMP_CIRCULATE_DISTRIBUTION_IDLE])

        # Section "process"
        self.sparging_temperature = int(self.cp[PombruConfig.SECTION_PROCESS][PombruConfig.PROPERTY_SPARGING_TEMPERATURE])
        self.sparging_circulate_secs = int(self.cp[PombruConfig.SECTION_PROCESS][PombruConfig.PROPERTY_SPARGING_CIRCULATE_SECS])

        # Section "pid"
        self.pid_proportional = float(self.cp[PombruConfig.SECTION_PID][PombruConfig.PROPERTY_PROPORTIONAL])
        self.pid_integral = float(self.cp[PombruConfig.SECTION_PID][PombruConfig.PROPERTY_INTEGRAL])
        self.pid_derivative = float(self.cp[PombruConfig.SECTION_PID][PombruConfig.PROPERTY_DERIVATIVE])

config = PombruConfig()

if __name__ == '__main__':
    print PombruConfig.PROPERTY_SECONDS_PER_LITER, config.pump_seconds_per_liter
