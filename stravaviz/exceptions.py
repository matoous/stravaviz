class DrawerError(Exception):
    "Base class for all errors"


class TrackLoadError(DrawerError):
    "Something went wrong when loading a track file"


class ParameterError(DrawerError):
    "Something's wrong with user supplied parameters"
