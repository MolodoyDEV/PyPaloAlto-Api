import copy
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Dict, Set

from requests.auth import HTTPBasicAuth, AuthBase
from pypaloalto_api.configuration_commands import XmlApiConfigAction, ConfigAction, XmlApiRequestType, CCXPathBuilder
from pypaloalto_api.enums import HaPeerState
import json
import time
import xml.etree.ElementTree as ET
import requests
import urllib3
from pypaloalto_api.enums import HttpRequestMethod
from pypaloalto_api import settings, logger
from pypaloalto_api.exceptions import PaloAltoApiRequestException, PaloAltoException, ReplyParsingException, \
    EmptyReplyException
from pypaloalto_api.operational_commands import OPCmdBuilder
from pypaloalto_api.utils import ApiKeyAuth, custom_deepcopy

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class VsysInfo:
    def __init__(self, vsys_name: str, vsys_display_name: str, panorama_tags: List[str]):
        self._vsys_name = vsys_name
        self._vsys_display_name = vsys_display_name
        self._panorama_tags = panorama_tags

    @property
    def vsys_name(self) -> str:
        return self._vsys_name

    @property
    def vsys_display_name(self) -> str:
        return self._vsys_display_name

    @property
    def panorama_tags(self) -> List[str]:
        return copy.copy(self._panorama_tags)

    def __repr__(self):
        return json.dumps({
            'vsys_name': self.vsys_name,
            'vsys_display_name': self.vsys_display_name,
            'panorama_tags': self.panorama_tags,
        }, indent=2)


