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
    ACCEPT = 1
    DENY = 2
    SUCCESS = 3
    FAILURE = 4


@csbuilder.scheme(MyProtocols.SUBMIT, SubmitRoles.SERVER, SubmitClientStates.REQUEST)
class SubmitServerScheme(Scheme):
    def __init__(self) -> None:
        super().__init__()
        self._step = None

    def begin(self, *args, **kwargs) -> None:
        self._step = None
        return super().begin(*args, **kwargs)

    def cancel(self, *args, **kwargs) -> None:
        self._step = None
        super().cancel(*args, **kwargs)

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


@csbuilder.scheme(MyProtocols.SUBMIT, SubmitRoles.CLIENT)
class SubmitClientScheme(Scheme):
    def __init__(self, des: str) -> None:
        super().__init__()
        self._des = des
        self._step = None

    def begin(self, *args, **kwargs) -> None:
        self._step = "REQUESTING"
        return super().begin(*args, **kwargs)

    def cancel(self, *args, **kwargs):
        self._step = None
        return super().cancel(*args, **kwargs)

    @csbuilder.activation
    def activation(self):
        if self._step is not None:
            return None, None
        packet = self.generate_packet(self._states.REQUEST)
        return self._des, packet

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
