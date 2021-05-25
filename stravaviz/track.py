import datetime
import json
import os
import typing

import gpxpy  # type: ignore
import pint  # type: ignore
import s2sphere  # type: ignore
import polyline  # type: ignore

from stravaviz.exceptions import TrackLoadError
from stravaviz.units import Units


class Track:
    """Create and maintain info about a given activity track (corresponding to one GPX file).

    Attributes:
        file_names: Basename of a given file passed in load_gpx.
        polylines: Lines interpolated between each coordinate.
        start_time: Activity start time.
        end_time: Activity end time.
        length: Length of the track (2-dimensional).
        self.special: True if track is special, else False.

    Methods:
        load_gpx: Load a GPX file into the current track.
        bbox: Compute the border box of the track.
        append: Append other track to current track.
        load_cache: Load track from cached json data.
        store_cache: Cache the current track.
    """

    def __init__(self) -> None:
        self.file_names: typing.List[str] = []
        self.polylines: typing.List[typing.List[s2sphere.LatLng]] = []
        self.elevations = []
        self._start_time: typing.Optional[datetime.datetime] = None
        self._end_time: typing.Optional[datetime.datetime] = None
        # Don't use Units().meter here, as this constructor is called from
        # within a thread (which would create a second unit registry!)
        self._length_meters = 0.0
        self.special = False

    def load_gpx(self, file_name: str) -> None:
        """Load the GPX file into self.

        Args:
            file_name: GPX file to be loaded .

        Raises:
            TrackLoadError: An error occurred while parsing the GPX file (empty or bad format).
            PermissionError: An error occurred while opening the GPX file.
        """
        try:
            self.file_names = [os.path.basename(file_name)]
            # Handle empty gpx files
            # (for example, treadmill runs pulled via garmin-connect-export)
            if os.path.getsize(file_name) == 0:
                raise TrackLoadError("Empty GPX file")
            with open(file_name, "r") as file:
                self._load_gpx_data(gpxpy.parse(file))
        except TrackLoadError as e:
            raise e
        except gpxpy.gpx.GPXXMLSyntaxException as e:
            raise TrackLoadError("Failed to parse GPX.") from e
        except PermissionError as e:
            raise TrackLoadError("Cannot load GPX (bad permissions)") from e
        except Exception as e:
            raise TrackLoadError("Something went wrong when loading GPX.") from e

    def has_time(self) -> bool:
        return self._start_time is not None and self._end_time is not None

    def start_time(self) -> datetime.datetime:
        assert self._start_time is not None
        return self._start_time

    def set_start_time(self, value: datetime.datetime) -> None:
        self._start_time = value

    def end_time(self) -> datetime.datetime:
        assert self._end_time is not None
        return self._end_time

    def set_end_time(self, value: datetime.datetime) -> None:
        self._end_time = value

    @property
    def length_meters(self) -> float:
        return self._length_meters

    @length_meters.setter
    def length_meters(self, value: float) -> None:
        self._length_meters = value

    def length(self) -> pint.quantity.Quantity:
        return self._length_meters * Units().meter

    def bbox(self) -> s2sphere.LatLngRect:
        """Compute the smallest rectangle that contains the entire track (border box)."""
        bbox = s2sphere.LatLngRect()
        for line in self.polylines:
            for latlng in line:
                bbox = bbox.union(s2sphere.LatLngRect.from_point(latlng.normalized()))
        return bbox

    def _load_gpx_data(self, gpx: gpxpy.gpx.GPX) -> None:
        self._start_time, self._end_time = gpx.get_time_bounds()
        if not self.has_time():
            raise TrackLoadError("Track has no start or end time.")
        self._length_meters = gpx.length_2d()
        if self._length_meters <= 0:
            raise TrackLoadError("Track is empty.")
        gpx.simplify()
        for t in gpx.tracks:
            for s in t.segments:
                line = [s2sphere.LatLng.from_degrees(p.latitude, p.longitude) for p in s.points]
                self.polylines.append(line)
                elevation_line = [p.elevation for p in s.points]
                if not all(elevation_line):
                    raise TrackLoadError("Track has invalid elevations.")
                self.elevations.append(elevation_line)

    def append(self, other: "Track") -> None:
        """Append other track to self."""
        self._end_time = other.end_time()
        self.polylines.extend(other.polylines)
        self._length_meters += other.length_meters
        self.file_names.extend(other.file_names)
        self.special = self.special or other.special
