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
    "6F(1)",
    "3T(5)",
    "3J(5)",
    "3N(7)",
    "2T(5)",
    "1L(1)",
    "4M(5)",
    "5R(7)",
    "4B(1)",
    "4D(5)",
    "2J(7)",
    "4G(1)",
    "2P(1)",
    "2G(5)",
    "6M(5)",
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
