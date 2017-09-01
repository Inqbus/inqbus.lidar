# Here we define our own exceptions


class LidarError(Exception):
    """
    Our own Exception class namespace. We can differerentiate our self raised exceptions from the Python exceptions by
    deriving our exceptions from this base class
    """


class LidarFileNotFound(LidarError):
    """
    Raised if a file we need does not exists
    """


class NoCalIdxFound(LidarError):
    """
    Raised when try to sore depolcal without cal_idx
    """


class WrongFileFormat(LidarError):
    """
    Raised for unexpected File Types
    """
