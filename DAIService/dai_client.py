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

"""
Module for the Eggplant DAI Python client library

See `<http://docs.eggplantsoftware.com/EAI/api/eai-ai-api.htm>`
for full details of the API calls and messages.
"""

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from pprint import pprint
import requests


class DAIClientException(Exception):
    """
    Class for exceptions raised by the DAI API client
    """


# pylint: disable=too-many-public-methods
class DAIClient:
    """
    Client for the Eggplant DAI REST API
    """
    def __init__(self, url, username, password):
        """
        Construct with a URL, username, and password

        :param url: The base URL, e.g., `<http://localhost>`_
        :param username:
        :param password:
        """
        self.url = self.parse_url(url)
        self.username = username
        self.password = password
        self.auth_token = None
        self._get_auth_token()


    def _do_get(self, endpoint, operation):
        """
        Perform an authenticated HTTP GET request, returning the JSON result

        :param endpoint: The endpoint path, e.g., '/api/run'
        :param operation: Text description of the operation, for error reporting
        :returns: The JSON response
        """
        headers = {'Authorization' : 'bearer ' + self.auth_token}
        auth_failed = False
        while True:
            try:
                resp = requests.get(self.url + endpoint, headers=headers)
            except requests.exceptions.ConnectionError as err:
                raise DAIClientException("Failed to {}: {}".format(operation, err)) from err
            if resp.status_code == 401:
                # Invalid auth token
                if auth_failed:
                    # Don't try again if the new auth token doesn't work
                    raise DAIClientException("Authentication failed: {}".format(resp.text))

                # Auth token has expired: get a new one
                auth_failed = True
                self._get_auth_token()
            elif resp.status_code != 200:
                # Any other error
                raise DAIClientException("Failed to {}: {}".format(operation, resp.text))
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
        headers = {'Authorization' : 'bearer ' + self.auth_token}
        auth_failed = False
        while True:
            try:
                if form_encoded:
                    resp = requests.post(self.url + endpoint, headers=headers, data=payload)
                else:
                    resp = requests.post(self.url + endpoint, headers=headers, json=payload)
            except requests.exceptions.ConnectionError as err:
                raise DAIClientException("Failed to {}: {}".format(operation, err)) from err
            if resp.status_code == 401:
                # Invalid auth token
                if auth_failed:
                    # Don't try again if the new auth token doesn't work
                    raise DAIClientException("Authentication failed: {}".format(resp.text))

                # Auth token has expired: get a new one
                auth_failed = True
                self._get_auth_token()
            elif resp.status_code not in [200, 201]:
                # Any other error
                raise DAIClientException(
                    "Failed to {} ({}): {}".format(operation, resp.status_code, resp.text)
                )
            else:
                # Success
                return resp.json()


    def _do_put(self, endpoint, payload, operation):
        """
        Perform an authenticated HTTP PUT request, returning the JSON result

        :param endpoint: The endpoint path, e.g., '/api/run'
        :param payload: The urlencoded request body
        :param operation: Text description of the operation, for error reporting
        :returns: The JSON response
        """
        headers = {'Authorization' : 'bearer ' + self.auth_token}
        auth_failed = False
        while True:
            try:
                resp = requests.put(self.url + endpoint, headers=headers, json=payload)
            except requests.exceptions.ConnectionError as err:
                raise DAIClientException("Failed to {}: {}".format(operation, err)) from err
            if resp.status_code == 401:
                # Invalid auth token
                if auth_failed:
                    # Don't try again if the new auth token doesn't work
                    raise DAIClientException("Authentication failed: {}".format(resp.text))

                # Auth token has expired: get a new one
                auth_failed = True
                self._get_auth_token()
            elif resp.status_code != 200:
                # Any other error
                raise DAIClientException("Failed to {}: {}".format(operation, resp.text))
            else:
                # Success
                return resp.json()


    def _do_delete(self, endpoint, operation):
        """
        Perform an authenticated HTTP DELETE request, returning the JSON result

        :param endpoint: The endpoint path, e.g., '/api/run'
        :param operation: Text description of the operation, for error reporting
        :returns: The JSON response
        """
        headers = {'Authorization' : 'bearer ' + self.auth_token}
        auth_failed = False
        while True:
            try:
                resp = requests.delete(self.url + endpoint, headers=headers)
            except requests.exceptions.ConnectionError as err:
                raise DAIClientException("Failed to {}: {}".format(operation, err)) from err
            if resp.status_code == 401:
                # Invalid auth token
                if auth_failed:
                    # Don't try again if the new auth token doesn't work
                    raise DAIClientException("Authentication failed: {}".format(resp.text))

                # Auth token has expired: get a new one
                auth_failed = True
                self._get_auth_token()
            elif resp.status_code == 204:
                return f"delete status code: {resp.status_code}"
            elif resp.status_code != 200:
                # Any other error
                raise DAIClientException("Failed to {}: {}".format(operation, resp.text))
            else:
                # Success
                return resp.json()


    def _get_auth_token(self):
        """
        Get an API access token
        """
        payload = {'username' : self.username, 'password' : self.password}
        auth_url = '/ai/auth'
        error_message = 'Failed to get access token: {}'
        try:
            resp = requests.post(self.url + auth_url, data=payload)
        except requests.exceptions.ConnectionError as err:
            raise DAIClientException(error_message.format(err)) from err
        if resp.status_code != 200:
            raise DAIClientException(error_message.format(resp.text))
        response = resp.json()
        self.auth_token = response['access_token']


    def delete_auth_token(self):
        """
        Delete the auth token currently being used
        """
        return self._do_delete('/ai/auth', "delete auth token")


    # pylint: disable=too-many-arguments, too-many-locals
    def run_model(self, model, modeluuid, group, directed_test=None, agent_name=None, agent_type=None,
                  suite_location=None, bins=100, coverdb='ttdb', covertarget=1, execute=True,
                  iterations=1, logdir='logs', logfile=None, max_actions=10000, onerror='clean',
                  path=None, replay=None, seed=None, verbosity=None):
        """
        Run a model

        :param model:
        :param group:
        :param directed_test: Name of a directed test to run. Default: None
        :param agent_name: The Eggplant DAI Agent name. Default: None
        :param suite_location: The Eggplant Functional suite location. Default: None
        :param bins: Number of bins. Default: 100
        :param coverdb: The name of the coverage database, Default: 'ttdb'
        :covertarget: The target coverage order. Default: 1
        :param execute: Execute SenseTalk snippets? Default: True
        :param iterations: Number of iterations: Default: 1
        :param logdir: Log file directory. Default: 'logs'
        :param logfile: Log filename. Default: None (uses 'modelname_seed_date.log')
        :param max_actions: Maximum number of actions. Default: 10000
        :param onerror: Action to take on error. One of 'clean', 'continue', 'immediate', or
                        'debug'. Default: 'clean'
        :param path: Path. Default: None
        :param replay: Test ID to replay. Default: None
        :param seed: Test seed. Default: None
        :param verbosity: Verbosity. Default: None
        :returns: The JSON response
        """
        payload = { 'modelName': model, 'modelId':modeluuid , 'group': group }

        def add_to_payload_if(key=None, value=None, predicate=False):
            if predicate:
                payload[key] = value

        add_to_payload_if(
            key='directedTest', value=directed_test,
            predicate=directed_test is not None)
        add_to_payload_if(
            key='agentName', value=agent_name,
            predicate=agent_name is not None)
        add_to_payload_if(
            key='agentType', value=agent_type,
            predicate=agent_type is not None)
        add_to_payload_if(
            key='suiteLocation', value=suite_location,
            predicate=suite_location is not None)
        add_to_payload_if(
            key='bins', value=bins,
            predicate=bins is not None and bins != 100)
        add_to_payload_if(
            key='coverdb', value=coverdb,
            predicate=coverdb is not None and coverdb != 'ttdb')
        add_to_payload_if(
            key='covertarget', value=covertarget,
            predicate=covertarget is not None and covertarget != 1)
        add_to_payload_if(
            key='execute', value=execute,
            predicate=not execute)
        add_to_payload_if(
            key='iterations', value=iterations,
            predicate=iterations is not None and iterations != 1)
        add_to_payload_if(
            key='logdir', value=logdir,
            predicate=logdir is not None and logdir != 'logs')
        add_to_payload_if(
            key='logfile', value=logfile,
            predicate=logfile is not None)
        add_to_payload_if(
            key='maxActions', value=max_actions,
            predicate=max_actions is not None and max_actions != 10000)
        add_to_payload_if(
            key='onerror', value=onerror,
            predicate=onerror is not None and onerror != 'clean')
        add_to_payload_if(
            key='path', value=path,
            predicate=path is not None)
        add_to_payload_if(
            key='replay', value=replay,
            predicate=replay is not None)
        add_to_payload_if(
            key='seed', value=seed,
            predicate=seed is not None)
        add_to_payload_if(
            key='verbosity', value=verbosity,
            predicate=verbosity is not None and verbosity != '0x300')

        #print('Payload:')
        #pprint(payload)

        return self._do_post('/api/run', payload, "run model", form_encoded=True)


    def get_progress(self, run_id):
        """
        Get the progress of a run

        :param id: The run id as returned in the `id` field by `runModel()`
        :returns: The JSON response
        """
        payload = {'id': run_id}
        return self._do_post('/api/run/progress', payload, "get progress")


    def get_sut_status(self):
        """
        Get the status of the SUT

        :returns: The JSON response
        """
        return self._do_post('/api/sut/status', None, "get SUT status")


    def abort_run(self, process_id):
        """
        Abort a run

        :param process_id: The process id, as returned in the `processid` field by `runModel()`
        :returns: The JSON response
        """
        payload = {'processid': process_id}
        return self._do_post('/api/run/abort', payload, "abort run")


    def get_run_logs(self, run_id):
        """
        Get a single run log
        """
        return self._do_get('/ai/runlogs/{}'.format(run_id), "get run log")


    def get_model_run_logs(self, model_id):
        """
        Get model run logs
        """
        return self._do_get('/ai/runs/{}'.format(model_id), "get model run logs")


    # pylint: disable=too-many-arguments
    def create_agent(self, agent_id, name, epp_host="", suite="", epp_test_controller_port=0,
                     record_path="", epp_analyzer_port=0, epp_workspace_path=""):
        """
        Create an agent
        """
        payload = {
            'epphost': epp_host,
            'suite': suite,
            'epptestcontrollerport': epp_test_controller_port,
            'recordpath': record_path,
            'eppanalyzerport': epp_analyzer_port,
            'id': agent_id,
            'name': name,
            'eppworkspacepath': epp_workspace_path
        }

        return self._do_post('/ai/agents', payload, "create agent")


    def get_agent_list(self):
        """
        Get a list of agents
        """
        return self._do_get('/ai/agents', "get a list of agents")


    def get_coverage_report(self, model_id):
        """
        Get a list of agents
        """
        return self._do_get(
            '/ai/models/{}/coverage'.format(model_id),
            "get coverage for model {}".format(model_id)
        )


    def delete_agent(self, agent_id):
        """
        Delete an agent
        """
        return self._do_delete('/ai/agents/{}'.format(agent_id), "delete agent")


    def update_agent(self, agent_id, payload):
        """
        Update an agent
        """
        return self._do_put('/ai/agents/{}'.format(agent_id), payload, "update agent")


    def get_agent(self, agent_id):
        """
        Get an agent
        """
        return self._do_get('/ai/agents/{}'.format(agent_id), "get agent")


    def associate_agent_with_model(self, agent_id, model_id):
        """
        Associate an agent with a model
        """
        payload = {
            'agent': agent_id
        }
        return self._do_put(
            '/ai/models/{}/agent'.format(model_id),
            payload,
            "associate agent with model"
        )


    def get_agent_associated_to_model(self, model_id):
        """
        Get the agent associated with a model
        """
        return self._do_get(
            '/ai/models/{}/agent'.format(model_id),
            "get agent associated with model"
        )


    def get_coverage_model_list(self):
        """
        Get a list of all coverage models
        """
        return self._do_get('/ai/coverage/models', "get list of coverage models")


    def get_coverage_model(self, coverage_id):
        """
        Get a coverage model
        """
        return self._do_get('/ai/coverage/model/{}'.format(coverage_id), "get coverage model")


    def create_coverage_model(self, name, path_depth, variable_depth):
        """
        Create new coverage model
        """
        payload = {
            'name': name,
            'path_depth': path_depth,
            'variable_depth': variable_depth
        }
        return self._do_post(
            '/ai/coverage/models',
            payload,
            "create coverage model {}".format(name)
        )


    def update_coverage_model(self, coverage_id, payload):
        """
        Update coverage model
        """
        return self._do_put(
            '/ai/coverage/model/{}'.format(coverage_id), payload,
            "update coverage model {}".format(coverage_id)
        )


    def delete_coverage_model(self, coverage_id):
        """
        Delete coverage model
        """
        return self._do_delete(
            '/ai/coverage/model/{}'.format(coverage_id),
            "delete coverage model {}".format(coverage_id)
        )


    def create_group(self, name):
        """
        Create group
        """
        payload = {'groupname': name}
        return self._do_post('/ai/groups', payload, "create group {}".format(name))


    def get_group_list(self):
        """
        Get group list
        """
        return self._do_get('/ai/groups', "get group list")


    def get_group(self, group_id):
        """
        Get group
        """
        return self._do_get('/ai/groups/{}'.format(group_id), "get group {}".format(group_id))


    def update_group(self, group_id, payload):
        """
        Update group
        """
        return self._do_put(
            '/ai/groups/{}'.format(group_id),
            payload,
            "Update group {}".format(group_id)
        )


    def delete_group(self, group_id):
        """
        Delete group
        """
        return self._do_delete('/ai/groups/{}'.format(group_id), "delete group {}".format(group_id))


    def create_license(self, license_string, serial_number):
        """
        Create license
        """
        payload = {'license': license_string, 'serialNumber': serial_number}
        return self._do_post('/ai/licenses', payload, "create license")


    def get_license_list(self):
        """
        Get license list
        """
        return self._do_get('/ai/licenses', "get license list")


    def get_license(self, serial_number):
        """
        Get license
        """
        return self._do_get(
            '/ai/licenses/{}'.format(serial_number),
            "get license {}".format(serial_number)
        )


    def get_status_info(self):
        """
        Get status info
        """
        return self._do_get('/ai/status', "get status")


    def get_license_usage_details(self):
        """
        Get license usage details
        """
        return self._do_get('/ai/usage', "get license usage details")


    def delete_license(self, serial_number):
        """
        Delete group
        """
        return self._do_delete(
            '/ai/licenses/{}'.format(serial_number),
            "delete license {}".format(serial_number)
        )


    def create_model(self, name, group, model_json):
        """
        Create model
        """
        payload = {
            'name': name,
            'group': group,
            'modeljson': model_json
        }
        return self._do_post('/ai/models', payload, "create model {}".format(name))


    def get_model_list(self):
        """
        Get model list
        """
        return self._do_get('/ai/models', "get model list")

    def get_model_id(self, model_name):
        """
        Get model id
        """
        try:
            return next(
                model_obj['id'] for model_obj in self.get_model_list()
                if model_obj['name'] == model_name
            )
        except StopIteration as err:
            raise DAIClientException("Failed to get model id, model name not found") from err

    def get_model_uuid(self, model_name):
        """
        Get model id
        """
        try:
            model_list = self.get_model_list()
            if 'modeluuid' in model_list[0].keys():
                return next(
                    model_obj['modeluuid'] for model_obj in model_list #self.get_model_list()
                    if model_obj['name'] == model_name
                )
            else:
                return None
            
        except StopIteration as err:
            raise DAIClientException("Failed to get model id, model name not found") from err


    def get_model(self, model_id):
        """
        Get a model
        """
        return self._do_get('/ai/models/{}'.format(model_id), "get model")


    def update_model(self, model_id, payload):
        """
        Update model
        """
        return self._do_put(
            '/ai/models/{}'.format(model_id),
            payload,
            "update model {}".format(model_id)
        )


    def delete_model(self, model_id):
        """
        Delete model
        """
        return self._do_delete('/ai/models/{}'.format(model_id), "delete model {}".format(model_id))


    def get_model_defect_list(self, model_id):
        """
        Get the list of model defects
        """
        return self._do_get('/ai/models/{}/defects'.format(model_id), "get list of model defects")


    def get_model_tag_list(self, model_id):
        """
        Get the list of model tags
        """
        return self._do_get('/ai/models/{}/tags'.format(model_id), "get list of model tags")


    def create_tag(self, model_id, tag):
        """
        Add a new tag
        """
        payload = {
            # 'author': author,
            # 'model': model,
            'tag': tag
        }
        return self._do_post(
            '/ai/models/{}/tags'.format(model_id), payload,
            'create a new tag for model {}'.format(model_id)
        )


    def update_tag(self, model_id, tag_id, payload):
        """
        Update a tag
        """
        return self._do_put(
            '/ai/models/{}/tags/{}'.format(model_id, tag_id),
            payload,
            "update tag {} in model {}".format(tag_id, model_id)
        )


    def get_model_release_insights(self, model_id):
        """
        Get release insights
        """
        return self._do_get(
            '/ai/models/{}/release-insights'.format(model_id),
            "get release insights for model {}".format(model_id)
        )


    def get_model_run_list(self, model_id):
        """
        Get model test runs
        """
        return self._do_get(
            '/ai/models/{}/runs'.format(model_id),
            "get model test runs for {}".format(model_id)
        )

    def get_list_runs_details(self, limit=20, offset=0):
        
        return self._do_get(f'/ai/runs?limit={limit}&offset={offset}', "get run list")
    
        #?limit=1&offset=

    def get_run(self, run_id):
        """
        Get run details
        """
        return self._do_get('/ai/runs/{}'.format(run_id), "get run details for {}".format(run_id))


    def delete_run(self, run_id):
        """
        Delete a run
        """
        return self._do_delete('/ai/runs/{}'.format(run_id), "delete run {}".format(run_id))


    def get_model_testcase_run_list(self, model_id):
        """
        Get model testcase runs
        """
        return self._do_get(
            '/ai/models/{}/testcaseruns'.format(model_id),
            "get model testcase runs for {}".format(model_id)
        )


    def create_model_testcase(self, model_id, name, testcase, description="", tags=None, origin=""):
        """
        Create new testcase
        """
        payload = {
            'testcaseName': name,
            'testcase': testcase
        }
        if description:
            payload['description'] = description
        if tags is not None:
            payload['tags'] = ','.join(tags)
        if origin:
            payload['origin'] = origin
        return self._do_post(
            '/ai/models/{}/testcases'.format(model_id), payload,
            "Create testcase {} for model {}".format(name, model_id)
        )


    def get_model_testcase_list(self, model_id):
        """
        Get a list of model testcases
        """
        return self._do_get(
            '/ai/models/{}/testcases'.format(model_id),
            "get a list of model testcases for {}".format(model_id)
        )


    def get_model_testcase(self, model_id, testcase_id):
        """
        Get a model testcase
        """
        return self._do_get(
            '/ai/models/{}/testcases/{}'.format(model_id, testcase_id),
            "get model {} testcase {}".format(model_id, testcase_id)
        )


    def update_model_testcase(self, model_id, testcase_id, payload):
        """
        Update a test case
        """
        return self._do_put(
            '/ai/models/{}/testcases/{}'.format(model_id, testcase_id), payload,
            "update test case {}".format(testcase_id)
        )


    def delete_model_testcase(self, model_id, testcase_id):
        """
        Delete a model testcase
        """
        return self._do_delete(
            '/ai/models/{}/testcases/{}'.format(model_id, testcase_id),
            "delete model {} testcase {}".format(model_id, testcase_id)
        )


    def ping(self):
        """
        Ensure the API is up
        """
        return self._do_get('/ai/ping', "ensure the API is up")


    def get_run_timings_list(self, run_id):
        """
        Get model run timings
        """
        return self._do_get(
            '/ai/runs/{}/timings'.format(run_id),
            "get model run timings for {}".format(run_id)
        )


    def get_smtp_config(self):
        """
        Get SMTP config
        """
        return self._do_get('/ai/smtp', "get smtp config")


    def update_smtp_config(self, payload):
        """
        Update SMTP config
        """
        return self._do_put('/ai/smtp', payload, "update SMTP config")


    def create_user(self, username, password=None, groups=None, license_string=None, role=None):
        """
        Create user
        """
        payload = {'username': username}
        if password is not None:
            payload['password'] = password
        if groups is not None:
            payload['groups'] = groups
        if license is not None:
            payload['license'] = license_string
        if role is not None:
            payload['role'] = role
        return self._do_post('/ai/users', payload, "create user {}".format(username))


    def get_user_list(self):
        """
        Get user list
        """
        return self._do_get('/ai/users', "get user list")


    def get_user(self, user_id):
        """
        Get user
        """
        return self._do_get('/ai/users/{}'.format(user_id), "get user {}".format(user_id))


    def update_user(self, user_id, payload):
        """
        Update user
        """
        return self._do_put(
            '/ai/users/{}'.format(user_id),
            payload,
            "update user {}".format(user_id)
        )


    def delete_user(self, user_id):
        """
        Delete user
        """
        return self._do_delete('/ai/users/{}'.format(user_id), "delete user {}".format(user_id))

    def get_execution(self, execution_id):
        """
        Get user
        """
        return self._do_get(
            '/ai/executions/{}'.format(execution_id),
            "get execution {}".format(execution_id)
        )


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
    '''
    The following section has API calls to none public exposed services
    '''
    def myget_run(self,testconfigtask_id):
        
        return self._do_get(f'/ai/runs?task_instance_id={testconfigtask_id}',"Get run details for a Testconfig")
    
    def myget_testconfigtask(self,testconfigtask_id):
        
        return self._do_get(f'/ai/testconfigtasks/{testconfigtask_id}',"Get a single test config task")
        
    def myget_testconfgitasksummary(self,testconfigtask_id):
        
        return self._do_get(f'/ai/testconfigtasks/{testconfigtask_id}/summary',"Get summary information for a task instance")
        

    '''
    The following section has API calls to none public exposed services
    '''
    def mydelete_lock(self,sut_id):
        
        return self._do_delete(f'/sut_service/api/v1/suts/{sut_id}/lock',"Unlock a SUT")
        
    def myget_test_configurations(self):
        
        return self._do_get('/test_config_service/api/v1/test_configurations',"Get Test Configurations")
    
    def mypost_task_instance(self, username):
        
        payload = {'username': username}
        
        return self._do_post('/task_scheduler_service/api/v1/task_instances/{}'.format(username), payload, "create user {}".format(username))
        #return self._do_post('/task_scheduler_service/api/v1/task_instances/87b2507a-8e28-4662-985c-f65d2b5cee31',"Doing a run")
    