import abc
import re
from typing import Optional

from gateway.exc import HTTPNotFoundException, HTTPBadGatewayException
from gateway.req import Request


URL_REGEX = re.compile(r'^/(?P<service>[^/?]+)(?P<path>[^?]+)?(?P<query>\?.*)?$')  # noqa


def _build_url(path: Optional[str], query: Optional[str], abs_url: str) -> str:
    """
    Combine the parts to make the URL

    TODO: Does anyone want the service part of the path included,
    or is stripping it always the right thing?

    :param path: Path, everything after the service name
    :param query: Query string
    :param abs_url: absolute url to the service
    :return: str
    """
    abs_url = bytearray(abs_url.encode())
    if path is not None:
        abs_url.extend(path.encode())
    if query is not None:
        abs_url.extend(query.encode())
    return abs_url.decode()


class AbstractServiceResolver(metaclass=abc.ABCMeta):
    """
    Interface to resolve a service from some parameter of the
    request. This is the "service discovery" portion of an HTTP
    based microservice system.

    # TODO: Maybe use a context manager for any resolvers that
            may want to use a lease-like strategy.
    """
    @abc.abstractmethod
    async def resolve(self, request: Request) -> str:
        """
        Resolve a service address.
        :param request: Request object
        :response str: Absolute url to a service that can satisfy the request
        """


class DictResolver(dict, AbstractServiceResolver):
    def __setitem__(self, key, value: str) -> None:
        super().__setitem__(key, value.encode())

    async def resolve(self, request: Request) -> str:
        url = request.url
        match = URL_REGEX.search(url)
        if not match:
            # TODO: Should use non-http specific errors
            raise HTTPNotFoundException('URL does not contain service route.')

        service, path, query = match.groups()
        if service not in self:
            raise HTTPBadGatewayException('Unable to satisfy routes for '
                                          'service: ' + service)

        return _build_url(path, query, self[service])
