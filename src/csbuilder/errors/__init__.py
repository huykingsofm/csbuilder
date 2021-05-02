from hkserror import HKSError


class CSError(HKSError):
    "The exception is raised by failures in csbuilder."


class ManagementScopeError(CSError):
    """The exception is raised when an entity 
    doesn't belong to the management scope of another entity."""
