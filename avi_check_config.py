#!/usr/bin/env python
import json
from jsondiff import diff
import re
import pprint
import argparse

__version__ = '0.1.1'

parser = argparse.ArgumentParser(
    description='avi_check_config - configuration validation and differ tool')
parser.add_argument('--config', action='store',
                    dest='CONFIG', help='Avi JSON configuration file')
parser.add_argument('--config-pattern', action='store',
                    dest='CONFIGPATTERN', help='Avi JSON configuration pattern')
parser.add_argument('--output', action='store',
                    dest='OUTPUTFOLDER', help='Output report folder')
flags = parser.parse_args()


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

    def _list_related_objects(self,obj_type, obj_name):
        related_config = {}
        if obj_type in self.__dict__.keys():
            for config_obj in self.__dict__[obj_type]:
                if config_obj().name == obj_name:
                    for ref in config_obj()._refs().values():
                        for ref_config_obj in self.__dict__[config_obj()._lowercase_to_uppercase_config_obj_name[ref['_config_obj_type']]]:
                            if ref_config_obj().name == ref['name']:
                                related_config[ref_config_obj(
                                )._lowercase_to_uppercase_config_obj_name[ref['_config_obj_type']]] = [ref_config_obj()]
        #pprint.pprint(related_config)
        #print json.dumps(related_config, indent=2, sort_keys=True)
        return related_config

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
        if flags.CONFIGPATTERN:
            avi_config_from_file = avi_config(
                flags.CONFIG, "config", avi_object)
            avi_config_pattern_from_file = avi_config(
                flags.CONFIGPATTERN, "pattern", avi_object)
            pattern_match_report = avi_config_from_file._pattern_match(avi_config_pattern_from_file)
            avi_config_from_file._list_related_objects(
                'VirtualService', 'vs_192.168.3.11')
        if flags.OUTPUTFOLDER:
            for key in pattern_match_report:
                file_path = flags.OUTPUTFOLDER+'/'+flags.CONFIG+'_'+key
                with open(file_path, "w") as report_file:
                    json.dump(
                        pattern_match_report[key], report_file, sort_keys=True, indent=4)


'''
    # get all configuration related to the object
    config_from_backup._list_related_objects('VirtualService', 'vs_192.168.3.11')
'''
