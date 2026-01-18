#dose.api.classmethods.dosebase.py


class DoseBase(object):
    _request = {}
    _instruction = {}
    _response = {}

    def init(request, instruction):
         _request = request
         _instruction = instruction

    def execute(request, instruction):
        print('DoseBase.execute')
        return ()

    def fetchonesubclass(subclassname):
        for cls in DoseBase.__subclasses__():
            if subclassname == cls.__name__:
                return cls