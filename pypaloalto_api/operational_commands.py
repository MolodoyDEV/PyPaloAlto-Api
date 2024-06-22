from enum import Enum


class Command(Enum):
    check = 'check'  # Check configuration status
    clear = 'clear'  # Clear data
    delete = 'delete'  # Remove files from hard disk
    import_load = 'import-load'  # Load configuration from disk
    load = 'load'  # Load configuration from disk
    monitoring = 'monitoring'  # Device Monitoring Operations
    replace = 'replace'  # replace device serial number
    request = 'request'  # Make system-level requests
    request_batch = 'request-batch'  # run test command on devices
    revert = 'revert'  # Revert changes from configuration
    save = 'save'  # Save configuration to disk
    schedule = 'schedule'  # schedule test jobs
    set = 'set'  # Set operational parameters
    show = 'show'  # Show operational parameters
    test = 'test'  # verify system settings with test cases
    validate = 'validate'  # Validate current set of changes


class ContentType(Enum):
    anti_virus = 'anti-virus'
    wildfire = 'wildfire'
    content = 'content'


class OPCmdBuilder:
    @staticmethod
    def request_batch_info(content_type: ContentType) -> str:
        """Panorama only!
<result>
    <content-updates last-updated-at="2022/06/11 03:00:03 MSK">
    <entry>
        <version>8521-7220</version>
        <app-version>8521-7220</app-version>
        <filename>panupv2-all-contents-8521-7220</filename>
        <size>53</size>
        <size-kb>54552</size-kb>
        <released-on>2022/02/01 09:12:37 MSK</released-on>
        <release-notes>
            <![CDATA[
            ]]>
        </release-notes>
        <downloaded>no</downloaded>
        <current>no</current>
        <previous>no</previous>
        <installing>no</installing>
        <features>contents</features>
        <update-type>Full</update-type>
        <feature-desc>Unknown</feature-desc>
        <sha256>
        XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        </sha256>
    </entry>
    <entry>
        .........
        ........
        .......
    </entry>
</result>"""
        return f'<request><batch><{content_type.value}><info></info></{content_type.value}></batch></request>'

    @staticmethod
    def show_devices_all() -> str:
        """Panorama only!
<result>
    <devices>
        <entry name="XXXXXXXXXXXX">
            <serial>XXXXXXXXXXXX</serial>
            <connected>yes</connected>
            <unsupported-version>yes</unsupported-version>
            <wildfire-rt>no</wildfire-rt>
            <hostname>PA-5260-XXXX-XXXX</hostname>
            <ip-address>10.10.10.10</ip-address>
            <mac-addr/>
            <uptime>237 days, 23:54:00</uptime>
            <family>5200</family>
            <model>PA-5260</model>
            <sw-version>10.0.8</sw-version>
            <app-version>8581-7430</app-version>
            <av-version>4109-4622</av-version>
            <device-dictionary-version>44-316</device-dictionary-version>
            <wildfire-version>0</wildfire-version>
            <threat-version>8581-7430</threat-version>
            <url-db>paloaltonetwork</url-db>
            <url-filtering-version>0000.00.00.000</url-filtering-version>
            <logdb-version>10.0.3</logdb-version>
            <vpnclient-package-version/>
            <global-protect-client-package-version>0.0.0</global-protect-client-package-version>
            <prev-app-version>8571-7398</prev-app-version>
            <prev-av-version>4087-4599</prev-av-version>
            <prev-threat-version>8571-7398</prev-threat-version>
            <prev-wildfire-version>0</prev-wildfire-version>
            <prev-device-dictionary-version>43-313</prev-device-dictionary-version>
            <domain/>
            <slot-count>0</slot-count>
            <type/>
            <tag/>
            <ha>
                <state>passive</state>
                <peer>
                    <serial>XXXXXXXXXXXX</serial>
                </peer>
            </ha>
            <vpn-disable-mode>no</vpn-disable-mode>
            <operational-mode>normal</operational-mode>
            <high-speed-mode>no</high-speed-mode>
            <certificate-status/>
            <certificate-subject-name>XXXXXXXXXXXX</certificate-subject-name>
            <certificate-expiry>2031/03/02 09:13:53</certificate-expiry>
            <connected-at>2022/06/30 12:37:09</connected-at>
            <custom-certificate-usage>no</custom-certificate-usage>
            <multi-vsys>yes</multi-vsys>
            <vsys>
                <entry name="vsys1">
                    <display-name>vsys1</display-name>
                    <shared-policy-status/>
                    <shared-policy-md5sum>XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX</shared-policy-md5sum>
                    <shared-policy-version>12862</shared-policy-version>
                </entry>
                    <entry name="vsys2">
                    <display-name>vsys2</display-name>
                    <shared-policy-status/>
                    <shared-policy-md5sum>XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX</shared-policy-md5sum>
                    <shared-policy-version>12862</shared-policy-version>
                </entry>
            </vsys>
            <last-masterkey-push-status>Unknown</last-masterkey-push-status>
            <last-masterkey-push-timestamp/>
            <express-mode>no</express-mode>
            <device-cert-present/>
            <device-cert-expiry-date>N/A</device-cert-expiry-date>
        </entry>
        <entry>
            .........
            .......
            ......
        </entry>
    </devices>
</result>
"""
        return '<show><devices><all></all></devices></show>'

    @staticmethod
    def show_devices_connected() -> str:
        """Panorama only!
<result>
    <devices>
        <entry name="XXXXXXXXXXXX">
            <serial>XXXXXXXXXXXX</serial>
            <connected>yes</connected>
            <unsupported-version>yes</unsupported-version>
            <wildfire-rt>no</wildfire-rt>
            <hostname>PA-5260-XXXX-XXXX</hostname>
            <ip-address>10.10.10.10</ip-address>
            <mac-addr/>
            <uptime>237 days, 23:54:00</uptime>
            <family>5200</family>
            <model>PA-5260</model>
            <sw-version>10.0.8</sw-version>
            <app-version>8581-7430</app-version>
            <av-version>4109-4622</av-version>
            <device-dictionary-version>44-316</device-dictionary-version>
            <wildfire-version>0</wildfire-version>
            <threat-version>8581-7430</threat-version>
            <url-db>paloaltonetwork</url-db>
            <url-filtering-version>0000.00.00.000</url-filtering-version>
            <logdb-version>10.0.3</logdb-version>
            <vpnclient-package-version/>
            <global-protect-client-package-version>0.0.0</global-protect-client-package-version>
            <prev-app-version>8571-7398</prev-app-version>
            <prev-av-version>4087-4599</prev-av-version>
            <prev-threat-version>8571-7398</prev-threat-version>
            <prev-wildfire-version>0</prev-wildfire-version>
            <prev-device-dictionary-version>43-313</prev-device-dictionary-version>
            <domain/>
            <slot-count>0</slot-count>
            <type/>
            <tag/>
            <ha>
                <state>passive</state>
                <peer>
                    <serial>XXXXXXXXXXXX</serial>
                </peer>
            </ha>
            <vpn-disable-mode>no</vpn-disable-mode>
            <operational-mode>normal</operational-mode>
            <high-speed-mode>no</high-speed-mode>
            <certificate-status/>
            <certificate-subject-name>XXXXXXXXXXXX</certificate-subject-name>
            <certificate-expiry>2031/03/02 09:13:53</certificate-expiry>
            <connected-at>2022/06/30 12:37:09</connected-at>
            <custom-certificate-usage>no</custom-certificate-usage>
            <multi-vsys>yes</multi-vsys>
            <vsys>
                <entry name="vsys1">
                    <display-name>vsys1</display-name>
                    <shared-policy-status/>
                    <shared-policy-md5sum>XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX</shared-policy-md5sum>
                    <shared-policy-version>12862</shared-policy-version>
                </entry>
                    <entry name="vsys2">
                    <display-name>vsys2</display-name>
                    <shared-policy-status/>
                    <shared-policy-md5sum>XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX</shared-policy-md5sum>
                    <shared-policy-version>12862</shared-policy-version>
                </entry>
            </vsys>
            <last-masterkey-push-status>Unknown</last-masterkey-push-status>
            <last-masterkey-push-timestamp/>
            <express-mode>no</express-mode>
            <device-cert-present/>
            <device-cert-expiry-date>N/A</device-cert-expiry-date>
        </entry>
        <entry>
            .........
            .......
            ......
        </entry>
    </devices>
</result>
"""
        return '<show><devices><connected></connected></devices></show>'

    @staticmethod
    def show_devicegroups() -> str:
        """Panorama only!
<result>
    <devicegroups>
        <entry name="DG1">
            <shared-policy-md5sum>XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX</shared-policy-md5sum>
            <devices>
                <entry name="XXXXXXXXXXXX">
                    FULL DEVICE INFO
                    ......
                </entry>
                ......
                ......
            </devices>
        </entry>
        <entry name="DG2">
            ......
            ......
        </entry>
    </devicegroups>
</result>"""
        return '<show><devicegroups></devicegroups></show>'

    @staticmethod
    def request_batch_upload_install_file(content_type: ContentType, file_name: str, device_serial: str,
                                          is_uploaded_file=False) -> str:
        """Panorama only!"""
        file_tag = 'uploaded-file' if is_uploaded_file else 'file'

        return f'<request><batch><{content_type.value}><upload-install><{file_tag}>{file_name}</{file_tag}>' \
               f'<devices>{device_serial}</devices></upload-install></{content_type.value}></batch></request>'

    @staticmethod
    def request_batch_content_upload_install_file(file_name: str, device_serial: str,
                                                  skip_content_validity_check=False, is_uploaded_file=False) -> str:
        """Panorama only!"""
        file_tag = 'uploaded-file' if is_uploaded_file else 'file'
        content_validity_check_tag = '' if skip_content_validity_check else '<skip-content-validity-check>yes</skip-content-validity-check>'

        return f'<request><batch><{ContentType.content.value}><upload-install><{file_tag}>{file_name}</{file_tag}>' \
               f'{content_validity_check_tag}<devices>{device_serial}</devices>' \
               f'</upload-install></{ContentType.content.value}></batch></request>'

    @staticmethod
    def show_jobs(job_id=None) -> str:
        """
<result>
    <job>
        <tenq>2022/07/14 19:18:18</tenq>
        <tdeq>19:18:18</tdeq>
        <id>468663</id>
        <user/>
        <type>load_custom_threats</type>
        <status>FIN</status>
        <queued>NO</queued>
        <stoppable>no</stoppable>
        <result>OK</result>
        <tfin>2022/07/14 19:34:15</tfin>
        <description/>
        <positionInQ>0</positionInQ>
        <progress>100</progress>
        </job>
        <job>
        <tenq>2022/07/14 19:18:18</tenq>
        <tdeq>19:18:18</tdeq>
        <id>468662</id>
        <user/>
        <type>load_sdwan_saasmon</type>
        <status>FIN</status>
        <queued>NO</queued>
        <stoppable>no</stoppable>
        <result>OK</result>
        <tfin>2022/07/14 19:18:24</tfin>
        <description/>
        <positionInQ>0</positionInQ>
        <progress>100</progress>
    </job>
    <job>
        ........
        .......
        .....
    </job>
</result>"""
        if job_id:
            return f'<show><jobs><id>{job_id}</id></jobs></show>'
        else:
            return '<show><jobs><all></all></jobs></show>'

    @staticmethod
    def show_ha_state() -> str:
        """
<result>
    <enabled>yes</enabled>
    <local-info>
        <url-compat>Match</url-compat>
        <app-version>8581-7430</app-version>
        <av-compat>Match</av-compat>
        <url-version>Not Installed</url-version>
        <av-version>4109-4622</av-version>
        <build-rel>10.1.5-h2</build-rel>
        <encrypt-enable>yes</encrypt-enable>
        <monitor-fail-holdup>0</monitor-fail-holdup>
        <priority>primary</priority>
        <preempt-hold>1</preempt-hold>
        <state>primary-active</state>
        <version>1</version>
        <promotion-hold>2000</promotion-hold>
        <addon-master-holdup>7000</addon-master-holdup>
        <heartbeat-interval>2000</heartbeat-interval>
        <hello-interval>8000</hello-interval>
        <mgmt-ip>10.10.10.10/23</mgmt-ip>
        <mgmt-macaddr>ac:1f:XX:XX:XX:XX</mgmt-macaddr>
        <link-mon-intv>3000</link-mon-intv>
        <state-duration>1235584</state-duration>
        <mgmt-ipv6/>
        <preemptive>no</preemptive>
        <iot-version>43-313</iot-version>
        <build-compat>Match</build-compat>
        <encrypt-imported>yes</encrypt-imported>
        <iot-compat>Match</iot-compat>
        <app-compat>Match</app-compat>
    </local-info>
    <peer-info>
        <iot-version>43-313</iot-version>
        <app-version>8581-7430</app-version>
        <conn-status>up</conn-status>
        <build-rel>10.1.5-h2</build-rel>
        <mgmt-macaddr>ac:1f:XX:XX:XX:XX</mgmt-macaddr>
        <state-duration>1235578</state-duration>
        <mgmt-ip>10.20.20.20</mgmt-ip>
        <preemptive>no</preemptive>
        <priority>secondary</priority>
        <last-error-state>secondary-suspended</last-error-state>
        <state>secondary-passive</state>
        <version>1</version>
        <url-version>Not Installed</url-version>
        <av-version>4109-4622</av-version>
        <conn-ha1>
            <conn-status>up</conn-status>
            <conn-primary>yes</conn-primary>
            <conn-desc>heartbeat status</conn-desc>
        </conn-ha1>
        <last-error-reason>User requested</last-error-reason>
    </peer-info>
    <path-monitoring>
        <failure-condition>any</failure-condition>
        <enabled>no</enabled>
        <groups/>
    </path-monitoring>
    <running-sync>synchronized</running-sync>
    <running-sync-enabled>yes</running-sync-enabled>
</result>"""
        return '<show><high-availability><state></state></high-availability></show>'

    @staticmethod
    def set_user_id_data() -> str:
        return '<set><user-id><data></data></user-id></set>'

    @staticmethod
    def show_system_info() -> str:
        """
<result>
    <system>
        <hostname>Panorama-MCOD</hostname>
        <ip-address>10.10.10.10</ip-address>
        <public-ip-address>unknown</public-ip-address>
        <netmask>255.255.254.0</netmask>
        <default-gateway>10.10.10.250</default-gateway>
        <ipv6-address>unknown</ipv6-address>
        <ipv6-link-local-address>fe80::XXXX:XXXX:XXXX:XXXX/64</ipv6-link-local-address>
        <mac-address>ac:1f:XX:XX:XX:XX</mac-address>
        <time>Thu Jul 14 19:48:39 2022 </time>
        <uptime>14 days, 7:15:17</uptime>
        <devicename>Panorama-MCOD</devicename>
        <family>m</family>
        <model>M-600</model>
        <serial>XXXXXXXXXXXX</serial>
        <cloud-mode>non-cloud</cloud-mode>
        <sw-version>10.1.5-h2</sw-version>
        <device-dictionary-version>43-313</device-dictionary-version>
        <device-dictionary-release-date>2022/02/18 02:23:26 MSK</device-dictionary-release-date>
        <app-version>8581-7430</app-version>
        <app-release-date>2022/06/08 14:25:08 MSK</app-release-date>
        <av-version>4109-4622</av-version>
        <av-release-date>2022/06/09 14:56:41 MSK</av-release-date>
        <wf-private-version>79438-2020-12-16T16-28-18</wf-private-version>
        <wf-private-release-date>2020/12/16 13:28:18</wf-private-release-date>
        <url-db>paloaltonetworks</url-db>
        <wildfire-version>640725-643959</wildfire-version>
        <wildfire-release-date>2022/02/24 21:12:14 MSK</wildfire-release-date>
        <wildfire-rt>Disabled</wildfire-rt>
        <logdb-version>10.1.2</logdb-version>
        <platform-family>m</platform-family>
        <system-mode>panorama</system-mode>
        <operational-mode>normal</operational-mode>
        <licensed-device-capacity>100</licensed-device-capacity>
        <device-certificate-status>None</device-certificate-status>
    </system>
</result>"""
        return '<show><system><info></info></system></show>'

    @staticmethod
    def show_dg_hierarchy() -> str:
        """
<result>
    <dg-hierarchy>
        <dg name="DG1" dg_id="123"/>
        <dg name="DG2" dg_id="456"/>
        </dg>
            <dg name="RootDG1" dg_id="1234">
                <dg name="SubDG1" dg_id="1235">
                    <dg name="SubDG3" dg_id="1236">
                        <dg name="DG3" dg_id="1111"/>
                        <dg name="DG4" dg_id="2222"/>
                        </dg>
                    <dg name="DG5" dg_id="3333"/>
                    <dg name="DG6" dg_id="4444">
                </dg>
            </dg>
        </dg>
    </dg-hierarchy>
</result>"""
        return '<show><dg-hierarchy></dg-hierarchy></show>'
