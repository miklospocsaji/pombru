"""Contans classes for beer recipe handling"""

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
