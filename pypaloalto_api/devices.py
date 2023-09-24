import copy
import logging
import typing
from abc import ABC, abstractmethod
from collections import namedtuple
from requests.auth import HTTPBasicAuth, AuthBase
from pypaloalto_api.enums import HaPeerState
import json
import time
import xml.etree.ElementTree as ET
import requests
import urllib3
from pypaloalto_api.enums import HttpRequestMethod
from pypaloalto_api import settings
from pypaloalto_api.exceptions import PaloAltoApiRequestException, PaloAltoException, RequestParsingException
from pypaloalto_api.operational_commands import Builder as OpBuilder
from pypaloalto_api.utils import ApiKeyAuth
from pypaloalto_api.xmlapi import XmlApiRequestType, XmlApiConfigAction, ConfigAction

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PaloAltoDevice(ABC):
    _restapi_version: str
    _ipv4: str
    _primary_ip: str
    _exception_on_request_error: bool
    request_delay_seconds: float
    _cached_ha_peer_state: HaPeerState

    @abstractmethod
    def __init__(self):
        raise Exception("You can't instantiate an abstract class!")

    @property
    def ha_peer_state(self):
        """Will return cached ha peer state. To get actual state use function update_and_get_ha_peer_state()"""
        return self._cached_ha_peer_state

    @property
    def restapi_version(self):
        return self._restapi_version

    @property
    def ipv4(self):
        return self._ipv4

    @abstractmethod
    def _get_auth(self):
        pass

    def update_and_get_ha_peer_state(self):
        _ha_info, _status_code = self.xml_api_operational_request(OpBuilder.show_ha_state())

        if _ha_info.find('result/enabled').text == 'yes':
            self._cached_ha_peer_state = HaPeerState(_ha_info.find('result/group/local-info/state').text)
        else:
            self._cached_ha_peer_state = HaPeerState.ha_not_enabled

        return self._cached_ha_peer_state

    def restapi_generate_key(self, user: str, password: str) -> str:
        """Be careful! If you generate an API key for user credential then his previous api key will be expired!"""
        _response = requests.request(HttpRequestMethod.get.value,
                                     f'https://{self._ipv4}/api/?type=keygen&user={user}&password={password}',
                                     verify=False)

        if _response.status_code != 200:
            if self._exception_on_request_error:
                raise PaloAltoApiRequestException(_response.status_code, _response.content.decode(), 'bad status code')
            else:
                return _response.content.decode()

        else:
            return ET.fromstring(_response.content).find('result/key').text

    def restapi_request(self, route: str, request_method: HttpRequestMethod,
                        data: dict or str = None, params: dict = None, ssl_verify=False) -> (str, int):
        """With delay"""
        if isinstance(data, dict):
            data = json.dumps(data)

        time.sleep(self.request_delay_seconds)
        _url = f'https://{self._primary_ip}/restapi/v{self._restapi_version}/{route}'
        reply, status_code = self.http_request(request_method, _url, data, params, ssl_verify)

        try:
            reply_json = json.loads(reply)
        except Exception as e:
            raise RequestParsingException(status_code, reply, f'Failed convert response to JSON: {e}')

        reply_msg = reply_json.get('msg')

        if reply_msg:
            if 'error' in reply_msg or 'invalid' in reply_msg or 'unauth' in reply_msg:
                if self._exception_on_request_error:
                    raise PaloAltoApiRequestException(status_code, reply, 'status is error')

                else:
                    logging.error(f'{reply} {status_code}')

        return reply, status_code

    def http_request(self, request_method: HttpRequestMethod, url: str,
                     data: dict or str or None = None, params: dict = None, ssl_verify=False) -> (str, int):
        MAX_REPEATS_COUNT = 3
        repeats_count = 0

        while True:
            _response = requests.request(request_method.value, url, auth=self._get_auth(), verify=ssl_verify, data=data,
                                         params=params)

            try:
                _response_content = _response.content.decode()
            except ValueError:
                _response_content = _response.content

            if _response.status_code != 200:
                if 'Timed out while getting config lock. Please try again.' in _response_content:
                    logging.warning('Timed out while getting config lock. Retrying after 30 seconds..')
                    time.sleep(30)
                    repeats_count += 1

                    if repeats_count >= MAX_REPEATS_COUNT:
                        raise PaloAltoApiRequestException(_response.status_code, _response_content,
                                                          'bad status code')

                    continue

                elif self._exception_on_request_error:
                    raise PaloAltoApiRequestException(_response.status_code, _response_content,
                                                      'bad status code')

                else:
                    logging.error(f'{_response.content} {_response.status_code}')

            return _response_content, _response.status_code

    def _xml_api_request(self, request_data: dict, params: dict = None, ssl_verify=False) -> (str, int):
        _url = f'https://{self._ipv4}/api/'
        time.sleep(self.request_delay_seconds)

        content, status_code = self.http_request(HttpRequestMethod.post, _url, request_data, params, ssl_verify)

        try:
            content_xml = ET.fromstring(content)
        except Exception as e:
            raise RequestParsingException(status_code, content, f'Failed convert response to XML: {e}')

        if content_xml.get('status') in ['error', 'unauth']:
            if self._exception_on_request_error:
                raise PaloAltoApiRequestException(status_code, content,
                                                  'status is error')

            else:
                logging.error(f'{content} {status_code}')

        return content_xml, status_code

    def xml_api_export_request(self, params: dict, ssl_verify=False):
        _url = f'https://{self._ipv4}/api/'
        params['type'] = XmlApiRequestType.export_files.value

        content, status_code = self.http_request(HttpRequestMethod.get, _url, params=params, ssl_verify=ssl_verify)

        if self._exception_on_request_error:
            if status_code == 200:
                try:
                    reply_xml = ET.fromstring(content)

                except (ValueError, ET.ParseError):
                    pass

                else:
                    if reply_xml.get('status') == 'error':
                        pa_msg = ET.tostring(reply_xml.find("msg"))
                        error_msg = f'Can\'t export the file.\nParams: {params}\nMsg: {pa_msg}'

                        if 'file not found' in error_msg.lower():
                            raise FileNotFoundError(error_msg)
                        else:
                            raise PaloAltoApiRequestException(status_code, content, error_msg)

        return content, status_code

    def xml_api_operational_request(self, cmd: str, params: dict = None):
        _request_data = {
            'type': XmlApiRequestType.op.value,
            'cmd': cmd
        }

        return self._xml_api_request(_request_data, params)

    def xml_api_config_request(self, action: XmlApiConfigAction or ConfigAction, xpath: str,
                               elements: typing.List[ET.Element] = None, params: dict = None):
        """takes: xml api action, xml path, xml elements list
        returns: xml reply from palo alto"""

        _request_data = {
            'type': XmlApiRequestType.config.value,
            'action': action.value,
            'xpath': xpath
        }

        if elements:
            elements_string = ''

            for _element in elements:
                if not isinstance(_element, ET.Element):
                    raise TypeError(f"Expected Element type, got {type(_element)}")

                else:
                    elements_string += ET.tostring(_element).decode()

            _request_data['element'] = elements_string

        return self._xml_api_request(_request_data, params)


