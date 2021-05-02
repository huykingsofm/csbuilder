from csbuilder.errors import CSError


class SessionError(CSError):
    "The exception is raised by failures in session."


class InProcessError(SessionError):
    "The exception is raised when a running process is called again."
