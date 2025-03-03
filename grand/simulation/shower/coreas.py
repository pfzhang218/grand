from __future__ import annotations

from collections import OrderedDict
from datetime import datetime
from logging import getLogger
import os
from pathlib import Path
import re
from typing import Dict, Optional, List

# import astropy.constants
# from astropy.coordinates import CartesianRepresentation,                       \
#                                PhysicsSphericalRepresentation
# from astropy.time import Time
# import astropy.units as u

from grand import CartesianRepresentation, SphericalRepresentation
import numpy

from .generic import CollectionEntry, FieldsCollection, ShowerEvent
from ..antenna import ElectricField
from ..pdg import ParticleCode
from ...tools.coordinates import ECEF, LTP

__all__ = ["CoreasShower"]


logger = getLogger(__name__)


"""CORSIKA particle Id to PDG code"""
_id_to_code: Dict[int, ParticleCode] = {
    14: ParticleCode.PROTON,
    5626: ParticleCode.IRON,
}

# RK. TODO: This class has not been checked properly. Rework on this.
class CoreasShower(ShowerEvent):
    @classmethod
    def _check_dir(cls, path: Path) -> bool:
        try:
            info_file = path.glob("*.reas").__next__()
        except StopIteration:
            return False
        return True

    @classmethod
    def _from_dir(cls, path: Path) -> CoreasShower:
        if not path.exists():
            raise FileNotFoundError(path)

        matches = path.glob("*.reas")
        try:
            reas_path = matches.__next__()
        except StopIteration:
            raise FileNotFoundError(path / "*.reas")
        else:
            index = int(reas_path.name[3:9])
            reas = cls._parse_reas(path, index)

            try:
                matches.__next__()
            except StopIteration:
                pass
            else:
                logger.warning(f"Multiple shower simulations in {path}. Loading only one.")
        if not reas:
            raise TypeError
        config = {
            "energy": float(reas["PrimaryParticleEnergy"]) * 1e-09,  # << u.GeV,
            "zenith": (180 - float(reas["ShowerZenithAngle"])),  # << u.deg,
            "azimuth": float(reas["ShowerAzimuthAngle"]),  # << u.deg,
            "primary": _id_to_code[int(reas["PrimaryParticleType"])],
        }

        core = CartesianRepresentation(
            x=float(reas["CoreCoordinateNorth"]) * 1e-02,
            y=float(reas["CoreCoordinateWest"]) * 1e-02,
            z=float(reas["CoreCoordinateVertical"]) * 1e-02,
        )

        # unit = u.m)
        config["core"] = core

        # geomagnet = PhysicsSphericalRepresentation(
        geomagnet = SphericalRepresentation(
            theta=(90 + float(reas["MagneticFieldInclinationAngle"])),  # << u.deg,
            phi=0,  # << u.deg,
            # r = float(reas['MagneticFieldStrength']) * 1E-04 << u.T)
            r=float(reas["MagneticFieldStrength"]) * 1e05,
        )  # nT
        # config['geomagnet'] = geomagnet.represent_as(CartesianRepresentation)
        config["geomagnet"] = CartesianRepresentation(geomagnet)

        distance = float(reas["DistanceOfShowerMaximum"]) * 1e-02  # << u.m
        theta, phi = config["zenith"], config["azimuth"]
        # ct, st = numpy.cos(theta), numpy.sin(theta) #RK, was this wrong? theta is in deg.
        ct, st = numpy.cos(numpy.deg2rad(theta)), numpy.sin(numpy.deg2rad(theta))
        direction = CartesianRepresentation(x=st * numpy.cos(phi), y=st * numpy.sin(phi), z=ct)
        config["maximum"] = core - distance * direction

        antpos = cls._parse_coreas_bins(path, index)
        if antpos is None:
            antpos = cls._parse_list(path, index)
            if antpos is None:
                antpos = cls._parse_info(path, index)

        positions = {}
        if antpos is not None:
            for (antenna, r) in antpos:
                positions[antenna] = CartesianRepresentation(x=r[0], y=r[1], z=r[2])

        fields: Optional[FieldsCollection] = None
        raw_fields = {}
        try:
            fields_path = path.glob("*_coreas").__next__()
        except StopIteration:
            pass
        else:
            # cgs2si = (astropy.constants.c / (u.m / u.s)).value * 1E+02 * u.uV / u.m
            cgs2si = 29979245800.0
            pattern = re.compile("(\d+).dat$")
            for antenna_path in fields_path.glob("*.dat"):
                antenna = int(pattern.search(str(antenna_path))[1])  # type: ignore[index]
                logger.debug(f"Loading trace for antenna {antenna}")
                data = numpy.loadtxt(antenna_path)
                t = data[:, 0] * 1e09  # * u.ns
                Ex = data[:, 1] * cgs2si
                Ey = data[:, 2] * cgs2si
                Ez = data[:, 3] * cgs2si
                electric = ElectricField(
                    t, CartesianRepresentation(x=Ex, y=Ey, z=Ez), positions[antenna]
                )
                raw_fields[antenna] = CollectionEntry(electric)

            fields = FieldsCollection()
            for key in sorted(raw_fields.keys()):
                fields[key] = raw_fields[key]

        ret = cls(fields=fields, **config)  # type: ignore[arg-type]
        return ret

    @classmethod
    def _parse_reas(cls, path: Path, index: int) -> Optional[Dict]:
        """Parse a SIMxxxxxx.reas file"""
        reas_file = path / f"SIM{index:06d}.reas"
        if not reas_file.exists():
            return None

        with reas_file.open() as f:
            txt = f.read()

        pattern = re.compile("([^=# \n\t]+)[ \t]*=[ \t]*([^ ;\t]*)[ \t]*;")
        setattr(cls, "_reas_pattern", pattern)

        matches = pattern.findall(txt)

        def tonum(s):
            s2 = s[1:] if s.startswith("-") else s
            return int(s) if s2.isdecimal() else float(s)

        return {key: tonum(value) for (key, value) in matches}

    @classmethod
    def _parse_coreas_bins(cls, path: Path, index: int):
        """Parse a SIMxxxxxx_coreas.bins file"""
        bins_file = path / f"SIM{index:06d}_coreas.bins"
        if not bins_file.exists():
            return None

        data = []
        pattern = re.compile("(\d+).dat$")
        with bins_file.open() as f:
            for line in f:
                d = line.split()
                if not d:
                    continue
                antenna = int(pattern.search(d[0])[1])  # type: ignore[index]
                position = tuple(float(v) * 1e-02 for v in d[1:4])  # << u.m
                data.append((antenna, position))

        return data

    @classmethod
    def _parse_list(cls, path: Path, index: int):
        """Parse a SIMxxxxxx.list file"""

        list_file = path / f"SIM{index:06d}.list"
        if not list_file.exists():
            return None

        data = []
        pattern = re.compile("(\d+)$")
        with list_file.open() as f:
            for line in f:
                d = line.split()
                if not d:
                    continue
                antenna = int(pattern.search(d[5])[1])  # type: ignore[index]
                position = tuple(float(v) * 1e-02 for v in d[2:5])  # << u.m
                data.append((antenna, position))

        return data

    @classmethod
    def _parse_info(cls, path: Path, index: int) -> Optional[List]:
        """Parse a SIMxxxxxx.info file"""

        info_file = path / f"SIM{index:06d}.info"
        if not info_file.exists():
            return None

        with info_file.open() as f:
            txt = f.read()

        pattern = re.compile(
            "ANTENNA[ \t]+([^ \t]+)[ \t]+([^ \t]+)" "[ \t]+([^ \t]+)[ \t]+([^ \t]+)"
        )
        setattr(cls, "_info_pattern", pattern)

        matches = pattern.findall(txt)

        # return [(int(antenna), tuple(float(v) for v in values) << u.m)
        return [(int(antenna), tuple(float(v) for v in values)) for (antenna, *values) in matches]
