import re


class ConstGroup():
    """
    ConstGroup
    ===========
    The parent class for creating a constants group.

    Examples of constants groups:
        - The types of packet in some protocols: `REQUIRE = 1, SUBMIT = 2`
        - The days of the week: `MONDAY = 2, TUESDAY = 3, ...,
        SARTUDAY = 7, SUNDAY = 8`

    -----------------
    The class has an protected attribute specifying the prefix
    of all constants in the group called `_prefix`.

    If `_prefix = "TYPE"`, all constants must be stated with `"TYPE"`.
    For example, `TYPE_REQUIRE, TYPE_SUBMIT`.

    By default, `_prefix = ""`. To set this attribute, you use method `setPrefix(prefix)`.

    -----------------
    If you want to declare a constants group, let inherit class `ConstGroup`.
    You will declare your all constants in the initial method of childrent class.
    Note that: the constants only include uppercase characters and underscores (_).

    Example:
    >>> class ConstType(ConstGroup):
    >>>     def __init__(self):
    >>>         super().__init__()
    >>>         self.NONE = 0
    >>>         self.TYPE_SUBMIT = 1
    >>>         self.TYPE_REQUIRE = 2
    >>>         super().set_prefix("TYPE")
    >>>     const_dict = ConstType().get_dict()
    >>>     print(const_dict)
    >>>     # {"TYPE_SUBMIT": 1, "TYPE_REQUIRE": 2}

    ----------------
    The method `get_dict(invert = False)` will
    return a dictionary specifying all constant names
    and responding constant values in your group.
    If `invert = True`, the position of names and values in dictionary is inverted.
    """

    def __init__(self) -> None:
        self._prefix = ""
        self._dict = self.get_dict(invert= True)

    def set_prefix(self, prefix: str):
        assert isinstance(prefix, str)
        self._prefix = prefix

    def get_dict(self, invert=False):
        attributes_dict = self.__dict__

        def check_const(attr):
            if re.match("^{}[A-Z_]+$".format(self._prefix), attr):
                return True
            return False

        const_names = filter(check_const, attributes_dict.keys())
        const_dict = {}

        def update_const_to_dict(const_name):
            return None if const_dict.update({const_name: attributes_dict[const_name]}) else None
        # Apply `get` function to all element in actual_key
        list(map(update_const_to_dict, const_names))

        if invert:
            const_dict = {v: k for k, v in const_dict.items()}

        return const_dict

    def __contains__(self, item: int):
        return item in self._dict.keys()

# Examples of inheriting ConstGroup class
# class ConstType(ConstGroup):
#       def __init__(self) -> None:
#           super().__init__()
#           self.NONE = 0
#           self.ID_SUBMIT = 1
#           self.ID_REQUIRE = 2
#           super().set_prefix("ID")
#