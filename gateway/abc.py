import abc

from gateway.req import Request


class AbstractDispatcher(metaclass=abc.ABCMeta):
    """
    Definition of a dispatcher, effectively the translation
    from the gateway's REST call to the backend architecture's
    tongue.
    """
    @abc.abstractmethod
    async def dispatch(self, request: Request) -> None:
        raise NotImplementedError