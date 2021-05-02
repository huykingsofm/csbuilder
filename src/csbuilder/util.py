import inspect

from hkserror import HTypeError


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
