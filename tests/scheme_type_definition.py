from csbuilder.packet import PacketUtil
from csbuilder.const_group import ConstGroup
from csbuilder.predefined_scheme import InternalSchemeType, ExternalSchemeType

class ExtendedExternalSchemeType(ExternalSchemeType):
    def __init__(self) -> None:
        self.AUTHENTICATE = 0
        super().__init__()

class ExtendedInternalSchemeType(InternalSchemeType):
    def __init__(self) -> None:
        super().__init__()

class StatusAuthenticateClient(ConstGroup):
    def __init__(self) -> None:
        self.RESET = 99
        self.REQUEST = 0
        super().__init__()

class StatusAuthenticateServer(ConstGroup):
    def __init__(self) -> None:
        self.RESET = 99
        self.ACCEPT = 0
        self.DENY = 1
        super().__init__()

PacketUtil.add_scheme(
        scheme_type=ExtendedExternalSchemeType().AUTHENTICATE,
        scheme_name="AUTHENTICATE",
        client_status_group=StatusAuthenticateClient(),
        server_status_group=StatusAuthenticateServer()
    )