class PaloAltoDevice(ABC):
    _restapi_version: str
    _ipv4: str
    _primary_ip: str
    _exception_on_request_error: bool = True
    request_delay_seconds: float = 1
    _cached_ha_peer_state: HaPeerState
    _self_config_file: str or Path or dict
    _device_name: str = 'unknown'
    _hostname: str = 'unknown'
    _serial: str = 'unknown'

    def _read_config(self):
        if isinstance(self._self_config_file, dict):
            return copy.deepcopy(self._self_config_file)
        else:
            return settings.get_config_from_yaml_file(self._self_config_file)

    @abstractmethod
    def __init__(self):
        raise Exception("You can't instantiate an abstract class!")

    @property
    def device_name(self) -> str:
        return self._device_name

    @property
    def hostname(self) -> str:
        return self._hostname

    @property
    def serial(self) -> str:
        return self._serial

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

    def __get_auth(self) -> AuthBase:
        _config = self._read_config()
        api_key = _config.get('ApiKey')

        if api_key:
            return ApiKeyAuth(api_key)
        else:
            login = _config.get('Login')
            password = _config.get('Password')

            if login and password:
                return HTTPBasicAuth(login, password)
            else:
                raise Exception('Config must contains ApiKey or Login and Password!')

    def update_and_get_ha_peer_state(self):
        _ha_info, _status_code = self.xml_api_operational_request(OPCmdBuilder.show_ha_state())

        if _ha_info.find('result/enabled').text == 'yes':
            state_node = _ha_info.find('result/local-info/state')

            if state_node is None:
                state_node = _ha_info.find('result/group/local-info/state')

            self._cached_ha_peer_state = HaPeerState(state_node.text)
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
                raise PaloAltoApiRequestException(self.device_name, _response.status_code, _response.content.decode(),
                                                  'bad status code')
            else:
                return _response.content.decode()

        else:
            return ET.fromstring(_response.content).find('result/key').text

    def restapi_request(self, route: str, request_method: HttpRequestMethod,
                        data: dict or str = None, params: dict = None, ssl_verify=False,
                        request_timeout_seconds: int = None) -> (str, int):
        """With delay"""
        if isinstance(data, dict):
            data = json.dumps(data)

        time.sleep(self.request_delay_seconds)
        _url = f'https://{self._primary_ip}/restapi/v{self._restapi_version}/{route}'
        reply, status_code = self.http_request(request_method, _url, data, params, ssl_verify, request_timeout_seconds)

        try:
            reply_json = json.loads(reply)
        except Exception as e:
            if reply:
                raise ReplyParsingException(self.device_name, status_code, reply,
                                            f'Failed convert response to JSON: {e}')
            else:
                raise EmptyReplyException(self.device_name, status_code)

        reply_msg = reply_json.get('msg')

        if reply_msg:
            if 'error' in reply_msg or 'invalid' in reply_msg or 'unauth' in reply_msg:
                if self._exception_on_request_error:
                    raise PaloAltoApiRequestException(self.device_name, status_code, reply, 'status is error')

                else:
                    logger.error(f'[{self.device_name}]:{reply} {status_code}')

        return reply, status_code

    def http_request(self, request_method: HttpRequestMethod, url: str,
                     data: dict or str or None = None, params: dict = None, ssl_verify=False,
                     timeout_seconds: int = None) -> (str, int):
        config_lock_max_repeats_count = 4
        config_lock_wait_seconds = 30
        config_lock_repeats_count = 0

        while True:
            _response = requests.request(request_method.value, url, auth=self.__get_auth(), verify=ssl_verify,
                                         data=data, params=params, timeout=timeout_seconds)

            try:
                _response_content = _response.content.decode()
            except ValueError:
                _response_content = _response.content

            if _response.status_code != 200:
                if 'Timed out while getting config lock. Please try again.' in _response_content:
                    logger.warning(
                        f'[{self.device_name}]:Timed out while getting config lock. Retrying after {config_lock_wait_seconds} seconds..'
                    )
                    time.sleep(config_lock_wait_seconds)
                    config_lock_repeats_count += 1

                    if config_lock_repeats_count >= config_lock_max_repeats_count:
                        raise PaloAltoApiRequestException(self.device_name, _response.status_code, _response_content,
                                                          'bad status code')

                    continue

                elif self._exception_on_request_error:
                    raise PaloAltoApiRequestException(self.device_name, _response.status_code, _response_content,
                                                      'bad status code')

                else:
                    logger.error(f'[{self.device_name}]:{_response.content} {_response.status_code}')

            return _response_content, _response.status_code

    def xml_api_request(self, request_data: dict, params: dict = None, ssl_verify=False,
                        request_timeout_seconds: int = None) -> (str, int):
        _url = f'https://{self._ipv4}/api/'
        time.sleep(self.request_delay_seconds)
        content, status_code = self.http_request(HttpRequestMethod.post,
                                                 _url,
                                                 request_data,
                                                 params,
                                                 ssl_verify,
                                                 request_timeout_seconds)

        try:
            content_xml = ET.fromstring(content)
        except Exception as e:
            if content:
                raise ReplyParsingException(self.device_name, status_code, content,
                                            f'Failed convert response to XML: {e}')
            else:
                raise EmptyReplyException(self.device_name, status_code)

        if content_xml.get('status') in ['error', 'unauth']:
            if self._exception_on_request_error:
                raise PaloAltoApiRequestException(self.device_name, status_code, content,
                                                  'status is error')

            else:
                logger.error(f'[{self.device_name}]:{content} {status_code}')

        return content_xml, status_code

    def xml_api_export_request(self, params: dict, ssl_verify=False, request_timeout_seconds: int = None):
        _url = f'https://{self._ipv4}/api/'
        params['type'] = XmlApiRequestType.export_files.value

        content, status_code = self.http_request(HttpRequestMethod.get, _url, params=params, ssl_verify=ssl_verify,
                                                 timeout_seconds=request_timeout_seconds)

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
                            raise PaloAltoApiRequestException(self.device_name, status_code, content, error_msg)

        return content, status_code

    def xml_api_operational_request(self, cmd: str, params: dict = None, ssl_verify=False,
                                    request_timeout_seconds: int = None, **additional_request_data):
        return self.xml_api_cmd_request(XmlApiRequestType.op, cmd, params, ssl_verify,
                                        request_timeout_seconds, **additional_request_data)

    def xml_api_cmd_request(self, request_type: XmlApiRequestType, cmd: str, params: dict = None, ssl_verify=False,
                            request_timeout_seconds: int = None, **additional_request_data):
        _request_data = {
            'type': request_type.value,
            'cmd': cmd
        }

        _request_data.update(additional_request_data)

        return self.xml_api_request(_request_data, params, ssl_verify, request_timeout_seconds)

    def xml_api_config_request(self, action: XmlApiConfigAction or ConfigAction, xpath: str,
                               elements: List[ET.Element] = None, params: dict = None, ssl_verify=False,
                               request_timeout_seconds: int = None):
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

        return self.xml_api_request(_request_data, params, ssl_verify, request_timeout_seconds)


