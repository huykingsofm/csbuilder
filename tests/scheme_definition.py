import scheme_type_definition
from csbuilder.session import Scheme, SchemeSession


class SchemeAuthenticateClient(Scheme):
    def __init__(self, forwarder_name: str) -> None:
        super().__init__(
            scheme_type=scheme_type_definition.ExtendedExternalSchemeType().AUTHENTICATE,
            outcoming_status_group=scheme_type_definition.StatusAuthenticateClient(),
            incoming_status_group=scheme_type_definition.StatusAuthenticateServer()
        )

        assert isinstance(forwarder_name, str)
        self._forwarder_name = forwarder_name

    def initial(self, username: str, password: str):
        packet = self._packet_generator.generate(self._outcoming_status_group.REQUEST)
        packet.set_data(username.encode() + b" " + password.encode())
        return packet.create(), self._forwarder_name

    def reset(self, source: str, packet_dict: dict):
        return None, source, False

    def accept(self, source: str, packet_dict: dict):
        if not self.in_process:
            packet = self._packet_generator.generate(self._outcoming_status_group.RESET)
            return packet.create(), source, False

        print("Authenticating success. You are {}.".format(packet_dict["data"].decode()))
        return None, source, False

    def deny(self, source: str, packet_dict: dict):
        if not self.in_process:
            packet = self._packet_generator.generate(self._outcoming_status_group.RESET)
            return packet.create(), source, False

        print("Authenticating fails")
        return None, None, False

    def __assign__(self, session: SchemeSession):
        session.assign_status_fn(self._incoming_status_group.RESET, self.reset)
        session.assign_status_fn(self._incoming_status_group.ACCEPT, self.accept)
        session.assign_status_fn(self._incoming_status_group.DENY, self.deny)
        session.assign_initial(self.initial)
        session.assign_reset_packet(self._reset_packet.create())


class SchemeAuthenticateServer(Scheme):
    def __init__(self, **kwargs) -> None:
        super().__init__(
            scheme_type=scheme_type_definition.ExtendedExternalSchemeType().AUTHENTICATE,
            outcoming_status_group=scheme_type_definition.StatusAuthenticateServer(),
            incoming_status_group=scheme_type_definition.StatusAuthenticateClient()
        )

    def reset(self, source: str, packet_dict: dict):
        return None, source, False

    def request(self, source: str, packet_dict: dict):
        username, password = packet_dict["data"].decode().split(" ")
        if username == "huykingsofm" and password == "123456":
            response = self._packet_generator.generate(self._outcoming_status_group.ACCEPT)
            response.set_data(username.encode())
            return response.create(), source, False

        response = self._packet_generator.generate(self._outcoming_status_group.DENY)
        return response.create(), source, False

    def __assign__(self, session: SchemeSession):
        session.assign_status_fn(self._incoming_status_group.RESET, self.reset)
        session.assign_status_fn(self._incoming_status_group.REQUEST, self.request)
        session.assign_initial(self._incoming_status_group.REQUEST)
        session.assign_reset_packet(self._reset_packet.create())