DEBUG = False # True = Testing, False = Running program 
SHIFT_REGISTER_SIZE = 16384
TDC_SHIFT_REGISTER_SIZE = 32

TDC_INPUT_MODES = ("Targets", "Targets Test", "HFPG")
LOG_COLUMNS = [
    "run",
    "part",
    "ion",
    "let",
    "angle",
    "test_type",
    "start_time",
    "start_date",
    "end_time",
    "end_date",
    "transients",
    "fluence",
    "test/error",
]
PARTS = [
    "2T5",
    "4J7",
    "5D5",
    "5R7",
    "3T5",
    "4M5",
    "6M5",
    "3N9",
    "4D5"
]
PARTS.sort()


IONS = [
    "Ne",
    "Tb",
    "Ag",
    "N",
    "Al",
    "O",
    "V",
    "Kr",
    "He",
    "Cu",
    "Ta",
    "Xe",
    "Ar",
    "Y",
    "Ca",
    "B",
    "Cl",
    "Si",
    "Bi",
]
IONS.sort()


FONT = ("Arial", 18)
PS_THRESHOLD_A = 0.1
PS_THRESHOLD_B = 0.2
PS_LATCH_CYCLES = 4

PS_CH1 = "P6V"
PS_CH2 = "P25V"
PS_CH3 = "N25V"
