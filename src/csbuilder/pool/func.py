from typing import Any, Type

from csbuilder.pool.pool import Pool
from csbuilder.standard import Protocols, Roles, States


def protocols(group: Protocols):
    return Pool.protocols(group)


def roles(protocol: Type[Protocols]):
    return Pool.roles(protocol)


def states(protocol: Type[Protocols], role: Roles):
    return Pool.states(protocol, role)


def scheme(protocol: Type[Protocols], role: Roles, passive_activation: States = None):
    return Pool.scheme(protocol, role, passive_activation)


def response(state: States):
    return Pool.response(state)


def active_activation(method):
    return Pool.active_activation(method)
