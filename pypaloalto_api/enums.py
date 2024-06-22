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
    primary_active = 'primary-active'
    primary_passive = 'primary-passive'
    secondary_passive = 'secondary-passive'
    secondary_active = 'secondary-active'
    active = 'active'
    passive = 'passive'
    non_functional = 'non-func'
    primary_non_functional = 'primary-non-functional'
    secondary_non_functional = 'secondary-non-functional'
    init = 'init'
    suspended = 'suspended'
    ha_not_enabled = ''


HA_ACTIVE_PEER_STATES = (
    HaPeerState.active, HaPeerState.primary_active, HaPeerState.secondary_active,
    HaPeerState.ha_not_enabled, HaPeerState.primary_non_functional,
)
HA_PEER_ACTIVE_STATES = HA_ACTIVE_PEER_STATES

HA_PASSIVE_PEER_STATES = (
    HaPeerState.passive, HaPeerState.primary_passive, HaPeerState.secondary_passive, HaPeerState.non_functional,
    HaPeerState.secondary_non_functional
)
HA_PEER_PASSIVE_STATES = HA_PASSIVE_PEER_STATES


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
