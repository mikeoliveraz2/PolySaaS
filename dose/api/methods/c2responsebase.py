#Dose.api.methods.c2responsebase.py this is the super class for the Dose 2 dynamic
#orchestrataion classes that can be called by name in the instruction executescript field
# on the response direction.  Some processing but usually mostly redirection to 
#the path set in the urllist

class C2ResponseMethods(object):
    _instruction = {}
    _response = {}
    _paramter = {}
    _responsedata = {}

    def init(response, instruction, parameter):
        _instruction = instruction
        _response = response
        _paramter = parameter


    def execute(response, instruction, parameter):
        print('execute')
        _responsedata = {}
        return (_responsedata)

    def get_all_subclasses():
        allsubclasses = C2ResponseMethods.__subclasses__()
        return allsubclasses

    def fetchonesubclass(subclassname):
        allsubclasses = C2ResponseMethods.__subclasses__()
        for cls in allsubclasses:
            if subclassname == cls.__name__:
                return cls

class InternalSubclass(C2ResponseMethods):
    pass