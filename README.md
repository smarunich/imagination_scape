# avi_check_config - avi configuration validation tool
## Description
*avi_check_config* is built to address the use cases below:
1. Ease configuration validation for migration needs
2. Validate configuration against known best practices
3. Perform scoped queries and visualization to better understand deployed configuration
```bash
root@avitools:~# ./avi_check_config.py -h
usage: avi_check_config.py [-h] [--config CONFIG]
                           [--config-pattern CONFIG_PATTERN]
                           [--check-related-only] [--output OUTPUT_FOLDER]
                           [--get-object-list GET_OBJECT_LIST]
                           [--get-config GET_CONFIG]
                           [--get-related-config GET_RELATED_CONFIG]

avi_check_config - avi configuration validation tool

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG       Name of Avi JSON configuration file
  --config-pattern CONFIG_PATTERN
                        Name of Avi JSON configuration pattern file
  --check-related-only  *EXPERIMENTAL* Truncate provided Avi JSON
                        configuration file to related objects defined within
                        pattern, i.e. allows to search against related objects
                        only. In the background, generates only in scope
                        configuration based on mentioned objects within
                        pattern
  --output OUTPUT_FOLDER
                        Folder path for output files to be created in
  --get-object-list GET_OBJECT_LIST
                        Type and name of objects to be listed. For example:
                        VirtualService
  --get-config GET_CONFIG
                        Type and name of object to be checked. For example:
                        VirtualService:vs1
  --get-related-config GET_RELATED_CONFIG
                        *EXPERIMENTAL* Type and name of object to be checked.
                        For example: VirtualService:vs1
```
## HowTo
### Configuration JSON file and Configuration Pattern JSON file
Tool is designed to use offline backup of configuration as not necessary access to controller is always available or migration tool generated JSON configuration file. To obtain a configuration backup from controller:
```bash
GET https://[CONTROLLER-IP]/api/configuration/export?full_system=true
```
Pattern file is defined using the same format as Configuration file with few exceptions:
* name field is used to supply list of target objects to be searched, if name field is not specified all objects of the specified time are checked.
* non-nested fields other than name within pattern are used by re.search(a, b) function, meaning exact or partial or pyregex format can be used to search.
* for nested fields jsondiff library is utilized.
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
### (IN DEVELOPMENT) Check related configuration only
For example, the list of VirtualServices has to be checked with the list of attacheds objects to them like Pools, AppPersistenceProfiles and SSLProfiles, however names for associated objects are not know. "Check related" functionality can allow to generate partial (in-scope) configuration that relates only to the virtualservices and perform check within it, instead of checking every SSLProfile or Pool that is not associated with listed VirtualServices.

