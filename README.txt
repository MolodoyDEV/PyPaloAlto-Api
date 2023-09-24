Framework grant simple access to PaloAlto devices Rest API and Xml API via Python objects.

Device/Panorama config template:
ApiKey: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX==
    or
Login: admin
Password: password

ApiVersion: 10.0
RequestsDelaySeconds: 1

You also can create a dict with keys defined abowe and pass in into config_file_full_name on device __init__()


Code examples:
Create an addresses and address group:
#####################################################################################################
import xml.etree.ElementTree as ET

config_file_full_name = os.getcwd() + '/configurations/PanoramaConfigTest.yml'
_panorama = Panorama(config_file_full_name, load_managed_devices=False)
_ip_element_1 = XmlApiElementsBuilder.get_ip_address_xml('10.10.10.0-31', '10.10.10.0/31', ['test1', 'test2'],
                                                         'desc1')
_ip_element_2 = XmlApiElementsBuilder.get_ip_address_xml('10.10.10.2-31', '10.10.10.2/31', ['test1', 'test2'],
                                                         'desc2')
_ip_element_3 = XmlApiElementsBuilder.get_ip_address_xml('10.10.10.4-31', '10.10.10.4/31', ['test1', 'test2'],
                                                         'desc3')

_elements = [_ip_element_1, _ip_element_2, _ip_element_3]
_dg_1 = XmlApiElementsBuilder.get_device_group_xml('Test_DG_1', _elements)

_xml, _code = _panorama.xml_api_config_request(
            XmlApiConfigAction.set,
            f'{PathBuilder.config_this_device()}{PathBuilder.device_group("PA-VM")}{PathBuilder.address()}',
            _elements
        )

print('Reply:')
print(ET.dump(_xml), _code)

_xml, _code = _panorama.xml_api_config_request(
            XmlApiConfigAction.set,
            f'{PathBuilder.config_this_device()}{PathBuilder.device_group("PA-VM")}{PathBuilder.address_group()}',
            [_dg_1]
        )

print('Reply:')
print(ET.dump(_xml), _code)
#####################################################################################################
or:
#####################################################################################################
import xml.etree.ElementTree as ET

config_file_full_name = os.getcwd() + '/configurations/PanoramaConfigTest.yml'
panorama = Panorama(config_file_full_name, load_managed_devices=False)
ips = ["10.10.10.0/31",
       "10.10.10.2/31",
       "10.10.10.4/31"]

path = XmlApiXPathBuilder.config_this_device() + XmlApiXPathBuilder.device_group('PA-VM') + XmlApiXPathBuilder.address()
ip_addresses_xml = [
    XmlApiElementsBuilder.get_ip_address_xml(x.replace('/', '-'), x, description='xml api test') for x
    in ips]
xml, code = panorama.xml_api_config_request(XmlApiConfigAction.set, path, ip_addresses_xml)
print(code)
print(ET.tostring(xml))

path = XmlApiXPathBuilder.config_this_device() + XmlApiXPathBuilder.device_group('PA-VM') + XmlApiXPathBuilder.address_group()
group_xml = XmlApiElementsBuilder.get_device_group_xml('xml_api_test_group', ip_addresses_xml, description='xml api test')
xml, code = panorama.xml_api_config_request(XmlApiConfigAction.set, path, [group_xml])
print(code)
print(ET.tostring(xml))
#####################################################################################################


Get all security pre rules:
#####################################################################################################
import xml.etree.ElementTree as ET

config_file_full_name = os.getcwd() + '/configurations/PanoramaConfigTest.yml'
panorama = Panorama(config_file_full_name, load_managed_devices=False)
_xpath = XmlApiXPathBuilder.config_this_device() + XmlApiXPathBuilder.device_group('PA-VM') + XmlApiXPathBuilder.rule(
    RulebaseType.pre_rule, RuleType.security)
_xml, _code = panorama.xml_api_config_request(XmlApiConfigAction.get, _xpath)

_rules = SecurityRulesBuilder.create_security_rules_list(_xml)

print(non_string_list_join(_rules, '\n'))
#####################################################################################################


Get managed device in device group from panorama and print system info from active devices:
#####################################################################################################
import xml.etree.ElementTree as ET
from pypaloalto_api.operational_commands import Builder as OpBuilder

panorama_config_file_full_name = 'configurations/PanoramaConfigTest.yml'
device_config_file_full_name = 'configurations/DeviceConfigTest.yml'

panorama = Panorama(panorama_config_file_full_name, device_config_file_full_name)
devices = panorama.get_devices_in_group('Test-Device-Group')
active_devices = []

for device in devices:
    if device.ha_peer_state == HaPeerState.active or device.ha_peer_state == HaPeerState.ha_not_enabled:
        active_devices.append(device)

for device in active_devices:
    xml, code = device.xml_api_operational_request(OpBuilder.show_system_info())

    if code != 200:
        raise Exception(f'Error ' + ET.tostring(xml).decode())
    else:
        print(ET.tostring(xml))
#####################################################################################################
