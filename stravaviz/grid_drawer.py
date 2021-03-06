import argparse
import typing

import svgwrite  # type: ignore

from stravaviz.exceptions import DrawerError
from stravaviz.track import Track
from stravaviz.tracks_drawer import TracksDrawer
from stravaviz.xy import XY
from stravaviz import utils


class GridDrawer(TracksDrawer):
    """Drawer used to draw a grid image

    Methods:
        draw: For each track, draw it on the drawer.
    """

    def __init__(self, tracks: typing.List[Track], args: argparse.Namespace) -> None:
        super().__init__(tracks, args)

    def draw(self, dr: svgwrite.Drawing, g: svgwrite.container.Group, size: XY, offset: XY) -> None:
        if self.tracks is None:
            raise DrawerError("No tracks to draw.")
        cell_size, counts = utils.compute_grid(len(self.tracks), size)
        if cell_size is None or counts is None:
            raise DrawerError("Unable to compute grid.")
        count_x, count_y = counts[0], counts[1]
        spacing_x = 0 if count_x <= 1 else (size.x - cell_size * count_x) / (count_x - 1)
        spacing_y = 0 if count_y <= 1 else (size.y - cell_size * count_y) / (count_y - 1)
        offset.x += (size.x - count_x * cell_size - (count_x - 1) * spacing_x) / 2
        offset.y += (size.y - count_y * cell_size - (count_y - 1) * spacing_y) / 2
        year_groups: typing.Dict[int, svgwrite.container.Group] = {}
        for (index, tr) in enumerate(self.tracks):
            year = tr.start_time().year
            if year not in year_groups:
                g_year = dr.g(id=f"year{year}")
                g.add(g_year)
                year_groups[year] = g_year
            else:
                g_year = year_groups[year]
            p = XY(index % count_x, index // count_x) * XY(cell_size + spacing_x, cell_size + spacing_y)
            self._draw_track(
                dr,
                g_year,
                tr,
                0.9 * XY(cell_size, cell_size),
                offset + 0.05 * XY(cell_size, cell_size) + p,
            )

    def _draw_track(self, dr: svgwrite.Drawing, g: svgwrite.container.Group, tr: Track, size: XY, offset: XY) -> None:
        for line in utils.project(tr.bbox(), size, offset, tr.polylines):
            polyline = dr.polyline(
                points=line,
                stroke="#000000",
                fill="none",
                stroke_width=0.5,
                stroke_linejoin="round",
                stroke_linecap="round",
            )
            g.add(polyline)
