from hks_pylib.math import Bitwise
from hks_pylib.hksenum import HKSEnum

from hkserror import HFormatError, HTypeError


INT_SIZE = 2


class LimitedInt(object):
    LOW = 0
    HIGH = Bitwise.max_natural_number(INT_SIZE * 8)
    def __init__(self, value: int) -> None:
        if not isinstance(value, int):
            raise HTypeError("value", value, int)

        if value < LimitedInt.LOW or value > LimitedInt.HIGH:
            raise HFormatError("Parameter value expected to "
            "be between {} and {}, but got {}.".format(LimitedInt.LOW, LimitedInt.HIGH, value))
        
        self._value = value

    def to_bytes(self, length, byteorder):
        return self._value.to_bytes(length, byteorder)


class Protocols(LimitedInt, HKSEnum):
    pass


class States(LimitedInt, HKSEnum):
    pass


class StandardRole(HKSEnum):
    ACTIVE = "active"
    PASSIVE = "passive"


class Roles(HKSEnum):
    pass
