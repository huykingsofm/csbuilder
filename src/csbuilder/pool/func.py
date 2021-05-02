from typing import Type

from csbuilder.pool.pool import Pool
from csbuilder.standard import Protocols, Roles, States


def protocols(group: Type[Protocols]):
    return Pool.protocols(group)


def roles(protocol: Type[Protocols]):
    return Pool.roles(protocol)


def states(protocol: Protocols, role: Roles):
    return Pool.states(protocol, role)


def scheme(protocol: Protocols, role: Roles, activation = None):
    return Pool.scheme(protocol, role, activation)


def response(state: States):
    return Pool.response(state)


def activation(method):
    return Pool.activation(method)
