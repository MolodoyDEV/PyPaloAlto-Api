from enum import Enum


class YesNo(Enum):
    yes = 'yes'
    no = 'no'


class Location(Enum):
    device_group = 'location=device-group&device-group='
    shared = 'location=shared'
    vsys = 'location=vsys&vsys='


class EntityType(Enum):
    policies_pre_rules = 'Policies/SecurityPreRules'
    policies_post_rules = 'Policies/SecurityPostRules'
    policies_rules = 'Policies/SecurityRules'


class HaPeerState(Enum):
    primaty_active = 'primary-active'
    primary_active = 'primary-active'
    active = 'active'
    passive = 'passive'
    non_functional = 'non-func'
    init = 'init'
    ha_not_enabled = ''


class HttpRequestMethod(Enum):
    put = "PUT"
    post = "POST"
    get = "GET"
    patch = "PATCH"


class Protocol(Enum):
    tcp = 'tcp'
    urp = 'udp'


class RulebaseType(Enum):
    pre_rule = 'pre-rulebase'
    post_rule = 'post-rulebase'


class RuleType(Enum):
    security = 'security'
    nat = 'nat'
    sdwan = 'sdwan'
    tunnel_inspect = 'tunnel-inspect'
    qos = 'qos'
    pbf = 'pbf'
    dos = 'dos'
    decryption = 'decryption'
    authentication = 'authentication'
    application_override = 'application-override'
