#!/usr/bin/env python
# -*- coding: utf-8 -*-

import httplib
import base64
from copy import deepcopy
try:
    import json
except ImportError:
    import simplejson as json
import time
import logging
import subprocess
import os
import pwd
import sys
#from exceptions import PostCheckException


if False:
    logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='aspy.log',
                filemode='w')

#################################################################################################
#定义一个StreamHandler，将INFO级别或更高的日志信息打印到标准错误，并将其添加到当前的日志处理对象#

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)


logger = logging.getLogger('aspy')

class analyticServer:
    https = None
    server_version = None
    request_token = None
    reply_nonce = None
    last_response_body = None
    knox_url_context = None
    knox_enable = False
    sslEnable = False
    authCache = None

    def __init__(self, host, port, urlcontext=None, useSSL=True):
        if useSSL:
            self.sslEnable = True
            self.https = httplib.HTTPSConnection(host, port)
        else:
            self.https = httplib.HTTPConnection(host, port)

    def __executeHttp(self, method, url, headers_in = None, body = None):
        logger.info("Execute : %s" % url)
        headers = {}
        if headers_in is not None:
            headers = headers_in
        if self.request_token is not None:
            headers["request-token"] = self.request_token
        if self.reply_nonce is not None:
            headers["reply-nonce"] = self.reply_nonce
        if self.request_token is not None and self.reply_nonce is not None:
            cookie = "request-token=" + self.request_token + "; reply-token=balancer.http1; reply-nonce=" + self.reply_nonce
            headers["Cookie"] = cookie
        self.https.request(method, url, body, headers)
        response = self.https.getresponse()
        self.request_token = response.getheader("request-token")
        self.reply_nonce = response.getheader("reply-nonce")
        self.last_response_body = response.read()
        logger.info(self.last_response_body)
        return response

    def login(self, username, password, tenant = None):
        auth = base64.b64encode('%s:%s' % (username, password))
        headers = { "Authorization" : "Basic %s" % auth}
        if tenant is not None:
            headers["consumer"] = tenant
        else:
            tenant = "None"
        if self.sslEnable and self.authCache is None:
            self.authCache = deepcopy(headers)
        headers["Content-Type"] = "application/json"
        logger.info("Logging in to analytic server tenant '" + tenant + "' as user '" + username + "'")
        url = "%s/analyticserver/security/login" % (self.knox_url_context if self.knox_enable else '')
        response = self.__executeHttp("GET", url, headers)
        self.server_version = response.getheader("server-version")
        if self.server_version is None:
            raise PostCheckException("Can't login Analytic Server, please check username and password")

        logger.info("Login succeeded, AS version is : %s" % self.server_version)
        

    def get_components(self):
        logger.info("Getting components")
        url = "%s/analyticserver/analytic/components" % (self.knox_url_context if self.knox_enable else '')
        self.__executeHttp("GET", url, self.__generateReqHeader())

    def delete_tenant(self, tenant):
        logger.info("Deleting tenant: '" + tenant + "'")
        url = "%s/analyticserver/security/consumer/" % (self.knox_url_context if self.knox_enable else '')
        self.__executeHttp("DELETE", url + tenant, self.__generateReqHeader())

    def create_tenant(self, tenant):
        logger.info("Creating tenant: '" + tenant + "'")
        url = "%s/analyticserver/security/consumer/" % (self.knox_url_context if self.knox_enable else '')
        self.__executeHttp("PUT", url + tenant, self.__generateReqHeader())

    def delete_project(self, project):
        logger.info("Deleting project: '" + project + "'")
        url = "%s/analyticserver/project/" % (self.knox_url_context if self.knox_enable else '')
        self.__executeHttp("DELETE", url + project, self.__generateReqHeader())

    def create_project(self, project):
        logger.info("Creating project: '" + project + "'")
        url = "%s/analyticserver/project/" % (self.knox_url_context if self.knox_enable else '')
        self.__executeHttp("PUT", url + project, self.__generateReqHeader())

    def lock_project(self, project):
        logger.info("Locking project: '" + project + "'")
        url = "%s/analyticserver/project/lock/" % (self.knox_url_context if self.knox_enable else '')
        self.__executeHttp("PUT", url + project, self.__generateReqHeader())

    def commit_project(self, project):
        logger.info("Committing project: '" + project + "'")
        url = "%s/analyticserver/project/commit/" % (self.knox_url_context if self.knox_enable else '')
        self.__executeHttp("PUT", url + project, self.__generateReqHeader())

    def create_folder(self, project, folder):
        logger.info("Creating folder: '" + folder + "' in project '" + project + "'")
        url = "%s/analyticserver/fs/folder/" % (self.knox_url_context if self.knox_enable else '')
        self.__executeHttp("PUT", url + project + "/" + folder, self.__generateReqHeader())

    def create_file(self, project, filename, local_file, flag=True):
        logger.info("Creating file: '" + filename + "' in project '" + project + "' (" + local_file.name + ")")
        url = "%s/analyticserver/fs/file/" % (self.knox_url_context if self.knox_enable else '')
        self.__executeHttp("PUT", url + project + "/" + filename, self.__generateReqHeader(flag), local_file)

    def get_file(self, project, filename):
        logger.info("Getting file: '" + filename + "' in project '" + project)
        url = "%s/analyticserver/fs/file/" % (self.knox_url_context if self.knox_enable else '')
        self.__executeHttp("GET", url + project + "/" + filename, self.__generateReqHeader())

    def create_datasource(self, datasource, project, datafile, datamodel, datainproject=True):
        logger.info("Creating datasource: '" + datasource + "' in project '" + project)
        datasource_data = json.dumps({"data-model" : project + "/" + datamodel, "projects" : [project], "files" : [], "type" : "file"})
        url = "%s/analyticserver/ds/" % (self.knox_url_context if self.knox_enable else '')
        self.__executeHttp("PUT", url + datasource, self.__generateReqHeader(), datasource_data)
        logger.info("Adding file '" + datafile + "' to datasource: '" + datasource)

        if datainproject==True:
            file_data = json.dumps([{"path" : project + "/" + datafile, "inputSpecification" : {"parser" : {"name" : "delimited_parser", "config" : {}}}}])
        else:
            file_data = json.dumps([{"path" : "file:/" + "/" + datafile, "inputSpecification" : {"parser" : {"name" : "delimited_parser", "config" : {}}}}])

        url = "%s/analyticserver/ds/files/" % (self.knox_url_context if self.knox_enable else '')
        self.__executeHttp("POST", url + datasource, self.__generateReqHeader(), file_data)

    def create_hcatalog_datasource(self, datasource, project, hiveTabelName, datamodel):
        self.__uploadFileToHDFS('/data/testdata.xml', '/tmp/creatinghivetabletesting')
        logger.info("Creating hcatalog datasource: '" + datasource + "' in project '" + project)
        datasource_data = json.dumps({"data-model" : "file://"+datamodel, "projects" : [project], "type" : "hcatalog","systemAttributes" : {"com.ibm.spss.ae.hcatalog.tablename":hiveTabelName}})
        url = "%s/analyticserver/ds/" % (self.knox_url_context if self.knox_enable else '')
        self.__executeHttp("PUT", url + datasource, self.__generateReqHeader(), datasource_data)

    def create_writable_datasource(self, datasource, project):
        logger.info("Creating writable datasource: '" + datasource + "' in project '" + project)
        datasource_data = json.dumps({"projects" : [project], "files" : [], "type" : "file", "systemAttributes" : { "writable":"true", "dataDestination":"ds://"+datasource+"/data" }})
        url = "%s/analyticserver/ds/" % (self.knox_url_context if self.knox_enable else '')
        self.__executeHttp("PUT", url + datasource, self.__generateReqHeader(), datasource_data)

    def remove_datasource(self, datasource):
        logger.info("Removing datasource: '" + datasource)
        url = "%s/analyticserver/ds/" % (self.knox_url_context if self.knox_enable else '')
        self.__executeHttp("DELETE", url + datasource, self.__generateReqHeader(), "")

    def get_datasource_datamodel(self, datasource):
        headers = {}
        url = "%s/analyticserver/ds/datamodel/" % (self.knox_url_context if self.knox_enable else '')
        response = self.__executeHttp("GET", url + datasource, self.__generateReqHeader())
        return self.last_response_body

    def get_datasource_records(self, datasource, page_start, page_count):
        headers = self.__generateReqHeader()
        headers["items-start"] = str(page_start)
        headers["items-count"] = str(page_count)
        url = "%s/analyticserver/ds/records/" % (self.knox_url_context if self.knox_enable else '')
        response = self.__executeHttp("GET", url + datasource, headers)
        return self.last_response_body

    def run_asl(self, project, asl, extra_headers = None):
        # Note: asl parameter may be a file or string
        if hasattr(asl, "name"):
            logger.info("Running ASL from file: '" + asl.name + "' in project '" + project)
        else:
            logger.info("Running ASL: '" + asl + "' in project '" + project)
        headers = self.__generateReqHeader(False)
        headers["project"] = project
        if extra_headers is not None:
            headers.update(extra_headers)
        url = "%s/analyticserver/analytic/asl/execution" % (self.knox_url_context if self.knox_enable else '')
        self.__executeHttp("POST", url, headers, asl)
        json_response = json.loads(self.last_response_body)
        exeutionId = json_response['status']['executionId']

        status = self.get_status(exeutionId)
        while status['status']['code'] == "AEQAE1600I":
            logger.info("Waiting for job, current status = " + status['status']['code'])
            time.sleep(1)
            status = self.get_status(exeutionId)
        if not status['status']['code'] == "AEQAE1601I":
            logger.info("Job failed with code " + status['status']['code'])
            logger.info(status)
            raise Exception("ASL Execution failed")

    def get_status(self, executionId):
        logger.info("Getting status for job: '" + executionId + "'")
        url = "%s/analyticserver/analytic/execution/status/" % (self.knox_url_context if self.knox_enable else '')
        self.__executeHttp("GET", url + executionId, self.__generateReqHeader())
        json_response = json.loads(self.last_response_body)
        return json_response

    def logout(self):
        url = "%s/analyticserver/security/logout" % (self.knox_url_context if self.knox_enable else '')
        self.__executeHttp("GET", url, self.__generateReqHeader())
        self.request_token = None
        self.reply_nonce = None

    def create_absolute_path_file(self, filename, local_file):
        logger.info("Creating file: '" + filename + "' (" + local_file.name + ")")
        url = "%s/analyticserver/fs/file/~/file://" % (self.knox_url_context if self.knox_enable else '')
        self.__executeHttp("PUT", url + filename, self.__generateReqHeader(), local_file)

    def delelte_absolute_path_file(self, filename):
        logger.info("Delete file: " + filename)
        url = "%s/analyticserver/fs/~/file://" % (self.knox_url_context if self.knox_enable else '')
        self.__executeHttp("DELETE", url + filename, self.__generateReqHeader(), None)

    def removeHcatalogData(self):
        try:
            #need to remove created dir "/user/creatinghivetabletesting" in pre check 
            FNULL = open(os.devnull,'w')
            rmCommand = "hadoop fs -rm -r /tmp/creatinghivetabletesting"
            popen = subprocess.Popen( rmCommand, shell=True, stdout=FNULL,stderr=subprocess.STDOUT)             
            #popen.communicate()
            #Do not hive table "testds" in order to make postcheck still pass at the second time, if not run precheck in advance
