"""Contains classes for beer recipe handling"""

import config


class Recipe(object):
    "Contains data needed for Pombru to brew a beer."

    def __init__(self, mash_stages=None, boiling_time=60, mash_water=15, sparge_water=20, hop_timing=None):
        """Constructor. The parameters are:
        mash_stages: array of (temperature, minutes) pairs
        boiling_time: how long boil the wort (minutes)
        mash_water: amount of mash water (litres)
        sparge_water: amount of sparging water (litres)
        hop_timing: array of (arm id, minutes) pairs, after start of boil,
            how many minutes later should an arm release its hop
            arms start from 1
        """
        if mash_stages is None:
            mash_stages = [(64, 90)]
        if hop_timing is None:
            hop_timing = []
        self.mash_stages = mash_stages
        self.boiling_time = boiling_time
        self.mash_water = mash_water
        self.sparge_water = sparge_water
        self.hop_timing = hop_timing

    def __str__(self):
        return ("Recipe[mash stages: " + str(self.mash_stages) + ", boiling time: " +
                str(self.boiling_time) + "min, mash water: " + str(self.mash_water) + "L, sparge water: " + str(self.sparge_water) + "L]")


def from_config():
    cp = config.config.cp
    recipe = cp["recipe"]

    mash_stages = []
    mashcount = int(recipe["MashStageCount"])
    for mashstage in range(1, mashcount + 1):
        temp = int(recipe["MashStage" + str(mashstage) + "Temp"])
        minutes = int(recipe["MashStage" + str(mashstage) + "Min"])
        mash_stages.append((temp, minutes))

    boiling_time = int(recipe["BoilingTime"])
    mash_water = int(recipe["MashWaterLiter"])
    sparge_water = int(recipe["SpargeWaterLiter"])
    # TODO hop timing

    ret = Recipe(mash_stages, boiling_time, mash_water, sparge_water)
    return ret
