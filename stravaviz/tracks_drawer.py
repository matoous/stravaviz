import argparse
import typing

import pint  # type: ignore
import svgwrite  # type: ignore

from stravaviz.track import Track
from stravaviz.xy import XY


class TracksDrawer:
    """Base class that other drawer classes inherit from."""

    def __init__(self, tracks: typing.List[Track], _: argparse.Namespace):
        self.tracks = tracks

    def draw(self, dr: svgwrite.Drawing, g: svgwrite.container.Group, size: XY, offset: XY) -> None:
        pass
