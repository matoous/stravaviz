from collections import defaultdict
import logging
import typing

import pint  # type: ignore
import svgwrite  # type: ignore

from stravaviz.track import Track
from stravaviz.xy import XY
from stravaviz.year_range import YearRange
from stravaviz.tracks_drawer import TracksDrawer  # pylint: disable=cyclic-import


log = logging.getLogger(__name__)


class Drawer:
    """Create a drawer from track data.

    Attributes:
        tracks_by_date: Tracks organized temporally if needed.
        tracks: List of tracks to be used in the images.
        units: Length units to be used in images.
        width: Poster width.
        height: Poster height.
        years: Years included in the images.
        tracks_drawer: drawer used to draw the final image.

    Methods:
        set_tracks: Associate the Poster with a set of tracks
        draw: Draw the tracks on the image.
        u: Return distance unit (km or mi)
    """

    def __init__(self) -> None:
        self.tracks_by_date: typing.Dict[str, typing.List[Track]] = defaultdict(list)
        self.tracks: typing.List[Track] = []
        self.total_length_year_dict: typing.Dict[int, pint.quantity.Quantity] = defaultdict(int)
        self.units = "metric"
        self.colors = {
            "background": "#FFFFFF",
            "track": "#000000",
        }
        self.width = 300
        self.height = 300
        self.years = YearRange()
        self.tracks_drawer: typing.Optional["TracksDrawer"] = None
        self._trans: typing.Optional[typing.Callable[[str], str]] = None

    def set_tracks(self, tracks: typing.List[Track]) -> None:
        """Associate the set of tracks with this drawer.

        In addition to setting self.tracks, also compute the necessary attributes for the Poster
        based on this set of tracks.
        """
        self.tracks = tracks
        self.tracks_by_date.clear()
        self._compute_years(tracks)
        for track in tracks:
            if not self.years.contains(track.start_time()):
                continue
            text_date = track.start_time().strftime("%Y-%m-%d")
            self.tracks_by_date[text_date].append(track)

    def draw(self, drawer: "TracksDrawer", output: str) -> None:
        """Set the Poster's drawer and draw the tracks."""
        self.tracks_drawer = drawer
        d = svgwrite.Drawing(output, (f"{self.width}mm", f"{self.height}mm"))
        d.viewbox(0, 0, self.width, self.height)
        d.add(d.rect((0, 0), (self.width, self.height), fill=self.colors["background"]))
        self._draw_tracks(d, XY(self.width - 20, self.height - 20), XY(10, 10))
        d.save()

    def _draw_tracks(self, d: svgwrite.Drawing, size: XY, offset: XY) -> None:
        assert self.tracks_drawer

        g = d.g(id="tracks")
        d.add(g)

        self.tracks_drawer.draw(d, g, size, offset)

    def _compute_years(self, tracks: typing.List[Track]) -> None:
        self.years.clear()
        for t in tracks:
            self.years.add(t.start_time())
