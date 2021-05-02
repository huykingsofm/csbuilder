import threading
from typing import Iterable, Optional

from hks_pynetwork.external import STCPSocket
from hks_pynetwork.internal import ForwardNode

from hks_pylib.cryptography.ciphers.hkscipher import HKSCipher
from hks_pylib.cryptography.ciphers.symmetrics import NoCipher
from hks_pylib.logger import LoggerGenerator, InvisibleLoggerGenerator

from csbuilder.standard import Protocols
from csbuilder.responser import Responser

from hkserror.hkserror import HFormatError, HTypeError
from hks_pynetwork.errors.external import STCPSocketError


class ClientResponser(Responser):
    def __init__(
                    self,
                    address: tuple,
                    cipher: HKSCipher = NoCipher(),
                    buffer_size: int = 1024,
                    name: Optional[str] = None,
                    logger_generator: LoggerGenerator = InvisibleLoggerGenerator(),
                    display: dict = {}
            ) -> None:
        if not isinstance(address, Iterable):
            raise HTypeError("address", address, Iterable)

        if len(address) != 2:
            raise HFormatError("Parameter address expected an "
            "pair of two elements - (ip/hostname/domain, port).")

        if not isinstance(cipher, HKSCipher):
            raise HTypeError("cipher", cipher, HKSCipher)

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

        super().__init__(
                name=name,
                logger_generator=logger_generator,
                display=display
            )
        
        self._socket = STCPSocket(
                cipher=cipher,
                name="STCP Socket of {}".format(self._name),
                buffer_size=buffer_size,
                logger_generator=logger_generator,
                display=display
            )

        self._address = address

        self._forwarder = ForwardNode(
                self._node,
                self._socket,
                name="Forwarder of {}".format(name),
                implicated_die=True,
                logger_generator=logger_generator,
                display=display
            )

    def activate(self, protocol: Protocols, *args, **kwargs) -> bool:
        if not isinstance(protocol, Protocols):
            raise HTypeError("protocol", protocol, Protocols)

        if not self._socket.isworking():
            raise STCPSocketError("The socket is not started")

        return super().activate(protocol, *args, **kwargs)

    def connect(self) -> None:
        self._socket.connect(self._address)
        threading.Thread(
                target=self._forwarder.start,
                name="Thread forwarder of {}".format(self._name)
            ).start()

    def _start(self) -> None:
        if self._socket.isworking() is False:
            raise STCPSocketError("Client has not connected to the Server.")

        super()._start()

    def close(self) -> None:
        self._socket.close()
        self._forwarder.close()
        super().close()