class Gateway(PaloAltoDevice):

    def __init__(self, ipv4: str, config_file: str or Path or dict, exception_on_request_error=True,
                 init_requests_timeout_seconds=120):
        """
Config file structure:

ApiKey: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX==
    or
Login: admin
Password: password

ApiVersion: 10.0
RequestsDelaySeconds: 1
"""

        self._self_config_file = config_file
        _device_config = self._read_config()

        self._exception_on_request_error = True
        self._ipv4 = ipv4
        self._primary_ip = self._ipv4
        self._restapi_version = _device_config['ApiVersion']
        self.request_delay_seconds = _device_config['RequestsDelaySeconds']

        _system_info = self.xml_api_operational_request(OPCmdBuilder.show_system_info(),
                                                        request_timeout_seconds=init_requests_timeout_seconds)[0]
        self._is_multi_vsys = True if _system_info.find('result/system/multi-vsys').text == 'on' else False
        self._device_name = _system_info.find('result/system/hostname').text
        self._serial = _system_info.find('result/system/serial').text
        self._cached_ha_peer_state = self.update_and_get_ha_peer_state()
        self._vsys_display_name_by_vsys_name = {}
        self._vsys_info = []
        self._exception_on_request_error = exception_on_request_error

    @property
    def vsys_display_name_by_vsys_name(self) -> dict:
        if not self._vsys_display_name_by_vsys_name:
            self._init_vsys_info()

        return copy.copy(self._vsys_display_name_by_vsys_name)

    @property
    def vsys_info(self) -> List[VsysInfo]:
        if not self._vsys_info:
            self._init_vsys_info()

        return copy.deepcopy(self._vsys_info)

    @property
    def is_multi_vsys(self):
        return self._is_multi_vsys

    def _init_vsys_info(self):
        _temp_vsys_list = self.restapi_request('Device/VirtualSystems', HttpRequestMethod.get)[0]
        _temp_vsys_list = json.loads(_temp_vsys_list)['result']['entry']

        for _vsys in _temp_vsys_list:
            _display_name = _vsys['display-name']

            if isinstance(_display_name, dict):
                _display_name = _display_name['text']

            self._vsys_display_name_by_vsys_name[_vsys['@name']] = _display_name
            self._vsys_info.append(
                VsysInfo(_vsys['@name'], _display_name, [])
            )


class _ManagedDevice(Gateway):
    """Panorama managed device. Gateway version for instantiating by panorama from panorama config."""

    def __init__(self, ipv4: str, serial: str, device_name: str, ha_state: HaPeerState,
                 config_file: str or Path or dict, exception_on_request_error: bool,
                 vsys_info: List[VsysInfo], is_multi_vsys: bool):

        self._self_config_file = config_file
        _device_config = self._read_config()

        self._ipv4 = ipv4
        self._primary_ip = self._ipv4
        self._restapi_version = _device_config['ApiVersion']

        api_key = _device_config.get('ApiKey')

        if api_key:
            self.__auth = ApiKeyAuth(api_key)
        else:
            login = _device_config.get('Login')
            password = _device_config.get('Password')

            if login and password:
                self.__auth = HTTPBasicAuth(login, password)
            else:
                raise Exception('Config must contains ApiKey or Login and Password!')

        self.request_delay_seconds = _device_config['RequestsDelaySeconds']
        self._cached_ha_peer_state = ha_state
        self._device_name = device_name
        self._serial = serial
        self._vsys_info = vsys_info
        self._vsys_display_name_by_vsys_name = {x.vsys_name: x.vsys_display_name for x in vsys_info}
        self._exception_on_request_error = exception_on_request_error
        self._is_multi_vsys = is_multi_vsys


