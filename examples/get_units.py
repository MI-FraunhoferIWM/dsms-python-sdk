"""DSMS unit conversion example"""

import os

from dotenv import load_dotenv

from dsms import DSMS
from dsms.knowledge.semantics.units import get_conversion_factor

env = os.path.join("..", ".env")

load_dotenv(env)

dsms = DSMS()

# Meters to millimeters
print(get_conversion_factor("m", "mm"))

# Kilometers to Inches, we can also round the factor in decimal places
print(get_conversion_factor("km", "in", rounded=1))

# GigaPascal to MegaPascal
print(get_conversion_factor("GPa", "MPa"))

# we can also use the qudt iris
print(
    get_conversion_factor(
        "http://qudt.org/vocab/unit/M", "http://qudt.org/vocab/unit/IN"
    )
)

# this will raise an error because the units are not compatible
try:
    # Kilopascal to Centimeter
    get_conversion_factor("kPa", "cm")
except ValueError as error:
    print(error.args)
