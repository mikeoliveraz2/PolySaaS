# DO NOT MODIFY: Critical system file. Ask before making changes.
from dose.models import Instruction
from django.utils.deprecation import MiddlewareMixin

import re
from urllib.parse import parse_qs
from django.contrib import messages

from dose.api.methods.c2responsebase import C2ResponseMethods
#from django.http import JsonResponse
import urllib.parse
import requests
from django.http import HttpResponseRedirect
import validators
from urllib.parse import _NetlocResultMixinBase, parse_qs, urlsplit
import logging
logger = logging.getLogger(__name__)
logger.info("Now logging in DoseResponseController")

from dose.middleware.debug import DebugStackMiddleware   # ← ADD THIS

class DoseResponseController(DebugStackMiddleware, MiddlewareMixin):  # ← FIRST!
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Custom response logic can be added here
        response = self.get_response(request)
        # Optionally process the response
        return response

    def process_response(path, response):

        logger.info("DoseResponseController.path=")
        logger.info('Response path = %s', path)


        # logger.info('pathstr = ', pathstr)

        response_headers = response.headers
        logger.debug("response_headers= %s", response_headers)

        content = response.content

        logger.debug('content = %s', content)
        contentdecoded = content.decode("utf-8")
        logger.debug('contentdecoded = %s', contentdecoded)
        #extract the ID from the contentdecoded
        #Execute Script(s)
        instructions = Instruction.objects.filter(requestpath=path).filter(direction='RES')

        # Import Parameter model
        try:
            from parameters.models import Parameter
        except ImportError:
            Parameter = None

        for instruction_row in instructions:
            executeScript = instruction_row.executescript
            logger.debug('executeScript = %s', executeScript)
            # Attach parameters to response before atomic service execution
            if Parameter is not None:
                matching_key = None
                if hasattr(instruction_row, 'matchingKey') and getattr(instruction_row, 'matchingKey', None):
                    matching_key = getattr(instruction_row, 'matchingKey')
                elif hasattr(instruction_row, 'eventKey') and getattr(instruction_row, 'eventKey', None):
                    matching_key = getattr(instruction_row, 'eventKey')
                if not matching_key and executeScript:
                    matching_key = executeScript
                if matching_key:
                    params_qs = Parameter.objects.filter(matchingKey=matching_key).order_by('sequence')
                    response.atomic_parameters = list(params_qs)
                    logger.info(f"[PARAM-ATTACH-RES] Attached {len(response.atomic_parameters)} parameters for key '{matching_key}' to response.")
                else:
                    response.atomic_parameters = []
                    logger.info("[PARAM-ATTACH-RES] No matchingKey found; attached empty parameter list to response.")
            else:
                response.atomic_parameters = []
                logger.warning("[PARAM-ATTACH-RES] Parameter model not available; attached empty parameter list to response.")

            # Save atomic service result to CallBackData if flag is set
            if hasattr(instruction_row, 'save_callbackdata') and instruction_row.save_callbackdata:
                from dose.models import CallBackData
                atomic_result = None
                if executeScript is not None:
                    cls = C2ResponseMethods.fetchonesubclass(executeScript)
                    logger.info('cls =%s', cls)
                    if cls:
                        try:
                            atomic_result = cls.execute_and_save(response, instruction_row)
                        except Exception as e:
                            logger.error('ExecuteScript failed: %s', str(e))
                # Fallback to response content if no atomic_result
                if not atomic_result:
                    atomic_result = contentdecoded
                try:
                    cb = CallBackData.objects.create(
                        matchingEventKey=getattr(instruction_row, 'eventKey', None),
                        description=atomic_result,
                        parameters_json=getattr(instruction_row, 'parameters_json', None)
                    )
                    logger.info("Saved CallBackData id %s for instruction id %s", cb.id, instruction_row.id)
                except Exception as e:
                    logger.error("Failed to save CallBackData: %s", str(e))



        #on the response side, the urllist last entry will be for redirect so if there are three
        #in the urllist then the first two will be executed and the third will be for
        #redirect.  This allows a process of multiple steps to be executed totally within
        #the Dose 2.  If the last url in urllist is the same as the path then there would be
        #no redirection.


        for instruction_row in instructions:
            logger.info("instructions.count()={} %s",instructions.count())

            urllist = instruction_row.urllist
            logger.info('urllist =%s', urllist)
            parameters_json = instruction_row.parameters_json
            logger.debug('parameters_json =%s', parameters_json)
            logger.debug('urllist =%s', urllist)
            _urllist = urllist.split(', ')
            llen = len(_urllist)
            counter = 0
            for serviceUrl in _urllist:
                #logger.info("serviceUrl=", serviceUrl)
                #check how to add message at response if possible
                # if not validators.url(serviceUrl):
                #     messages.add_message(DoseResponseController, messages.ERROR, serviceUrl + ' IS INVALID')
                #     return responseparameters_json
                counter += 1
                if counter == llen:
                    if serviceUrl == path:
                        return response
                    else:
                        return HttpResponseRedirect(serviceUrl)

                #TODO we will want to use the registry so we can put just the name of the atomic service and not the full URL
                #if the last url in the list is not the same as the path then redirect from here

                getdata = requests.get(serviceUrl, headers=response_headers, params=response.content)

                logger.debug("response getdata.headers =%s", getdata.headers)
                logger.info("response getdata.status_code =%s", getdata.status_code)
                status_code = getdata.status_code
                atomicMessage = 'Atomic Service 1 Executed with status code = ' + str(status_code)
                logger.info(atomicMessage)
            response.headers["atomicMessage"] = atomicMessage
        return response #if possible we may want to be able to modify the request on the fly before going to the model
