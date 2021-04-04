import socket
import threading

from csbuilder.responser import Responser
from csbuilder.session import SessionManager
from csbuilder.const_group import ConstGroup

from hks_pylib.cipher import _Cipher
from hks_pylib.logger import LoggerGenerator

from hks_pynetwork.external import STCPSocket
from hks_pynetwork.internal import ForwardNode


class ServerResponser(Responser):
    def __init__(
                    self,
                    client_socket: STCPSocket,
                    client_address: tuple,
                    session_manager: SessionManager,
                    logger_generator: LoggerGenerator = ...,
                    display: dict = ...
                ) -> None:
        assert isinstance(client_socket, STCPSocket)
        assert isinstance(client_address, tuple)
        assert isinstance(session_manager, SessionManager)
        assert isinstance(display, dict)
        super().__init__(
                            name="Server Reponser of {}".format(client_address),
                            session_manager=session_manager,
                            logger_generator=logger_generator,
                            display=display
                        )
        self._socket = client_socket
        self._address = client_address
        self._forwarder = ForwardNode(
            self._node,
            self._socket,
            name= "Forwarder of Server Responser {}".format(client_address),
            implicated_die=True,
            logger_generator=logger_generator,
            display=display
        )

    def is_valid_source(self, source: str, packet_dict: dict):
        if not (packet_dict["scheme"] in self._external_scheme_type_group and source == self._forwarder.name) and\
            not (packet_dict["scheme"] in self._internal_scheme_type_group and source != self._forwarder.name):
            self._print("dev", "warning", "Packet comes from invalid source ({})".format(source))
            return False
        return super().is_valid_source(source, packet_dict)

    def start(self):
        threading.Thread(target=self._forwarder.start).start()
        super().start()

class Listener(object):
    def __init__(
                    self,
                    cipher: _Cipher,
                    server_address: tuple,
                    external_scheme_type_group: ConstGroup,
                    internal_scheme_type_group: ConstGroup = ConstGroup(),
                    responser_cls = ServerResponser,
                    buffer_size: ConstGroup = 1024,
                    logger_generator: LoggerGenerator = ...,
                    display: dict = ...
                ) -> None:
        super().__init__()
        
        self._server_address = server_address
        
        self._reponser_cls = responser_cls
        self._reponser_optional_args = ()

        self._socket = STCPSocket(
                cipher=cipher,
                buffer_size=buffer_size,
                logger_generator=logger_generator,
                display=display
            )
        
        self._logger_generator = logger_generator
        self._display = display
        self.__print = logger_generator.generate(
                "Listener of {}".format(self._server_address), 
                self._display
            )

        self._session_manager = SessionManager(
            external_scheme_type_group,
            internal_scheme_type_group,
            name="Listener of {}".format(self._server_address),
            logger_generator=logger_generator,
            display=display
        )

    @property
    def session_manager(self):
        return self._session_manager

    def set_reponser_args(self, args):
        self._reponser_optional_args = args

    def listen(self) -> None:
        self._socket.bind(self._server_address)
        self._socket.listen(0)
        self._socket.settimeout(3)
        
    def accept(self):
        client_socket, client_addr = self._socket.accept()
        self.__print("user", "info", "Client {} connect to server".format(client_addr))
        responser = self._reponser_cls(
                client_socket=client_socket,
                client_address=client_addr,
                session_manager=self._session_manager.clone(),
                logger_generator = self._logger_generator,
                display=self._display,
                *self._reponser_optional_args
            )
        responser_thread = threading.Thread(target=responser.start)
        responser_thread.start()
        return responser

    def start(self):
        self.__print("user", "info", "Listener start")
        self.listen()
        try:
            while True:
                try:
                    self.accept()
                except socket.timeout:
                    continue
        except KeyboardInterrupt:
            self._socket.close()
            self.__print("user", "info", "Listener stops")