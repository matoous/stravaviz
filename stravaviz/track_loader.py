import concurrent.futures
import logging
import os
import typing

import pint  # type: ignore
import s2sphere  # type: ignore
from stravaviz.units import Units

from stravaviz.exceptions import ParameterError, TrackLoadError
from stravaviz.track import Track
from stravaviz.year_range import YearRange

log = logging.getLogger(__name__)


def load_gpx_file(file_name: str) -> Track:
    """Load an individual GPX file as a track by using Track.load_gpx()"""
    log.info("Loading track %s...", os.path.basename(file_name))
    t = Track()
    t.load_gpx(file_name)
    return t


class TrackLoader:
    """Handle the loading of tracks from cache and/or GPX files

    Attributes:
        min_length: All tracks shorter than this value are filtered out.
        special_file_names: Tracks marked as special in command line args
        year_range: All tracks outside of this range will be filtered out.

    Methods:
        load_tracks: Load all data from cache and GPX files
    """

    def __init__(self) -> None:
        self._min_length: pint.quantity.Quantity = 1 * Units().km
        self.special_file_names: typing.List[str] = []
        self.year_range = YearRange()

    def set_min_length(self, min_length: pint.quantity.Quantity) -> None:
        self._min_length = min_length

    def load_tracks(self, base_dir: str) -> typing.List[Track]:
        """Load tracks base_dir and return as a List of tracks"""
        file_names = list(self._list_gpx_files(base_dir))
        log.info("GPX files: %d", len(file_names))

        tracks: typing.List[Track] = []

        log.info("Trying to load %d track(s) from GPX files; this may take a while...", len(file_names))
        loaded_tracks = self._load_tracks(file_names)
        tracks.extend(loaded_tracks.values())
        log.info("Conventionally loaded tracks: %d", len(loaded_tracks))

        return self._filter_and_merge_tracks(tracks)

    def _filter_tracks(self, tracks: typing.List[Track]) -> typing.List[Track]:
        filtered_tracks = []
        for t in tracks:
            file_name = t.file_names[0]
            if t.length().magnitude == 0:
                log.info("%s: skipping empty track", file_name)
            elif not t.has_time():
                log.info("%s: skipping track without start or end time", file_name)
            elif not self.year_range.contains(t.start_time()):
                log.info("%s: skipping track with wrong year %d", file_name, t.start_time().year)
            elif len(t.elevations) == 0:
                log.info("%s: skipping track without elevations", file_name)
            else:
                t.special = file_name in self.special_file_names
                filtered_tracks.append(t)
        return filtered_tracks

    def _filter_and_merge_tracks(self, tracks: typing.List[Track]) -> typing.List[Track]:
        tracks = self._filter_tracks(tracks)
        # merge tracks that took place within one hour
        tracks = self._merge_tracks(tracks)
        # filter out tracks with length < min_length
        return [t for t in tracks if t.length() >= self._min_length]

    @staticmethod
    def _merge_tracks(tracks: typing.List[Track]) -> typing.List[Track]:
        log.info("Merging tracks...")
        tracks = sorted(tracks, key=lambda t1: t1.start_time())
        merged_tracks = []
        last_end_time = None
        for t in tracks:
            if last_end_time is None:
                merged_tracks.append(t)
            else:
                dt = (t.start_time() - last_end_time).total_seconds()
                if 0 < dt < 3600:
                    merged_tracks[-1].append(t)
                else:
                    merged_tracks.append(t)
            last_end_time = t.end_time()
        log.info("Merged %d track(s)", len(tracks) - len(merged_tracks))
        return merged_tracks

    @staticmethod
    def _load_tracks(file_names: typing.List[str]) -> typing.Dict[str, Track]:
        tracks = {}
        with concurrent.futures.ProcessPoolExecutor() as executor:
            future_to_file_name = {executor.submit(load_gpx_file, file_name): file_name for file_name in file_names}
        for future in concurrent.futures.as_completed(future_to_file_name):
            file_name = future_to_file_name[future]
            try:
                t = future.result()
            except TrackLoadError as e:
                log.error("Error while loading %s: %s", file_name, str(e))
            else:
                tracks[file_name] = t

        return tracks

    @staticmethod
    def _list_gpx_files(base_dir: str) -> typing.Generator[str, None, None]:
        base_dir = os.path.abspath(base_dir)
        if not os.path.isdir(base_dir):
            raise ParameterError(f"Not a directory: {base_dir}")
        for name in os.listdir(base_dir):
            path_name = os.path.join(base_dir, name)
            if name.endswith(".gpx") and os.path.isfile(path_name):
                yield path_name
