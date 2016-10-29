import asyncio
import functools
from http import HTTPStatus
from typing import Optional

import httptools

from .abc import AbstractDispatcher
from .exc import HTTPException
from .req import Request


class GatewayProtocol(asyncio.Protocol):
    __slots__ = ('dispatcher', 'loop', 'parser', 'transport', 'connections',
                 'request_timeout', 'reader', 'url', 'headers')

    """
    This is a specialized HTTP protocol meant to be a low-latency API Gateway.
    For the HTTP dispatcher this means that data in/out will be streamed each
    direction, other dispatchers may require full request/response bodies be
    read into memory.

    :param loop: event loop
    :param dispatcher: dispatcher strategy
    :param request_timeout: Max length of a request cycle in secs (def: 15s)
    """
    def __init__(self, loop: asyncio.BaseEventLoop,
                 dispatcher: AbstractDispatcher, *, request_timeout: int=15):
        assert isinstance(dispatcher, AbstractDispatcher), dispatcher

        self.dispatcher = dispatcher
        self.loop = loop

        self.parser = None
        self.transport = None
        self.connections = set()
        self.request_timeout = request_timeout

        self.reader = None  # request content reader
        self.timeout = None  # call length limit

        # request info
        self.url = None
        self.headers = None

    # ===========================
    # asyncio.Protocol callbacks
    # ===========================
    def connection_made(self, transport: asyncio.Transport) -> None:
        self.transport = transport
        self.connections.add(self)
        self.parser = httptools.HttpRequestParser(self)
        self.reader = asyncio.StreamReader(loop=self.loop)

        self.start_timeout()

    def connection_lost(self, exc: Optional[Exception]) -> None:
        self.cancel_timeout()
        self.connections.remove(self)

    def data_received(self, data: bytes) -> None:
        try:
            self.parser.feed_data(data)
        except httptools.parser.errors.HttpParserError:
            self.transport.close()

    # ===========================
    # httptools parser callbacks
    # ===========================
    def on_message_begin(self) -> None:
        self.url = None
        self.headers = []

    def on_header(self, name: bytes, value: bytes) -> None:
        self.headers.append((name, value))

    def on_url(self, url: bytes) -> None:
        self.url = url.decode()

    def on_headers_complete(self) -> None:
        request = Request(self.parser.get_method(),
                          self.parser.get_http_version(),
                          self.headers, self.reader,
                          self.url, self.transport, self.loop)
        task = self.loop.create_task(self.dispatcher.dispatch(request))
        task.add_done_callback(functools.partial(self.handle_task_complete,
                                                 request=request))

    def on_body(self, body: bytes) -> None:
        self.reader.feed_data(body)

    def on_message_complete(self) -> None:
        self.reader.feed_eof()

    # ================================
    # ours
    # ================================
    def start_timeout(self) -> None:
        """
        Start the request timeout task, triggering on_timeout_elapsed if the
        request time exceeds the time set.
        :return:
        """
        self.timeout = self.loop.call_later(self.request_timeout,
                                            self.on_timeout_elapsed)

    def cancel_timeout(self) -> None:
        """
        Cancel the request timeout task.
        :return:
        """
        if self.timeout:
            self.timeout.cancel()

    def on_timeout_elapsed(self) -> None:
        """
        Callback to handle connection timeouts
        :return:
        """
        print('Error: request duration timeout.')
        self.transport.close()

    def handle_task_complete(self, task: asyncio.Task,
                             request: Request) -> None:
        """
        Handle the cleanup after a handler/dispatcher completed
        its job.

        :param task: Completed task
        :param request: Request
        :return: None
        """
        # There isn't really anything we can do with the transport once it's
        # shut or shutting down. Allows dispatchers to use the low-level
        # interface without bombing the server.
        if self.transport.is_closing():
            return

        f = self.handle_task_error if task.exception()\
            else self.handle_task_ok
        f(task, request)
        self.transport.close()

    def handle_task_ok(self, task: asyncio.Task, request: Request) -> None:
        """
        Handle the successful execution of a handler task, effectively this
        writes and closes the transport.

        :param task: Completed task, task.exception() is None
        :param request: Original request
        :return: None
        """
        content = task.result() or b''
        self.transport.write((
            b'HTTP/%b 200 OK\r\n'
            b'Content-Type: text/plain\r\n'
            b'Content-Length: %d\r\n'
            b'\r\n'
            b'%b'
        ) % (request.version.encode(), len(content), content))

    def handle_task_error(self, task: asyncio.Task, request: Request) -> None:
        """
        Handle the non-successful execution of a handler task, effectively
        this writes and closes the transport.

        :param task: Completed task, task.exception() is not None
        :param request: Original request
        :return: None
        """
        # TODO: Log the exception, map to a different statuses
        exc = task.exception()
        print('exception:', exc)
        if isinstance(exc, HTTPException):
            status = exc.status
            message = str(exc)
        else:
            status = HTTPStatus.INTERNAL_SERVER_ERROR
            message = ''

        self.transport.write((
            b'HTTP/%b %d %b\r\n'
            b'Content-Type: text/plain\r\n'
            b'Content-Length: %d\r\n'
            b'\r\n'
            b'%b'
        ) % (
            request.version.encode(),
            status.value,
            status.phrase.encode(),
            len(message),
            message.encode()
        ))
