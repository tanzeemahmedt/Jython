'''
Created on Sep 22, 2017

@author: riteshagarwal
'''
import base64
import json
import urllib
from membase.api import httplib2
import logger
from lib.membase.api.rest_client import RestConnection as rest_base

log = logger.Logger.get_logger()

class RestConnection_cbas(rest_base):
    
    def __init__(self,serverInfo):
        super(self.__class__, self).__init__(serverInfo)
        self.cbas_base_url = "http://{0}:{1}".format(self.ip, 8095)
        
    def execute_statement_on_cbas(self, statement, mode, pretty=True,
                                  timeout=70, client_context_id=None):
        api = self.cbas_base_url + "/analytics/service"
        authorization = base64.encodestring('%s:%s' % (self.username, self.password))
        headers = {'Content-Type': 'application/json',
                'Authorization': 'Basic %s' % authorization,
                'Accept': '*/*'}
        
        params = {'statement': statement, 'mode': mode, 'pretty': pretty,
                  'client_context_id': client_context_id}
        params = json.dumps(params)
        status, content, header = self._http_request(api, 'POST',
                                                     headers=headers,
                                                     params=params,
                                                     timeout=timeout)
        if status:
            return content
        elif str(header['status']) == '503':
            log.info("Request Rejected")
            raise Exception("Request Rejected")
        elif str(header['status']) in ['500','400']:
            json_content = json.loads(content)
            msg = json_content['errors'][0]['msg']
            if "Job requirement" in  msg and "exceeds capacity" in msg:
                raise Exception("Capacity cannot meet job requirement")
            else:
                return content
        else:
            log.error("/analytics/service status:{0},content:{1}".format(
                status, content))
            raise Exception("Analytics Service API failed")

    def delete_active_request_on_cbas(self, client_context_id):
        api = self.cbas_base_url + "/analytics/admin/active_requests?client_context_id={0}".format(
            client_context_id)
        authorization = base64.encodestring('%s:%s' % (self.username, self.password))
        headers = {'Content-Type': 'application/json',
                'Authorization': 'Basic %s' % authorization,
                'Accept': '*/*'}

        status, content, header = self._http_request(api, 'DELETE',
                                                     headers=headers,
                                                     timeout=60)
        if status:
            return header['status']
        elif str(header['status']) == '404':
            log.info("Request Not Found")
            return header['status']
        else:
            log.error(
                "/analytics/admin/active_requests status:{0},content:{1}".format(
                    status, content))
            raise Exception("Analytics Admin API failed")
    
    def analytics_tool(self, query, port=8095, timeout=650, query_params={}, is_prepared=False, named_prepare=None,
                   verbose = True, encoded_plan=None, servers=None):
        key = 'prepared' if is_prepared else 'statement'
        headers = None
        content=""
        prepared = json.dumps(query)
        if is_prepared:
            if named_prepare and encoded_plan:
                http = httplib2.Http()
                if len(servers)>1:
                    url = "http://%s:%s/query/service" % (servers[1].ip, port)
                else:
                    url = "http://%s:%s/query/service" % (self.ip, port)

                headers = {'Content-type': 'application/json'}
                body = {'prepared': named_prepare, 'encoded_plan':encoded_plan}

                response, content = http.request(url, 'POST', headers=headers, body=json.dumps(body))

                return eval(content)

            elif named_prepare and not encoded_plan:
                params = 'prepared=' + urllib.quote(prepared, '~()')
                params = 'prepared="%s"'% named_prepare
            else:
                prepared = json.dumps(query)
                prepared = str(prepared.encode('utf-8'))
                params = 'prepared=' + urllib.quote(prepared, '~()')
            if 'creds' in query_params and query_params['creds']:
                headers = self._create_headers_with_auth(query_params['creds'][0]['user'].encode('utf-8'),
                                                         query_params['creds'][0]['pass'].encode('utf-8'))
            api = "%s/analytics/service?%s" % (self.cbas_base_url, params)
            log.info("%s"%api)
        else:
            params = {key : query}
            if 'creds' in query_params and query_params['creds']:
                headers = self._create_headers_with_auth(query_params['creds'][0]['user'].encode('utf-8'),
                                                         query_params['creds'][0]['pass'].encode('utf-8'))
                del query_params['creds']
            params.update(query_params)
            params = urllib.urlencode(params)
            if verbose:
                log.info('query params : {0}'.format(params))
            api = "%s/analytics/service?%s" % (self.cbas_base_url, params)
        status, content, header = self._http_request(api, 'POST', timeout=timeout, headers=headers)
        try:
            return json.loads(content)
        except ValueError:
            return content
        