import time
import copy
import threading
from typing import Any, Callable, Dict

from hks_pylib.done import Done
from hks_pylib.hksenum import HKSEnum
from hks_pylib.logger import LoggerGenerator
from hks_pylib.logger import InvisibleLoggerGenerator
from hks_pylib.logger.standard import StdLevels, StdUsers

from csbuilder.util import func2method

from csbuilder.pool import Pool
from csbuilder.scheme import Scheme
from csbuilder.scheme import SchemeResult

from csbuilder.cspacket import CSPacket
from csbuilder.session.result import SessionResult
from csbuilder.standard import Protocols, StandardRole, States


from hkserror import HTypeError
from hkserror import HFormatError
from csbuilder.errors.scheme import SchemeError
from csbuilder.errors.session import SessionError
from csbuilder.errors.pool import PredefinitionError


class HookArgument(HKSEnum):
    ARGS = "args"
    KWARGS = "kwargs"


def run_hook(protocol: Protocols, hook_dict: Dict[Any, Dict[HookArgument, Any]]):
    for hook_fn in hook_dict:
        args = hook_dict[hook_fn][HookArgument.ARGS]
        kwargs = hook_dict[hook_fn][HookArgument.KWARGS]
        hook_fn(protocol=protocol, *args, **kwargs)


