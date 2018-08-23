#!/usr/bin/env python
import json
import re
import pprint

SKIP_TYPE = [
    "META",
    "_url_to_obj_type_lookup_table"
]

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

def json2object(file_path, file_type, obj_class ):
    obj_dict = {}
    with open(file_path) as file_name:
        config_file = json.load(file_name)
    if file_type == "config":
        _lowercase_to_uppercase_config_obj_name = {}
    for obj_type in config_file.keys():
        if obj_type not in SKIP_TYPE:
            obj_dict[obj_type] = {}
            for obj in config_file[obj_type]:
                obj = type(str(obj_type), (obj_class,), obj)
                obj_dict[obj_type][obj] = obj
                if file_type == "config":
                    try:
                        attr_name = obj()['_avi_obj_type']
                        _lowercase_to_uppercase_config_obj_name[attr_name] = obj_type
                        setattr(obj_class, '_lowercase_to_uppercase_config_obj_name', _lowercase_to_uppercase_config_obj_name)
                    except:
                        pass
    return obj_dict



def universal_cmp(a,b):
    if type(a) == str and type(b) == str:
        if re.search(a,b):
            return True
    if type(a) == unicode and type(b) == unicode:
        if re.search(a.decode('utf-8'),b.decode('utf-8')):
            return True
    elif type(a) == int and type(b) == int:
        if re.search(str(a), str(b)):
            return True
    elif type(a) == list and type(b) ==list:
        if a == b:
            return True
    elif type(a) == dict and type(b) == dict:
        mismatched_nested_keys = {k: a[k] for k in a if k in b and a[k] != b[k]}
        if mismatched_nested_keys == {}:
            return True
        else:
            return mismatched_nested_keys
    else:
        if a == b:
            return True


def _list_related_objects(config, obj_type, obj_name):
    related_config = {}
    if obj_type in config.keys():
        for config_obj in config[obj_type]:
            if config_obj().name == obj_name:
                for ref in config_obj()._refs().values():
                    for ref_config_obj in config[config_obj()._lowercase_to_uppercase_config_obj_name[ref['_config_obj_type']]]:
                        if ref_config_obj().name == ref['name']:
                            related_config[ref_config_obj(
                            )._lowercase_to_uppercase_config_obj_name[ref['_config_obj_type']]] = [ref_config_obj()]
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(related_config)
    return related_config
    #print json.dumps(related_config, indent=2, sort_keys=True)

# __cmp__, config becomes self
#config.cmp(pattern)

