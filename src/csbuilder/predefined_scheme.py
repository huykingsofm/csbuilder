from csbuilder.const_group import ConstGroup


class ExternalSchemeType(ConstGroup):
    def __init__(self) -> None:
        super().__init__()
        keys = sorted(self._dict.keys())
        for i, value in enumerate(keys):
            if i != value:
                raise Exception("External Scheme Type must start at 0, and increases by 1 with each additional type")


class InternalSchemeType(ConstGroup):
    def __init__(self) -> None:
        super().__init__()
        keys = sorted(self._dict.keys(), reverse=True)
        for i, value in enumerate(keys):
            if 99 - i != value:
                raise Exception("Internal Scheme Type must start at 99, and decreases by 1 with each additional type")