import enum

_OUTPUTFINAL = "output_files/final/"

_OUTPUTINTERMEDIATE = "output_files/intermediate/"


class Outputfiles(enum.Enum):
    NationalBefore2000 = 1
    StateCountyBefore2000 = 2
    StateCountyAfter2000 = 3
    NationalAfter2000 = 4
