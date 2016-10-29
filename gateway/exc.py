from http import HTTPStatus


class HTTPException(Exception):
    __status__ = HTTPStatus.INTERNAL_SERVER_ERROR

    @property
    def status(self):
        return self.__status__


# ==============================
# 4xx
# ==============================
class HTTPNotFoundException(HTTPException):
    __status__ = HTTPStatus.NOT_FOUND


class HTTPBadRequestException(HTTPException):
    __status__ = HTTPStatus.BAD_REQUEST


# ==============================
# 5xx
# ==============================
class HTTPBadGatewayException(HTTPException):
    __status__ = HTTPStatus.BAD_GATEWAY
