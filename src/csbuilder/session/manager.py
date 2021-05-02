from typing import Any, Callable, Dict, List, Tuple

from hks_pylib.logger import LoggerGenerator
from hks_pylib.logger import InvisibleLoggerGenerator
from hks_pylib.logger.standard import StdLevels, StdUsers

from csbuilder.cspacket import CSPacket
from csbuilder.scheme.scheme import Scheme
from csbuilder.session.result import SessionResult
from csbuilder.standard import Protocols, StandardRole

from csbuilder.session.active import ActiveSession
from csbuilder.session.passive import PassiveSession
from csbuilder.session.session import Session, HookArgument

from hkserror.hkserror import HTypeError
from csbuilder.errors import ManagementScopeError
from csbuilder.errors.session import SessionError


class SessionManager(object):
    def __init__(
                self,
                name: str = None,
                logger_generator: LoggerGenerator = InvisibleLoggerGenerator(),
                display: dict = {}
            ) -> None:
        
        if name is not None and not isinstance(name, str):
            raise HTypeError("name", name, str, None)

        if not isinstance(logger_generator, LoggerGenerator):
            raise HTypeError("logger_generator", logger_generator, LoggerGenerator)

        if not isinstance(display, dict):
            raise HTypeError("display", display, dict)

        self.__sessions: Dict[Protocols, Session] = {}

        self._name = name

        self._logger_generator = logger_generator
        self._display = display
        self._print = self._logger_generator.generate(self._name, self._display)

        self.__index_of_clone = 0

        self._timeout_hook: Dict[Any, Dict[HookArgument, object]] = {}
        self._activate_hook: Dict[Any, Dict[HookArgument, object]] = {}
        self._cancle_hook: Dict[Any, Dict[HookArgument, object]] = {}

    def get_protocols(self) -> List[Protocols]:
        return self.__sessions.keys()

    def get_session(self, protocol: Protocols):
        if not isinstance(protocol, Protocols):
            raise HTypeError("protocol", protocol, Protocols)

        if protocol not in self.__sessions.keys():
            raise ManagementScopeError("The protocol {} doesn't "
            "belong to the management of {}".format(protocol, self._name))

        return self.__sessions[protocol]

    def get_scheme(self, protocol: Protocols):
        if not isinstance(protocol, Protocols):
            raise HTypeError("protocol", protocol, Protocols)

        if protocol not in self.__sessions.keys():
            raise ManagementScopeError("The protocol {} doesn't "
            "belong to the management of {}".format(protocol, self._name))

        return self.__sessions[protocol].scheme()

    def create_session(
                    self,
                    scheme: Scheme,
                    timeout: float=10,
                    logger_generator: LoggerGenerator = None,
                    display: dict = None,
                ) -> Session:
        """
        logger_generator, display = (None or a LoggerGenerator)\n
        If logger_generator, display is None, they are inherited from the session manager.
        """
        if not isinstance(scheme, Scheme):
            raise HTypeError("protocol", scheme, Scheme)

        if scheme.protocol() in self.__sessions.keys():
            raise ManagementScopeError("The protocol of scheme {} has "
            "been created in {}".format(type(scheme).__name__, self._name))

        if self._name:
            session_name = "[{}({})]".format(self._name, scheme.protocol().name)
        else:
            session = scheme.protocol().name

        if logger_generator is None:
            logger_generator = self._logger_generator  
        else:
            logger_generator = logger_generator

        if display is None:
            display = self._display
        else:
            display = display

        if scheme.role().value == StandardRole.ACTIVE:
            _cls = ActiveSession
        else:
            _cls = PassiveSession
        
        session = _cls(
                scheme=scheme,
                timeout=timeout,
                name=session_name,
                logger_generator=logger_generator,
                display=display
            )

        for hook_fn in self._timeout_hook:
            args = self._timeout_hook[hook_fn][HookArgument.ARGS]
            kwargs = self._timeout_hook[hook_fn][HookArgument.KWARGS]
            session.add_timeout_hook(hook_fn, *args, **kwargs)

        for hook_fn in self._activate_hook:
            args = self._activate_hook[hook_fn][HookArgument.ARGS]
            kwargs = self._activate_hook[hook_fn][HookArgument.KWARGS]
            session.add_begin_hook(hook_fn, *args, **kwargs)

        for hook_fn in self._cancle_hook:
            args = self._cancle_hook[hook_fn][HookArgument.ARGS]
            kwargs = self._cancle_hook[hook_fn][HookArgument.KWARGS]
            session.add_cancle_hook(hook_fn, *args, **kwargs)

        self.__sessions.update({scheme.protocol(): session})

        self._print(StdUsers.DEV, StdLevels.DEBUG, "You added a "
        "{} session".format(session_name))
        return session

    def add_timeout_hook(self, hook_fn, *args, **kwargs) -> None:
        if hook_fn is None or not callable(hook_fn):
            raise HTypeError("hook_fn", hook_fn, Callable)

        self._timeout_hook.update({
                hook_fn: {
                    HookArgument.ARGS: args,
                    HookArgument.KWARGS: kwargs
                }
            })

        for session in self.__sessions.values():
            session.add_timeout_hook(hook_fn, *args, **kwargs)

    def add_begin_hook(self, hook_fn, *args, **kwargs) -> None:
        if hook_fn is None or not callable(hook_fn):
            raise HTypeError("hook_fn", hook_fn, Callable)

        self._activate_hook.update({
                hook_fn: {
                    HookArgument.ARGS: args,
                    HookArgument.KWARGS: kwargs
                }
            })

        for session in self.__sessions.values():
            session.add_begin_hook(hook_fn, *args, **kwargs)

    def add_cancel_hook(self, hook_fn, *args, **kwargs) -> None:
        if hook_fn is None or not callable(hook_fn):
            raise HTypeError("hook_fn", hook_fn, Callable)

        self._cancel_hook.update({
                hook_fn: {
                    HookArgument.ARGS: args,
                    HookArgument.KWARGS: kwargs
                }
            })

        for session in self.__sessions.values():
            session.add_cancle_hook(hook_fn, *args, **kwargs)

    def activate(self, protocol: Protocols, *args, **kwargs) -> Tuple[str, CSPacket]:
        if not isinstance(protocol, Protocols):
            raise HTypeError("protocol", protocol, Protocols)

        if protocol not in self.__sessions.keys():
            raise ManagementScopeError("The protocol {} doesn't belong "
            "to the management of {}".format(protocol, self._name))

        if not isinstance(self.__sessions[protocol], ActiveSession):
            raise SessionError("Only ActiveSession objects can call the "
            "method activate() from SessionManager.")
        
        return self.__sessions[protocol].begin(*args, **kwargs)

    def respond(self,
            source: str,
            packet: CSPacket,
            *args,
            **kwargs
        ) -> SessionResult:
        if not isinstance(source, str):
            raise HTypeError("source", source, str)

        if not isinstance(packet, CSPacket):
            raise HTypeError("packet", packet, CSPacket)

        protocol = packet.protocol()

        session = self.get_session(protocol)

        return session.respond(source, packet, *args, **kwargs)

    def wait_result(self, protocol: Protocols, timeout: float = None):
        if timeout is not None and not isinstance(timeout, (int, float)):
            raise HTypeError("timeout", timeout, int, float, None)

        session = self.get_session(protocol)

        return session.wait_result(timeout)

    def clone(self):
        new_session_manager = SessionManager(
                name="{} (clone {})".format(self._name, self.__index_of_clone),
                logger_generator=self._logger_generator,
                display=self._display
            )

        new_session_manager._activate_hook = self._activate_hook.copy()
        new_session_manager._timeout_hook = self._timeout_hook.copy()
        new_session_manager._cancle_hook = self._cancle_hook.copy()

        for protocol in self.__sessions.keys():
            new_session_manager.__sessions[protocol] = self.__sessions[protocol].clone()
        
        return new_session_manager

    def extend(self, another):
        if not isinstance(another, SessionManager):
            raise HTypeError("another", another, SessionManager)
        
        self._activate_hook.update(another._activate_hook)
        self._timeout_hook.update(another._timeout_hook)
        self._cancle_hook.update(another._cancle_hook)

        for protocol in another.get_protocols():
            if protocol not in self.get_protocols():
                self.__sessions[protocol] = another.__sessions[protocol].clone()
