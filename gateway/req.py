import asyncio
from typing import Dict, Tuple, List


class Request:
    __slots__ = ('_method', '_version', '_headers', '_content', '_url',
                 '_transport', '_loop')

    def __init__(self, method, version, headers, content, url, transport, loop):
        """
        Model of an HTTP Request, likely unbuffered.

        :param method: Request METHOD
        :param version: HTTP Version
        :param headers: List of Tuples
        :param content: Raw stream reader
        :param url: Target URL
        :param transport: asyncio transport, not to be used directly
        :param loop: asyncio loop to read the content on
        """
        self._method = method
        self._version = version
        self._headers = headers
        self._content = content
        self._url = url
        self._transport = transport
        self._loop = loop

    @property
    def method(self) -> bytes:
        return self._method

    @property
    def version(self) -> bytes:
        return self._version

    @property
    def headers(self) -> List[Tuple[bytes, bytes]]:
        return self._headers

    @property
    def content(self) -> asyncio.StreamReader:
        """The raw content reader, note this can only be read once."""
        return self._content

    @property
    def url(self) -> str:
        return self._url

    @property
    def transport(self) -> asyncio.Transport:
        # TODO: remove this being exposed.
        return self._transport

    @property
    def loop(self) -> asyncio.BaseEventLoop:
        return self._loop
