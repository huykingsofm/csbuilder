import inspect
from hks_pylib.math import Bitwise
from hkserror import HTypeError, HFormatError


INT_SIZE = 4


class LimitedInt(object):
    LOW = None
    HIGH = None

    @classmethod
    def config(cls, **kwargs):
        size = kwargs.pop("size", None)
        low = kwargs.pop("low", None)
        high = kwargs.pop("high", None)

        if kwargs:
            raise HFormatError("Unexpected parameter ({}).".format(set(kwargs.keys())))

        if size is not None and (low is not None or high is not None):
            raise HFormatError("Only (low, high) or (size) "
            "is specified, dont pass both of them.")

        if (low is not None and high is None) or (low is None and high is not None):
            raise HFormatError("Both of low and high must be passed.")

        if size:
            if not isinstance(size, int):
                raise HTypeError("size", size, int)

            cls.LOW = 0
            cls.HIGH = Bitwise.max_natural_number(size * 8)

        if low is not None and high is not None:
            if not isinstance(low, int):
                raise HTypeError("low", low, int)

            if not isinstance(high, int):
                raise HTypeError("high", high, int)

            if low > high:
                raise HFormatError("The parameter low must "
                "equal to or less than the high.")

            cls.LOW = low
            cls.HIGH = high

    def __init__(self, value: int) -> None:
        if not isinstance(value, int):
            raise HTypeError("value", value, int)

        if value < self.LOW or value > self.HIGH:
            raise HFormatError("Parameter value expected to "
            "be between {} and {}, but got {}.".format(self.LOW, self.HIGH, value))
        
        self._value = value

    def to_bytes(self, length, byteorder):
        return self._value.to_bytes(length, byteorder)


LimitedInt.config(size=INT_SIZE)

def func2method(func, obj):
    if not inspect.isfunction(func):
        raise HTypeError("func", func, "function")

    if type(obj).__name__ == "type":
        raise HTypeError("obj", obj, object)

    for method_name in dir(obj):
        method = getattr(obj, method_name)

        if hasattr(method, "__func__") and method.__func__ == func:
            return method

    return None