class DeviceGroupTarget:
    """Panorama Device Group target info"""

    def __init__(self, device_name: str, vsys_name: Optional[str], gateway: Gateway):
        self._device_name = device_name
        self._vsys_name = vsys_name
        self._gateway = gateway

    @property
    def device_name(self) -> str:
        return self._device_name

    @property
    def vsys_name(self) -> Optional[str]:
        return self._vsys_name

    @property
    def gateway(self) -> Gateway:
        return self._gateway

    def __repr__(self):
        return json.dumps({
            'device_name': self._device_name,
            'vsys_name': self._vsys_name,
            'gateway': self._gateway.__repr__(),
        }, indent=2)


class PanoramaDeviceGroup:
    def __init__(self, device_group_name: str, targets: List[DeviceGroupTarget]):
        self._device_group_name = device_group_name
        self._targets = []

        for target in targets:
            if target.vsys_name and target.vsys_name not in target.gateway.vsys_display_name_by_vsys_name.keys():
                logger.warning(
                    f'Vsys name "{target.vsys_name}" not found on device "{target.device_name}"'
                    f' but it associated with device group "{self._device_group_name}"!'
                )
                continue

            self._targets.append(target)

    @property
    def device_group_name(self):
        return self._device_group_name

    @property
    def targets(self):
        return custom_deepcopy(self._targets)

    def __repr__(self):
        return json.dumps({
            'device_group_name': self._device_group_name,
            'targets': [x.__repr__() for x in self._targets],
        }, indent=2)