class Gateway(PaloAltoDevice):

    def __init__(self, ipv4: str, config_file_full_name: str, exception_on_request_error=True):
        """
Config file structure:

ApiKey: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX==
    or
Login: admin
Password: password

ApiVersion: 10.0
RequestsDelaySeconds: 1
"""

        _config = settings.get_config_from_yaml_file(config_file_full_name)
        self._device_config_file_full_name = config_file_full_name
        self._exception_on_request_error = True
        self._ipv4 = ipv4
        self._primary_ip = self._ipv4
        self._restapi_version = _config['ApiVersion']
        self.request_delay_seconds = _config['RequestsDelaySeconds']

        api_key = _config.get('ApiKey')

        if api_key:
            self._auth = ApiKeyAuth(api_key)
        else:
            login = _config.get('Login')
            password = _config.get('Password')

            if login and password:
                self._auth = HTTPBasicAuth(login, password)
            else:
                raise Exception('Config must contains ApiKey or Login and Password!')

        _system_info = self.xml_api_operational_request(OpBuilder.show_system_info())[0]
        self._is_multi_vsys = True if _system_info.find('result/system/multi-vsys').text == 'on' else False
        self._device_name = _system_info.find('result/system/hostname').text
        self._serial = _system_info.find('result/system/serial').text
        self._cached_ha_peer_state = self.update_and_get_ha_peer_state()
        self._vsys_display_name_by_vsys_name = {}

        if self._is_multi_vsys:
            _temp_vsys_list = self.restapi_request('Device/VirtualSystems', HttpRequestMethod.get)[0]
            _temp_vsys_list = json.loads(_temp_vsys_list)

            for _vsys in _temp_vsys_list:
                _display_name = _vsys['display-name']

                if isinstance(_display_name, dict):
                    _display_name = _display_name['text']

                self._vsys_display_name_by_vsys_name[_vsys['@name']] = _display_name

        self._exception_on_request_error = exception_on_request_error

    def _get_auth(self):
        return self._auth

    @property
    def device_name(self):
        return self._device_name

    @property
    def vsys_display_name_by_vsys_name(self) -> dict:
        return copy.copy(self._vsys_display_name_by_vsys_name)

    @property
    def is_multi_vsys(self):
        return self._is_multi_vsys

    @property
    def serial(self):
        return self._serial


