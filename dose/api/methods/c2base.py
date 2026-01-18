#Dose.api.methods.c2base.py this is the super class for the Dose 2 dynamic
#orchestrataion classes that can be called by name in the instruction executescript field

class C2Methods(object):
    _instruction = {}
    _request = {}
    _paramter = {}
    _data = {}
    _responsedata = {}

    def init(request, instruction, parameter, data):
        _instruction = instruction
        _request = request
        _paramter = parameter
        _data = _data

    def execute(request, instruction, parameter, data):
        print('execute')
        _responsedata = {}
        return (_responsedata)

    def get_all_subclasses():
        allsubclasses = C2Methods.__subclasses__()
        return allsubclasses

    def fetchonesubclass(subclassname):
        allsubclasses = C2Methods.__subclasses__()
        for cls in allsubclasses:
            if subclassname == cls.__name__:
                return cls

class InternalSubclass(C2Methods):
    pass