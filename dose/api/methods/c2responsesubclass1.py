#dose.api.methods.c2responsesubclass1.py this is the super class for the dose 2 dynamic
#orchestrataion classes that can be called by name in the instruction executescript field
# on the response direction.  Some processing but usually mostly redirection to 
#the path set in the urllist

from dose.api.methods.c2responsebase import C2ResponseMethods

class C2ResponseSubclass1(C2ResponseMethods):
    
    def execute(response, instruction, parameter):
        print('execute>', __name__)
        _responsedata = {}
        return (_responsedata)

    