#!/usr/bin/env python
import json
import re
import pprint

SKIP_TYPE = [
    "META",
]

class avi_object(object):
    def __init__(self):
        attrs = filter(lambda x: x.startswith("_") == False, dir(self))
        for attr in attrs:
            self.__dict__[attr] = getattr(self, attr)
    def __getitem__(self, key):
        return self.__dict__[key]
    def __repr__(self):
        return repr(self.__dict__)
    def _keys(self):
        return self.__dict__.keys()
    def _values(self):
        return self.__dict__.values()

def json2object(file_path):
    obj_dict = {}
    with open(file_path) as file_name:
        config_file = json.load(file_name)

    for obj_type in config_file.keys():
        if obj_type not in SKIP_TYPE:
            obj_dict[obj_type] = {}
            for obj in config_file[obj_type]:
                obj = type(str(obj_type), (avi_object,), obj)
                obj_dict[obj_type][obj] = obj
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
        if sorted(a) == sorted(b):
            return True
    elif type(a) == dict and type(b) == dict:
        shared_items = {k: a[k] for k in a if k in b and a[k] != b[k]}
        print "test",shared_items
        if sorted(a) == sorted(b):
            return True
    else:
        if a == b:
            return True


config_from_backup = json2object('config.json')

# pattern1: key and value match
pattern1_from_file = json2object('pattern1.json')
# pattern2: key match only
pattern2_from_file = json2object('pattern2.json')
# pattern3: value match only
pattern3_from_file = json2object('pattern3.json')
# pattern4: no match
pattern4_from_file = json2object('pattern4.json')
# pattern5: full match on key, partial match on values
pattern5_from_file = json2object('pattern5.json')
# pattern6: full match on key, partial match on values, includes lists and dicts in lists
pattern6_from_file = json2object('pattern6.json')
# pattern7: full match on key, partial match on values, includes lists and dicts in lists
pattern7_from_file = json2object('pattern7.json')


# __cmp__, config becomes self
#config.cmp(pattern)

def pattern_match(config,pattern):
    report = {}
    report_matching_values = {}
    report_missing_keys = {}
    report_missing_values = {}
    matching_values = {}
    missing_values = {}
    missing_keys = {}
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
                            if universal_cmp(getattr(pattern_obj, pattern_obj_key), getattr(config_obj, pattern_obj_key)):
                                matching_values[pattern_obj_type][config_obj.name][pattern_obj_key] = getattr(
                                    config_obj, pattern_obj_key)
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
            pprint.pprint(missing_values[pattern_obj_type])
            report_missing_values[pattern_obj_type] = missing_values[pattern_obj_type]
            print("MATCHING OBJECTS")
            pprint.pprint(pattern_obj_type)
            pprint.pprint(matching_values[pattern_obj_type])
            report_matching_values[pattern_obj_type] = matching_values[pattern_obj_type]
    report = {"missing_keys": report_missing_keys, "missing_values": report_missing_values, "matching_values": report_matching_values }
    #return report

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
