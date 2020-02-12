#! /usr/bin/env python
from grand import LTP
from grand.simulation import Antenna, ShowerEvent, TabulatedAntennaModel


# XXX Get this from the shower
from astropy.coordinates import CartesianRepresentation
import astropy.units as u
xmax = CartesianRepresentation(0 * u.m, 0 * u.m, 2.9 * u.km)


# Load the radio shower simulation data
#
# XXX Handle COREAS data / with the missing frame case
shower = ShowerEvent.load("tests/simulation/data/zhaires")

# Define an antenna model
#
# A tabulated model of the Butterfly antenna is used. Note that a single EW
# arm is assumed here for the sake of simplicity

antenna_model = TabulatedAntennaModel.load(
    "HorizonAntenna_EWarm_leff_loaded.npy")

# Loop over electric fields and compute the corresponding voltages
for antenna_index, field in shower.fields.items():
    # Compute the antenna local frame
    #
    # The antenna is placed within the shower frame. It is oriented along the
    # local magnetic North by using an ENU/LTP frame (x: East, y: North, z:
    # Upward)

    antenna_location = shower.frame.realize_frame(field.r)
    antenna_frame = LTP(location=antenna_location, orientation="ENU",
                        magnetic=True, obstime=shower.frame.obstime)
    antenna = Antenna(model=antenna_model, frame=antenna_frame)

    # Compute the voltage on the antenna
    #
    # The electric field is assumed to be a plane-wave originating from the
    # shower axis at the depth of maximum development. Note that the direction
    # of observation and the electric field components are provided in the
    # shower frame. This is indicated by the `frame` named argument.

    direction = field.r - xmax
    voltage = antenna.compute_voltage(direction, field, frame=shower.frame)

    # XXX Add to a voltage collection