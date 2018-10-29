# avi_check_config - avi configuration validation tool
## Description
*avi_check_config* is built to address the use cases below:
1. Ease configuration validation for migration needs
2. Validate configuration against known best practices
3. Perform scoped queries and visualization to better understand deployed configuration
```bash
root@avitools:~# ./avi_check_config.py -h
usage: avi_check_config.py [-h] [--get-avi-config GET_AVI_CONFIG]
                           [--config CONFIG] [--config-pattern CONFIG_PATTERN]
                           [--check-related-only] [--output OUTPUT_FOLDER]
                           [--get-object-list GET_OBJECT_LIST]
                           [--get-shared-objects-list GET_SHARED_OBJECTS_LIST]
                           [--get-referred-by-list GET_REFERRED_BY_LIST]
                           [--get-config GET_OBJ_CONFIG]
                           [--get-related-config GET_RELATED_CONFIG]

avi_check_config - avi configuration validation tool

optional arguments:
  -h, --help            show this help message and exit
  --get-avi-config GET_AVI_CONFIG
                        Download configuration from controller: GET api/config
                        uration/export?include_name=true&uuid_refs=true.
                        Controller FQDN or IP, username and password
                        delimitted by ":" has to be provided. For example
                        avi_controller1.avi:admin:password
  --config CONFIG       Name of Avi JSON configuration file. Please ensure
                        configuration is exported with options
                        include_name=true&uuid_refs=true or please leverage
                        --get-avi-config option to acquite Avi JSON
                        configuration file.
  --config-pattern CONFIG_PATTERN
                        Name of Avi JSON configuration pattern file
  --check-related-only  *EXPERIMENTAL* Truncate provided Avi JSON
                        configuration file to related objects defined within
                        pattern, i.e. allows to search against related objects
                        only. In the background, generates only in scope
                        configuration based on mentioned objects within
                        pattern. *REQUIRES EXPORTED CONFIGURATION FROM
                        CONTROLLER*
  --output OUTPUT_FOLDER
                        Folder path for output files to be created in
  --get-object-list GET_OBJECT_LIST
                        Get list of objects of specified type. Type of object
                        is required attributes. For example: VirtualService
  --get-shared-objects-list GET_SHARED_OBJECTS_LIST
                        Get list of common referred objects across specified
                        objects. Object type and list of names are required
                        attributes. For example: VirtualService:vs1,vs2,vs3.
                        *REQUIRES EXPORTED CONFIGURATION FROM CONTROLLER*
  --get-referred-by-list GET_REFERRED_BY_LIST
                        Get list of objects leveraging specified object, i.e
                        referring the object. Object type and name are
                        required attributes. For example: Pool:pool1.
                        *REQUIRES EXPORTED CONFIGURATION FROM CONTROLLER*
  --get-config GET_OBJ_CONFIG
                        Get configuration file for specified object. Type is
                        required attribute, Name is optional, if Name is not
                        provided configuration file generated for all objects
                        of the specified Type. For example: VirtualService:vs1
  --get-related-config GET_RELATED_CONFIG
                        Provide configuration file for specified child or
                        related objects of parent object. Object type and name
                        are required attributes. For example: Pool:pool11.
                        *REQUIRES EXPORTED CONFIGURATION FROM CONTROLLER*
```
## HowTo
### Configuration JSON file and Configuration Pattern JSON file
Tool is designed to use offline backup of configuration as not necessary access to controller is always available or migration tool generated JSON configuration file. To obtain a configuration backup from controller:
```bash
GET https://[CONTROLLER-IP]/api/configuration/export?include_name=true&uuid_refs=true
```
or
```
./avi_check_config.py --get-avi-config 192.168.1.11:admin:password
```
Pattern file is defined using the same format as avi json configuration file with few exceptions:
* name field is used to supply list of target objects to be searched, if name field is not specified all objects of the specified type are checked.
* non-nested fields other than name within pattern are used by re.search(a, b) function, meaning exact or partial or pyregex format can be used to search.
* for nested fields search jsondiff library is utilized.
* Pattern example:
```json
{
    "VirtualService": [
        {
            "name": ["vs_192.168.1.15", "vs_dns01a_192.168.1.16_53"],
	          "network_profile_ref": "UDP",
            "application_profile_ref": "DNS",
            "weight": 1
        }
    ]
}
```
The pattern example above outlines desired configuration for three properties for the specified two VirtualServices.
### Perform configuration validation against specified pattern
```bash
root@avitools:~# ./avi_check_config.py --config config.json --config-pattern pattern1.json
```
As result, the tool will produce three files to output folder:
```
config.json_matching_values.json
config.json_mismatching_values.json
config.json_missing_options.json
#
# config.json_matching_values.json will represent values and properties that matched as per pattern or do exist within the configuraiton.
#
{
    "VirtualService": {
        "vs_192.168.1.15": {
            "weight": 1
        },
        "vs_dns01a_192.168.1.16_53": {
            "application_profile_ref": "/api/applicationprofile/?tenant=admin&name=System-DNS",
            "network_profile_ref": "/api/networkprofile/?tenant=admin&name=System-UDP-Per-Pkt",
            "weight": 1
        }
    }
#
# config.json_mismatching_values.json will represent values and properties that configured, but don't match as per pattern
#
{
    "VirtualService": {
        "vs_192.168.1.15": {
            "application_profile_ref": "/api/applicationprofile/?tenant=admin&name=System-HTTP",
            "network_profile_ref": "/api/networkprofile/?tenant=admin&name=System-TCP-Proxy"
        }
    }
#
# config.json_missing_options.json will represent options that are missing and not configured, but required to be set as per pattern
#
{
    "VirtualService": {}
}
```
### Advanced patterns
Patterns can include multiple different objects inside
```json
{
    "VirtualService": [
        {
            "name": ["vs_192.168.1.15", "vs_dns01a_192.168.1.16_53"],
            "network_profile_ref": "System-TCP",
            "application_profile_ref": "Custom-HTTP",
            "weight": 1
        }
    ],
    "Pool": [
        {
            "rewrite_host_header_to_sni": false,
            "lb_algorithm": "LB_ALGORITHM_LEAST_CONNECTIONS" }
    ],
    "ApplicationPersistenceProfile": [
        {
            "app_cookie_persistence_profile": {
                "prst_hdr_name": "customhttpcookiename",
                "timeout": 20
            }
        }
    ],
    "SSLProfile": [
        {
            "ssl_session_timeout": 86400,
             "accepted_ciphers": "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-SHA:ECDHE-ECDSA-AES256-SHA:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-ECDSA-AES256-SHA384:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:DES-CBC3-SHA"
        }
    ]
}
```
### Get list of objects for specified type
Object type is defined as per Avi JSON configuration file. The output will be written to the file in the specified output folder.
```
root@avitools:~# ./avi_check_config.py --config config.json --get-object-list VirtualService
root@avitools:~# cat config.json_VirtualService_object_list.json
[
    "vs_gslb01a_192.168.1.14_53",
    "vs_gslb02a_192.168.1.17_53",
    "vs_192.168.1.15",
    "vs_dns01a_192.168.1.16_53",
    "vs_192.168.3.11"
]
```
### Get configuration for the specified object type or exact object
Can be useful to generate a full configuration for specified object type like VirtualService or for specific like  VirtualService:vs_gslb01a_192.168.1.14_53
```
root@avitools:~# ./avi_check_config.py --config config.json --get-config VirtualService:vs_gsb01a_192.168.1.14_53
root@avitools:~# head -10 config.json_VirtualService_vs_gslb01a_192.168.1.14_53_config.json
{
    "VirtualService": [
        {
            "_avi_obj_type": "virtualservice",
            "active_standby_se_tag": "ACTIVE_STANDBY_SE_1",
            "analytics_policy": {
                "client_insights": "NO_INSIGHTS",
                "enabled": true,
                "full_client_logs": {
                    "all_headers": false,
root@avitools:~# ./avi_check_config.py --config config.json --get-config VirtualService
root@avitools:~# head -10 config.json_VirtualService__config.json
{
    "VirtualService": [
        {
            "_avi_obj_type": "virtualservice",
            "active_standby_se_tag": "ACTIVE_STANDBY_SE_1",
            "analytics_policy": {
                "client_insights": "NO_INSIGHTS",
                "enabled": true,
                "full_client_logs": {
                    "all_headers": false,
```
### Get related configuration to the specified object type or exact object
Can be useful to generate a full related configuration for specified object type like VirtualService or for specific like VirtualService:vs_gslb01a_192.168.1.14_53
```
root@avitools:~# ./avi_check_config.py --config config.json --get-related-config VirtualService
root@avitools:~# head -10 config.json_VirtualService__related_config.json
{
    "AnalyticsProfile": [
        {
            "_avi_obj_type": "analyticsprofile",
            "apdex_response_threshold": 500,
            "apdex_response_tolerated_factor": 4.0,
            "apdex_rtt_threshold": 250,
            "apdex_rtt_tolerated_factor": 4.0,
            "apdex_rum_threshold": 5000,
            "apdex_rum_tolerated_factor": 4.0,
root@avitools:~# ./avi_check_config.py --config config.json --get-related-config VirtualService:vs_gslb01a_192.168.1.14_53
root@avitools:~# head -10 config.json_VirtualService_vs_gslb01a_192.168.1.14_53_related_config.json
{
    "AnalyticsProfile": [
        {
            "_avi_obj_type": "analyticsprofile",
            "apdex_response_threshold": 500,
            "apdex_response_tolerated_factor": 4.0,
            "apdex_rtt_threshold": 250,
            "apdex_rtt_tolerated_factor": 4.0,
            "apdex_rum_threshold": 5000,
            "apdex_rum_tolerated_factor": 4.0,
```
### Check only related child objects to the specified parent object
The use case is to perform pattern check againt list of virtualservices and only related to the list of  virtualservices child objects. "Check related" functionality can allow to generate partial (in-scope) configuration that relates only to the virtualservices and perform check within the scope of provided virtualservices. For example, the list of VirtualServices has to be checked with the list of attached objects to them like Pools, AppPersistenceProfiles and SSLProfiles, however names for associated objects are not known. Instead of providing the name for every related object, by using the functionality only related/referred objects to listed VirtualServices will be checked.
```
root@avitools:~# ./avi_check_config.py --config 192.168.1.11_avi_config_20181028-184229.json --config-pattern patterns/pattern2.json --check-related-only
root@avitools:~#  ls
192.168.1.11_avi_config_20181028-184229.json_related_config_20181029-012859.json
192.168.1.11_avi_config_20181028-184229.json_missing_options_20181029-012859.json
192.168.1.11_avi_config_20181028-184229.json_matching_values_20181029-012859.json
192.168.1.11_avi_config_20181028-184229.json_mismatching_values_20181029-012859.json
```
### Get list of common referred objects across specified objects
The use case is to search common properties against provided object list of the same type.
```
root@avitools:~# ./avi_check_config.py --config 192.168.1.11_avi_config_20181028-184229.json --get-shared-objects-list VirtualService:vs_avi_check_config_autoip1,vs_avi_check_config_autoip2,vs_avi_check_config_autoip3
./192.168.1.11_avi_config_20181028-184229.json_VirtualService_shared_objects_list_20181028-213817.json
{
    "network_profile_ref": "/api/networkprofile/networkprofile-0d9604be-f955-4b0c-8d0e-cb46aedba2a5#System-TCP-Proxy",
    "analytics_profile_ref": "/api/analyticsprofile/analyticsprofile-aa642be4-f05a-41c8-94ca-4efd2ca07fce#System-Analytics-Profile",
    "cloud_ref": "/api/cloud/cloud-66b8db25-93f6-4460-a250-f5e535be1d33#vmc",
    "se_group_ref": "/api/serviceenginegroup/serviceenginegroup-9fe09483-79df-4e7c-8f2f-a73eee0c0c11#seg01a",
    "tenant_ref": "/api/tenant/admin#admin",
    "application_profile_ref": "/api/applicationprofile/applicationprofile-3b6c5370-952f-43e7-a503-faa9067e6ba3#System-HTTP",
    "virtualservice_content_rewrite:rewritable_content_ref": "/api/stringgroup/stringgroup-572aea89-44a4-4650-a833-bb53bed8fb44#System-Rewritable-Content-Types",
    "vrf_context_ref": "/api/vrfcontext/vrfcontext-ca0361bd-c1c2-4323-a296-a61f00572547#global"
}
```
### Provide list of objects leveraging provided object
The use case is to understand how specified object is used and where.
```
root@avitools:~# cat 192.168.1.11_avi_config_20181028-184229.json_Pool_referred_by_list_20181028-212509.json
{
    "HTTPPolicySet": [
        "vs_avi_check_config_192.168.3.2-vmc-HTTP-Policy-Set",
        "vs_avi_check_config_192.168.3.2-vmc-HTTP-Policy-Set"
    ],
    "VirtualService": [
        "vs_avi_check_config_autoip1"
    ]
root@avitools:~# cat 192.168.1.11_avi_config_20181028-184229.json_StringGroup_referred_by_list_20181028-12207.json
{
    "ApplicationProfile": [
        "System-Secure-HTTP",
        "System-HTTP"
    ],
    "HTTPPolicySet": [
        "vs_avi_check_config_192.168.3.2-vmc-HTTP-Policy-Set",
        "vs_avi_check_config_192.168.3.2-vmc-HTTP-Policy-Set"
    ]
```