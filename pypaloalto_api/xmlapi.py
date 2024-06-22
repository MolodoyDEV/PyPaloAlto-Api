from enum import Enum
import xml.etree.ElementTree as ET
from typing import Tuple, List

from pypaloalto_api import logger
from pypaloalto_api.enums import Protocol
from pypaloalto_api.utils import deprecated

DEFAULT_VALUES = ['any', 'application-default', 'none']


class PaloAltoObjectType(Enum):
    security_pre_rule = 'security_pre_rule'
    security_post_rule = 'security_post_rule'
    address = 'address'
    address_group = 'address_group'
    service = 'service'
    service_group = 'service_group'
    application = 'application'
    application_group = 'application_group'
    application_filter = 'application_filter'
    schedule = 'schedule'
    log_profile = 'log_profile'
    profile = 'profile'
    group_profile = 'group_profile'
    tag = 'tag'
    region = 'region'
    zone = 'zone'


PALOALTO_OBJECT_GROUP_BY_TYPE = {
    PaloAltoObjectType.address: PaloAltoObjectType.address_group,
    PaloAltoObjectType.service: PaloAltoObjectType.service_group,
    PaloAltoObjectType.application: PaloAltoObjectType.application_group,
    PaloAltoObjectType.profile: PaloAltoObjectType.group_profile,
}

PALOALTO_OBJECT_TYPE_IN_GROUP = {
    PaloAltoObjectType.address_group: PaloAltoObjectType.address,
    PaloAltoObjectType.service_group: PaloAltoObjectType.service,
    PaloAltoObjectType.application_group: PaloAltoObjectType.application,
    PaloAltoObjectType.group_profile: PaloAltoObjectType.profile,
}

XPATH_BY_OBJECT_TYPE = {
    PaloAltoObjectType.security_pre_rule: '/pre-rulebase/security/rules',
    PaloAltoObjectType.security_post_rule: '/post-rulebase/security/rules',
    PaloAltoObjectType.address: '/address',
    PaloAltoObjectType.region: '/region',
    PaloAltoObjectType.address_group: '/address-group',
    PaloAltoObjectType.service: '/service',
    PaloAltoObjectType.service_group: '/service-group',
    PaloAltoObjectType.application: '/application',
    PaloAltoObjectType.application_group: '/application-group',
    PaloAltoObjectType.application_filter: '/application-filter',
    PaloAltoObjectType.schedule: '/schedule',
    PaloAltoObjectType.log_profile: '/log-settings/profiles',
    PaloAltoObjectType.profile: '/profiles',
    PaloAltoObjectType.group_profile: '/profile-group',
    PaloAltoObjectType.tag: '/tag',
}


