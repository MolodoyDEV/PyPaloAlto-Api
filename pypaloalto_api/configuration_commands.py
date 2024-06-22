from enum import Enum
from pypaloalto_api.enums import RulebaseType, RuleType

from pypaloalto_api.xmlapi import PaloAltoObjectType, XPATH_BY_OBJECT_TYPE


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
    def config_managed_devices() -> str:
        return '/config/mgt-config/devices/entry'

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


class CCXPathBuilder(XmlApiXPathBuilder):
    """Just short named XmlApiXPathBuilder"""
    pass
