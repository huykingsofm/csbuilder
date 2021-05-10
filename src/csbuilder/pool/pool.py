from typing import Any, Callable, Dict, List, Tuple, Type

from hks_pylib.hksenum import get_enum

from csbuilder.scheme import Scheme
from csbuilder.standard import Roles, Protocols, States

from csbuilder.errors.pool import PoolError
from csbuilder.errors.pool import PredefinitionError
from hkserror.hkserror import HFormatError, HTypeError


def is_preparing():
    pass

def none():
    pass

class SchemaStructure(object):
    def __init__(self) -> None:
        self._states: Type[States] = None
        self._scheme: Scheme = None
        self._active_activation = none
        self._passive_activation = None

    def states(self, states: Type[States] = None) -> Type[States]:
        if states is None:
            return self._states

        assert issubclass(states, States)
        self._states = states

    def scheme(self, scheme: Scheme = None) -> Scheme:
        if scheme is None:
            return self._scheme

        assert issubclass(scheme, Scheme)
        self._scheme = scheme

    def active_activation(self, active_activation: Callable = None):
        if active_activation is None:
            if self._active_activation == none:
                return None
            return self._active_activation

        if not callable(active_activation):
            raise HTypeError("active_activation", active_activation, Callable, None)

        self._active_activation = active_activation

    def passive_activation(self, passive_activation: States = None):
        if passive_activation is None:
            return self._passive_activation

        if not isinstance(passive_activation, States):
            raise HTypeError("passive_activation", passive_activation, States, None)

        self._passive_activation = passive_activation

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return ("{" + "scheme = {}, states = {}, active_activation = "
                "{} passive_activation = {}".format(
                self._scheme,
                self._states,
                self._active_activation,
                self._passive_activation
            ) + "}")


class RevertSchemaStructure(object):
    def __init__(self, protocol: Protocols, role: Roles) -> None:
        self._protocol = protocol
        self._role = role

    def protocol(self):
        return self._protocol
    
    def role(self):
        return self._role
    
    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return "{" + "protocol = {}, role = {}".format(self._protocol, self._role) + "}"


