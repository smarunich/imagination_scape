#!/usr/bin/env python
import json
from jsondiff import diff
import re
import argparse
import collections

__version__ = '0.1.2'
__credits__ = 'Avi Networks PS'

parser = argparse.ArgumentParser(
    description='avi_check_config - avi configuration validation tool')
parser.add_argument('--config', action='store',
                    dest='CONFIG', help='Name of Avi JSON configuration file')
parser.add_argument('--config-pattern', action='store',
                    dest='CONFIG_PATTERN', help='Name of Avi JSON configuration pattern file')
parser.add_argument('--check-related-only', action='store_true',
                    dest='CHECK_RELATED_ONLY', help='*EXPERIMENTAL* Truncate provided Avi JSON configuration file to related objects defined within pattern, i.e. allows to search against related objects only. In the background, generates only in scope configuration based on mentioned objects within pattern')
parser.add_argument('--output', action='store',
                    dest='OUTPUT_FOLDER', default='.', help='Folder path for output files to be created in')
parser.add_argument('--get-object-list', action='store',
                    dest='GET_OBJECT_LIST', help='Type and name of objects to be listed. For example: VirtualService')
parser.add_argument('--get-shared-objects-list', action='store',
                    dest='GET_SHARED_OBJECTS_LIST', help='Object type and list of names to provide. For example: VirtualService:vs1,vs2,vs3')
parser.add_argument('--get-config', action='store',
                    dest='GET_CONFIG', help='Type and name of object to be checked. For example: VirtualService:vs1')
parser.add_argument('--get-related-config', action='store',
                    dest='GET_RELATED_CONFIG', help='*EXPERIMENTAL* Type and name of object to be checked. For example: VirtualService:vs1')
flags = parser.parse_args()


def json_to_file(output,file_path):
    with open(file_path, "w") as file_path:
        json.dump(output, file_path, sort_keys=True, indent=4)

def universal_cmp(a, b):
    if type(a) == str and type(b) == str:
        if re.search(a, b):
            return True
    if type(a) == unicode and type(b) == unicode:
        if re.search(a.decode('utf-8'), b.decode('utf-8')):
            return True
    elif type(a) == int and type(b) == int:
        if re.search(str(a), str(b)):
            return True
    else:
        if a == b:
            return True
        else:
            return diff(a, b, syntax='compact')

''' Dictionary update function '''
def update(d, u):
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