class _ManagedDevice(Gateway):
    """Panorama managed device. Gateway version for instantiating by panorama from panorama config."""

    def __init__(self, ipv4: str, serial: str, device_name: str, ha_state: HaPeerState, config_file_full_name: str,
                 exception_on_request_error: bool, vsys_display_name_by_vsys_name: dict, is_multi_vsys: bool):
        _config = settings.get_config_from_yaml_file(config_file_full_name)
        self._device_config_file_full_name = config_file_full_name
        self._ipv4 = ipv4
        self._primary_ip = self._ipv4
        self._restapi_version = _config['ApiVersion']

        api_key = _config.get('ApiKey')

        if api_key:
            self._auth = ApiKeyAuth(api_key)
        else:
            login = _config.get('Login')
            password = _config.get('Password')

            if login and password:
                self._auth = HTTPBasicAuth(login, password)
            else:
                raise Exception('Config must contains ApiKey or Login and Password!')

        self.request_delay_seconds = _config['RequestsDelaySeconds']
        self._cached_ha_peer_state = ha_state
        self._device_name = device_name
        self._serial = serial
        self._vsys_display_name_by_vsys_name = vsys_display_name_by_vsys_name
        self._exception_on_request_error = exception_on_request_error
        self._is_multi_vsys = is_multi_vsys


#
# def _init_paloalto_gateway_from_panorama_config(ipv4: str, serial: str, device_name: str, ha_state: HaPeerState,
#                                                 config_file_full_name: str,
#                                                 exception_on_request_error: bool, vsys_display_name_by_vsys_name: dict,
#                                                 is_multi_vsys: bool) -> Gateway:
#     pass


DeviceGroupTarget = namedtuple('DeviceGroupTarget', ('device_name', 'vsys_name', 'gateway'))


class PanoramaDeviceGroup:

    def __init__(self, device_group_name: str, targets: typing.List[DeviceGroupTarget]):
        self.__device_group_name = device_group_name
        self.__targets = targets

        for target in self.__targets:
            if target.gateway.is_multi_vsys:
                if target.vsys_name not in target.gateway.vsys_display_name_by_vsys_name.keys():
                    raise PaloAltoException(f'Error while loading DeviceGroup "{self.__device_group_name}"!\n'
                                            f'Vsys name "{target.vsys_name}" not found on device "{target.device_name}"!')

    @property
    def device_group_name(self):
        return self.__device_group_name

    @property
    def targets(self):
        return copy.deepcopy(self.__targets)


