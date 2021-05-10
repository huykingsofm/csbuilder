import threading
from typing import Optional, Tuple

from hks_pylib.done import Done
from hks_pylib.logger.standard import StdLevels, StdUsers
from hks_pylib.logger import LoggerGenerator, InvisibleLoggerGenerator

from hks_pynetwork.internal import LocalNode

from csbuilder.standard import Protocols, Roles
from csbuilder.session import SessionManager
from csbuilder.cspacket import CSPacket, CSPacketField

from hkserror import HTypeError
from hks_pynetwork.errors.internal import ChannelClosedError

from csbuilder.errors.packet import PacketExtractingError


class Responser(object):
    def __init__(
                    self,
                    name: Optional[str] = None,
                    logger_generator: LoggerGenerator = InvisibleLoggerGenerator(),
                    display: dict = {}
                ) -> None:
        if name is not None and not isinstance(name, str):
            raise HTypeError("name", name, str, None)

        if not isinstance(logger_generator, LoggerGenerator):
            raise HTypeError("logger_generator", logger_generator, LoggerGenerator)

        if not isinstance(display, dict):
            raise HTypeError("display", display, dict)

        super().__init__()
        
        self._name = name

        self._session_manager = SessionManager(
                name="SessionManager of {}".format(self._name),
                logger_generator=logger_generator,
                display=display
            )

        self._print = logger_generator.generate(
            name=name, 
            display=display
        )

        # Create nodes for communicating between objects in this program
        self._node = LocalNode(
            name="Node of " + name,
            logger_generator=logger_generator,
            display=display
        )

    def session_manager(self, session_manager: SessionManager = None) -> SessionManager:
        if session_manager is None:
            return self._session_manager

        if not isinstance(session_manager, SessionManager):
            raise HTypeError("session_manager", session_manager, SessionManager, None)

        self._session_manager = session_manager

    def get_scheme(self, protocol: Protocols, role: Roles = None):
        if not isinstance(protocol, Protocols):
            raise HTypeError("protocol", protocol, Protocols)

        if role is not None and not isinstance(role, Roles):
            raise HTypeError("role", role, Roles, None)

        return self._session_manager.get_scheme(protocol, role)

    def get_session(self, protocol: Protocols, role: Roles = None):
        if not isinstance(protocol, Protocols):
            raise HTypeError("protocol", protocol, Protocols)

        if role is not None and not isinstance(role, Roles):
            raise HTypeError("role", role, Roles, None)

        return self._session_manager.get_session(protocol, role) 

    def wait_result(self, protocol: Protocols, role: Roles = None, timeout: float = None) -> Done:
        if not isinstance(protocol, Protocols):
            raise HTypeError("protocol", protocol, Protocols)

        if role is not None and not isinstance(role, Roles):
            raise HTypeError("role", role, Roles, None)

        if timeout is not None and not isinstance(timeout, (int, float)):
            raise HTypeError("timeout", timeout, int, float, None)

        return self._session_manager.wait_result(protocol, role, timeout)

    def get_response(self, source: str, packet: CSPacket) -> Tuple[str, CSPacket]:
        if source is not None and not isinstance(source, str):
            raise HTypeError("source", source, str, None)

        if packet is not None and not isinstance(packet, CSPacket):
            raise HTypeError("packet", packet, CSPacket, None)

        if source is None or packet is None:
            return

        result = self._session_manager.respond(source, packet)

        return result.destination, result.packet

    def send_response(self, destination: str, response_packet: CSPacket) -> bool:
        if destination is not None and not isinstance(destination, str):
            raise HTypeError("destination", destination, str, None)

        if response_packet is not None and not isinstance(response_packet, CSPacket):
            raise HTypeError("response_packet", response_packet, CSPacket, None)

        if destination and response_packet:
            self._node.send(destination, response_packet.to_bytes())
            return True

        return False

    def validate_packet(self, source: str, packet: CSPacket) -> bool:
        if not isinstance(source, str):
            raise HTypeError("source", source, str)

        if not isinstance(packet, CSPacket):
            raise HTypeError("packet", packet, CSPacket)

        protocol = packet[CSPacketField.PROTOCOL]

        if protocol not in self._session_manager.get_protocols():
            self._print(StdUsers.DEV, StdLevels.WARNING, "Unknown protocol "
            "({})".format(protocol.name))
            return False

        return True

    def activate(self, protocol: Protocols, role: Roles = None, *args, **kwargs) -> bool:
        if not isinstance(protocol, Protocols):
            raise HTypeError("protocol", protocol, Protocols)

        if role is not None and not isinstance(role, Roles):
            raise HTypeError("role", role, Roles, None)

        des, response_packet = self._session_manager.activate(
                protocol,
                role,
                *args,
                **kwargs
            )

        return self.send_response(des, response_packet)

    def _start(self) -> None:
        self._print(StdUsers.USER, StdLevels.INFO, "Responser started.")
        self._print(StdUsers.DEV, StdLevels.INFO, "Responser started")
        while True:
            try:
                source, data, _ = self._node.recv()
            except ChannelClosedError:
                self._print(StdUsers.DEV, StdLevels.INFO, "Stop because Channel closed.")
                break
            except Exception as e:
                self._print(StdUsers.USER, StdLevels.INFO, "Something errors when "
                "receving connection.")
                self._print(StdUsers.DEV, StdLevels.ERROR, "Something errors when "
                "receving connection ({}).".format(repr(e)))
                break

            try:
                packet = CSPacket.from_bytes(data)
            except PacketExtractingError as e:
                self._print(StdUsers.DEV, StdLevels.WARNING, "Error when data "
                "extracting ({})".format(e))
                continue
            except KeyError:
                self._print(StdUsers.DEV, StdLevels.WARNING, "Unknown packet protocols.")
            except Exception as e:
                self._print(StdUsers.DEV, StdLevels.ERROR, "Unknown error occurs "
                "when data extracting ({})".format(e))
                continue

            try:
                if self.validate_packet(source, packet) is False:
                    continue

                des, resp = self.get_response(source, packet)
                self.send_response(des, resp)
            except Exception as e:
                self._print(StdUsers.DEV, StdLevels.ERROR, "Unknown error occurs "
                "when solving data ({})".format(e))
                continue

        self.close()
        self._print(StdUsers.USER, StdLevels.INFO, "Responser stops")
        self._print(StdUsers.DEV, StdLevels.INFO, "Responser stops")

    def start(self, thread = False) -> None:
        if thread:
            threading.Thread(
                    target=self._start,
                    name=self._name
                ).start()
        else:
            self._start()

    def close(self) -> None:
        self._node.close()