class avi_config():
    _SKIP_TYPE = [
        "META"
    ]
    _SKIP_KEY = [
        "name"
    ]
    def __init__(self,file_path, file_type, obj_class):
        self._json2object(file_path, file_type, obj_class)

    def _json2object(self,file_path, file_type, obj_class):
        with open(file_path) as file_name:
            config_file = json.load(file_name)
        if file_type == "config":
            _lowercase_to_uppercase_config_obj_name = {}
        for obj_type in config_file.keys():
            if obj_type not in self._SKIP_TYPE:
                self.__dict__[obj_type] = {}
                for obj in config_file[obj_type]:
                    obj = type(str(obj_type), (obj_class,), obj)
                    self.__dict__[obj_type][obj] = obj
                    if file_type == "config":
                        try:
                            attr_name = obj()['_avi_obj_type']
                            _lowercase_to_uppercase_config_obj_name[attr_name] = obj_type
                            setattr(obj_class, '_lowercase_to_uppercase_config_obj_name',
                                    _lowercase_to_uppercase_config_obj_name)
                        except:
                            pass

    # Function to print list of objects and object names
    # {u'VirtualService': [[u'vs_192.168.1.15', u'vs_dns01a_192.168.1.16_53']], u'VrfContext': [u'global'], u'ServiceEngineGroup': [u'gslb'], u'SSLProfile': [], u'Pool': [], u'ApplicationPersistenceProfile': []}
    def _get_objects_dict(self):
        obj_dict = {}
        for obj_type in self._keys():
            obj_dict[obj_type] = []
            for config_obj in self[obj_type]:
                try:
                    obj_name = config_obj.name
                    obj_dict[obj_type].append(obj_name)
                except:
                    pass
        return obj_dict

    # Function to generate configuration for provided object
    def _get_config(self, obj_type, obj_name=''):
        config = {}
        if obj_type in self.__dict__.keys():
            for config_obj in self.__dict__[obj_type]:
                if config_obj().name == obj_name or obj_name == '':
                    config[obj_type] = [config_obj().__dict__]
        return config

    # Function to provide list of shared properties i.e. shared objects for provided list of objects
    def _get_shared_objects_list(self, obj_type, obj_list):
        obj_name_list = obj_list.split(',')
        config_refs = {}
        if obj_type in self.__dict__.keys():
            for config_obj in self.__dict__[obj_type]:
                for obj_name in obj_name_list:
                    if config_obj().name == obj_name:
                        config_refs[obj_name] =  config_obj()._refs()
        # Perform compare between first and next object within list of objects for shared properties, i.e. for identical references, intermediate results of shared_items save to obj0_refs for further comparison in the list with next object
        obj0_refs = config_refs[obj_name_list[0]]
        for name in obj_name_list[1:]:
            obj1_refs = config_refs[name]
            shared_refs = {k: obj0_refs[k] for k in obj0_refs if k in obj1_refs and obj0_refs[k] == obj1_refs[k]}
            obj0_refs = shared_refs
        return shared_refs

    # Function to generate configuration related to provided object
    def _get_related_config(self, obj_type, obj_name=''):
        related_config = {}
        if obj_type in self.__dict__.keys():
            obj_related_config = {}
            for config_obj in self.__dict__[obj_type]:
                if config_obj().name == obj_name:
                    for ref in config_obj()._refs().values():
                        for ref_config_obj in self.__dict__[config_obj()._lowercase_to_uppercase_config_obj_name[ref['_config_obj_type']]]:
                            if ref_config_obj().name == ref['name']:
                                obj_related_config[ref_config_obj(
                                )._lowercase_to_uppercase_config_obj_name[ref['_config_obj_type']]] = []
                            if ref_config_obj().name == ref['name']:
                                obj_related_config[ref_config_obj(
                                )._lowercase_to_uppercase_config_obj_name[ref['_config_obj_type']]].append(ref_config_obj().__dict__)
                if obj_name == '':
                    for ref in config_obj()._refs().values():
                        for ref_config_obj in self.__dict__[config_obj()._lowercase_to_uppercase_config_obj_name[ref['_config_obj_type']]]:
                            obj_related_config[ref_config_obj(
                            )._lowercase_to_uppercase_config_obj_name[ref['_config_obj_type']]] = []
                        for ref_config_obj in self.__dict__[config_obj()._lowercase_to_uppercase_config_obj_name[ref['_config_obj_type']]]:
                            obj_related_config[ref_config_obj(
                            )._lowercase_to_uppercase_config_obj_name[ref['_config_obj_type']]].append(ref_config_obj().__dict__)
            related_config.update(obj_related_config)
        return related_config

    # Function to truncate config file, i.e. generate related configuration based on provided pattern to limit search boundaries
    def _truncate_config_based_on_pattern(self, pattern):
        truncated_config = {}
        obj_dict = pattern._get_objects_dict()
        for obj_type in obj_dict.keys():
            truncated_config[obj_type] = []
            if obj_dict[obj_type] == []:
                truncated_config.update(self._get_config(obj_type))
                try:
                    truncated_config.update(self._get_related_config(obj_type))
                except:
                    pass
            else:
                for obj_name in obj_dict[obj_type]:
                    truncated_config.update(self._get_config(obj_type, obj_name))
                    truncated_config.update(self._get_related_config(obj_type, obj_name))
        return truncated_config

    def _pattern_match(self, pattern):
        matching_values = {}
        mismatching_values = {}
        missing_options = {}
        report_matching_values = {}
        report_missing_options = {}
        report_mismatching_values = {}
        report = {}
        # Extract keys from pattern (keys will be VirtualService, Pool, etc) - pattern_obj_type
        for pattern_obj_type in pattern._keys():
            # Only interact with object types of interest (like VirtualService, Pool, etc) defined in pattern file
            matching_values[pattern_obj_type] = {}
            mismatching_values[pattern_obj_type] = {}
            missing_options[pattern_obj_type] = {}
            # Extract config objects of interest (based on pattert_obj_type)
            if pattern_obj_type in self._keys():
                for config_obj in self[pattern_obj_type]:
                    # Place holders for match and miss objects, to be filled later
                    matching_values[pattern_obj_type][config_obj.name] = {}
                    mismatching_values[pattern_obj_type][config_obj.name] = {}
                    missing_options[pattern_obj_type][config_obj.name] = []
                    # Extract pattern objects of interest and compare with config objects of interest
                    for pattern_obj in pattern[pattern_obj_type]:
                        try:
                            pattern_obj_name = pattern_obj.name
                        except:
                            pattern_obj_name = [config_obj.name]
                        if config_obj.name in pattern_obj_name:
                            # verifying if keys are part of existing configuration, if not report and exclude missing pattern keys from compare function
                            if set(pattern_obj()._keys()).issubset(set(config_obj()._keys())):
                                pattern_obj_keys = pattern_obj()._keys()
                            else:
                                missing_options[pattern_obj_type][config_obj.name] += set(pattern_obj()._keys()) - set(
                                    config_obj()._keys())
                                pattern_obj_keys = set(pattern_obj()._keys()) - \
                                    set(missing_options[pattern_obj_type]
                                        [config_obj.name])
                            # perform compare if pattern keys exist
                            if pattern_obj_keys:
                                # Extract pattern object keys for comparison
                                for pattern_obj_key in pattern_obj_keys:
                                    if pattern_obj_key not in self._SKIP_KEY:
                                        # Extract value of pattern_obj and value of config_obj based on pattern_obj_key for comparison
                                        if universal_cmp(getattr(pattern_obj, pattern_obj_key), getattr(config_obj, pattern_obj_key)) == True:
                                            matching_values[pattern_obj_type][config_obj.name][pattern_obj_key] = getattr(
                                                config_obj, pattern_obj_key)
                                        elif universal_cmp(getattr(pattern_obj, pattern_obj_key), getattr(config_obj, pattern_obj_key)):
                                            mismatching_values[pattern_obj_type][config_obj.name][pattern_obj_key] = universal_cmp(
                                                getattr(pattern_obj, pattern_obj_key), getattr(config_obj, pattern_obj_key))
                                        else:
                                            mismatching_values[pattern_obj_type][config_obj.name][pattern_obj_key] = getattr(
                                                config_obj, pattern_obj_key)
                    missing_options[pattern_obj_type][config_obj.name] = list(set(
                        missing_options[pattern_obj_type][config_obj.name]))
                    # clean empty keys within dicts
                    if matching_values[pattern_obj_type][config_obj.name] == {}:
                        del matching_values[pattern_obj_type][config_obj.name]
                    if mismatching_values[pattern_obj_type][config_obj.name] == {}:
                        del mismatching_values[pattern_obj_type][config_obj.name]
                    if missing_options[pattern_obj_type][config_obj.name] == []:
                        del missing_options[pattern_obj_type][config_obj.name]
                report_missing_options[pattern_obj_type] = missing_options[pattern_obj_type]
                report_mismatching_values[pattern_obj_type] = mismatching_values[pattern_obj_type]
                report_matching_values[pattern_obj_type] = matching_values[pattern_obj_type]
        report = {"missing_options": report_missing_options,
                "mismatching_values": report_mismatching_values, "matching_values": report_matching_values}
        return report
    def __getitem__(self, key):
        return self.__dict__[key]
    def __repr__(self):
        return repr(self.__dict__)
    def _keys(self):
        return self.__dict__.keys()
    def _values(self):
        return self.__dict__.values


