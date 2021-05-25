#!/usr/bin/env python

import argparse
import logging
import sys
from os.path import join
from pathlib import Path

from stravaviz import drawer, track_loader, grid_drawer, heatmap_drawer, elevations_drawer
from stravaviz.exceptions import ParameterError, DrawerError


def main() -> None:
    d = drawer.Drawer()

    args_parser = argparse.ArgumentParser(prog="stravaviz")
    args_parser.add_argument(
        "--gpx-dir",
        dest="gpx_dir",
        metavar="DIR",
        type=str,
        default=".",
        help="Directory containing GPX files (default: current directory).",
    )
    args_parser.add_argument(
        "--output",
        metavar="PATH",
        type=str,
        default="out/",
        help='Output directory (default: "out/").',
    )
    args_parser.add_argument(
        "--year",
        metavar="YEAR",
        type=str,
        default="all",
        help='Filter tracks by year; "NUM", "NUM-NUM", "all" (default: all years)',
    )
    args = args_parser.add_argument_group("Heatmap Type Options")
    args.add_argument(
            "--heatmap-center",
            dest="heatmap_center",
            metavar="LAT,LNG",
            type=str,
            help="Center of the heatmap (default: automatic).",
    )
    args.add_argument(
            "--heatmap-radius",
            dest="heatmap_radius",
            metavar="RADIUS_KM",
            type=float,
            help="Scale the heatmap such that at least a circle with radius=RADIUS_KM is visible "
                 "(default: automatic).",
    )

    args = args_parser.parse_args()

    log = logging.getLogger("stravaviz")
    log.setLevel(logging.INFO)

    loader = track_loader.TrackLoader()
    if not loader.year_range.parse(args.year):
        raise ParameterError(f"Bad year range: {args.year}.")

    tracks = loader.load_tracks(args.gpx_dir)
    if not tracks:
        return

    print(f"Creating images for {len(tracks)} tracks and storing them in directory '{args.output}'...")
    Path(args.output).mkdir(parents=True, exist_ok=True)
    d.set_tracks(tracks)
    d.draw(grid_drawer.GridDrawer(d.tracks, args), join(args.output, "facets.svg"))
    d.draw(elevations_drawer.ElevationsDrawer(d.tracks, args), join(args.output, "elevations.svg"))
    d.draw(heatmap_drawer.HeatmapDrawer(d.tracks, args), join(args.output, "heatmap.svg"))


if __name__ == "__main__":
    try:
        main()
    except DrawerError as e:
        print(e)
        sys.exit(1)
