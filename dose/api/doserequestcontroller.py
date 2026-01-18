from dose.models import Instruction

from dose.api.methods.dosebase import DoseBase

from django.contrib import messages
import urllib.parse
import validators
import requests
from urllib.parse import parse_qs, urlsplit
import logging

logger = logging.getLogger(__name__)
logger.info("Now Logging in doserequestcontroller")
 
class DoseRequestController:
    def process_request(path, request):
        logger.info('DoseRequestController path = %s', path)

        if path in ['localhost:8000/admin/jsi18n/']:
            logger.info("not in list")
            return request

        request_get_params = request.GET
        logger.info("request_get_params= %s", request_get_params)

        request_post_params = request.POST
        logger.info("request_post_params= %s", request_post_params)
        
        request_scheme = request.scheme
        logger.info("request_scheme= %s", request_scheme)

        request_headers = request.headers
        logger.info("DoseRequestController process_request")
        
        logger.info("request_headers= %s", request_headers)
        
        logger.info("DoseRequestController process_request ")
        
        requestmethod = request.method
        logger.info('requestmethod= %s', requestmethod)

        instructions = Instruction.objects.filter(requestpath=path).filter(requestmethod=requestmethod).filter(direction='REQ')

        logger.info("instructions.count()= %s",instructions.count())

        if instructions.count() == 0:
            return request

        if requestmethod == 'POST':
            logger.info("dose request controller POST method %s", requestmethod)
            mybody = str(request.body)
            logger.info("mybody= %s", mybody)
            decoded_body = urllib.parse.parse_qs(mybody)

            logger.info("decoded_body= %s", decoded_body)
            
            urllist = []
            for instruction_row in instructions:

                #executescript
                executescript_name = instruction_row.executescript
                logger.info('executescript_name = %s', executescript_name)
                if executescript_name.__len__() > 0:
                    
                    logger.info('DoseBase.__subclasses__() = %s', DoseBase.__subclasses__())
                    cls  = DoseBase.fetchonesubclass(executescript_name)
                    if cls:
                        classresults = cls.execute(request, instruction_row)
                        logger.info('classresults = %s', classresults)

                urllist = instruction_row.urllist
                
                logger.info('urllist = %s', urllist)
                
                for serviceUrl in urllist.split(', '):
                    logger.info("serviceUrl= %s", serviceUrl)
                    if not validators.url(serviceUrl):
                        logger.error("not valid")
                        return request

                    data = requests.post(serviceUrl, json= decoded_body)
                    logger.info("response data = %s", data)
                   
                    #eventually we will append the results in the atomic services
        elif requestmethod == 'PUT': #TODO change to PUT
            
            logger.info("dose request controller PUT")
            mybody = str(request.body)
            logger.info("mybody= %s", mybody)
            
            urllist = []
            for instruction_row in instructions:
                urllist = instruction_row.urllist
                
                logger.info('urllist = %s', urllist)
                
                for serviceUrl in urllist.split(', '):
                    logger.info("serviceUrl= %s", serviceUrl)
                    if not validators.url(serviceUrl):
                        logger.info("not valid")
                        return request

                    data = requests.get(serviceUrl, json= decoded_body)
                    
                    logger.info("response data = %s", data)
                    
                    #eventually we will append the results in the atomic services
        
        else: #get
            logger.info("DoseRequestController  GET ")
            urllist = []
            for instruction_row in instructions:
                
                #executescript
                executescript_name = instruction_row.executescript
                logger.info('executescript_name = %s', executescript_name)
                if executescript_name.__len__() > 5:
                    
                    logger.info('DoseBase.__subclasses__() = %s ', DoseBase.__subclasses__())
                    
                    cls = DoseBase.fetchonesubclass(executescript_name)
                    if cls:
                        script_results = cls.execute(request, instruction_row)
                        logger.info('script_results = %s', script_results)
                    else:
                        logger.info('no cls')

                urllist = instruction_row.urllist
                
                logger.info('urllist = %s', urllist)
                
                for serviceUrl in urllist.split(', '):
                    logger.info("serviceUrl= %s", serviceUrl)
                    if not validators.url(serviceUrl):
                         messages.add_message(request, messages.ERROR, serviceUrl + ' IS INVALID')
                         return request

                    if len(serviceUrl) > 10:
                        mybody={}
                        mybody['Cookie'] = 'cookieStr'
                        mybody['otherStuff'] = 'as25'
                        mybody['moreStuff'] = 'as35'
                        mybody['description'] = 'Some will prepend this 555 some will replace this and some will append this.'
                        mybody['datetimestamp'] = '2022-09-01T00:00:00Z'
                        
                        logger.info('mybody = %s', mybody)
                        getdata = requests.get(serviceUrl, headers=request_headers, json=mybody)
                        
                        
                        logger.info("response getdata = %s", getdata.headers)
                        messages.add_message(request, messages.INFO, serviceUrl + ' Executed!')
                        
        return request