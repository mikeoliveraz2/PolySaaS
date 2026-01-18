#dose/dosemqrequestcontroller.py

from dose.models import Instruction
from django.contrib import messages
from dose.api.methods.c2base import C2Methods
from ast import literal_eval
import urllib.parse
import requests
import validators
from urllib.parse import _NetlocResultMixinBase, parse_qs, urlsplit

import logging
logger = logging.getLogger(__name__)
logger.info("Now logging in doseMqRequestController")

class doseMqRequestController:
    def process_request(ch, method, properties, body):
        
        logger.info("process_mq_request")
        #messages.add_message(request, messages.INFO, 'doseRequestController has executed!')
        
        logger.info("MQRequestController process_request ")
        
        requestmethod = method
        logger.info('requestmethod=%s', requestmethod)

        instructions = Instruction.objects.filter(requestpath="dose2")

        logger.info("instructions.count()= %s",instructions.count())
        #now process executeScript before the other branches as they are independent

        data = literal_eval(body.decode('utf-8'))

        for instruction_row in instructions:
            executeScript = instruction_row.executescript
            
            logger.debug('executeScript = %s', executeScript)
            
            #if executeScript is not null run it first
            if executeScript is not None:
                #remember that executeScript executes before the web services in urllist.
                cls = C2Methods.fetchonesubclass(executeScript)
                logger.info('cls =%s', cls)
                if cls:
                    try:
                        request2 = cls.execute(request, instruction_row, instruction_row.parameters_json, data )
                    except:
                        logger.error('ExecuteScript failed')

                logger.debug('request2 = %s',request2)

            mybody = body.decode('utf-8')
            logger.debug("mybody= %s", mybody)

            """ decoded_body = urllib.parse.parse_qs(mybody)
            logger.info()
            logger.info("decoded_body=", decoded_body) """
            
            urllist = 'na'
            for instruction_row in instructions:
                urllist = instruction_row.urllist
                
                logger.debug('urllist =%s', urllist)
                
                for serviceUrl in urllist.split(', '):
                    logger.info("serviceUrl= %s", serviceUrl)
                    if not validators.url(serviceUrl):
                        return request
            
                    data = requests.post('serviceUrl, json= decoded_body')
                    
                    
                    logger.debug("and data=%s", data)
                    
                    #eventually we will append the results in the atomic services
        