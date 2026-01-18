#dose.api.methods.c2responsesubclass2.py Some processing but usually mostly redirection to 
#the path set in the urllist

from dose.api.methods.c2responsebase import C2ResponseMethods

class C2ResponseSubclass3(C2ResponseMethods):
    
    def execute(response, instruction, parameter):
        print('execute>', __name__)
        _responsedata = {}
        return (_responsedata)

    