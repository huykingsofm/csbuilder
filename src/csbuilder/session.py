import time
import copy
import threading

from csbuilder.scheme import Scheme
from csbuilder.const_group import ConstGroup
from hks_pylib.logger import LoggerGenerator


class SchemeSession(object):
    N_PERIOD = 10
    MAX_PERIODIC_TIME = 1  # second

    def __init__(
                    self,
                    scheme_type: int,
                    timeout: float,
                    name: str,
                    logger_generator: LoggerGenerator = ...,
                    display = ...
                ) -> None:
        self._scheme_obj = None
        self._scheme_type = scheme_type
        self._timeout = timeout
        self._name = name
        self._lock = threading.Lock()
        self._state = {}
        self._in_process = False
        self._initial = None
        self._reset_packet = None
        self._logger_generator = logger_generator
        self._display = display
        self.__print = logger_generator.generate(
            "Session of {}".format(name), 
            display=display
        )

    def clone(self):
        session = type(self)(
                        self._scheme_type,
                        self._timeout,
                        self._name,
                        self._logger_generator,
                        self._display
                    )
        session._scheme_obj = copy.deepcopy(self._scheme_obj)
        session._state = copy.deepcopy(self._state)
        session._initial = self._initial
        session._reset_packet = self._reset_packet
        return session

    def assign_status_fn(self, status: int, responser_fn):
        assert isinstance(status, int)
        assert hasattr(responser_fn, "__call__")

        self._state[status] = responser_fn

    def assign_reset_packet(self, reset_packet):
        assert isinstance(reset_packet, bytes)
        self._reset_packet = reset_packet

    def assign_initial(self, initial):
        self._initial = initial

    def set_scheme(
                    self,
                    scheme: Scheme
                ) -> None:
        self._scheme_obj = scheme
        self._scheme_obj.__assign__(self)

    def response(self, source: str, packet_dict: dict, *args):
        assert isinstance(packet_dict, dict)
        packet_status = packet_dict["status"]
        assert isinstance(packet_status, int)
        assert packet_status in self._state.keys(),\
            "Please assign a function to response this status ({})".format(packet_status)

        if self._in_process:
            self._reset_time_counter()
        else:
            if self._reset_packet is None:
                raise Exception("You must assign the reset packet to this session in case of accident appearance")
            return self._reset_packet, source

        fn = self._state[packet_status]
        packet, des, cont = fn(source, packet_dict, *args)

        if not cont:
            self.cancel()

        return packet, des

    def activate(self, *args):
        if self._in_process:
            raise Exception("Can not activate the session when it is in process")

        self._in_process = True
        if self._scheme_obj:
            self._scheme_obj._in_process = True
        counter_thread = threading.Thread(target=self._begin_time_counter)
        counter_thread.start()

    def cancel(self):
        self._cancel_time_counter()
        self._in_process = False
        if self._scheme_obj:
            self._scheme_obj._in_process = False

    def _begin_time_counter(self):
        self.__print("dev", "debug", "Begin session")
        periodic_check_time = min(self._timeout / SchemeSession.N_PERIOD, SchemeSession.MAX_PERIODIC_TIME)
        self._current_time_counter = self._timeout
        while self._current_time_counter > 0:
            time.sleep(periodic_check_time)
            self._lock.acquire()
            self._current_time_counter -= periodic_check_time
            self._lock.release()
        self.cancel()
        self.__print("dev", "debug", "End session")

    def _reset_time_counter(self):
        self.__print("dev", "debug", "Reset time counter")
        self._lock.acquire()
        self._current_time_counter = self._timeout
        self._lock.release()

    def _cancel_time_counter(self):
        self._lock.acquire()
        self._current_time_counter = 0
        self._lock.release()


class ActiveSchemeSession(SchemeSession):
    def activate(self, *args):
        if self._in_process:
            return None, None

        if self._initial is None:
            raise Exception("You must assign initial function to your session before calling activate()")
        
        packet, des = self._initial(*args)
        if packet is not None:
            super().activate()
        return packet, des

    def assign_initial(self, initial_fn):
        assert hasattr(initial_fn, "__call__"), "Initial of ActiveSession must be callable"
        return super().assign_initial(initial_fn)


class PassiveSchemeSession(SchemeSession):
    def assign_initial(self, initial_status):
        assert isinstance(initial_status, int), "Initial of ActiveSession must be an integer"
        assert initial_status in self._state.keys()
        return super().assign_initial(initial_status)

    def response(self, source: str, packet_dict: dict):
        assert isinstance(packet_dict, dict)
        assert self._initial is not None

        packet_status = packet_dict["status"]
        if packet_status == self._initial and not self._in_process:
            self.activate()

        return super().response(source, packet_dict)


class SessionManager(object):
    def __init__(
                self, 
                external_scheme_type_group: ConstGroup,
                internal_scheme_type_group: ConstGroup,
                name: str = None,
                logger_generator: LoggerGenerator = ...,
                display: dict = ...
            ) -> None:
        self.__sessions = {}
        self._external_scheme_type_group = external_scheme_type_group
        self._internal_scheme_type_group = internal_scheme_type_group
        self._manager_name = name
        self._logger_generator = logger_generator
        self._display = display

    def create_session(
                    self,
                    scheme_type: int,
                    timeout: float,
                    active: bool = True,
                    logger_generator: LoggerGenerator = None,
                    display: dict = None
                ) -> SchemeSession:
        assert scheme_type not in self.__sessions.keys(),\
            "You created a session of this packet type ({})".format(scheme_type)

        assert scheme_type in self._external_scheme_type_group\
            or scheme_type in self._internal_scheme_type_group

        if scheme_type in self._external_scheme_type_group:
            session_name = self._external_scheme_type_group._dict[scheme_type]
        else:
            session_name = self._internal_scheme_type_group._dict[scheme_type]

        if self._manager_name:
            session_name = "[{}({})]".format(self._manager_name, session_name)

        logger_generator = self._logger_generator if logger_generator is None else logger_generator
        display = self._display if display is None else display
        if active:
            session = ActiveSchemeSession(scheme_type, timeout, session_name, logger_generator, display)
        else:
            session = PassiveSchemeSession(scheme_type, timeout, session_name, logger_generator, display)
        self.__sessions.update({scheme_type: session})
        return session

    def activate(self, scheme_type, *args):
        assert scheme_type in self.__sessions.keys(),\
            "You must create a session for this packet type ({})".format(scheme_type)
        if not isinstance(self.__sessions[scheme_type], ActiveSchemeSession):
            raise Exception("Only ActiveSession objects can call method activate() directly")
        return self.__sessions[scheme_type].activate(*args)

    def response(self, source: str, packet_dict: dict, *args):
        packet_type = packet_dict["scheme"]

        assert packet_type in self.__sessions.keys()
        return self.__sessions[packet_type].response(source, packet_dict, *args)

    def clone(self):
        session_manager = SessionManager(
            self._external_scheme_type_group,
            self._internal_scheme_type_group,
            self._manager_name,
            self._logger_generator,
            self._display
        )
        for key in self.__sessions.keys():
            session_manager.__sessions[key] = self.__sessions[key].clone()
        return session_manager