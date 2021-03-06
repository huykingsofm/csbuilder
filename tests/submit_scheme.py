import csbuilder

from hks_pylib.done import Done

from csbuilder.scheme import Scheme
from csbuilder.scheme import SchemeResult

from csbuilder.standard import States
from csbuilder.cspacket import CSPacket

from tests.schemes import MyProtocols, SubmitRoles


@csbuilder.states(MyProtocols.SUBMIT, role=SubmitRoles.CLIENT)
class SubmitClientStates(States):
    IGNORE = 0
    REQUEST = 1
    SEND = 2


@csbuilder.states(MyProtocols.SUBMIT, SubmitRoles.SERVER)
class SubmitServerStates(States):
    IGNORE = 0
    REQUEST = 1
    ACCEPT = 2
    DENY = 3
    SUCCESS = 4
    FAILURE = 5


@csbuilder.scheme(MyProtocols.SUBMIT, SubmitRoles.SERVER, SubmitClientStates.REQUEST)
class SubmitServerScheme(Scheme):
    def __init__(self, forwarder_name = None) -> None:
        super().__init__()
        self._step = None
        self._forwarder_name = forwarder_name

    def config(self, **kwargs):
        forwarder_name = kwargs.pop("forwarder_name", None)
        if forwarder_name:
            self._forwarder_name = forwarder_name

        return super().config(**kwargs)

    def begin(self, *args, **kwargs) -> None:
        self._step = None
        return super().begin(*args, **kwargs)

    def cancel(self, *args, **kwargs) -> None:
        self._step = None
        super().cancel(*args, **kwargs)

    @csbuilder.active_activation
    def activation(self):
        return self._forwarder_name, self.generate_packet(self._states.REQUEST)

    @csbuilder.response(SubmitClientStates.IGNORE)
    def resp_ignore(self, source: str, packet: CSPacket, **kwargs):
        print("Server: Receive ignore packet --> Stop")
        return SchemeResult(None, None, False, Done(False, reason = "ignore"))

    @csbuilder.response(SubmitClientStates.REQUEST)
    def resp_request(self, source: str, packet: CSPacket, **kwargs):
        print("Server: Receive request packet --> ", end="")
        if self._step is None:
            packet = self.generate_packet(self._states.ACCEPT)
            self._step = "REQUESTED"
            print("Accept")
            return SchemeResult(source, packet, True, Done(None))
        else:
            print("Reset")
            return self.ignore(source)

    @csbuilder.response(SubmitClientStates.SEND)
    def resp_send(self, source: str, packet: CSPacket, **kwargs):
        print("Server: Receive send packet --> ", end="")
        if self._step == "REQUESTED":
            packet = self.generate_packet(self._states.SUCCESS)
            print("Success")
            return SchemeResult(source, packet, False, Done(True))
        else:
            print("Reset")
            return self.ignore(source)


@csbuilder.scheme(MyProtocols.SUBMIT, SubmitRoles.CLIENT, SubmitServerStates.REQUEST)
class SubmitClientScheme(Scheme):
    def __init__(self, des: str = None) -> None:
        super().__init__()
        self._des = des
        self._step = None
        self._is_activate = False

    def begin(self, *args, **kwargs) -> None:
        self._step = "REQUESTING"
        return super().begin(*args, **kwargs)

    def cancel(self, *args, **kwargs):
        self._step = None
        self._is_activate = False
        return super().cancel(*args, **kwargs)

    def config(self, des):
        self._des = des

    @csbuilder.active_activation
    def activation(self):
        if self._step is not None:
            return None, None
        packet = self.generate_packet(self._states.REQUEST)
        self._step = "REQUESTING"
        self._is_activate = True
        return self._des, packet

    @csbuilder.response(SubmitServerStates.REQUEST)
    def resp_request(self, source: str, packet: CSPacket):
        print("Client: Receive request packet -->", end=" ")
        if not self._is_activate and self._step is None:
            print("REQUEST")
            self._step = "REQUESTING"
            packet = self.generate_packet(self._states.REQUEST)
            return SchemeResult(source, packet, True, Done(None))
        else:
            print("RESET")
            return self.ignore(source)

    @csbuilder.response(SubmitServerStates.IGNORE)
    def resp_ignore(self, source: str, packet: CSPacket):
        print("Client: Receive ignore packet --> Stop")
        return SchemeResult(None, None, False, Done(False, reason = "ignore"))

    @csbuilder.response(SubmitServerStates.ACCEPT)
    def resp_accept(self, source: str, packet: CSPacket):
        print("Client: Receive accept packet --> ", end="")
        if self._step == "REQUESTING":
            packet = self.generate_packet(self._states.SEND)
            self._step = "SENDING"
            print("Send")
            return SchemeResult(source, packet, True, Done(None))
        else:
            print("Reset")
            return self.ignore(source)

    @csbuilder.response(SubmitServerStates.DENY)
    def resp_deny(self, source: str, packet: CSPacket):
        print("Client: Receive deny packet --> ", end="'")
        if self._step == "REQUESTING":
            print("Stop")
            return SchemeResult(None, None, False, Done(False, reason = "deny"))
        else:
            print("Reset")
            return self.ignore(source)

    @csbuilder.response(SubmitServerStates.SUCCESS)
    def resp_success(self, source: str, packet: CSPacket):
        print("Client: Receive success packet --> ", end="")
        if self._step == "SENDING":
            print("Stop")
            return SchemeResult (None, None, False, Done(True, reason = "OK."))
        else:
            print("Reset")
            return self.ignore(source)

    @csbuilder.response(SubmitServerStates.FAILURE)
    def resp_failure(self, source: str, packet: CSPacket):
        print("Client: Receive failure packet --> ", end="'")
        if self._step == "SENDING":
            print("Stop")
            return SchemeResult(None, None, False, Done(False, reason = "failure"))
        else:
            print("Reset")
            return self.ignore(source)
