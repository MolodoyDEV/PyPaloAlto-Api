import typing
from enum import Enum
import xml.etree.ElementTree as ET
from pypaloalto_api.enums import Protocol, RulebaseType, RuleType
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


class XmlApiRequestType(Enum):
    keygen = 'keygen'  # Generate API keys for authentication.
    config = 'config'  # Modify the configuration.
    commit = 'commit'  # Commit firewall configuration, including partial commits.
    op = 'op'  # Perform operational mode commands, including checking system status and validating configurations.
    report = 'report'  # Get reports, including predefined, dynamic, and custom reports.
    log = 'log'  # Get logs, including traffic, threat, and event logs.
    import_files = 'import'  # Import files including configurations and certificates.
    export_files = 'export'  # Export files including packet captures, certificates, and keys.
    user_id = 'user-id'  # Update User-ID mappings.
    version = 'version'  # Show the PAN-OS version, serial number, and model number.


class RequestType(Enum):
    """Just short named XmlApiRequestType"""
    keygen = 'keygen'  # Generate API keys for authentication.
    config = 'config'  # Modify the configuration.
    commit = 'commit'  # Commit firewall configuration, including partial commits.
    op = 'op'  # Perform operational mode commands, including checking system status and validating configurations.
    report = 'report'  # Get reports, including predefined, dynamic, and custom reports.
    log = 'log'  # Get logs, including traffic, threat, and event logs.
    import_files = 'import'  # Import files including configurations and certificates.
    export_files = 'export'  # Export files including packet captures, certificates, and keys.
    user_id = 'user-id'  # Update User-ID mappings.
    version = 'version'  # Show the PAN-OS version, serial number, and model number.


class XmlApiConfigAction(Enum):
    show = 'show'  # Get active configuration
    get = 'get'  # Get candidate configuration
    set = 'set'  # Set candidate configuration. Add to config
    edit = 'edit'  # Edit candidate configuration. Replace config
    delete = 'delete'  # Delete candidate object
    rename = 'rename'  # Rename a configuration object
    clone = 'clone'  # Clone a configuration object
    move = 'move'  # Move a configuration object
    override = 'override'  # Override a template setting
    multi_move = 'multi-move'  # Move multiple objects in a device group or virtual system
    multi_clone = 'multi-clone'  # Clone multiple objects in a device group or virtual system
    complete = 'complete'  # Show available subnode values and XPaths for a given XPath.


class ConfigAction(Enum):
    """Just short named XmlApiConfigAction"""
    show = 'show'  # Get active configuration
    get = 'get'  # Get candidate configuration
    set = 'set'  # Set candidate configuration. Add to config
    edit = 'edit'  # Edit candidate configuration. Replace config
    delete = 'delete'  # Delete candidate object
    rename = 'rename'  # Rename a configuration object
    clone = 'clone'  # Clone a configuration object
    move = 'move'  # Move a configuration object
    override = 'override'  # Override a template setting
    multi_move = 'multi-move'  # Move multiple objects in a device group or virtual system
    multi_clone = 'multi-clone'  # Clone multiple objects in a device group or virtual system
    complete = 'complete'  # Show available subnode values and XPaths for a given XPath.


class XmlApiElementsBuilder:

    @staticmethod
    def __attach_description_xml(description: str, root):
        if description:
            _description_entry = ET.SubElement(root, 'description')
            _description_entry.text = description

    @staticmethod
    def __attach_tags_xml(tags: typing.Tuple[str,], root):
        if tags:
            _tags_root = ET.SubElement(root, 'tag')

            for _tag in tags:
                _tag_entry = ET.SubElement(_tags_root, 'member')
                _tag_entry.text = _tag

    @staticmethod
    def create_service_xml(name: str, destination_port: str, protocol: Protocol, source_port='',
                           tags: typing.Tuple[str,] = (), description='') -> ET.Element:
        return XmlApiElementsBuilder.__get_service_xml(name, destination_port, protocol, source_port, tags, description)

    @staticmethod
    @deprecated('XmlApiElementsBuilder.create_service_xml')
    def get_service_xml(name: str, destination_port: str, protocol: Protocol, source_port='',
                        tags: typing.Tuple[str,] = (), description='') -> ET.Element:
        """Deprecated! Use create_service_xml instead"""
        return XmlApiElementsBuilder.__get_service_xml(name, destination_port, protocol, source_port, tags, description)

    @staticmethod
    def __get_service_xml(name: str, destination_port: str, protocol: Protocol, source_port='',
                          tags: typing.Tuple[str,] = (), description='') -> ET.Element:
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
    def create_ip_address_xml(name: str, ip_netmask: str, tags: typing.Tuple[str,] = (), description='') -> ET.Element:
        return XmlApiElementsBuilder.__get_ip_address_xml(name, ip_netmask, tags, description)

    @staticmethod
    @deprecated('XmlApiElementsBuilder.create_ip_address_xml')
    def get_ip_address_xml(name: str, ip_netmask: str, tags: typing.Tuple[str,] = (), description='') -> ET.Element:
        """Deprecated! Use create_ip_address_xml instead"""
        return XmlApiElementsBuilder.__get_ip_address_xml(name, ip_netmask, tags, description)

    @staticmethod
    def __get_ip_address_xml(name: str, ip_netmask: str, tags: typing.Tuple[str,] = (), description='') -> ET.Element:
        """Deprecated! Use create_ip_address_xml instead"""
        _root_element = ET.Element('entry', {'name': name})
        _ip = ET.SubElement(_root_element, 'ip-netmask')
        _ip.text = ip_netmask

        XmlApiElementsBuilder.__attach_tags_xml(tags, _root_element)
        XmlApiElementsBuilder.__attach_description_xml(description, _root_element)

        return _root_element

    @staticmethod
    def create_address_group_xml(name: str, members: typing.List[ET.Element], tags: typing.Tuple[str,] = (),
                                 description='') -> ET.Element:
        return XmlApiElementsBuilder.__get_address_group_xml(name, members, tags, description)

    @staticmethod
    @deprecated('XmlApiElementsBuilder.create_address_group_xml')
    def get_address_group_xml(name: str, members: typing.List[ET.Element], tags: typing.Tuple[str,] = (),
                              description='') -> ET.Element:
        """Deprecated! Use create_address_group_xml instead"""
        return XmlApiElementsBuilder.__get_address_group_xml(name, members, tags, description)

    @staticmethod
    def __get_address_group_xml(name: str, members: typing.List[ET.Element], tags: typing.Tuple[str,] = (),
                                description='') -> ET.Element:
        if not members:
            raise ValueError('Members list cannot be empty!')

        _root_element = ET.Element('entry', {'name': name})
        _static = ET.SubElement(_root_element, 'static')

        XmlApiElementsBuilder.__attach_tags_xml(tags, _root_element)
        XmlApiElementsBuilder.__attach_description_xml(description, _root_element)

        for _entry in members:
            if isinstance(_entry, ET.Element):
                _entry = _entry.get('name')

            if not isinstance(_entry, str):
                raise ValueError("Entry must be a string!")

            _entry_element = ET.SubElement(_static, 'member')
            _entry_element.text = _entry

        return _root_element


