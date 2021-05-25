import argparse
import logging
import math
import typing

import svgwrite  # type: ignore
import s2sphere  # type: ignore

from stravaviz.exceptions import ParameterError
from stravaviz.track import Track
from stravaviz.tracks_drawer import TracksDrawer
from stravaviz.xy import XY
from stravaviz import utils

log = logging.getLogger(__name__)


class HeatmapDrawer(TracksDrawer):
    """Draw a heatmap Poster based on the tracks.

    Attributes:
        center: Center of the heatmap.
        radius: Scale the heatmap so that a circle with radius (in KM) is visible.

    Methods:
        Create_args: Create arguments for heatmap.
        fetch_args: Get arguments passed.
        draw: Draw the heatmap based on the Poster's tracks.

    """
    def __init__(self, tracks: typing.List[Track], args: argparse.Namespace):
        super().__init__(tracks, args)
        self._center = None
        if args.heatmap_center:
            latlng_str = args.heatmap_center.split(",")
            if len(latlng_str) != 2:
                raise ParameterError(f"Not a valid LAT,LNG pair: {args.heatmap_center}")
            try:
                lat = float(latlng_str[0].strip())
                lng = float(latlng_str[1].strip())
            except ValueError as e:
                raise ParameterError(f"Not a valid LAT,LNG pair: {args.heatmap_center}") from e
            if not -90 <= lat <= 90 or not -180 <= lng <= 180:
                raise ParameterError(f"Not a valid LAT,LNG pair: {args.heatmap_center}")
            self._center = s2sphere.LatLng.from_degrees(lat, lng)
        if args.heatmap_radius:
            if args.heatmap_radius <= 0:
                raise ParameterError(f"Not a valid radius: {args.heatmap_radius} (must be > 0)")
            if not args.heatmap_center:
                raise ParameterError("--heatmap-radius needs --heatmap-center")
            self._radius = args.heatmap_radius

    def _determine_bbox(self) -> s2sphere.LatLngRect:
        if self._center:
            log.info("Forcing heatmap center to %s", str(self._center))
            dlat, dlng = 0, 0
            if self._radius:
                er = 6378.1
                quarter = er * math.pi / 2
                dlat = 90 * self._radius / quarter
                scale = 1 / math.cos(self._center.lat().radians)
                dlng = scale * 90 * self._radius / quarter
            else:
                for tr in self.tracks:
                    for line in tr.polylines:
                        for latlng in line:
                            d = abs(self._center.lat().degrees - latlng.lat().degrees)
                            dlat = max(dlat, d)
                            d = abs(self._center.lng().degrees - latlng.lng().degrees)
                            while d > 360:
                                d -= 360
                            if d > 180:
                                d = 360 - d
                            dlng = max(dlng, d)
            return s2sphere.LatLngRect.from_center_size(self._center, s2sphere.LatLng.from_degrees(2 * dlat, 2 * dlng))

        tracks_bbox = s2sphere.LatLngRect()
        for tr in self.tracks:
            tracks_bbox = tracks_bbox.union(tr.bbox())
        return tracks_bbox

    def draw(self, dr: svgwrite.Drawing, g: svgwrite.container.Group, size: XY, offset: XY) -> None:
        """Draw the heatmap based on tracks."""
        bbox = self._determine_bbox()
        year_groups: typing.Dict[int, svgwrite.container.Group] = {}
        for tr in self.tracks:
            year = tr.start_time().year
            if year not in year_groups:
                g_year = dr.g(id=f"year{year}")
                g.add(g_year)
                year_groups[year] = g_year
            else:
                g_year = year_groups[year]
            for line in utils.project(bbox, size, offset, tr.polylines):
                g_year.add(
                        dr.polyline(
                                points=line,
                                stroke="#000000",
                                fill="none",
                                stroke_width=0.5,
                                stroke_linejoin="round",
                                stroke_linecap="round",
                        )
                )