class avi_object(object):
    def __init__(self):
        attrs = filter(lambda x: x.startswith("_") == False, dir(self))
        for attr in attrs:
            # avi object properties transformed to class attributes one to one
            self.__dict__[attr] = getattr(self, attr)
            # adding internal custom property to handle class lookup (meaning identify object type)
            # placeholder for __type__
            if 'url' == attr:
                self.__dict__['_avi_obj_type'] = (re.search(r"(\/api\/)(\w+)", self.__dict__[attr])).group(2)
            if '_ref' in attr:
                # /api/pool/?tenant=admin&name=vs_192.168.3.11-local_pool&cloud=vmc
                ref_url = getattr(self, attr)
                if type(ref_url) is list:
                    ref_url = ref_url[0]
                self.__dict__[attr] = { u'url': ref_url }
                if 'tenant=' in ref_url:
                    tenant = (re.search(r"tenant=([^&]*)", ref_url)).group(1)
                    self.__dict__[attr][u'tenant'] = tenant
                if 'cloud=' in ref_url:
                    cloud = (re.search(r"cloud=([^&]*)", ref_url)).group(1)
                    self.__dict__[attr][u'cloud'] = cloud
                if 'name=' in ref_url:
                    name = (re.search(r"name=([^&]*)", ref_url)).group(1)
                    self.__dict__[attr][u'name'] = name
                try:
                    self.__dict__[attr][u'_config_obj_type'] = (
                        re.search(r"(\/api\/)(\w+)", ref_url)).group(2)
                except:
                    pass
    def __getitem__(self, key):
        return self.__dict__[key]
    def __repr__(self):
        return repr(self.__dict__)
    def _keys(self):
        return self.__dict__.keys()
    def _values(self):
        return self.__dict__.values
    def _refs (self):
        refs = {}
        for key in self._keys():
            if re.search('ref',key):
                refs[key] = self.__dict__[key]
        return refs

