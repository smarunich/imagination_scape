#!/usr/bin/env python
import json
import pprint

SKIP_TYPE = [
    "META",
]

class avi_object(object):
    def _get_config(self):
        get_config = {}
        attrs = filter(lambda x: x.startswith("_") == False, dir(self))
        for attr in attrs:
            get_config[attr] = getattr(self,attr)
        return get_config


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
        if a == b:
            return True
    if type(a) == unicode and type(b) == unicode:
        if a.decode('utf-8') == b.decode('utf-8'):
            return True
    elif type(a) == int and type(b) == int:
        if a == b:
            return True
    elif type(a) == int and type(b) == int:
        if a == b:
            return True
    elif type(a) == list and type(b) ==list:
        return [i for i, j in zip(a, b) if i != j]


print(universal_cmp('test','test'))
print(universal_cmp(1, 1))
print(universal_cmp([1,2],[1,2]))

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

def pattern_match(config,pattern):
    match_obj = {}
    miss_obj = {}
    # Extract keys from pattern (keys will be VirtualService, Pool, etc) - patter_obj_type
    for pattern_obj_type in pattern.keys():
        # Only interact with object types of interest (like VirtualService, Pool, etc) defined in pattern file
        if pattern_obj_type in config.keys():
            # Extract config objects of interest (based on pattert_obj_type)
            for config_obj in config[pattern_obj_type]:
                # Place holders for match and miss objects, to be filled later
                match_obj[config_obj.name] = []
                miss_obj[config_obj.name] = []
                # Extract pattern objects of interest and compare with config objects of interest
                for pattern_obj in pattern[pattern_obj_type]:
                    # Perform comparison only if all pattern dict keys are part of config object dict keys
                    if set(pattern_obj()._get_config().keys()).issubset(set(config_obj()._get_config().keys())):
                        # Extract pattern object keys for comparison
                        for pattern_obj_key in pattern_obj()._get_config().keys():
                            # Extract value of pattern_obj and value of config_obj based on pattern_obj_key for comparison
                            if universal_cmp(getattr(pattern_obj, pattern_obj_key), getattr(config_obj, pattern_obj_key)):
                                match_obj[config_obj.name] += pattern_obj_key, getattr(pattern_obj, pattern_obj_key)
                            else:
                                miss_obj[config_obj.name] += pattern_obj_key, getattr(
                                    config_obj, pattern_obj_key)
                    #else if pattern key is missing from configuraion file
                if match_obj[config_obj.name] == []:
                    del match_obj[config_obj.name]
                if miss_obj[config_obj.name] == []:
                    del miss_obj[config_obj.name]
            print("MISS")
            pprint.pprint(miss_obj)
            print("MATCH")
            pprint.pprint(match_obj)


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
