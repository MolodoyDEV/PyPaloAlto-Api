import json
from typing import Optional


class PaloAltoException(Exception):
    def __init__(self, message: str or Exception, device_name: Optional[str] = None):
        self.device_name = device_name
        self.message = message

    def __repr__(self):
        if self.device_name:
            return f'{[self.device_name]}:{self.message.__repr__()}'

        return self.message.__repr__()


class _RequestExceptionBase:
    def __init__(self, device_name: str, status_code: int = 0, content: str = '', description: str = ''):
        self.device_name = device_name
        self.status_code = status_code
        self.content = content
        self.description = description

    @property
    def json(self) -> dict:
        try:
            return json.loads(self.content)
        except:
            return {}

    def __repr__(self) -> str:
        return f'[{self.device_name}]:{self.description} - {self.status_code}, {self.json}'


class RequestParsingException(_RequestExceptionBase, Exception):
    """Deprecated, use ReplyParsingException instead"""
    pass


class ReplyParsingException(RequestParsingException):
    pass


class EmptyReplyException(ReplyParsingException, PaloAltoException):
    def __init__(self, device_name: str, status_code: int = 0):
        super(EmptyReplyException, self).__init__(device_name, status_code, '', f'PaloAlto reply is empty.')


class PaloAltoApiRequestException(_RequestExceptionBase, PaloAltoException):
    pass
