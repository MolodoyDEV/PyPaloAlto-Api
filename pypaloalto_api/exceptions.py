import json


class PaloAltoException(Exception):
    pass


class _RequestExceptionMixin(Exception):
    def __init__(self, status_code: int = 0, content: str = '', description: str = ''):
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
        return f'{self.description} - {self.status_code}, {self.json}'


class RequestParsingException(Exception, _RequestExceptionMixin):
    pass


class PaloAltoApiRequestException(PaloAltoException, _RequestExceptionMixin):
    pass