class Panorama(PaloAltoDevice):
    def __init__(self, panorama_config_file: str or Path or dict, device_config_file: str or Path or dict = '',
                 exception_on_request_error=True, load_managed_devices=True, init_requests_timeout_seconds=120):
        """Config file structure:

ApiKey: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX==
    or
Login: admin
Password: password

ApiVersion: 10.1
IPv4: 10.10.10.10
RequestsDelaySeconds: 1
"""
        self._self_config_file = panorama_config_file
        _panorama_config = self._read_config()

        api_key = _panorama_config.get('ApiKey')

        if api_key:
            self.__auth = ApiKeyAuth(api_key)
        else:
            login = _panorama_config.get('Login')
            password = _panorama_config.get('Password')

            if login and password:
                self.__auth = HTTPBasicAuth(login, password)
            else:
                raise Exception('Config must contains ApiKey or Login and Password!')

        self.api_key = _panorama_config['ApiKey']
        self._restapi_version = _panorama_config['ApiVersion']
        self._ipv4 = _panorama_config['IPv4']
        self._primary_ip = self._ipv4
        self.request_delay_seconds = float(_panorama_config['RequestsDelaySeconds'])
        self._managed_devices: List[_ManagedDevice] = []
        self.__device_groups_info: List[PanoramaDeviceGroup] = []
        self._exception_on_request_error = True
        self._device_config_file = device_config_file
        self.__device_groups_names: List[str] = []
        self.__device_groups_hierarchy_xml = None
        self.__should_load_managed_devices = load_managed_devices
        self._cached_ha_peer_state = self.update_and_get_ha_peer_state()

        _system_info = self.xml_api_operational_request(OPCmdBuilder.show_system_info(),
                                                        request_timeout_seconds=init_requests_timeout_seconds)[0]
        _system_info = _system_info.find('result/system')
        self._hostname = _system_info.find('hostname').text
        self._device_name = _system_info.find('devicename').text
        self._serial = _system_info.find('serial').text

        self.try_update_managed_devices()
        self.update_device_groups()
        self._exception_on_request_error = exception_on_request_error

    def __create_device_group_hierarchy_dict(self, _hierarchy_xml) -> Dict[str, List[dict]]:
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
        _all_dg_hierarchy_xml = self.xml_api_operational_request(OPCmdBuilder.show_dg_hierarchy())[0].find(
            './/dg-hierarchy')
        _all_dg_names = _all_dg_hierarchy_xml.findall('.//dg')
        self.__device_groups_names = [x.get('name') for x in _all_dg_names]
        self.__device_groups_hierarchy_xml = _all_dg_hierarchy_xml
        self.__device_groups_info = []

        _cmd = OPCmdBuilder.show_devicegroups()
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
                                        DeviceGroupTarget(_device.device_name, _vsys.get('name'), _device)
                                    )
                            else:
                                _device_group_targets.append(
                                    DeviceGroupTarget(_device.device_name, None, _device)
                                )
                        else:
                            logger.warning(
                                f'[{self.device_name}]:Device with serial {_serial.text} configured on panorama in device group {_device_group.get("name")} but it status is "not connected"! Can\'t load this device.')
                            # raise Exception(
                            #    f'Panorama class desync error. Device with serial {_serial.text} not in panorama managed devices list!')

            self.__device_groups_info.append(
                PanoramaDeviceGroup(_device_group.get('name'), _device_group_targets)
            )

    def try_update_managed_devices(self):
        if self.__should_load_managed_devices:
            self.__load_managed_devices(self._device_config_file)
        else:
            logger.warning(
                f'[{self.device_name}]:panorama should_load_managed_devices is False! Managed devices not loaded.')

    @property
    def device_groups_hierarchy_dict(self) -> Dict[str, List[dict]]:
        return self.__create_device_group_hierarchy_dict(self.__device_groups_hierarchy_xml)

    @property
    def device_groups_hierarchy_xml(self) -> ET.Element:
        return copy.copy(self.__device_groups_hierarchy_xml)

    @property
    def device_groups_names(self) -> List[str]:
        return copy.copy(self.__device_groups_names)

    @property
    def managed_devices(self) -> List[Gateway]:
        """Raise exception if 'load_managed_devices=False'"""
        if not self.__should_load_managed_devices:
            raise PaloAltoException(
                "You must set 'should_load_managed_devices=True' at Panorama instantiating to use this method!",
                self.device_name
            )

        return copy.deepcopy(self._managed_devices)

    def __load_managed_devices(self, device_config_file: str or Path or dict):
        if not device_config_file:
            raise PaloAltoException(
                "You trying to load managed devices from panorama but device config file not specified!",
                self.device_name
            )

        self._managed_devices = []
        _cmd = OPCmdBuilder.show_devices_connected()
        _connected_devices_info, _status_code = self.xml_api_operational_request(_cmd)
        _xpath = CCXPathBuilder.config_managed_devices()
        _mgmt_devices_info, _status_code = self.xml_api_config_request(ConfigAction.get, _xpath)

        for _device_info in _connected_devices_info.findall('result/devices/entry'):
            _device_vsys_info = []
            _device_serial = _device_info.find('serial').text

            for _vsys in _device_info.findall('.//vsys/entry'):
                _vsys_name = _vsys.get('name')
                _panorama_tags = _mgmt_devices_info.findall(
                    f'result/entry[@name="{_device_serial}"]/vsys/entry[@name="{_vsys_name}"]/tags/member'
                )

                if _panorama_tags is None:
                    _panorama_tags = []
                else:
                    _panorama_tags = [x.text for x in _panorama_tags]

                _device_vsys_info.append(
                    VsysInfo(_vsys_name, _vsys.find('display-name').text, _panorama_tags)
                )

            _device = _ManagedDevice(
                _device_info.find('ip-address').text,
                _device_serial,
                _device_info.find('hostname').text,
                HaPeerState.ha_not_enabled if not _device_info.find('ha') else HaPeerState(
                    _device_info.find('ha/state').text),
                device_config_file,
                self._exception_on_request_error,
                _device_vsys_info,
                True if _device_info.find('multi-vsys').text == 'yes' else False,
            )

            self._managed_devices.append(_device)

    def get_devices_in_descendant_groups(self, device_group_name: str) -> List[Gateway]:
        _all_dg_names = self.get_descendant_dg_names(device_group_name)
        _all_devices = []

        for _dg_name in _all_dg_names:
            _all_devices += self.get_devices_in_group(_dg_name)

        return _all_devices

    def get_descendant_dg_names(self, device_group_name: str) -> List[str]:
        _all_dgs_hierarchy = self.device_groups_hierarchy_xml
        _all_dgs = _all_dgs_hierarchy.findall(f".//dg[@name='{device_group_name}']//dg")
        return [x.get('name') for x in _all_dgs]

    def get_devices_in_group(self, device_group_name: str) -> List[Gateway]:
        """Raise exception if 'load_managed_devices=False'"""
        if not self.__should_load_managed_devices:
            raise PaloAltoException(
                "You must set 'load_managed_devices=True' at Panorama instantiating to use this method!",
                self.device_name,
            )

        for _device_group in self.__device_groups_info:
            if _device_group.device_group_name == device_group_name:
                return [x.gateway for x in _device_group.targets]

        raise PaloAltoException(f"Device group with name {device_group_name} not present!", self.device_name)

    def get_device_group(self, device_group_name: str) -> PanoramaDeviceGroup:
        for _device_group in self.__device_groups_info:
            if _device_group.device_group_name == device_group_name:
                return _device_group

        raise PaloAltoException(f"Device group with name {device_group_name} not present!", self.device_name)

    def get_managed_device_by_serial(self, serial: str) -> Gateway or None:
        """
        :return: * Gateway if device with serial was found in panorama managed devices.
        * None if device with serial not found in panorama managed devices."""
        for _device in self._managed_devices:
            if _device.serial == serial:
                return _device

        return None

    def get_managed_device_by_name(self, device_name: str) -> Gateway or None:
        """
        :return: * Gateway if device with name was found in panorama managed devices.
        * None if device with name not found in panorama managed devices."""
        for _device in self.managed_devices:
            if _device.device_name == device_name:
                return _device

        return None

    def get_device_names_with_panorama_tag(self, panorama_tag: str,
                                           mgmt_device_entry_xml: Optional[ET.Element] = None) -> Set[str]:
        if mgmt_device_entry_xml is None:
            mgmt_device_entry_xml, reply_status = self.xml_api_config_request(
                ConfigAction.get, f"/config/mgt-config/devices/entry",
            )
            mgmt_device_entry_xml = mgmt_device_entry_xml.find('result')

        device_serials_with_tag = set()

        for device_entry in mgmt_device_entry_xml:
            device_entry: ET.Element
            device_serial = device_entry.get('name')
            device_vsys_info = device_entry.findall(f".//vsys/entry")

            if device_vsys_info is None:
                if panorama_tag in [x.text for x in device_entry.findall(f".//tags/member")]:
                    device_serials_with_tag.add(device_serial)

                continue

            for vsys_entry in device_vsys_info:
                vsys_entry: ET.Element
                vsys_name = vsys_entry.get('name')

                if panorama_tag in [x.text for x in vsys_entry.findall(f"tags/member")]:
                    device_serials_with_tag.add(f'{device_serial}/{vsys_name}')

        return device_serials_with_tag

    def get_all_panorama_tags_by_device_name(self, mgmt_device_entry_xml: Optional[ET.Element] = None
                                             ) -> Dict[str, List[str]]:

        if mgmt_device_entry_xml is None:
            mgmt_device_entry_xml, reply_status = self.xml_api_config_request(
                ConfigAction.get, f"/config/mgt-config/devices/entry",
            )
            mgmt_device_entry_xml = mgmt_device_entry_xml.find('result')

        panorama_tags_by_device_name = {}

        for device_entry in mgmt_device_entry_xml:
            device_entry: ET.Element
            device_name = device_entry.get('name')
            device_vsys_info = device_entry.findall(f".//vsys/entry")

            if device_vsys_info is None:
                panorama_tags = panorama_tags_by_device_name.setdefault(device_name, [])
                panorama_tags += [x.text for x in device_entry.findall(f".//tags/member")]
                continue

            for vsys_entry in device_vsys_info:
                vsys_entry: ET.Element
                vsys_name = vsys_entry.get('name')
                panorama_tags = panorama_tags_by_device_name.setdefault(f'{device_name}/{vsys_name}', [])
                panorama_tags += [x.text for x in vsys_entry.findall(f"tags/member")]

        return panorama_tags_by_device_name

    def get_panorama_tags_by_device_serial(self, device_serial: str, vsys_name: str = None) -> List[str]:
        reply_xml, reply_status = self.xml_api_config_request(
            ConfigAction.get, f"/config/mgt-config/devices/entry[@name='{device_serial}']",
        )

        if vsys_name:
            tags = [x.text for x in reply_xml.findall(f".//vsys/entry[@name='{vsys_name}']/tags/member")]
        else:
            tags = [x.text for x in reply_xml.findall(f".//tags/member")]

        return tags
