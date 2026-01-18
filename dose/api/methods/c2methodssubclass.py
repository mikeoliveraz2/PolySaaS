#Dose.api.methods.testsubclass.py
#this class is a subclass of Dose.api.methods.c2base.C2Methods for testing

from .c2base import C2Methods

class C2MethodsSubclass(C2Methods):
    
     def execute(request,instruction, parameter, data):
        print('C2MethodsSubclass.execute()')
        _responsedata = {}
        return (_responsedata)