class Session(object):
    TIME_PERIODIC = 0.1

    def __init__(
                    self,
                    scheme: Scheme,
                    timeout: float = 10,
                    logger_generator: LoggerGenerator = InvisibleLoggerGenerator(),
                    display: dict = {},
                    name: str = None
                ) -> None:
        if not isinstance(scheme, Scheme):
            raise HTypeError("scheme", scheme, Scheme)

        if not isinstance(timeout, (float, int)):
            raise HTypeError("timeout", timeout, float, int)

        if not isinstance(logger_generator, LoggerGenerator):
            raise HTypeError("logger_generator", logger_generator, LoggerGenerator)

        if not isinstance(display, dict):
            raise HTypeError("display", display, dict)

        if not isinstance(name, str) or name is None:
            raise HTypeError("name", name, str, None)

        self._scheme = scheme
        self._protocol, self._role = scheme.protocol(), scheme.role()

        self._activation = Pool.get_activation(self._protocol, self._role)
        if self._activation is None:
            raise PredefinitionError("The activation must be defined "
            "in the scheme before creating a session.")

        if self._role.value == StandardRole.ACTIVE:
            self._activation = func2method(self._activation, self._scheme)

            if self._activation is None:
                raise PredefinitionError("The predefined activation must be a method of "
                "the scheme {}.".format(type(scheme).__name__))

        states = Pool.get_states(self._protocol, self._role)
        self._ignore_packet = CSPacket(self._protocol, states.IGNORE)

        self._response_methods: Dict[States, Any] = {}

        opposite_role = Pool.get_opposite_role(self._protocol, self._role)
        for state in Pool.get_states(self._protocol, opposite_role):
            resp_func = Pool.get_response(state)
            resp_method = func2method(resp_func, self._scheme)

            if resp_method is None:
                raise PredefinitionError("The predefined response must be a method of "
                "the scheme {}".format(type(scheme).__name__))

            self._response_methods.update({state: resp_method})

        self._timeout_hook: Dict[Any, Dict[HookArgument, object]] = {}
        self._activate_hook: Dict[Any, Dict[HookArgument, object]] = {}
        self._cancel_hook: Dict[Any, Dict[HookArgument, object]] = {}

        self._result = None
        self._result_lock = threading.Lock()

        self._name = name

        self._timeout = timeout
        self._timeout_lock = threading.Lock()
        self._cancel_the_timeout = False

        self._is_running = False

        self._logger_generator = logger_generator
        self._display = display
        self._print = logger_generator.generate(
                "Session of {}".format(name), 
                display=display
            )

        self.add_begin_hook(self._scheme.begin)
        self.add_cancle_hook(self._scheme.cancel)
        self.add_begin_hook(self._set_result, value=Done(None))
        self.add_timeout_hook(self._set_result, value=Done(False, reason="Timeout"))

    def _set_result(self, value: Done, *args, **kwargs):
        if not isinstance(value, Done):
            raise HTypeError("value", value, Done)

        self._result_lock.acquire()
        self._result = value
        self._result_lock.release()

    def wait_result(self, timeout: float = None):
        if timeout is not None and not isinstance(timeout, (int, float)):
            raise HTypeError("timeout", timeout, float, int, None)

        if timeout is not None and timeout <= 0:
            raise HFormatError("The parameter timeout expected an positive number.")

        while not self._is_running and (timeout is None or timeout > 0):
            time.sleep(self.TIME_PERIODIC)
            if timeout is not None:
                timeout -= self.TIME_PERIODIC

        if not self._is_running:
            raise SessionError("The session must be begun before waiting its result.")

        while timeout is None or timeout > 0:
            if self._result != None:
                result = self._result
                self._set_result(Done(None))
                return result

            time.sleep(self.TIME_PERIODIC)
            if timeout is not None:
                timeout -= self.TIME_PERIODIC

        return None

    def protocol(self):
        return self._protocol

    def role(self):
        return self._role

    def scheme(self):
        return self._scheme

    def clone(self):
        new_session = type(self)(
                        scheme=copy.deepcopy(self._scheme),
                        timeout=self._timeout,
                        name=self._name,
                        logger_generator=self._logger_generator,
                        display=self._display
                    )

        new_session._timeout_hook = self._timeout_hook.copy()
        new_session._activate_hook = self._activate_hook.copy()
        new_session._cancel_hook = self._cancel_hook.copy()

        return new_session

    def add_timeout_hook(self, hook_fn, *args, **kwargs) -> None:
        if hook_fn is None or not callable(hook_fn):
            raise HTypeError("hook_fn", hook_fn, Callable)

        self._timeout_hook.update({
                hook_fn: {
                    HookArgument.ARGS: args,
                    HookArgument.KWARGS: kwargs
                }
            })

    def add_begin_hook(self, hook_fn, *args, **kwargs) -> None:
        if hook_fn is None or not callable(hook_fn):
            raise HTypeError("hook_fn", hook_fn, Callable)

        self._activate_hook.update({
                hook_fn: {
                    HookArgument.ARGS: args,
                    HookArgument.KWARGS: kwargs
                }
            })

    def add_cancle_hook(self, hook_fn, *args, **kwargs) -> None:
        if hook_fn is None or not callable(hook_fn):
            raise HTypeError("hook_fn", hook_fn, Callable)

        self._cancel_hook.update({
                hook_fn: {
                    HookArgument.ARGS: args,
                    HookArgument.KWARGS: kwargs
                }
            })

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

        state = packet.state()
        if state not in self._response_methods.keys():
            raise PredefinitionError("Please assign a method "
            "to respond this state ({})").format(state)

        if self._is_running:
            self._set_time_counter(self._timeout)  # reset the counter
        else:
            return SessionResult(source, self._ignore_packet)

        self._print(StdUsers.DEV, StdLevels.DEBUG, "Solving [{}]".format(state.name))
        response_fn = self._response_methods[state]
        scheme_result: SchemeResult = response_fn(source, packet, *args, **kwargs)

        if scheme_result.is_continue and scheme_result.result != None:
            raise SchemeError("The result can be set to not-None "
            "only when is_continue is False")

        self._set_result(scheme_result.result)

        if not scheme_result.is_continue:
            self.cancel()

        return SessionResult(scheme_result.destination, scheme_result.packet)

    def begin(self, *args, **kwargs) -> None:
        if self._is_running:
            raise SchemeError("Can not begin the session when it is in process.")

        self._is_running = True

        self._print(StdUsers.DEV, StdLevels.DEBUG, "Session began.")
        self._cancel_the_timeout = False
        run_hook(self._protocol, self._activate_hook)

        counter_thread = threading.Thread(
                target=self._time_counter,
                name="Timecounter [{}]".format(self._name)
            )
        counter_thread.start()

    def cancel(self) -> None:
        if self._cancel_the_timeout is True:
            return

        self._set_time_counter(None)   # cancel the counter
        self._print(StdUsers.DEV, StdLevels.DEBUG, "Session is canceled")

        self._is_running = False
        run_hook(self._protocol, self._cancel_hook)

    def _time_counter(self) -> None:
        self._current_time_counter = self._timeout

        while self._current_time_counter > 0 and not self._cancel_the_timeout:
            time.sleep(self.TIME_PERIODIC)
            self._set_time_counter(self._current_time_counter - self.TIME_PERIODIC)
        
        if self._current_time_counter <= 0 and not self._cancel_the_timeout:
            self._print(StdUsers.DEV, StdLevels.DEBUG, "Exceed timeout")

            run_hook(self._protocol, self._timeout_hook)

        self.cancel()

    def _set_time_counter(self, value: float = None) -> None:
        if value is not None and not isinstance(value, (float, int)):
            raise HTypeError("value", value, float, int, None)

        self._timeout_lock.acquire()

        if value == None:
            self._cancel_the_timeout = True
        else:
            self._current_time_counter = value

        self._timeout_lock.release()