class XmlApiElementsBuilder:

    @staticmethod
    def __attach_description_xml(description: str, root):
        if description:
            _description_entry = ET.SubElement(root, 'description')
            _description_entry.text = description

    @staticmethod
    def __attach_tags_xml(tags: Tuple[str, ...], root):
        if tags:
            _tags_root = ET.SubElement(root, 'tag')

            for _tag in tags:
                _tag_entry = ET.SubElement(_tags_root, 'member')
                _tag_entry.text = _tag

    @staticmethod
    def create_service_xml(name: str, destination_port: str, protocol: Protocol, source_port='',
                           tags: Tuple[str, ...] = (), description='') -> ET.Element:
        return XmlApiElementsBuilder.__get_service_xml(name, destination_port, protocol, source_port, tags, description)

    @staticmethod
    @deprecated('XmlApiElementsBuilder.create_service_xml')
    def get_service_xml(name: str, destination_port: str, protocol: Protocol, source_port='',
                        tags: Tuple[str, ...] = (), description='') -> ET.Element:
        """Deprecated! Use create_service_xml instead"""
        return XmlApiElementsBuilder.__get_service_xml(name, destination_port, protocol, source_port, tags, description)

    @staticmethod
    def __get_service_xml(name: str, destination_port: str, protocol: Protocol, source_port='',
                          tags: Tuple[str, ...] = (), description='') -> ET.Element:
        _root_element = ET.Element('entry', {'name': name})
        _protocol = ET.SubElement(_root_element, 'protocol')
        _concrete_protocol = ET.SubElement(_protocol, protocol.value)

        _port = ET.SubElement(_concrete_protocol, 'port')
        _port.text = destination_port

        if source_port:
            _source_port = ET.SubElement(_concrete_protocol, 'source-port')
            _source_port.text = source_port

        XmlApiElementsBuilder.__attach_tags_xml(tags, _root_element)
        XmlApiElementsBuilder.__attach_description_xml(description, _root_element)

        return _root_element

    @staticmethod
    def create_ip_address_xml(name: str, ip_netmask: str, tags: Tuple[str, ...] = (), description='') -> ET.Element:
        return XmlApiElementsBuilder.__get_ip_address_xml(name, ip_netmask, tags, description)

    @staticmethod
    @deprecated('XmlApiElementsBuilder.create_ip_address_xml')
    def get_ip_address_xml(name: str, ip_netmask: str, tags: Tuple[str, ...] = (), description='') -> ET.Element:
        """Deprecated! Use create_ip_address_xml instead"""
        return XmlApiElementsBuilder.__get_ip_address_xml(name, ip_netmask, tags, description)

    @staticmethod
    def __get_ip_address_xml(name: str, ip_netmask: str, tags: Tuple[str, ...] = (), description='') -> ET.Element:
        """Deprecated! Use create_ip_address_xml instead"""
        _root_element = ET.Element('entry', {'name': name})
        _ip = ET.SubElement(_root_element, 'ip-netmask')
        _ip.text = ip_netmask

        XmlApiElementsBuilder.__attach_tags_xml(tags, _root_element)
        XmlApiElementsBuilder.__attach_description_xml(description, _root_element)

        return _root_element

    @staticmethod
    def create_address_group_xml(name: str, members: List[ET.Element or str], tags: Tuple[str, ...] = (),
                                 description='', dynamic_filter='') -> ET.Element:
        return XmlApiElementsBuilder.__get_address_group_xml(name, members, tags, description, dynamic_filter)

    @staticmethod
    @deprecated('XmlApiElementsBuilder.create_address_group_xml')
    def get_address_group_xml(name: str, members: List[ET.Element or str], tags: Tuple[str, ...] = (),
                              description='', dynamic_filter='') -> ET.Element:
        """Deprecated! Use create_address_group_xml instead"""
        """is_dynamic deprecated and not working! Use dynamic_filter instead!"""
        return XmlApiElementsBuilder.__get_address_group_xml(name, members, tags, description, dynamic_filter)

    @staticmethod
    def __get_address_group_xml(name: str, members: List[ET.Element or str], tags: Tuple[str, ...] = (),
                                description='', dynamic_filter='') -> ET.Element:
        _root_element = ET.Element('entry', {'name': name})
        XmlApiElementsBuilder.__attach_tags_xml(tags, _root_element)
        XmlApiElementsBuilder.__attach_description_xml(description, _root_element)

        if dynamic_filter:
            if members:
                logger.warning(
                    f'Members given for address group {name} will be ignored because you provide the dynamic_filter and address group will be dynamic!'
                )

            _members_root = ET.SubElement(_root_element, 'dynamic')
            _entry_element = ET.SubElement(_members_root, 'filter')
            _entry_element.text = dynamic_filter
        else:
            if not members:
                raise ValueError('Members list cannot be empty if dynamic_filter is not defined!')

            _members_root = ET.SubElement(_root_element, 'static')

            for _entry in members:
                if isinstance(_entry, ET.Element):
                    _entry = _entry.get('name')

                if not isinstance(_entry, str):
                    raise ValueError("Entry must be a string!")

                _entry_element = ET.SubElement(_members_root, 'member')
                _entry_element.text = _entry

        return _root_element


class ElementsBuilder(XmlApiElementsBuilder):
    """Just short named XmlApiElementsBuilder"""
    pass
