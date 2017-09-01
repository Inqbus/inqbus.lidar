

class Regions(dict):
    """
    Holds a list of regions that define metadata for a linear of multidimensional field of data.
    An simple example may be a time series for which some time intervals are marked invalid.
    """

    def __init__(self, full_range):
        self.full_range = full_range
