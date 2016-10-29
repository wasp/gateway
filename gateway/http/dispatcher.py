import atexit

from aiohttp import ClientOSError, ClientSession
from multidict import CIMultiDict

from gateway.abc import AbstractDispatcher
from gateway.exc import HTTPBadGatewayException
from gateway.req import Request

from .resolver import AbstractServiceResolver


class HttpDispatcher(AbstractDispatcher):
    """
    Dispatcher that proxies HTTP messages back and forth, if
    a backend system can be resolved from the AbstractServiceResolver
    """
    __slots__ = ('_buf_size', '_resolver', '_session')

    def __init__(self, resolver_: AbstractServiceResolver, *, buf_size=128):
        self._resolver = resolver_
        self._buf_size = buf_size
        self._session = ClientSession()

    @atexit.register
    def close(self):
        if not self._session.closed:
            self._session.close()

    async def dispatch(self, request: Request):
        service_addr = await self._resolver.resolve(request)
        print('service_addr:', service_addr)

        # we need the headers as a dict:
        headers = CIMultiDict()
        for k, v in request.headers:
            headers[k.decode()] = v.decode()

        # aiohttp will try to do a len on the content if there is
        # no content-length header. Since we aren't currently supporting
        # streaming incoming, we are going to just pretend that there is
        # no data...
        if headers.get('Content-Length') is None:
            data = None
        else:
            data = request.content

        try:
            async with self._session.request(request.method.decode(), service_addr,
                                             data=data,
                                             headers=headers) as resp:
                # TODO: Need to support any other versions?
                # TODO: Abstract to response class.
                request.transport.write(b'HTTP/1.1 %d %b\r\n' % (resp.status, resp.reason.encode()))
                # TODO: Figure out a way to use raw_headers to avoid the decode/encode.
                #       right now they appear to be all caps - which I am not sure is OK
                for k, v in resp.headers.items():
                    request.transport.write(b'%b: %b\r\n' % (k.encode(), v.encode()))
                request.transport.write(b'\r\n')

                while True:
                    chunk = await resp.content.readany()
                    if not chunk:
                        break
                    request.transport.write(chunk)

                request.transport.close()
        except ClientOSError:
            raise HTTPBadGatewayException('Unable to reach destination, service unreachable.')
