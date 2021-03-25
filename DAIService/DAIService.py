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

import os
import sys
import logging
import json
from multiprocessing import Process, current_process
from multiprocessing import log_to_stderr, get_logger
from time import sleep
#from multiprocessing.util import _log_to_stderr
from dai_client import DAIClient, DAIClientException

from xray_client import XRAYClient,XRAYClientException


def dai_process(client,xrayclient,item):
    logger = logging.getLogger()
    process_id = os.getpid()
    process_name = current_process().name
    #print(f"[MSGS/{process_name}] process started with process id : {process_id}")
    logger.info(f"process started with process id : {process_id}")
    #model_id = client.get_model_id(item['modelname'])
    #testcase_id = next(model_obj['id'] for model_obj in client.get_model_testcase_list(model_id) if model_obj['testcaseName'] == item['testcase'])
    #testcase_result = client.get_model_testcase(model_id,testcase_id)
    #print(f"[MSGS/{process_name}] TestCase results {testcase_result}")
   
    run_result = client.get_run(item['id'])
    if run_result['runtype'] == 'directed':
        while run_result['teststatus'] == 'INCOMPLETE': 
            #print(run_result['teststatus'])
            print(f"[MSGS/{process_name}] Testcase {run_result}")
            sleep(5)
            run_result = client.get_run(item['id'])
            
        model_id = client.get_model_id(item['modelname'])
        #model_testcase_run = client.get_model_testcase_run_list(model_id)
        #testcase_list = client.get_model_testcase_list(model_id)
        #model_id = next(model_obj['id'] for model_obj in client.get_model_list() if model_obj['name'] == args.model)
        testcase_id = next(model_obj['id'] for model_obj in client.get_model_testcase_list(model_id) if model_obj['testcaseName'] == item['testcase'])
        testcase_result = client.get_model_testcase(model_id,testcase_id)
        print(f"[MSGS/{process_name}] Run results {run_result}")
        print(f"[MSGS/{process_name}] TestCase results {testcase_result}")
        #print(f"[MSGS/{process_name}] \"testKey\" : \"{testcase_result['testcaseExternalID']}\",")
        #print(f"[MSGS/{process_name}] \"status\" : \"{run_result['teststatus']}\"")
        #print(f"[MSGS/{process_name}] done with this one")
        with open(r'/Users/pmerrill/PycharmProjects/DAIListener/mapping.json') as jsonFile:
            mapping_data = json.load(jsonFile)

        testPlanKey = None
        for test_PlanKey in mapping_data['xray']['testPlanKey']:
            if testcase_result['testcaseExternalID'] in mapping_data['xray']['testPlanKey'][test_PlanKey]:testPlanKey = mapping_data['xray']['testPlanKey'][test_PlanKey]
        if testPlanKey == None: testPlanKey = mapping_data['xray']['testPlanKey']['DEFAULT']
        if run_result['teststatus'] in mapping_data['xray']['teststatus']: xray_teststatus = mapping_data['xray']['teststatus'][run_result['teststatus']]
        else: xray_teststatus = mapping_data['xray']['teststatus']['DEFAULT']
        xray_result = {"info": {"summary": "Execution of automated tests for release v1.0 - update via API","description": "This execution is automatically created when importing execution results from an external source","version": "1.0.0","user": "philippa","revision": "1.0.0","startDate": f"{run_result['starttime']}","finishDate": f"{run_result['endtime']}","testPlanKey": f"{testPlanKey}","testEnvironments": ["TestEnvironmentA"]},"tests": []}
        xray_test = {"testKey": f"{testcase_result['testcaseExternalID']}","start": f"{run_result['starttime']}","finish":f"{run_result['endtime']}","comment": "Execution finished","status": f"{xray_teststatus}"}
        xray_result['tests'].append(xray_test)
        print(f"\n[MSGS/{process_name}] {json.dumps(xray_result)}")
        testrun = xrayclient.post_execution(xray_result)
        print(f"[MSGS/{process_name}] {testrun}")
    else:
        print(f"[MSGS/{process_name}] Not a testcase execution so ignoring results for {item['id']}")
        while run_result['teststatus'] == 'INCOMPLETE': 
            #print(run_result['teststatus'])
            print(f"[MSGS/{process_name}] Exploratory {run_result}")
            sleep(5)
            run_result = client.get_run(item['id'])
        print(f"[MSGS/{process_name}] Execution of {item['id']} has finished")


if __name__ == '__main__':
    
    processes = []
    #numbers = [1, 2, 3, 4]
    log_to_stderr()
    logging.basicConfig(format='%(levelname)s:%(message)s DAI Service', level=logging.INFO)
    logger = get_logger()
    logger.setLevel(logging.INFO) 
    logging.basicConfig(format='%(levelname)s:%(message)s DAI Service', level=logging.INFO)
    logging.Formatter('%(levelname)s:%(message)s DAI Service')

    # create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # create console handler and set level to debug
    #ch = logging.StreamHandler()
    #ch.setLevel(logging.INFO)
    
    # create formatter
    #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # add formatter to ch
    #ch.setFormatter(formatter)
    
    # add ch to logger
    #logger.addHandler(ch)
    
    # 'application' code
    logger.info('main started')

    #for number in numbers:
    # url = "https://eggplant-partners.dai.eggplant.cloud"
    url = "https://eval50.dai.eggplant.cloud"
    username = "philippa.merrill1@eggplantsoftware.com"
    # group = "DAITest"
    group = "philippa.merrill1@eggplantsoftware.com"
    password = "p1an0K3y$28"
    
    keeprunning = True

    try:
        # Construct the client 
        client = DAIClient(url, username, password)
        group_id = next(group_obj['id'] for group_obj in client.get_group_list() if group_obj['groupname'] == group)
        xrayclient = XRAYClient("https://xray.cloud.xpand-it.com", "A9A206156F5E4D2D9892A603290F06FB", "4080db13e5e33b1b4782c553f0fa39de55bca6930c4beb5d1d2d841e9bd4c211")

    except DAIClientException as err:
        print(f"An DAI exception occurred: {err}")
        pass
    except XRAYClientException as err:
        print(f"An XRAY exception occurred: {err}")
        pass  
    except Exception as err:
        print(f"An unexpected exception occurred: {err}")
        
    while keeprunning == True:
        try:
            run_list = client.get_list_runs_details(5)
            #for item in run_list['items']:
                #print(f"limit 5 {item}")
            run_list = client.get_list_runs_details(20,run_list['total_count']-20)
            for item in run_list['items']:
                #print(f"Last runs {item}")
                process_running = False
                for process in processes: 
                    if process.name == f"RUNID{item['id']}":
                        process_running = True
                if (item['groupid'] == group_id and item['teststatus'] == 'INCOMPLETE' and not process_running):
                    #dai_process(client,item)
                    print (f"[MAIN] Starting new process RUNID{item['id']}")
                    process = Process(target=dai_process, name=f"RUNID{item['id']}", args=(client,xrayclient,item))
                    processes.append(process)
                    process.start()
            sleep(0.1)
            #print(f"[MAIN] processes running {len(processes)} = {processes}")
            for runprocess in processes:
                if not runprocess.is_alive():
                    print (f"[MAIN] Finished execution closing {runprocess}")
                    runprocess.join()
                    processes.remove(runprocess)
                    break
                #else:
                #    print(f"loop running process {runprocess}")
                    
        except DAIClientException as err:
            print(f"An DAI exception occurred: {err}")
            pass
        except XRAYClientException as err:
            print(f"An XRAY exception occurred: {err}")
            pass  
        except Exception as err:
            print(f"An unexpected exception occurred: {err}")
