# Copyright 2021 Eggplant
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from pprint import pprint
import requests

class XRAYClientException(Exception):
    """
    Class for exceptions raised by the DAI API client
    """


class XRAYClient:
    """
    Client for the XRAY REST API
    """
    def __init__(self, url, client_id, client_secret):
        """
        Construct with a URL, username, and password

        :param url: The base URL, e.g., `<http://localhost>`_
        :param client_id:
        :param client_secret:
        """
        self.url = self.parse_url(url)
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_token = None
        self._get_auth_token()

    '''
    headers = {
        'Accept': 'text/plain',
        'Authorization': 'Bearer ' + access_token,
        'Content-type': 'application/json'
    }

    '''

    def _do_get(self, endpoint, operation):
        """
        Perform an authenticated HTTP GET request, returning the JSON result

        :param endpoint: The endpoint path, e.g., '/api/run'
        :param operation: Text description of the operation, for error reporting
        :returns: The JSON response
        """
        #headers = {'Accept': 'text/plain','Authorization' : 'bearer ' + self.auth_token,'Content-type': 'application/json'}
        headers = {'Authorization' : 'bearer ' + self.auth_token}
        auth_failed = False
        while True:
            try:
                resp = requests.get(self.url + endpoint, headers=headers)
            except requests.exceptions.ConnectionError as err:
                raise XRAYClientException("Failed to {}: {}".format(operation, err)) from err
            if resp.status_code == 401:
                # Invalid auth token
                if auth_failed:
                    # Don't try again if the new auth token doesn't work
                    raise XRAYClientException("Authentication failed: {}".format(resp.text))

                # Auth token has expired: get a new one
                auth_failed = True
                self._get_auth_token()
            elif resp.status_code != 200:
                # Any other error
                raise XRAYClientException("Failed to {}: {}".format(operation, resp.text))
            else:
                # Success
                return resp.json()

    def _do_post(self, endpoint, payload, operation, form_encoded=False):
        """
        Perform an authenticated HTTP POST request, returning the JSON result

        :param endpoint: The endpoint path, e.g., '/api/run'
        :param payload: The urlencoded request body
        :param operation: Text description of the operation, for error reporting
        :returns: The JSON response
        """
        print(payload)
        headers = {'Authorization' : 'Bearer ' + self.auth_token}
        auth_failed = False
        while True:
            try:
                if form_encoded:
                    resp = requests.post(self.url + endpoint, headers=headers, data=payload)
                else:
                    resp = requests.post(self.url + endpoint, headers=headers, json=payload)
            except requests.exceptions.ConnectionError as err:
                raise XRAYClientException("Failed to {}: {}".format(operation, err)) from err
            if resp.status_code == 401:
                # Invalid auth token
                if auth_failed:
                    # Don't try again if the new auth token doesn't work
                    raise XRAYClientException("Authentication failed: {}".format(resp.text))

                # Auth token has expired: get a new one
                auth_failed = True
                self._get_auth_token()
            elif resp.status_code not in [200, 201]:
                # Any other error
                raise XRAYClientException(
                    "Failed to {} ({}): {}".format(operation, resp.status_code, resp.text)
                )
            else:
                # Success
                return resp.json()



    def _get_auth_token(self):
        """
        Get an API access token
        base_api_endpoint = "https://xray.cloud.xpand-it.com"
        auth_url = base_api_endpoint + "/api/v2/authenticate"

        """
        payload = {"client_id" : self.client_id, 'client_secret' : self.client_secret}
        auth_url = '/api/v2/authenticate'
        error_message = 'Failed to get access token: {}'
        try:
            resp = requests.post(self.url + auth_url, data=payload)
        except requests.exceptions.ConnectionError as err:
            raise XRAYClientException(error_message.format(err))(err)
        if resp.status_code != 200:
            raise XRAYClientException(error_message.format(resp.text))
        response = resp.json()
        self.auth_token = response
    
    def get_license(self):
        """
        Get the status of the SUT

        :returns: The JSON response
        """
        return self._do_get('/api/v2/xraylicense', "get XRAY license info")
    
    def get_testrun(self,testExecIssueKey,testIssueKey):
        return self._do_get(f'/api/v2/testrun?testExecIssueKey={testExecIssueKey}&testIssueKey={testIssueKey}', "Philippa getting testrun")
    
    def get_cucumber(self):
        
        return self._do_get('/api/v2/export/cucumber', "philippa get me a cucumber")
    
    def post_execution(self,payload):
        
        return self._do_post('/api/v2/import/execution',payload,"Unable to create test execution")
   
    def post_import_test(self, payload):
        return self._do_post('/api/v2/import/test/bulk', payload, "testing test creation")
    
    @staticmethod
    def parse_url(url):
        """
        Format host to be of the right form, adding domains
        and removing trailing /
        """
        if '//' not in url:
            url = "http://{}".format(url)
        url = urlparse(url)
        url = url.geturl().strip('/')

        return url