class Pool(object):
    __protocols: Dict[Protocols, Dict[Roles, SchemaStructure]] = {}
    __schemes: Dict[Scheme, RevertSchemaStructure] = {}
    __states: Dict[Type[States], RevertSchemaStructure] = {}
    __responses: Dict[States, Any] = {}

    @staticmethod
    def int2protocol(i: int) -> Protocols:
        if not isinstance(i, int):
            raise HTypeError("i", i, int)

        for protocol in Pool.__protocols.keys():
            if protocol.value == i:
                return protocol

        return None

    @staticmethod
    def protocols(group: Type[Protocols]):
        if not issubclass(group, Protocols):
            raise HTypeError("group", group, Type[Protocols])

        for protocol in group:
            if get_enum(Pool.__protocols, protocol.value, None) != None:
                raise PoolError("Protocol {} has already existed "
                "in the packet pool.".format(protocol))

            Pool.__protocols.update({protocol: {}})

        return group

    @staticmethod
    def roles(protocol: Protocols):
        if not isinstance(protocol, Protocols):
            raise HTypeError("protocol", protocol, Protocols)

        if protocol not in Pool.__protocols.keys():
            raise PoolError("The protocol {} has not been "
            "defined yet.".format(protocol))

        def _add_roles(group: Type[Roles]):
            if not issubclass(group, Roles):
                raise HTypeError("group", group, Type[Roles])

            if len(group) != 2:
                raise HFormatError("The role group must have exactly two elements.")

            for role in group:
                if role in Pool.__protocols[protocol].keys():
                    raise PoolError("Role {} has already "
                    "defined in the protocol {}.".format(role, protocol))

                Pool.__protocols[protocol].update({role: SchemaStructure()})

            return group

        return _add_roles

    @staticmethod
    def states(protocol: Protocols, role: Roles):
        if not isinstance(protocol, Protocols):
            raise HTypeError("protocol", protocol, Protocols)

        if protocol not in Pool.__protocols.keys():
            raise PoolError("The protocol {} has not been "
            "defined yet.".format(protocol))

        if not isinstance(role, Roles):
            raise HTypeError("role", role, Roles)

        if role not in Pool.__protocols[protocol].keys():
            raise PoolError("The role {} has not been "
            "defined yet.".format(role))

        if Pool.__protocols[protocol][role].states() is not None:
            raise PoolError("The states of {}.{} has been "
            "already defined.".format(protocol.value, role.value))

        def __add_state(group: Type[States]):
            if not issubclass(group, States):
                raise HTypeError("group", group, Type[States])

            if "IGNORE" not in group.names():
                raise HFormatError("The state group {} "
                "must contain the IGNORE element.".format(group.__name__))

            Pool.__protocols[protocol][role].states(group)
            Pool.__states.update({group: RevertSchemaStructure(protocol, role)})

            for state in group:
                Pool.__responses.update({state: None})

            return group

        return __add_state

    @staticmethod
    def scheme(protocol: Protocols, role: Roles, passive_activation: States = None):
        if not isinstance(protocol, Protocols):
            raise HTypeError("protocol", protocol, Protocols)

        if protocol not in Pool.__protocols.keys():
            raise PoolError("The protocol {} has not been "
            "defined yet.".format(protocol))

        if not isinstance(role, Roles):
            raise HTypeError("role", role, Roles)

        if role not in Pool.__protocols[protocol].keys():
            raise PoolError("The role {} has not been "
            "defined yet.".format(role))

        if passive_activation is not None and not isinstance(passive_activation, States):
            raise HTypeError("passive_activation", passive_activation, States, None)

        if Pool.__protocols[protocol][role].scheme() is not None:
            raise PoolError("The scheme of {}.{} has been "
            "already defined.".format(protocol.value, role.value))

        Pool.__protocols[protocol][role].passive_activation(passive_activation)
        Pool.__protocols[protocol][role].active_activation(is_preparing)

        def _add_scheme(cls: Type[Scheme]):
            if not issubclass(cls, Scheme):
                raise HTypeError("cls", cls, Type[Scheme])

            validate_activation(cls, protocol, role)
            validate_responses(cls, protocol, role)

            Pool.__protocols[protocol][role].scheme(cls)
            Pool.__schemes.update({cls: RevertSchemaStructure(protocol, role)})

            if Pool.get_active_activation(protocol, role) is is_preparing:
                Pool.__protocols[protocol][role].active_activation(none)
            return cls

        return _add_scheme

    @staticmethod
    def response(state: States):
        if not isinstance(state, States):
            raise HTypeError("state", state, States)

        if state not in Pool.__responses.keys():
            raise PoolError("The state {} has not defined yet.".format(state))

        if Pool.__responses[state] is not None:
            raise PoolError("The state {} has already defined.".format(state))

        def _add_response(method):
            if not callable(method):
                raise HTypeError("method", method, Callable)

            Pool.__responses[state] = method
            return method

        return _add_response

    @staticmethod
    def active_activation(method):
        if not callable(method):
            raise HTypeError("method", method, Callable)

        protocol = None
        role = None
        count = 0
        for p in Pool.__protocols.keys():
            for r in Pool.__protocols[p].keys():
                if Pool.__protocols[p][r].active_activation() == is_preparing:
                    count += 1
                    protocol = p
                    role = r

        if count == 0:
            raise PredefinitionError("Something wrongs. "
            "There are no preparing activation.")

        if count > 1:
            raise PredefinitionError("Something wrongs. "
            "There are many preparing activations.")

        Pool.__protocols[protocol][role].active_activation(method)
        return method

    @staticmethod
    def get_protocols() -> List[Protocols]:
        return list(Pool.__protocols.keys())

    @staticmethod
    def get_roles(protocol: Protocols) -> List[Roles]:
        if not isinstance(protocol, Protocols):
            raise HTypeError("protocol", protocol, Protocols)

        if protocol not in Pool.__protocols.keys():
            raise PoolError("The protocol {} has not defined yet.".format(protocol))

        return list(Pool.__protocols[protocol].keys())

    @staticmethod
    def get_opposite_role(
            protocol: Protocols,
            role: Roles
        ) -> Roles:
        if not isinstance(protocol, Protocols):
            raise HTypeError("protocol", protocol, Protocols)
        
        if not isinstance(role, Roles):
            raise HTypeError("role", role, Roles)

        all_roles = Pool.get_roles(protocol)

        if role not in all_roles:
            raise PoolError("The role {} is not in Pool.{}.".format(role, protocol.name))

        for opp_role in all_roles:
            if opp_role != role:
                return opp_role

    @staticmethod
    def get_states(protocol: Protocols, role: Roles) -> Type[States]:
        if not isinstance(protocol, Protocols):
            raise HTypeError("protocol", protocol, Protocols)
        
        if not isinstance(role, Roles):
            raise HTypeError("role", role, Roles)

        if protocol not in Pool.__protocols.keys():
            raise PoolError("The protocol {} doesn't exist "
            "in Pool.".format(protocol))

        if role not in Pool.__protocols[protocol].keys():
            raise PoolError("The role {} doesn't exist in "
            "Pool.{}.".format(role, protocol.name))

        return Pool.__protocols[protocol][role].states()

    @staticmethod
    def get_scheme(protocol: Protocols, role: Roles) -> Scheme:
        if not isinstance(protocol, Protocols):
            raise HTypeError("protocol", protocol, Protocols)
        
        if not isinstance(role, Roles):
            raise HTypeError("role", role, Roles)

        if protocol not in Pool.__protocols.keys():
            raise PoolError("The protocol {} doesn't exist "
            "in Pool.".format(protocol))

        if role not in Pool.__protocols[protocol].keys():
            raise PoolError("The role {} doesn't exist in "
            "Pool.{}.".format(role, protocol.name))

        return Pool.__protocols[protocol][role].scheme()

    @staticmethod
    def get_response(state: States):
        if not isinstance(state, States):
            raise HTypeError("state", state, States)

        if state not in Pool.__responses.keys():
            raise PoolError("The state {} doesn't exist in "
            "Pool.".format(state))

        return Pool.__responses[state]

    @staticmethod
    def get_active_activation(protocol: Protocols, role: Roles):
        if not isinstance(protocol, Protocols):
            raise HTypeError("protocol", protocol, Protocols)
        
        if not isinstance(role, Roles):
            raise HTypeError("role", role, Roles)

        if protocol not in Pool.__protocols.keys():
            raise PoolError("The protocol {} doesn't exist "
            "in Pool.".format(protocol))

        if role not in Pool.__protocols[protocol].keys():
            raise PoolError("The role {} doesn't exist in "
            "Pool.{}.".format(role, protocol.name))

        return Pool.__protocols[protocol][role].active_activation()

    @staticmethod
    def get_passive_activation(protocol: Protocols, role: Roles):
        if not isinstance(protocol, Protocols):
            raise HTypeError("protocol", protocol, Protocols)

        if not isinstance(role, Roles):
            raise HTypeError("role", role, Roles)

        if protocol not in Pool.__protocols.keys():
            raise PoolError("The protocol {} doesn't exist "
            "in Pool.".format(protocol))

        if role not in Pool.__protocols[protocol].keys():
            raise PoolError("The role {} doesn't exist in "
            "Pool.{}.".format(role, protocol.name))

        return Pool.__protocols[protocol][role].passive_activation()

    @staticmethod
    def revert_scheme(scheme: Type[Scheme]) -> Tuple[Protocols, Roles]:
        if not issubclass(scheme, Scheme):
            raise HTypeError("scheme", scheme, Type[Scheme])

        if scheme not in Pool.__schemes.keys():
            raise PoolError("The scheme {} has not "
            "defined yet in Pool.".format(scheme.__name__))

        revert = Pool.__schemes[scheme]
        return revert.protocol(), revert.role()

    @staticmethod
    def revert_states(states: Type[States]) -> Tuple[Protocols, Roles]:
        if not issubclass(states, States):
            raise HTypeError("states", states, Type[States])

        if states not in Pool.__states.keys():
            raise PoolError("The states {} has not "
            "defined yet in Pool.".format(states.__name__))
        
        revert = Pool.__states[states]
        return revert.protocol(), revert.role()

    @staticmethod
    def revert_state(state: States) -> Tuple[Protocols, Roles]:
        if not isinstance(state, States):
            raise HTypeError("state", state, States)

        states = type(state)
        return Pool.revert_states(states)


