import copy
import json
from enum import Enum
from abc import ABC
from pypaloalto_api import utils
from pypaloalto_api.enums import YesNo
import xml.etree.ElementTree as ET
from pypaloalto_api import dicttoxml


class CompositeType(ABC):
    pass


class ProfileSettings:
    pass


class NoneProfileSettings(ProfileSettings):
    pass


class Profiles(ProfileSettings):
    pass


class Groups(ProfileSettings):
    pass


class NoneTargetDeviceEntry:
    pass


class TargetDeviceEntry(CompositeType):

    def __init__(self, device_serial: str, vsys_names: list = None):
        self._serial = device_serial
        self._vsys_names = vsys_names
        self._dict = {'@name': self._serial}

        if self._vsys_names:
            self._dict['vsys'] = {'entry': []}
            _entry = self._dict['vsys']['entry']

            for _v in self._vsys_names:
                _entry.append({'@name': _v})

    def to_dict(self):
        return self._dict

    def __repr__(self):
        return self.to_dict()

    def __str__(self):
        return json.dumps(self.to_dict(), indent=2)


# class TargetDeviceEntry:
#    def __init__(self, device_serial: str, vsys_name=''):
#        self.serial = device_serial
#        self.vsys = vsys_name
#
#    def to_dict(self):
#        _dict = {
#            '@name': self.serial
#        }
#
#        if self.vsys:
#            _dict['vsys'] = {'entry': [{'@name': self.vsys}]}
#
#        return _dict
#
#    def __repr__(self):
#        return self.to_dict()
#
#    def __str__(self):
#        return json.dumps(self.to_dict(), indent=2)


class RuleAction(Enum):
    allow = 'allow'
    deny = 'deny'
    drop = 'drop'
    reset_client = 'reset-client'
    reset_server = 'reset-server'
    reset_both = 'reset-both'


class RuleKey(Enum):
    from_zone_list = 'from/member'
    to_zone_list = 'to/member'
    source_list = 'source/member'
    source_user_list = 'source-user/member'
    destination_list = 'destination/member'
    service_list = 'service/member'
    application_list = 'application/member'
    disabled = 'disabled'
    action = 'action'
    tag_root = 'tag'
    tag_list = 'tag/member'
    group_tag = 'group-tag'
    schedule = 'schedule'
    description = 'description'
    log_setting = 'log-setting'
    profile_setting = 'profile-setting'
    profile_setting_profiles = 'profile-setting/profiles'
    profile_setting_profiles_file_blocking = 'profile-setting/profiles/file-blocking'
    profile_setting_profiles_virus = 'profile-setting/profiles/virus'
    profile_setting_profiles_spyware = 'profile-setting/profiles/spyware'
    profile_setting_profiles_vulnerability = 'profile-setting/profiles/vulnerability'
    profile_setting_profiles_wildfire_analysis = 'profile-setting/profiles/wildfire-analysis'
    profile_setting_profiles_url_filtering = 'profile-setting/profiles/url-filtering'
    profile_setting_profiles_data_filtering = 'profile-setting/profiles/data-filtering'
    profile_setting_group = 'profile-setting/group/member'
    negate_destination = 'negate-destination'
    negate_source = 'negate-source'
    rule_name = '@name'
    log_start = 'log-start'
    log_end = 'log-end'
    target_tags = 'target/tags'
    target_tags_list = 'target/tags/member'
    target_devices = 'target/devices'
    target_devices_list = 'target/devices/entry'
    target_negate = 'target/negate'


DEFAULT_VALUES_BY_KEY = {
    RuleKey.from_zone_list: ['any'],
    RuleKey.to_zone_list: ['any'],
    RuleKey.source_list: ['any'],
    RuleKey.source_user_list: ['any'],
    RuleKey.destination_list: ['any'],
    RuleKey.service_list: ['any'],
    RuleKey.application_list: ['any'],
    RuleKey.disabled: YesNo.no,
    RuleKey.negate_destination: YesNo.no,
    RuleKey.negate_source: YesNo.no,
    RuleKey.log_start: YesNo.no,
    RuleKey.log_end: YesNo.yes,
    RuleKey.action: RuleAction.allow,
    RuleKey.tag_root: {},
    RuleKey.tag_list: [],
    RuleKey.group_tag: '',
    RuleKey.schedule: '',
    RuleKey.description: '',
    RuleKey.log_setting: '',
    RuleKey.target_tags_list: [],
    RuleKey.target_devices_list: [],
    RuleKey.target_negate: YesNo.no,
    RuleKey.profile_setting: {},
    RuleKey.profile_setting_group: [],
    RuleKey.profile_setting_profiles_file_blocking: [],
    RuleKey.profile_setting_profiles_virus: [],
    RuleKey.profile_setting_profiles_spyware: [],
    RuleKey.profile_setting_profiles_vulnerability: [],
    RuleKey.profile_setting_profiles_wildfire_analysis: [],
    RuleKey.profile_setting_profiles_url_filtering: [],
    RuleKey.profile_setting_profiles_data_filtering: []
}