class Panorama(PaloAltoDevice):
    def __init__(self, panorama_config_file_full_name: str, device_config_file_full_name='',
                 exception_on_request_error=True, load_managed_devices=True):
        """Config file structure:

ApiKey: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX==
    or
Login: admin
Password: password

ApiVersion: 10.1
IPv4: 10.10.10.10
RequestsDelaySeconds: 1
"""
        _config = settings.get_config_from_yaml_file(panorama_config_file_full_name)

        api_key = _config.get('ApiKey')

        if api_key:
            self._auth = ApiKeyAuth(api_key)
        else:
            login = _config.get('Login')
            password = _config.get('Password')

            if login and password:
                self._auth = HTTPBasicAuth(login, password)
            else:
                raise Exception('Config must contains ApiKey or Login and Password!')

        self.api_key = _config['ApiKey']
        self._restapi_version = _config['ApiVersion']
        self._ipv4 = _config['IPv4']
        self._primary_ip = self._ipv4
        self.request_delay_seconds = float(_config['RequestsDelaySeconds'])
        self.__managed_devices: typing.List[_ManagedDevice] = []
        self.__device_groups_info: typing.List[PanoramaDeviceGroup] = []
        self._exception_on_request_error = True
        self._panorama_config_file_full_name = panorama_config_file_full_name
        self._device_config_file_full_name = device_config_file_full_name
        self.__device_groups_names: typing.List[str] = []
        self.__device_groups_hierarchy_xml = None
        self.__should_load_managed_devices = load_managed_devices

        _system_info = self.xml_api_operational_request(OpBuilder.show_system_info())[0]
        _system_info = _system_info.find('result/system')
        self._hostname = _system_info.find('hostname').text
        self._device_name = _system_info.find('devicename').text
        self._serial = _system_info.find('serial').text

        self.try_update_managed_devices()
        self.update_device_groups()
        self._exception_on_request_error = exception_on_request_error

    def __create_device_group_hierarchy_dict(self, _hierarchy_xml) -> typing.Dict[str, typing.List[dict]]:
        _dict = {}

        for _child in list(_hierarchy_xml):
            if len(list(_child)) > 0:
                if _child.get('name') in _dict:
                    _dict[_child.get('name')].append(self.__create_device_group_hierarchy_dict(_child))
                else:
                    _dict[_child.get('name')] = [self.__create_device_group_hierarchy_dict(_child)]
            else:
                _dict[_child.get('name')] = [{}]

        return _dict

    def update_device_groups(self):
        _all_dg_hierarchy_xml = self.xml_api_operational_request(OpBuilder.show_dg_hierarchy())[0].find(
            './/dg-hierarchy')
        _all_dg_names = _all_dg_hierarchy_xml.findall('.//dg')
        self.__device_groups_names = [x.get('name') for x in _all_dg_names]
        self.__device_groups_hierarchy_xml = _all_dg_hierarchy_xml
        self.__device_groups_info = []

        _cmd = OpBuilder.show_devicegroups()
        _device_groups_info, _status_code = self.xml_api_operational_request(_cmd)

        for _device_group in _device_groups_info.findall('result/devicegroups/entry'):
            _device_group_targets = []

            if self.__should_load_managed_devices:
                if _device_group.find('devices'):
                    for _serial in _device_group.findall('devices/entry/serial'):
                        _device = self.get_managed_device_by_serial(_serial.text)

                        if _device:
                            _device_vsys_list = _device_group.findall(
                                f'devices/entry[@name="{_device.serial}"]/vsys/entry')

                            if _device_vsys_list:
                                for _vsys in _device_vsys_list:
                                    _device_group_targets.append(
                                        DeviceGroupTarget(_device.device_name,
                                                          _vsys.get('name'),
                                                          _device))
                            else:
                                _device_group_targets.append(
                                    DeviceGroupTarget(_device.device_name,
                                                      None,
                                                      _device)
                                )
                        else:
                            logging.warning(
                                f'Device with serial {_serial.text} configured on panorama in device group {_device_group.get("name")} but it status is "not connected"! Can\'t load this device.')
                            # raise Exception(
                            #    f'Panorama class desync error. Device with serial {_serial.text} not in panorama managed devices list!')

            self.__device_groups_info.append(PanoramaDeviceGroup(_device_group.get('name'), _device_group_targets))

    def try_update_managed_devices(self):
        if self.__should_load_managed_devices:
            self.__load_managed_devices(self._device_config_file_full_name)
        else:
            logging.warning('panorama should_load_managed_devices is False! Managed devices not loaded.')

    def _get_auth(self) -> AuthBase:
        return self._auth

    @property
    def device_name(self):
        return self._device_name

    @property
    def hostname(self):
        return self._hostname

    @property
    def serial(self):
        return self._serial

    @property
    def device_groups_hierarchy_dict(self) -> typing.Dict[str, typing.List[dict]]:
        return self.__create_device_group_hierarchy_dict(self.__device_groups_hierarchy_xml)

    @property
    def device_groups_hierarchy_xml(self) -> ET.Element:
        return copy.copy(self.__device_groups_hierarchy_xml)

    @property
    def device_groups_names(self) -> typing.List[str]:
        return copy.copy(self.__device_groups_names)

    @property
    def managed_devices(self) -> typing.List[Gateway]:
        """Raise exception if 'load_managed_devices=False'"""
        if not self.__should_load_managed_devices:
            raise PaloAltoException(
                "You must set 'should_load_managed_devices=True' at Panorama instantiating to use this method!")

        return copy.copy(self.__managed_devices)

    def __load_managed_devices(self, device_config_file_full_name: str):
        if not device_config_file_full_name:
            raise PaloAltoException(
                "You trying to load managed devices from panorama but device config file not specified!")

        self.__managed_devices = []
        _cmd = OpBuilder.show_devices_connected()
        _managed_devices_info, _status_code = self.xml_api_operational_request(_cmd)

        for _device_info in _managed_devices_info.findall('result/devices/entry'):
            _device_vsys_names = {}

            for _vsys in _device_info.findall('.//vsys/entry'):
                _device_vsys_names[_vsys.get('name')] = _vsys.find('display-name').text

            _device = _ManagedDevice(
                _device_info.find('ip-address').text,
                _device_info.find('serial').text,
                _device_info.find('hostname').text,
                HaPeerState.ha_not_enabled if not _device_info.find('ha') else HaPeerState(
                    _device_info.find('ha/state').text),
                device_config_file_full_name,
                self._exception_on_request_error,
                _device_vsys_names,
                True if _device_info.find('multi-vsys').text == 'yes' else False
            )

            self.__managed_devices.append(_device)

    def get_managed_device_by_serial(self, serial: str) -> Gateway or None:
        """
        :return: * Gateway if device with serial was found in panorama managed devices.
        * None if device with serial not found in panorama managed devices."""
        for _device in self.__managed_devices:
            if _device.serial == serial:
                return _device

        return None

    def get_devices_in_descendant_groups(self, device_group_name: str) -> typing.List[Gateway]:
        _all_dgs_hierarchy = self.device_groups_hierarchy_xml
        _all_dgs = _all_dgs_hierarchy.findall(f".//dg[@name='{device_group_name}']//dg")
        _all_devices = []

        for _dg in _all_dgs:
            _all_devices += self.get_devices_in_group(_dg.get('name'))

        return _all_devices

    def get_devices_in_group(self, device_group_name: str) -> typing.List[Gateway]:
        """Raise exception if 'load_managed_devices=False'"""
        if not self.__should_load_managed_devices:
            raise PaloAltoException(
                "You must set 'load_managed_devices=True' at Panorama instantiating to use this method!")

        for _device_group in self.__device_groups_info:
            if _device_group.device_group_name == device_group_name:
                return [x.gateway for x in _device_group.targets]

        raise PaloAltoException(f"Device group with name {device_group_name} not present!")

    def get_device_group(self, device_group_name: str) -> PanoramaDeviceGroup:
        for _device_group in self.__device_groups_info:
            if _device_group.device_group_name == device_group_name:
                return _device_group

        raise PaloAltoException(f"Device group with name {device_group_name} not present!")
