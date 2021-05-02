import socket
from typing import Iterable, Type

from hks_pylib.hksenum import HKSEnum
from hks_pylib.cryptography.ciphers.hkscipher import HKSCipher
from hks_pylib.cryptography.ciphers.symmetrics import NoCipher
from hks_pylib.logger import LoggerGenerator, InvisibleLoggerGenerator
from hks_pylib.logger.standard import StdLevels, StdUsers

from hks_pynetwork.external import STCPSocket

from csbuilder.session import SessionManager
from csbuilder.server.responser import ServerResponser

from hkserror.hkserror import HFormatError, HTypeError



class ResponserInfo(HKSEnum):
    CLASS = "class"
    ARGS = "args"
    KWARGS = "kwargs"


class Listener(object):
    def __init__(
                    self,
                    address: tuple,
                    cipher: HKSCipher = NoCipher(),
                    responser_cls: Type[ServerResponser] = ServerResponser,
                    name: str = None,
                    buffer_size: int = 1024,
                    logger_generator: LoggerGenerator = InvisibleLoggerGenerator(),
                    display: dict = {}
                ) -> None:
        super().__init__()

        if not isinstance(address, Iterable):
            raise HTypeError("address", address, Iterable)

        if len(address) != 2:
            raise HFormatError("Parameter address expected an "
            "pair of two elements - (ip/hostname/domain, port).")

        if not isinstance(cipher, HKSCipher):
            raise HTypeError("cipher", cipher, HKSCipher)

        if not issubclass(responser_cls, ServerResponser):
            raise HTypeError("responser_cls", responser_cls, ServerResponser)

        if not isinstance(buffer_size, int):
            raise HTypeError("buffer_size", buffer_size, int)
            
        if buffer_size <= 0:
            raise HFormatError("The parameter buffer_size expected an positive integer.")

        if name is not None and not isinstance(name, str):
            raise HTypeError("name", name, str, None)

        if not isinstance(logger_generator, LoggerGenerator):
            raise HTypeError("logger_generator", logger_generator, LoggerGenerator)

        if not isinstance(display, dict):
            raise HTypeError("display", display, dict)

        self._name = name
        self._listener_address = address

        self._socket = STCPSocket(
                cipher=cipher,
                name="STCP Socket of {}".format(self._name),
                buffer_size=buffer_size,
                logger_generator=logger_generator,
                display=display
            )
        
        self._logger_generator = logger_generator
        self._display = display
        self._print = logger_generator.generate(
                name=self._name, 
                display=self._display
            )

        self._responser = {
                ResponserInfo.CLASS: responser_cls,
                ResponserInfo.ARGS: (),
                ResponserInfo.KWARGS: {}
            }

        self._session_manager = SessionManager(
                name="Session Manager of {}".format(self._name),
                logger_generator=logger_generator,
                display=display
            )
        
    def session_manager(self) -> SessionManager:
        return self._session_manager

    def config_responser(self, *args, **kwargs) -> None:
        if args:
            self._responser[ResponserInfo.ARGS] = args
    
        if kwargs:
            self._responser[ResponserInfo.KWARGS] = kwargs

    def listen(self, __backlog: int = 0) -> None:
        self._socket.bind(self._listener_address)
        self._socket.listen(__backlog)
        self._socket.settimeout_raw(3)  # Wait 3s for a client's connection.
        self._print(StdUsers.USER, StdLevels.INFO, "Listener started.")
        self._print(StdUsers.DEV, StdLevels.INFO, "Listener started.")

    def construct_responser(self, socket: STCPSocket, address: tuple) -> ServerResponser:
        if not isinstance(socket, STCPSocket):
            raise HTypeError("socket", socket, STCPSocket)

        if not isinstance(address, Iterable):
            raise HTypeError("address", address, Iterable)

        if len(address) != 2:
            raise HFormatError("Parameter address expected an "
            "pair of two elements - (ip/hostname/domain, port).")

        responser: ServerResponser = self._responser[ResponserInfo.CLASS](
                socket=socket,
                address=address,
                logger_generator = self._logger_generator,
                display=self._display,
                *self._responser[ResponserInfo.ARGS],
                **self._responser[ResponserInfo.KWARGS]
            )

        responser.session_manager().extend(self._session_manager)
        return responser

    def accept(self, start_responser: bool = True) -> ServerResponser:
        if not isinstance(start_responser, bool):
            raise HTypeError("start_responser", start_responser, bool)

        client_socket, client_addr = self._socket.accept()
        self._print(StdUsers.USER, StdLevels.INFO, "Client {} connect "
        "to server".format(client_addr))

        responser = self.construct_responser(client_socket, client_addr)

        if start_responser:
            responser.start(thread=True)

        return responser

    def quickstart(self) -> None:
        self.listen()
        try:
            while True:
                try:
                    self.accept()
                except socket.timeout:
                    continue
        except KeyboardInterrupt:
            self.close()

    def close(self) -> None:
        self._socket.close()
        self._print(StdUsers.USER, StdLevels.INFO, "Listener closed.")
        self._print(StdUsers.DEV, StdLevels.INFO, "Listener closed.")