def validate_activation(cls: Type[Scheme], protocol, role):
    opposite_role = Pool.get_opposite_role(protocol, role)
    opposite_states = Pool.get_states(protocol, opposite_role)

    passive_activation = Pool.get_passive_activation(protocol, role)
    if passive_activation and passive_activation not in opposite_states:
        raise PredefinitionError("The passive activation must "
        "be a state of the opposite scheme.")

    active_activation = Pool.get_active_activation(protocol, role)
    if active_activation != is_preparing and active_activation not in cls.__dict__.values():
        raise PredefinitionError("The active activation must be a "
        "method of the scheme class.")

    if not active_activation and not passive_activation:
        raise PredefinitionError("A scheme must have at least a "
        "activation type (active activation or passive activation).")

def validate_responses(cls: Type[Scheme], protocol: Protocols, role: Roles):
    opposite_role = Pool.get_opposite_role(protocol, role)
    opposite_states = Pool.get_states(protocol, opposite_role)

    for state in opposite_states:
        response = Pool.get_response(state)
        if response is None:
            raise PredefinitionError("There is no definition of the state {}.".format(state))

        if response not in cls.__dict__.values():
            raise PredefinitionError("Scheme and response are mismatched ({}/{}). "
            "Requiring the response belonging to the scheme.".format(cls, response))
