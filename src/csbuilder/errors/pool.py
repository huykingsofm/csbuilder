from csbuilder.errors import CSError

class PoolError(CSError):
    "The exception is raised by failures in Pool."


class PredefinitionError(PoolError):
    "The exception is raised by failures in definition phase."