NONE_CLASSES = (NoneProfileSettings, NoneTargetDeviceEntry)


class SecurityRule:
    __is_modified = False

    def __init__(self, rule):
        rule = copy.deepcopy(rule)

        if isinstance(rule, dict):
            self.__uuid = rule.pop('@uuid', None)
            self.__real_location = rule.pop('@loc', None)
            self.__rule = rule
        elif isinstance(rule, ET.Element):
            if rule.tag == 'entry':
                _entry = rule
            else:
                _entry = rule.find('.//entry')

            _rule_name = _entry.get('name')

            target_node = _entry.find('.//target')

            if target_node:
                _entry.remove(target_node)

            self.__rule = parse_paloalto_xml_to_json(_entry, list_element_tags=['member', 'entry'])

            if target_node:
                self._set_target_xml_to_rule_json(target_node)

            print('test', self.__rule)
            self.__rule['@name'] = _rule_name
        else:
            raise TypeError(
                f"This class supports initializing only from dict and xml-element types! {type(rule)} was given")

    @property
    def real_location(self) -> str or None:
        return self.__real_location

    @property
    def is_modified(self) -> bool:
        return self.__is_modified

    @property
    def name(self):
        return self.__rule['@name']

    @property
    def device_group(self):
        return self.__rule['@device-group'] if self.__rule["@location"] == 'device-group' else 'shared'

    def _has_key(self, key: RuleKey):
        _key_chain = key.value.split('/')
        _value = self.__rule

        for _i in _key_chain:
            if _i in _value:
                _value = _value[_i]
            else:
                return False

        return True

    def get_value(self, key: RuleKey):
        _key_chain = key.value.split('/')
        _value = self.__rule

        for _i in _key_chain:
            if _i in _value:
                _value = _value[_i]
            else:
                return DEFAULT_VALUES_BY_KEY[key]

        return _value

    def append_value(self, key: RuleKey, addition_value: list):
        if not isinstance(DEFAULT_VALUES_BY_KEY[key], list):
            raise TypeError("Only list value can be extended")

        _key_chain = key.value.split('/')
        _target_key = _key_chain[len(_key_chain) - 1]
        _json = self.__rule

        for _i in _key_chain:
            if _i in _json:
                _json = _json[_i]
            else:
                break

        if len(addition_value) != 0:
            _new_value = list(set(self.get_value(key) + addition_value))
            self.try_set_value_if_diff(key, _new_value)

    def try_delete_key(self, key: RuleKey):
        _key_chain = key.value.split('/')
        _last_key = _key_chain[-1]
        _json = self.__rule

        for _k in _key_chain:
            if _k in _json:
                if _k != _last_key:
                    _json = _json[_k]
            else:
                return False

        _json.pop(_last_key)
        self.__is_modified = True
        return False

    def try_set_default_value(self, key: RuleKey):
        if key not in DEFAULT_VALUES_BY_KEY:
            raise Exception(f'No default value for key {key}')

        return self.try_set_value_if_diff(key, DEFAULT_VALUES_BY_KEY[key])

    def try_set_value_if_diff(self, key: RuleKey, value):
        if value is None:
            raise Exception('Value cannot be None!')

        # Returns None if key was deleted
        value = self.__prepare_value_to_set(key, value)

        if value:
            _is_settled = self.__set_value_if_diff(key, value)

            if _is_settled:
                if RuleKey.profile_setting_group.value in key.value:
                    self.try_delete_key(RuleKey.profile_setting_profiles)

                elif RuleKey.profile_setting_profiles.value in key.value:
                    self.try_delete_key(RuleKey.profile_setting_group)

                # elif RuleKey.target_tags.value in key.value:
                #    self.try_delete_key(RuleKey.target_devices)
            #
            # elif RuleKey.target_devices.value in key.value:
            #    self.try_delete_key(RuleKey.target_tags)

            return _is_settled
        else:
            return True

    def __prepare_value_to_set(self, key: RuleKey, value):
        """Returns None if key was deleted"""

        if key == RuleKey.rule_name:
            raise Exception("Rule name can't be settled!")

        if issubclass(type(value), Enum):
            value = value.value

        elif isinstance(value, list):
            if value == list():
                if key == RuleKey.tag_list:
                    self.try_delete_key(RuleKey.tag_root)
                    return None
                else:
                    # value = ['any']
                    value = []

            else:
                if value != ['any'] and 'any' in value:
                    value.remove('any')

                if isinstance(value[0], TargetDeviceEntry):
                    _new_value = []

                    for _v in value:
                        _new_value.append(_v.get_json())

                    value = _new_value

        elif issubclass(value.__class__, CompositeType):
            value = value.get_json()

        return value

    def __set_value_if_diff(self, rule_key: RuleKey, value):
        _key_chain = rule_key.value.split('/')
        _last_key = _key_chain[-1]
        _json = self.__rule

        for _key in _key_chain:
            # Если ключ является последним в цепочки искомых ключей, то пытаемся присвоить ему пользовательское значение
            if _key == _last_key:
                if _key not in _json:
                    _json[_key] = value
                    self.__is_modified = True

                elif isinstance(value, list):
                    if set(_json[_key]) != set(value):
                        _json[_key] = value
                        self.__is_modified = True

                elif _json[_key] != value:
                    _json[_key] = value
                    self.__is_modified = True

                return True

            # Если ключ есть в джейсоне, то получаем его значение для последующих итераций
            elif _key in _json:
                _json = _json[_key]

            # Если какого-то промежуточного ключа нет в json, То добавляем всю последовательность ключей после него.
            else:
                _index_of_current_key = _key_chain.index(_key)
                _missed_keys = _key_chain[_index_of_current_key::]
                _count = 0

                while _count < len(_missed_keys) - 1:
                    _json[_missed_keys[_count]] = {_missed_keys[_count + 1]: None}
                    _json = _json[_missed_keys[_count]]
                    _count += 1

                _json[_missed_keys[_count]] = value
                self.__is_modified = True
                return True

        return False

    def clear_is_modified_flag(self):
        self.__is_modified = False

    def to_dict(self) -> dict:
        _rule = copy.deepcopy(self.__rule)
        return _rule

    def to_entry_dict(self) -> dict:
        return {'entry': [self.to_dict()]}

    def to_json(self, indent=2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def to_xml(self) -> ET.Element:
        _temp_dict = self.to_dict()

        _temp_dict.pop('@device-group', '')
        _rule_name = _temp_dict['@name']
        _temp_dict.pop('@name', '')
        _temp_dict.pop('@location', '')
        target_json = {}

        if 'target' in _temp_dict:
            target_json = _temp_dict['target']
            del _temp_dict['target']

        _temp_dict = utils.remove_key_from_dict_recursively(_temp_dict, 'member')
        _xml = dicttoxml.dicttoxml(_temp_dict, attr_type=False, custom_root='entry', item_func=lambda x: 'member')
        _xml = ET.fromstring(_xml)
        _xml.set('name', _rule_name)

        if target_json:
            _set_target_json_to_rule_xml(target_json, _xml)

        return _xml

    def _set_target_xml_to_rule_json(self, target_node: ET.Element):
        negate_node = target_node.find('negate')
        devices_node = target_node.find('devices')
        tags_node = target_node.find('tags')

        self.try_set_value_if_diff(RuleKey.target_negate, negate_node.text)

        if devices_node:
            devices_list = []

            for entry in devices_node.findall('entry'):
                device_json = {'@name': entry.get('name')}

                if entry.find('vsys'):
                    vsys_entries = []

                    for vsys_entry in entry.findall('vsys/entry'):
                        vsys_entries.append({'@name': vsys_entry.get('name')})

                    device_json['vsys'] = {'entry': vsys_entries}

                devices_list.append(device_json)

            self.try_set_value_if_diff(RuleKey.target_devices_list, devices_list)

        # else:
        #    self.try_set_default_value(RuleKey.target_devices_list)

        if tags_node:
            tags_json = parse_paloalto_xml_to_json(tags_node, list_element_tags=['member'])
            self.try_set_value_if_diff(RuleKey.target_tags, tags_json)

        # else:
        #    self.try_set_default_value(RuleKey.target_tags_list)

    def __repr__(self):
        return str(self.__rule)


class SecurityRuleBuilder:
    @staticmethod
    def create_security_rules_list(rules) -> list:
        """Takes json or xml reply from PaloAlto device
        Returns list of SecurityRules"""
        _rules_list = []

        if isinstance(rules, list):
            pass

        elif isinstance(rules, ET.Element):
            rules = rules.findall('.//entry')

        else:
            raise TypeError("This class supports initializing only from dict and xml-element types!")

        for _rule in rules:
            _rules_list.append(SecurityRule(_rule))

        return _rules_list

    @staticmethod
    def security_rule_from_json(json_string: str):
        """Takes json as string
        Return an instance SecurityRule"""

        return SecurityRule(json.loads(json_string))

    @staticmethod
    def security_rule_from_dict(rule_as_dict: dict):
        """Takes a dict object
        Return an instance SecurityRule"""

        return SecurityRule(rule_as_dict)

    @staticmethod
    def security_rule_from_xml(rule_as_xml: ET.Element):
        """Takes a XML-Element object
        Return an instance SecurityRule"""

        return SecurityRule(rule_as_xml)

    @staticmethod
    def security_rule_from_arguments(rule_key_value_pairs: dict):
        """Takes dict like {RuleKeys.rule_name: 'test_name', RuleKeys.....}
        Return an instance SecurityRule"""

        if RuleKey.rule_name not in rule_key_value_pairs:
            raise Exception('RuleKeys.name must be in rule_key_value dict!')

        _security_rule = SecurityRule({'@name': rule_key_value_pairs.pop(RuleKey.rule_name)})

        for _key in RuleKey:
            if _key in rule_key_value_pairs:
                _value = rule_key_value_pairs[_key]

                if _key in DEFAULT_VALUES_BY_KEY:
                    expected_value_type = type(DEFAULT_VALUES_BY_KEY[_key])

                    if not isinstance(_value, expected_value_type):
                        raise Exception(f'Invalid value type for key {_key}.'
                                        f' Expected {expected_value_type}, got {type(_value)}')

                _security_rule.try_set_value_if_diff(_key, _value)

            elif _key in DEFAULT_VALUES_BY_KEY:
                _security_rule.try_set_value_if_diff(_key, DEFAULT_VALUES_BY_KEY[_key])

        _all_keys_as_string = ','.join([x.value for x in rule_key_value_pairs])

        if RuleKey.profile_setting_group.value in _all_keys_as_string:
            _security_rule.try_delete_key(RuleKey.profile_setting_profiles)

        elif RuleKey.profile_setting_profiles.value in _all_keys_as_string:
            _security_rule.try_delete_key(RuleKey.profile_setting_group)

        return _security_rule


def parse_paloalto_xml_to_json(xml: ET.Element, list_element_tags=[], empty_value=''):
    _result = {}

    for child in list(xml):
        if len(list(child)) > 0:
            _result[child.tag] = parse_paloalto_xml_to_json(child, list_element_tags, empty_value)
        else:
            if child.tag in list_element_tags:
                if child.tag in _result:
                    _result[child.tag].append(child.text or empty_value)
                else:
                    _result[child.tag] = [child.text] if child.text else [empty_value]
            else:
                if child.text:
                    _result[child.tag] = child.text

                else:
                    _result[child.tag] = empty_value

    return _result


def _set_target_json_to_rule_xml(target_json: dict, rule_xml: ET.Element):
    if 'devices' in target_json or 'tags' in target_json:
        target_root_element = ET.SubElement(rule_xml, 'target')
        negate_element = ET.SubElement(target_root_element, 'negate')

        if 'negate' in target_json:
            negate_element.text = target_json['negate']
        else:
            negate_element.text = target_json.get('negate', DEFAULT_VALUES_BY_KEY[RuleKey.target_negate].value)

        if 'devices' in target_json and target_json['devices'].get('entry', ['any']) != ['any']:
            devices_root_element = ET.SubElement(target_root_element, 'devices')

            for entry in target_json['devices'].get('entry', []):
                device_entry_element = ET.SubElement(devices_root_element, 'entry', {'name': entry['@name']})

                if 'vsys' in entry:
                    vsys_element = ET.SubElement(device_entry_element, 'vsys')

                    for vsys_entry in entry['vsys'].get('entry', []):
                        ET.SubElement(vsys_element, 'entry', {'name': vsys_entry['@name']})

        if 'tags' in target_json and target_json['tags'].get('member', ['any']) != ['any']:
            tags_root_element = ET.SubElement(target_root_element, 'tags')

            for tag in target_json['tags']['member']:
                tag_member_elements = ET.SubElement(tags_root_element, 'member')
                tag_member_elements.text = tag
