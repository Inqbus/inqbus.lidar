import pprint
from collections import MutableMapping


class NamedDict(MutableMapping):
    """class to hold attributes and rerieve the naturally"""

    def __init__(self):
        # Dict to store attributes
        self.attrs = {}

    def __str__(self):
        return pprint.pformat(self.attrs)

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return __dict__[attr]
        else:
            if attr in self.attrs:
                return self.attrs[attr]
            else:
                msg = "Attribute %s not found" % attr
                raise AttributeError(msg)

    def __getitem__(self, key):
        return self.attrs.__getitem__(key)

    def __setitem__(self, key, val):
        return self.attrs.__setitem__(key, val)

    def __setattr__(self, attr, val):
        if attr == 'attrs':
            self.__dict__[attr] = val
        else:
            self.attrs[attr] = val

    def __iter__(self):
        return self.attrs.__iter__()

    def update(self, attr_dict):
        self.attrs.update(attr_dict)

    def items(self):
        return self.attrs.items()

    def __delitem__(self, item):
        self.attrs.__delitem__(item)

    def __len__(self):
        self.attrs.__len__()
