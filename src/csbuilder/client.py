import threading

from csbuilder.responser import Responser
from csbuilder.session import SessionManager

from hks_pynetwork.external import STCPSocket
from hks_pynetwork.internal import ForwardNode

from hks_pylib.cipher import _Cipher
from hks_pylib.logger import LoggerGenerator


class ClientResponser(Responser):
    def __init__(
                    self,
                    cipher: _Cipher,
                    server_address: tuple,
                    session_manager: SessionManager,
                    name:str = "Client",
                    logger_generator: LoggerGenerator = ...,
                    display: dict = ...) -> None:
        assert isinstance(server_address, tuple) and len(server_address) == 2
        assert isinstance(server_address[0], str) and isinstance(server_address[1], int)
        super().__init__(
                            name=name,
                            session_manager=session_manager,
                            logger_generator=logger_generator,
                            display=display
                        )
        
        self._socket = STCPSocket(cipher, logger_generator=logger_generator, display=display)
        self._server_address = server_address
        self._forwarder = ForwardNode(
            self._node,
            self._socket,
            name="Forwarder of {}".format(name),
            implicated_die=True,
            logger_generator=logger_generator,
            display=display
        )

    def is_valid_source(self, source: str, packet_dict: dict):
        if not (packet_dict["scheme"] in self._external_scheme_type_group and source == self._forwarder.name) and\
            not (packet_dict["scheme"] in self._internal_scheme_type_group and source != self._forwarder.name):
            self._print("dev", "warning", "Packet comes from invalid source")
            return False
        return super().is_valid_source(source, packet_dict)

    def start(self):
        self._socket.connect(self._server_address)
        threading.Thread(target=self._forwarder.start).start()
        super().start()
        self._forwarder.close()