#             pw_record = pwd.getpwnam('hive')
#             hive_uid = pw_record.pw_uid
#             hive_gid = pw_record.pw_gid 
#             dropCommand = "hive -e 'drop table if exists testds'"
#             popen = subprocess.Popen( dropCommand, shell=True, stdout=FNULL,stderr=subprocess.STDOUT,preexec_fn=self.__setCommandUser(hive_uid, hive_gid))
            #popen.communicate()
        except Exception as e:
            logger.error(e)
            logger.info("can not remove uploaded data or hive table")

    def __generateReqHeader(self, hasContentType = True):
        headers = {}
        if self.sslEnable:
            headers = deepcopy(self.authCache)
        if hasContentType:
            headers["Content-Type"] = "application/json"
        return headers

    def __setCommandUser(self,user_uid, user_gid):
        def result():            
            os.setgid(user_gid)
            os.setuid(user_uid)           
        return result

    def __uploadFileToHDFS(self, file, dest):
        mkdirCommand = "hadoop fs -mkdir -p " + dest
        popen = subprocess.Popen(mkdirCommand, shell=True, stdout=subprocess.PIPE)
        upload_output = popen.communicate()
        logger.info(mkdirCommand + " output is " + str(upload_output))

        mkdirCommand = "hadoop fs -mkdir -p " + dest + "/data"
        popen = subprocess.Popen(mkdirCommand, shell=True, stdout=subprocess.PIPE)
        upload_output = popen.communicate()
        logger.info(mkdirCommand + " output is " + str(upload_output))

        putCommand = "hadoop fs -put -f ." + file + " " + dest + file
        popen = subprocess.Popen(putCommand, shell=True, stdout=subprocess.PIPE)
        upload_output =  popen.communicate()
        chmodCommand = "hadoop fs -chmod -R 777 " + dest + "/data"
        popen = subprocess.Popen(chmodCommand, shell=True, stdout=subprocess.PIPE)
        popen.communicate()
        logger.info(putCommand + " output is " + str(upload_output))