def pattern_match(config,pattern):
    matching_values = {}
    missing_values = {}
    missing_keys = {}
    report_matching_values = {}
    report_missing_keys = {}
    report_missing_values = {}
    report = {}
    # Extract keys from pattern (keys will be VirtualService, Pool, etc) - pattern_obj_type
    for pattern_obj_type in pattern.keys():
        # Only interact with object types of interest (like VirtualService, Pool, etc) defined in pattern file
        matching_values[pattern_obj_type] = {}
        missing_values[pattern_obj_type] = {}
        missing_keys[pattern_obj_type] = {}
        if pattern_obj_type in config.keys():
            # Extract config objects of interest (based on pattert_obj_type)
            for config_obj in config[pattern_obj_type]:
                # Place holders for match and miss objects, to be filled later
                matching_values[pattern_obj_type][config_obj.name] = {}
                missing_values[pattern_obj_type][config_obj.name] = {}
                missing_keys[pattern_obj_type][config_obj.name] = []
                # Extract pattern objects of interest and compare with config objects of interest
                for pattern_obj in pattern[pattern_obj_type]:
                    # verifying if keys are part of existing configuration, if not report and exclude missing pattern keys from compare function
                    if set(pattern_obj()._keys()).issubset(set(config_obj()._keys())):
                        pattern_obj_keys = pattern_obj()._keys()
                    else:
                        missing_keys[pattern_obj_type][config_obj.name] += set(pattern_obj()._keys()) - set(
                            config_obj()._keys())
                        pattern_obj_keys = set(pattern_obj()._keys()) - \
                            set(missing_keys[pattern_obj_type][config_obj.name])
                    # perform compare if pattern keys exist
                    if pattern_obj_keys:
                        # Extract pattern object keys for comparison
                        for pattern_obj_key in pattern_obj_keys:
                            # Extract value of pattern_obj and value of config_obj based on pattern_obj_key for comparison
                            if universal_cmp(getattr(pattern_obj, pattern_obj_key), getattr(config_obj, pattern_obj_key)) == True:
                                matching_values[pattern_obj_type][config_obj.name][pattern_obj_key] = getattr(
                                    config_obj, pattern_obj_key)
                            elif universal_cmp(getattr(pattern_obj, pattern_obj_key), getattr(config_obj, pattern_obj_key)) :
                                missing_values[pattern_obj_type][config_obj.name][pattern_obj_key] = universal_cmp(
                                    getattr(pattern_obj, pattern_obj_key), getattr(config_obj, pattern_obj_key))
                            else:
                                missing_values[pattern_obj_type][config_obj.name][pattern_obj_key] = getattr(
                                    config_obj, pattern_obj_key)
                missing_keys[pattern_obj_type][config_obj.name] = set(
                    missing_keys[pattern_obj_type][config_obj.name])
                # clean empty keys within dicts
                if matching_values[pattern_obj_type][config_obj.name] == {}:
                    del matching_values[pattern_obj_type][config_obj.name]
                if missing_values[pattern_obj_type][config_obj.name] == {}:
                    del missing_values[pattern_obj_type][config_obj.name]
                if missing_keys[pattern_obj_type][config_obj.name] == set([]):
                    del missing_keys[pattern_obj_type][config_obj.name]
            print("MISSING OPTIONS")
            pprint.pprint(pattern_obj_type)
            pprint.pprint(missing_keys[pattern_obj_type])
            report_missing_keys[pattern_obj_type] = missing_keys[pattern_obj_type]
            print("MISSING OBJECTS")
            pprint.pprint(pattern_obj_type)
            #pprint.pprint(missing_values[pattern_obj_type])
            print json.dumps(missing_values[pattern_obj_type], indent=2, sort_keys=True)
            report_missing_values[pattern_obj_type] = missing_values[pattern_obj_type]
            print("MATCHING OBJECTS")
            pprint.pprint(pattern_obj_type)
            #pprint.pprint(matching_values[pattern_obj_type])
            print json.dumps(matching_values[pattern_obj_type], indent=2, sort_keys=True)
            report_matching_values[pattern_obj_type] = matching_values[pattern_obj_type]
    report = {"missing_keys": report_missing_keys, "missing_values": report_missing_values, "matching_values": report_matching_values }
    #return report


config_from_backup = json2object('config.json', "config", avi_object)
# pattern1: empty pattern
pattern1_from_file = json2object('pattern1.json', "pattern", avi_object)
# pattern2: key match only
pattern2_from_file = json2object('pattern2.json', "pattern", avi_object)
# pattern3: value match only
pattern3_from_file = json2object('pattern3.json', "pattern", avi_object)
# pattern4: no match
pattern4_from_file = json2object('pattern4.json', "pattern", avi_object)
# pattern5: full match on key, partial match on values
pattern5_from_file = json2object('pattern5.json', "pattern", avi_object)
# pattern6: full match on key, partial match on values, includes lists and dicts in lists
pattern6_from_file = json2object('pattern6.json', "pattern", avi_object)
# pattern7: full match on key, partial match on values, includes lists and dicts in lists
pattern7_from_file = json2object('pattern7.json', "pattern", avi_object)

# get all configuration related to the object
_list_related_objects(config_from_backup, 'VirtualService', 'vs_192.168.3.11')

#print("GOLDEN TEMPLATE PROJECT")
#pattern_match(config_from_backup, config_from_backup)
print("PATTERN 1: key and value match ")
pattern_match(config_from_backup, pattern1_from_file)
print("PATTERN 2: key match only")
pattern_match(config_from_backup, pattern2_from_file)
print("PATTERN 3: value match only")
pattern_match(config_from_backup, pattern3_from_file)
print("PATTERN 4: no match")
pattern_match(config_from_backup, pattern4_from_file)
print("PATTERN 5: partial key and value match")
pattern_match(config_from_backup, pattern5_from_file)
print("PATTERN 6: full match on key, partial match on values, includes lists and dicts in lists")
pattern_match(config_from_backup, pattern6_from_file)
print("PATTERN 7: full match on key, partial match on values, includes lists and dicts in lists")
pattern_match(config_from_backup, pattern7_from_file)
