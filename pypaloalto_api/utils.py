import copy
import os
from functools import wraps
from requests.auth import AuthBase
import datetime

from pypaloalto_api import logger


class ApiKeyAuth(AuthBase):
    """Implements a custom authentication scheme."""

    def __init__(self, _token):
        self.token = _token

    def __call__(self, r):
        """Attach an API token to a custom auth header."""
        r.headers['X-PAN-KEY'] = f'{self.token}'  # Python 3.6+
        return r


def read_file(full_file_name: str):
    with open(full_file_name, "r", encoding="UTF-8") as my_file:
        _value = my_file.read()

    return _value


def write_file(full_file_name: str, value: str):
    with open(full_file_name, "w", encoding="UTF-8") as my_file:
        my_file.write(value.strip())


def append_file(full_file_name: str, new_value: str, at_the_top=False):
    if not os.path.isfile(full_file_name):
        write_file(full_file_name, new_value.strip())

    else:
        _current_value = ""
        with open(full_file_name, "r", encoding="UTF-8") as my_file:
            _current_value = my_file.read()

        with open(full_file_name, "w", encoding="UTF-8") as my_file:
            if at_the_top:
                my_file.write(f"{new_value}{_current_value}".strip())
            else:
                my_file.write(f"{_current_value}{new_value}".strip())


def list_to_string(values_list: list, delimiter: str = " ") -> str:
    _result = ""

    for _item in values_list:
        _result += str(_item) + delimiter

    return _result[:len(_result) - len(delimiter)]


def get_current_date_time():
    return datetime.datetime.now().replace(microsecond=0).replace(tzinfo=None)


def get_current_date_time_as_string():
    return format_datetime_as_string(get_current_date_time())


def format_datetime_as_string(_datetime: datetime):
    return _datetime.strftime('%Y-%m-%d %H:%M:%S')


def format_datetime_as_string_ru(_datetime: datetime):
    return _datetime.strftime('%d-%m-%Y %H:%M:%S')


def format_date_as_string_ru(_datetime: datetime.date):
    return _datetime.strftime('%d-%m-%Y')


def non_string_list_join(your_list: list, join_string: str):
    return join_string.join([str(x) for x in your_list])


def remove_key_from_dict_recursively(_dict: dict, key_to_remove: str) -> dict:
    for _key, _value in _dict.items():
        if isinstance(_value, dict):
            _dict[_key] = remove_key_from_dict_recursively(_value, key_to_remove)
        elif _key == key_to_remove:
            return _value

    return _dict


def deprecated(new_func_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.warning(f'Function {str(func)} is deprecated! Use {str(new_func_name)} instead.')
            return func(*args, **kwargs)

        return wrapper

    return decorator


_deepcopy_dispatcher = {}


def _copy_list(l: list, dispatch):
    ret = l.copy()
    for idx, item in enumerate(ret):
        cp = dispatch.get(type(item))
        if cp is not None:
            ret[idx] = cp(item, dispatch)
    return ret


def _copy_dict(d: dict, dispatch):
    ret = d.copy()
    for key, value in ret.items():
        cp = dispatch.get(type(value))
        if cp is not None:
            ret[key] = cp(value, dispatch)

    return ret


_deepcopy_dispatcher[list] = _copy_list
_deepcopy_dispatcher[dict] = _copy_dict


def custom_deepcopy(sth):
    cp = _deepcopy_dispatcher.get(type(sth))
    if cp is None:
        return copy.deepcopy(sth)
    else:
        return cp(sth, _deepcopy_dispatcher)
