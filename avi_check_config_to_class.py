#!/usr/bin/env python
import json
import re
import pprint

SKIP_TYPE = [
    "META",
]

class avi_object(object):
    _full_match_exists = False
    '''
    def __repr__(self):
        #self.__dict__ = {}
        attrs = filter(lambda x: x.startswith("_") == False, dir(self))
        for attr in attrs:
            self.__dict__[attr] = getattr(self, attr)
        return self.__dict__
    '''
    def _get_config(self):
        _get_config = {}
        attrs = filter(lambda x: x.startswith("_") == False, dir(self))
        for attr in attrs:
            _get_config[attr] = getattr(self, attr)
        return _get_config
    def _pattern_match(self, pattern):
        match_obj = {}
        miss_obj = {}
        miss_options = []
        # Extract keys from pattern (keys will be VirtualService, Pool, etc) - patter_obj_type
        for pattern_obj_type in pattern.keys():
            # Only interact with object types of interest (like VirtualService, Pool, etc) defined in pattern file
            if pattern_obj_type in self.keys():
                # Extract config objects of interest (based on pattert_obj_type)
                for config_obj in self[pattern_obj_type]:
                    # Place holders for match and miss objects, to be filled later
                    match_obj[config_obj.name] = {}
                    miss_obj[config_obj.name] = {}
                    # Extract pattern objects of interest and compare with config objects of interest
                    for pattern_obj in pattern[pattern_obj_type]:
                        # Perform comparison only if all pattern dict keys are part of config object dict keys
                        if set(pattern_obj()._get_config().keys()).issubset(set(config_obj()._get_config().keys())):
                            # Extract pattern object keys for comparison
                            for pattern_obj_key in pattern_obj()._get_config().keys():
                                # Extract value of pattern_obj and value of config_obj based on pattern_obj_key for comparison
                                if universal_cmp(getattr(pattern_obj, pattern_obj_key), getattr(config_obj, pattern_obj_key)):
                                    #print(getattr(config_obj, "_full_match_exists"))
                                    #if getattr(config_obj, "_full_match_exists"):
                                    match_obj[config_obj.name][pattern_obj_key] = getattr(
                                        config_obj, pattern_obj_key)
                                else:
                                    miss_obj[config_obj.name][pattern_obj_key] = getattr(
                                        config_obj, pattern_obj_key)
                        else:
                            miss_options += set(pattern_obj()._get_config().keys()) - \
                                set(config_obj()._get_config().keys())
                    # if object already found, ignore it in next iteration
                    #if match_obj[config_obj.name].keys() and (set(pattern_obj()._get_config().keys()) - set(miss_obj[config_obj.name].keys())) == set([]):
                    #    config_obj()._set_full_match_exists()
                    if match_obj[config_obj.name] == {}:
                        del match_obj[config_obj.name]
                    if miss_obj[config_obj.name] == {}:
                        del miss_obj[config_obj.name]
                print("MISS OPTIONS")
                pprint.pprint(set(miss_options))
                print("MISS OBJECTS")
                pprint.pprint(miss_obj)
                print("MATCH OBJECTS")
                pprint.pprint(match_obj)


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

config_from_backup._pattern_match(config_from_backup, pattern1_from_file)



#print("GOLDEN TEMPLATE PROJECT")
#pattern_match(config_from_backup, config_from_backup)
print("PATTERN 1: key and value match ")
_pattern_match(config_from_backup, pattern1_from_file)
print("PATTERN 2: key match only")
_pattern_match(config_from_backup, pattern2_from_file)
print("PATTERN 3: value match only")
_pattern_match(config_from_backup, pattern3_from_file)
print("PATTERN 4: no match")
_pattern_match(config_from_backup, pattern4_from_file)
print("PATTERN 5: partial key and value match")
_pattern_match(config_from_backup, pattern5_from_file)