class ElementsBuilder(XmlApiElementsBuilder):
    """Just short named XmlApiElementsBuilder"""
    pass


class XmlApiXPathBuilder:
    @staticmethod
    def location(location_name):
        if location_name == 'shared':
            return XmlApiXPathBuilder.config_shared()
        elif location_name == 'predefined':
            return XmlApiXPathBuilder.config_predefined()
        elif location_name == 'panorama':
            return XmlApiXPathBuilder.config_panorama()
        else:
            return XmlApiXPathBuilder.localhost_device_group(location_name)

    @staticmethod
    def config_panorama() -> str:
        return '/config/panorama'

    @staticmethod
    def config_shared() -> str:
        return '/config/shared'

    @staticmethod
    def config_predefined() -> str:
        return '/config/predefined'

    @staticmethod
    def device_group(name='') -> str:
        if name:
            return f"/device-group/entry[@name='{name}']"
        else:
            return "/device-group"

    @staticmethod
    def localhost_device_group(name='') -> str:
        return f"{XmlApiXPathBuilder.config_this_device()}{XmlApiXPathBuilder.device_group(name)}"

    @staticmethod
    def xpath_by_object_type(paloalto_object_type: PaloAltoObjectType, object_name='') -> str:
        xpath = XPATH_BY_OBJECT_TYPE[paloalto_object_type]

        if object_name:
            xpath += f"/entry[@name='{object_name}']"

        return xpath

    @staticmethod
    def vsys(name='') -> str:
        if name:
            return f"/vsys/entry[@name='{name}']"
        else:
            return "/vsys"

    @staticmethod
    def panorama_vsys(name='') -> str:
        config_panorama = XmlApiXPathBuilder.config_panorama()

        if name:
            return f"{config_panorama}/vsys/entry[@name='{name}']"
        else:
            return f"{config_panorama}/vsys"

    @staticmethod
    def config_this_device() -> str:
        return "/config/devices/entry[@name='localhost.localdomain']"

    @staticmethod
    def address(name='') -> str:
        return XmlApiXPathBuilder.xpath_by_object_type(PaloAltoObjectType.address, name)

    @staticmethod
    def address_group(name='') -> str:
        return XmlApiXPathBuilder.xpath_by_object_type(PaloAltoObjectType.address_group, name)

    @staticmethod
    def service(name='') -> str:
        return XmlApiXPathBuilder.xpath_by_object_type(PaloAltoObjectType.service, name)

    @staticmethod
    def service_group(name='') -> str:
        return XmlApiXPathBuilder.xpath_by_object_type(PaloAltoObjectType.service_group, name)

    @staticmethod
    def application(name='') -> str:
        return XmlApiXPathBuilder.xpath_by_object_type(PaloAltoObjectType.application, name)

    @staticmethod
    def application_group(name='') -> str:
        return XmlApiXPathBuilder.xpath_by_object_type(PaloAltoObjectType.application_group, name)

    @staticmethod
    def rule(rulebase_type: RulebaseType, rule_type: RuleType, rule_name='') -> str:
        if rule_name:
            return f"/{rulebase_type.value}/{rule_type.value}/rules/entry[@name='{rule_name}']"
        else:
            return f"/{rulebase_type.value}/{rule_type.value}/rules"


class XPathBuilder(XmlApiXPathBuilder):
    """Just short named XmlApiXPathBuilder"""
    pass
