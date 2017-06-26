"""
Functions for handling JSON files with settings
"""

import json
import os.path
import json


class Configuration(object):
    """
    Transform dictionary into object with properties correcponding to its keys
    
    Supports environment variables in values
    """
    def __init__(self, dictionary):
        for key, value in dictionary.items():
            if type(value) is dict:
                setattr(self, key, Configuration(value))
            else:
                if isinstance(value, str):
                    value = os.path.expandvars(value)
                setattr(self, key, value)

    def __str__(self):
        return json.dumps(self.dump(), indent=2)
                
    def dump(self):
        """Dump object attributes back into dictionary"""
        output = dict()
        for key, value in self.__dict__.items():
            if type(value) is type(self):
                output[key] = value.dump()
            else:
                output[key] = value
        return output


def settings(json_file, default):
    """
    Read settings from JSON file

    Arguments:
        json_file
            Settings file name. Must contain valid JSON
        default
            Dictionary containing default settings structure. Settings not
            specified in `default` dictionary will be ignored
    """
    with open(json_file) as f:
        input = json.load(f)
    return Configuration(mimic_dict(input, default))


def mimic_dict(source, default):
    """
    Copy a dictionary according to mask.

    Arguments:
        source
            Dictionary to be copied
        default
            Mask dictionary with default values

    Returns a dictionary with keys from `default` and values from `source`.
    If `source` has no value then value from `default` is used
    """
    for i in (source, default):
        if type(i) is not dict:
            raise TypeError("expected dict, but got %s" % type(i))

    result = dict()
    for i in default:
        value = source.get(i)
        preset = default[i]
        if value:
            if type(preset) is dict and type(value) is dict:
                result[i] = mimic_dict(value, preset)
            elif type(preset) is not dict and type(value) is not dict:
                result[i] = value
            else:
                raise TypeError("%s doesn't match pattern %s" % (value, preset))
        else:
            result[i] = preset
    return result