if __name__ == "__main__":
    if flags.CONFIG:
        # Load Avi JSON configuration file
        avi_config_from_file = avi_config(
                        flags.CONFIG, "config", avi_object)
        if flags.CONFIG_PATTERN and flags.OUTPUT_FOLDER:
            # Load Avi JSON pattern file
            avi_config_pattern_from_file = avi_config(
                flags.CONFIG_PATTERN, "pattern", avi_object)
            if flags.CHECK_RELATED_ONLY:
                related_config = avi_config_from_file._truncate_config_based_on_pattern(
                    avi_config_pattern_from_file)
                file_path = flags.OUTPUT_FOLDER+'/'+flags.CONFIG + \
                    '_related_config.json'
                json_to_file(related_config, file_path)
                related_avi_config_from_file = avi_config(
                        file_path, "config", avi_object)
                # perform pattern comparison
                pattern_match_report = related_avi_config_from_file._pattern_match(
                avi_config_pattern_from_file)
            else:
                # perform pattern comparison
                pattern_match_report = avi_config_from_file._pattern_match(avi_config_pattern_from_file)
            for key in pattern_match_report:
                file_path = flags.OUTPUT_FOLDER+'/'+flags.CONFIG+'_'+key+'.json'
                json_to_file(pattern_match_report[key], file_path)
        if flags.OUTPUT_FOLDER and flags.GET_CONFIG:
            related_config_options = flags.GET_CONFIG.split(':')
            obj_type = related_config_options[0]
            try:
                obj_name = related_config_options[1]
            except:
                obj_name = ''
            file_path = flags.OUTPUT_FOLDER+'/'+flags.CONFIG+'_'+obj_type+'_'+obj_name+'_config.json'
            json_to_file(avi_config_from_file._get_config(
                    obj_type, obj_name), file_path)
        if flags.OUTPUT_FOLDER and flags.GET_RELATED_CONFIG:
            # For example: flags.GET_RELATED_CONFIG = "VirtualService:vs1"
            related_config_options = flags.GET_RELATED_CONFIG.split(':')
            obj_type = related_config_options[0]
            try:
                obj_name = related_config_options[1]
            except:
                obj_name = ''
            file_path = flags.OUTPUT_FOLDER+'/'+flags.CONFIG + '_'+obj_type+'_'+obj_name+'_related_config.json'
            json_to_file(avi_config_from_file._get_related_config(
                obj_type, obj_name), file_path)
        if flags.GET_OBJECT_LIST:
            obj_type = flags.GET_OBJECT_LIST
            file_path = flags.OUTPUT_FOLDER+'/'+flags.CONFIG + \
                '_'+obj_type+'_object_list.json'
            json_to_file(avi_config_from_file._get_objects_dict()[
                flags.GET_OBJECT_LIST], file_path)
        if flags.GET_SHARED_OBJECTS_LIST:
            #  For example: flags.GET_SHARED_OBJECTS_LIST = "VirtualService:vs1,vs2,vs3"
            get_shared_objects_list_options = flags.GET_SHARED_OBJECTS_LIST.split(':')
            obj_type = get_shared_objects_list_options[0]
            obj_list = get_shared_objects_list_options[1]
            file_path = flags.OUTPUT_FOLDER+'/'+flags.CONFIG + \
                '_'+obj_type+'_shared_objects_list.json'
            json_to_file(avi_config_from_file._get_shared_objects_list(
                obj_type,obj_list), file_path)
