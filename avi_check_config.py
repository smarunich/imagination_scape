#!/usr/bin/env python
import json
import re
import pprint

SKIP_TYPE = [
    "META",
]

class avi_object(object):
    def _get_config(self):
        _get_config = {}
        attrs = filter(lambda x: x.startswith("_") == False, dir(self))
        for attr in attrs:
            _get_config[attr] = getattr(self, attr)
        return _get_config

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
    match_objs = {}
    miss_objs = {}
    miss_keys = {}
    # Extract keys from pattern (keys will be VirtualService, Pool, etc) - patter_obj_type
    for pattern_obj_type in pattern.keys():
        # Only interact with object types of interest (like VirtualService, Pool, etc) defined in pattern file
        if pattern_obj_type in config.keys():
            # Extract config objects of interest (based on pattert_obj_type)
            for config_obj in config[pattern_obj_type]:
                # Place holders for match and miss objects, to be filled later
                match_objs[config_obj.name] = {}
                miss_objs[config_obj.name] = {}
                miss_keys[config_obj.name] = []
                # Extract pattern objects of interest and compare with config objects of interest
                for pattern_obj in pattern[pattern_obj_type]:
                    # verifying if keys are part of existing configuration, if not report and exclude missing pattern keys from compare function
                    if set(pattern_obj()._get_config().keys()).issubset(set(config_obj()._get_config().keys())):
                        pattern_obj_keys = pattern_obj()._get_config().keys()
                    else:
                        miss_keys[config_obj.name] += set(pattern_obj()._get_config().keys()) - set(
                            config_obj()._get_config().keys())
                        pattern_obj_keys = set(pattern_obj()._get_config().keys()) - \
                            set(miss_keys[config_obj.name])
                    # perform compare if pattern keys exist
                    if pattern_obj_keys:
                        # Extract pattern object keys for comparison
                        for pattern_obj_key in pattern_obj_keys:
                            # Extract value of pattern_obj and value of config_obj based on pattern_obj_key for comparison
                            if universal_cmp(getattr(pattern_obj, pattern_obj_key), getattr(config_obj, pattern_obj_key)):
                                match_objs[config_obj.name][pattern_obj_key] = getattr(config_obj, pattern_obj_key)
                            else:
                                miss_objs[config_obj.name][pattern_obj_key] = getattr(config_obj, pattern_obj_key)

                miss_keys[config_obj.name] = set(miss_keys[config_obj.name])
                if match_objs[config_obj.name] == {}:
                    del match_objs[config_obj.name]
                if miss_objs[config_obj.name] == {}:
                    del miss_objs[config_obj.name]
                if miss_keys[config_obj.name] == set([]):
                    del miss_keys[config_obj.name]
            print("MISS OPTIONS")
            pprint.pprint(miss_keys)
            print("MISS OBJECTS")
            pprint.pprint(miss_objs)
            print("MATCH OBJECTS")
            pprint.pprint(match_objs)


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
