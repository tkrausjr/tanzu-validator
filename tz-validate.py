#!/usr/bin/env python3

import ssl
import requests
from datetime import datetime
from datetime import timedelta
import sys
import json
import os
import yaml
import subprocess
import argparse
import pyVmomi
from http import cookies
from pyVmomi import vim, vmodl
from pyVim import connect
from pyVmomi import pbm, VmomiSupport
import logging
from kubernetes import client
from kubernetes import config

# Define ANSI Colors
CRED = '\033[91m'
CEND = '\033[0m'
CGRN = '\033[92m'

parser = argparse.ArgumentParser(description='vcenter_checks.py validates environments for succcesful Supervisor Clusters setup in vSphere 7 with Tanzu. Uses YAML configuration files to specify environment information to test.')
parser.add_argument('--version', action='version',version='%(prog)s v0.6')
parser.add_argument('-f', '--file', required=True, action='store', help='(Required) Params YAML file')
#parser.add_argument('-n','--networking',choices=['nsxt','vsphere'], help='Networking Environment(nsxt, vsphere)', default='vsphere')
parser.add_argument('-v', '--verbosity', nargs="?", choices=['INFO','DEBUG'], default="INFO")
network_type="vsphere"
verbosity = parser.parse_args().verbosity

# Setup logging parser
logger=logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s: %(asctime)s: %(name)s: %(lineno)d: %(message)s', "%Y-%m-%d %H:%M:%S")

file_handler = logging.FileHandler('wcp_precheck_results.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

stream_handler=logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)

if verbosity == 'DEBUG':
    file_handler.setLevel(logging.DEBUG)
    stream_handler.setLevel(logging.DEBUG)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

logger.debug("Looking in for Parameters file {}".format(parser.parse_args().file))
cfg_yaml = yaml.load(open(parser.parse_args().file), Loader=yaml.Loader)

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
headers = {'content-type': 'application/json'}

def checkdns(hostname, ip):
    ## Validate Name Resolution for a hostname / IP pair
    try:
        for d in cfg_yaml["DNS_SERVERS"]:
            fwd_lookup = subprocess.check_output(['dig', cfg_yaml["VC_HOST"], '+short', str(d)], universal_newlines=True).strip()
            rev_lookup = subprocess.check_output(['dig', '-x', cfg_yaml["VC_IP"], '+short', str(d)], universal_newlines=True).strip()[:-1]
            logger.debug('---- Checking DNS Server {} for A Record for {}'.format(d, hostname))
            logger.debug("---- Result of Forward Lookup {}".format(fwd_lookup))
            logger.debug("---- Result of Reverse Lookup {}".format(rev_lookup))
            if cfg_yaml["VC_IP"] != fwd_lookup:
                logger.error(CRED + "---- ERROR - Missing A Record. The Hostname, " + hostname + " does not resolve to the IP " + ip + CEND)
            else:
                logger.info(CGRN +"---- SUCCESS-The Hostname, " + hostname + " resolves to the IP " + ip + CEND)
            
            if cfg_yaml["VC_HOST"] != rev_lookup:
                logger.error(CRED + "---- ERROR - Missing PTR Record. The IP, " + ip + " does not resolve to the Hostname " + hostname + CEND)
            else:
                logger.info(CGRN +"---- SUCCESS-The IP, " + ip + " resolves to the Hostname " + hostname + CEND)


    except subprocess.CalledProcessError as err:
        raise ValueError("---- ERROR - Failure in the NSLookup subprocess call")

def check_active(host):
    if os.system("ping -c 3 " + host.strip(";") + ">/dev/null 2>&1" ) == 0:
        logger.info(CGRN +"---- SUCCESS - Can ping {}. ".format(host) + CEND)
        #return 0
    
    else:
        logger.error(CRED +"---- ERROR - Cant ping {}. ".format(host) + CEND)
        #return 1

def vc_connect(s,vchost, vcuser, vcpass):
    si = None
    try:
        logger.info("---- Trying to connect to VCENTER SERVER . . .")
        si = connect.SmartConnectNoSSL('https', vchost, 443, vcuser, vcpass)
        logger.info(CGRN + "---- SUCCESS-Connected to vCenter {}".format(si.content.about.name) + CEND)

        # Get Rest session ID
        response = s.post('https://' + vchost + '/api/session', auth=(vcuser, vcpass))
        if response.ok:
            sessionId = response.json()
        return si, si.RetrieveContent(), sessionId

    except IOError as e:
        logger.error(CRED +"---- ERROR - connecting to vCenter, {}".format(vchost)  + CEND)
        logger.error(CRED +"---- Error is: {}".format(e) + CEND)
        logger.error("---- Exiting program. Please check vCenter connectivity and Name Resolution: ")
        sys.exit(e)
    


def get_vc_svc_status(s,vcip,svc_name, session_id):
    startup_json_response = s.get('https://' + vcip + '/api/vcenter/services/' + svc_name, headers={"vmware-api-session-id": session_id})
    if startup_json_response.status_code==200:
        logger.debug("---- DEBUG Successfully obtained Service Status for WCP Service. Response Code %s " % startup_json_response.status_code )
        logger.debug("---- DEBUG Response text is {}".format(startup_json_response.text))
        results = json.loads(startup_json_response.text)
        if (results['state']=="STARTED" and results['health']=="HEALTHY"):
            logger.info(CGRN + "---- SUCCESS-WCP Service Status {}".format(results['state']) + CEND)
            logger.info(CGRN + "---- SUCCESS-WCP Service Health {}".format(results['health']) + CEND)
        else :
            logger.error(CGRN + "---- ERROR-WCP Service Status {}".format(results['state']) + CEND)
            logger.error(CGRN + "---- ERROR-WCP Service Health {}".format(results['health']) + CEND)
    else:
        print("---- ERROR-Unable to get status of WCP Service")
        print("---- Response JSON is %s " % startup_json_response )
        return 0

def get_obj(content, vimtype, objectname):
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == objectname:
            logger.debug("---- Item:" + c.name) 
            logger.info(CGRN+"---- SUCCESS - Managed Object " + objectname + " found."+ CEND)
            obj = c
            break
    if not obj:
        logger.error(CRED +"---- ERROR - Managed Object " + objectname + " not found."+ CEND)
    return obj
      
def get_cluster(dc, objectname):
    obj = None
    clusters = dc.hostFolder.childEntity
    for cluster in clusters:  # Iterate through the clusters in the DC
        if cluster.name == objectname:
            logger.info(CGRN+"---- SUCCESS - Cluster Object " + objectname + " found."+ CEND)
            obj = cluster
            break
    if not obj:
        loggger.error(CRED + "---- ERROR - Cluster " + name + " not found.")
    return obj

def get_hosts_in_cluster(cluster):
    hosts = []
    for host in cluster.host :  # Iterate through the hosts in the cluster
        hosts.append(host)
        logger.debug ("---- Found ESX Host {} in cluster {}".format( host.name,cluster.name))
        if host.overallStatus != "green":
            logger.error(CRED+"---- WARNING - ESXi Host {} overall Status is {} and not Green. Please correct any issues with this host.".format(host.name,host.overallStatus ) + CEND)
        else:
            logger.info(CGRN+"---- SUCCESS - ESXi Host {} overall Status is Green. ".format(host.name)+ CEND)      
    return hosts


def get_host_times(esx_hosts, host_times):
    for host in esx_hosts :  # Iterate through the hosts in the cluster
        host_time=host.configManager.dateTimeSystem.QueryDateTime()
        logger.debug("---- ESXi Host {} time is {}.".format(host.name,host_time)+ CEND)
        corrected_time = host_time.strftime('%H:%M:%S')
        host_times[host.name]=corrected_time
        logger.debug("---- ESXi Host {} 24hr time is {}.".format(host.name,corrected_time)+ CEND)
    return host_times

def detect_time_drift(host_times):
    # Detect minimum and max time in a range of times in the host_times dict
    min_time = datetime.strptime(min(host_times.values()), '%H:%M:%S')
    logger.info("---- Lowest Time of all the Nodes is {}.".format(min_time)+ CEND)
    max_time = datetime.strptime(max(host_times.values()), '%H:%M:%S')
    logger.info("---- Highest Time of all the Nodes is {}.".format(max_time)+ CEND)
    # Define maximum allowable timedrift Min vs Max in Seconds
    max_delta =timedelta(days=0,seconds=30,minutes=0)
    delta = max_time - min_time
    logger.info("---- Maximum allowable time drift is {} seconds.".format(max_delta))
    logger.info("---- Largest Time delta between all nodes is {} seconds.".format(delta)+ CEND)
    
    if delta < max_delta:
        logger.info(CGRN+"---- SUCCESS - Max Time Drift between all nodes is {} which is below Maximum.".format(delta)+ CEND)

    else:
        logger.error(CRED+"---- ERROR - Max Time Drift between all nodes is {} which is higher than configured Max.".format(delta)+ CEND)
    

# retrieve SPBM API endpoint
def GetPbmConnection(vpxdStub):
    sessionCookie = vpxdStub.cookie.split('"')[1]
    httpContext = VmomiSupport.GetHttpContext()
    cookie = cookies.SimpleCookie()
    cookie["vmware_soap_session"] = sessionCookie
    httpContext["cookies"] = cookie
    VmomiSupport.GetRequestContext()["vcSessionCookie"] = sessionCookie
    hostname = vpxdStub.host.split(":")[0]

    context = ssl._create_unverified_context()
    pbmStub = pyVmomi.SoapStubAdapter(
        host=hostname,
        version="pbm.version.version1",
        path="/pbm/sdk",
        poolSize=0,
        sslContext=context)
    pbmSi = pbm.ServiceInstance("ServiceInstance", pbmStub)
    pbmContent = pbmSi.RetrieveContent()
    logger.debug(pbmContent)
    return (pbmSi, pbmContent)

def get_storageprofile(sp_name, pbmContent ):
    profiles = []
    pm = pbmContent.profileManager
    # Get all Storage Policies
    profileIds = pm.PbmQueryProfile(resourceType=pbm.profile.ResourceType(
        resourceType="STORAGE"), profileCategory="REQUIREMENT"
    )
    logger.debug(profileIds)
    if len(profileIds) > 0:
        logger.debug("---- Retrieved Storage Policies.")
        profiles = pm.PbmRetrieveContent(profileIds=profileIds)
        obj = None
        for profile in profiles:
            logger.debug("---- SP Name: %s " % profile.name)
            if profile.name == sp_name:
                logger.info(CGRN+"---- SUCCESS - Found Storage Policy {}.".format(sp_name)+ CEND)
                obj = profile
                break
        if not obj:
            logger.error(CRED + "---- ERROR - Storage Policy {} not found".format(sp_name)+ CEND) 
        return obj        
    else:
        logger.error(CRED + "---- ERROR - No Storage Policies found or defined "+ CEND)


def check_health_with_auth(verb, endpoint, port, url, username, password):
    s = requests.Session()
    s.verify = False
    if verb=="get":
        logger.debug("---- Performing Get")
        response=s.get('https://'+endpoint+':'+str(port)+url, auth=(username,password))
    elif verb=="post":
        logger.debug("---- Performing Post")
        response=s.post('https://'+endpoint+':'+str(port)+url, auth=(username,password))
        
    logger.debug(response)
    if not response.ok:
        logger.error(CRED + "---- ERROR - Received Status Code {} ".format(response.status_code) + CEND) 
    else:
        logger.info(CGRN + "---- SUCCESS - Received Status Code {} ".format(response.status_code) + CEND) 
       
def connect_vc_rest(vcip, userid, password):
    s = requests.Session()
    s.verify = False
    # Connect to VCenter and start a session
    session = s.post('https://' + vcip + '/rest/com/vmware/cis/session', auth=(userid, password))
    if not session.ok:
        logger.error(CRED + "---- ERROR - Could not establish session to VC, status_code ".format(session.status_code) + CEND) 
    else:
        logger.info(CGRN + "---- SUCCESS - Successfully established session to VC ".format(session.status_code) + CEND) 

    session_id = json.loads(session.text)["value"]
    # token_header = {'vmware-api-session-id': token}
    return s, session_id

def check_cluster_readiness(vc_session, vchost, cluster_id):
    response = vc_session.get('https://'+vchost+'/api/vcenter/namespace-management/cluster-compatibility?')
    if response.ok:
        logger.debug("---- response text is {}".format(response.text))
        wcp_clusters = json.loads(response.text)
        if len(json.loads(response.text)) == 0:
            logger.error(CRED+"---- ERROR - No clusters returned from WCP Check"+ CEND)
        else:
            # If we Found clusters that are not compatible with WCP
            logger.debug(type(wcp_clusters))
            reasons = None
            for c in wcp_clusters:
                logger.debug("cluster is {}".format(c['cluster']))
                if c['cluster'] == cluster_id:
                    if c["compatible"]==True:
                        logger.info(CGRN +"---- SUCCESS - Cluster {} IS compatible with Workload Control Plane.".format(cluster_id) + CEND)
                    else:
                        logger.error(CRED +"---- ERROR - Cluster {} is NOT compatible for reasons listed below.".format(cluster_id) + CEND)
                        reasons = c["incompatibility_reasons"]
                        logger.debug(reasons)
                        for reason in reasons:
                            logger.error(CRED +"---- + Reason-{}".format(reason['default_message'])+ CEND)
                    break
            return reasons   

def get_vc_time(vc_session,vc_host):
    host_times = {}
    json_response = vc_session.get('https://'+vc_host+'/rest/appliance/system/time')
    if json_response.ok:
        logger.debug("---- Response text is {}".format(json_response.text))
        results = json.loads(json_response.text)
        vctime = results["value"]["time"].replace(" ","")
        logger.debug(CGRN +"---- vCenter time is {}".format(vctime) + CEND )
        corrected_time = datetime.strptime(vctime, '%I:%M:%S%p').strftime('%H:%M:%S')
        logger.info("---- vCenter 24hr time is {}".format(corrected_time)  )
        host_times[vc_host]=corrected_time
    else:
        logger.error(CRED + "---- ERROR - Received Status Code {} ".format(json_response.status_code) + CEND) 
        host_times[vc_host]=None
    return host_times

def get_content_library(vc_session,vc_host):
    json_response = vc_session.get('https://' + vc_host + '/rest/com/vmware/content/library')
    if json_response.ok:
        results = json.loads(json_response.text)["value"]
        if len(results)== 0:
              logger.info(CRED +"---- ERROR - No content libraries found on vCenter" + CEND )
        else:
            for result in results:
                json_response = vc_session.get('https://' + vc_host + '/rest/com/vmware/content/library/id:' + result)
                if json_response.ok:
                    cl_library = json.loads(json_response.text)["value"]
                    logger.info(CGRN +"---- SUCCESS - Found Content Library named {}".format(cl_library["name"]) + CEND )
                    return cl_library["id"]
                else:
                    logger.info(CRED +"---- ERROR - Unable to return info about content library " + CEND )
    else:
        logger.info(CRED +"---- ERROR - Unable to return info about content libraries. " + CEND )
    return 0  

def check_wcp_cluster_status(s,vcip,cluster,session_id):
    response=s.get('https://' + vcip + '/api/vcenter/namespace-management/clusters/domain-c8', headers={"vmware-api-session-id": session_id} )
    result = json.loads(response.text)
    logger.debug(CRED +"---- DEBUG - RESPONSE TEXT = {}".format(response.text) + CEND )
    if response.ok:
        logger.debug(CRED +"---- DEBUG - Result = ".format(result) + CEND )
        if result["config_status"] == "RUNNING":
            if result["kubernetes_status"] == "READY":
                logger.info(CGRN +"---- SUCCESS - vSphere w/ Tanzu status is {}".format(result["config_status"]) + CEND )
                logger.info(CGRN +"---- SUCCESS - vSphere w/ Tanzu Supervisor Control Plane K8s API is {}".format(result["config_status"]) + CEND )
                return result["api_server_cluster_endpoint"]
        else:
            logger.info(CGRN +"---- ERROR - One or more problems found with vSphere w/ Tanzu" + CEND )
            logger.info(CGRN +"----         vSphere w/ Tanzu status is {}".format(result["config_status"]) + CEND )
            logger.info(CGRN +"----         vSphere w/ Tanzu Supervisor Control Plane K8s API is {}".format(result["config_status"]) + CEND )
            return 0
    else:
        logger.error(CRED +"---- ERROR - API Call JSON Result = ".format(result) + CEND )
        logger.error(CRED +"---- ERROR - API Call Result = ".format(response) + CEND )
        return 0

def avi_login(controller,username,password):
    login = requests.post('https://'+controller+'/login', verify=False, data={'username': username, 'password': password})
    if not login.ok:
        print ("Unable to Login to Avi Controller :  "+login.content.decode("utf-8"))
        return 0,0
    else:
        results = json.loads(login.text)
        logger.debug("Successfully Logged in, received Status Code  =" , login.status_code)
        return login.cookies['sessionid'],results["version"]['Version']


def get_avi_object_health(ip, avi_sessionid,object,uuid):
    resp = requests.get('https://'+ip+'/api/analytics/healthscore/'+object+'/'+uuid, verify=False, cookies=dict(sessionid= avi_sessionid))

    if not resp.ok:
        print ("Unable to get healthscore for pool :  "+resp.content.decode("utf-8"))
        return 0
    else:
        results = json.loads(resp.text)
        logger.debug("Successfully queried object health, received Status Code  =" , resp.status_code)
        return results

def get_avi_objects(ip, avi_sessionid,object):
    resp = requests.get('https://'+ip+'/api/'+object+'?fields=name,uuid', verify=False, cookies=dict(sessionid= avi_sessionid))
    if not resp.ok:
        print ("Unable to get Avi Object :  "+resp.content.decode("utf-8"))
        return 0
    else:
        logger.debug("Successfully queried Avi object received Status Code  =" , resp.status_code)
        dict_response = json.loads(resp.text)
        return dict_response['results']

#################################   MAIN   ################################
def main():
    logger.info("Workload Control Plane Network Type is {} ".format(network_type))
    # Check YAML file for missing paramters 
    logger.info("-- Checking Required YAML inputs for program: \n ")
    for k, v in cfg_yaml.items():
        if v == None:
            logger.error(CRED +"ERROR - Missing required value for {}".format(k) + CEND) 
        else:
            logger.debug(CGRN +"SUCCESS - Found value, {} for key, {}".format(v,k)+ CEND) 
    
    logger.info("************ Beginning vCenter Environment Testing ************")
    
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    headers = {'content-type': 'application/json'}
    s = "Global"
    s = requests.Session()
    s.verify = False

    # Check if VC is resolvable and responding
    logger.info("--vCenter TEST 2 - Checking vCenter IP is Active for vCenter")
    vc_status = check_active(cfg_yaml["VC_IP"])
    logger.info("--vCenter TEST 2 - Checking DNS Servers are reachable on network")
    for dns_svr in cfg_yaml["DNS_SERVERS"]:
        check_active(dns_svr)
    logger.info("--vCenter TEST 2 - Checking Name Resolution for vCenter FQDN {} to IP {}".format(cfg_yaml["VC_HOST"], cfg_yaml["VC_IP"] ))
    checkdns(cfg_yaml["VC_HOST"], cfg_yaml["VC_IP"] )
    
    logger.info("--vCenter TEST 3 - Checking VC is reachable via API using provided credentials")
    # Connect to vCenter and return VAPI content objects
    si, vc_content, sessionId = vc_connect(s,cfg_yaml['VC_HOST'],cfg_yaml['VC_SSO_USER'],cfg_yaml['VC_SSO_PWD'] )
    content = si.RetrieveContent()
    search_index=si.content.searchIndex

    # Search for all VM Objects in vSphere API
    objview = content.viewManager.CreateContainerView(content.rootFolder,[vim.VirtualMachine],True)
    vmList = objview.view
    objview.Destroy()
    logger.debug("--vCenter Found a total of %s VMS on VC. " % str(len(vmList)))

    # Check for THE DATACENTER
    logger.info("--vCenter TEST4 - Checking for the  Datacenter")
    dc = get_obj(vc_content, [vim.Datacenter], cfg_yaml['VC_DATACENTER'])

    # Check for the CLUSTER
    logger.info("--vCenter TEST 5 - Checking for the Cluster")
    cluster = get_cluster(dc, cfg_yaml['VC_CLUSTER'])
    cluster_id = str(cluster).split(':')[1][:-1]
    logger.debug(cluster_id)
    
    # Check Hosts in the Cluster 
    logger.info("--vCenter TEST 5a - Checking Hosts in the Cluster")
    esx_hosts = get_hosts_in_cluster(cluster)
    
    # Connect to SPBM Endpoint and existence of Storage Policies
    logger.debug("--vCenter TEST 6 - Checking Existence of Storage Policies")
    logger.debug("--vCenter TEST 6 - Checking Connection to SPBM")
    pbmSi, pbmContent = GetPbmConnection(si._stub)
    logger.info("--vCenter TEST 6 - Getting Storage Policies from SPBM")
    storagepolicies = cfg_yaml['VC_STORAGEPOLICIES']
    for policy in storagepolicies:
        storage_profile= get_storageprofile(policy, pbmContent )

    # EXTRA TEST Not Necessary - Check for a Datastore 
    logger.info("--vCenter TEST 7 - Checking Existence of the Datastores")
    ds = get_obj(vc_content, [vim.Datastore], cfg_yaml['VC_DATASTORE'])

    # Check for the vds 
    logger.info("--vCenter TEST 8 - Checking for the vds")
    vds = get_obj(vc_content, [vim.DistributedVirtualSwitch], cfg_yaml['VDS_NAME'])

    # Create VC REST Session
    logger.info("--vCenter TEST 9 - Establishing REST session to VC API")
    vc_session, session_id = connect_vc_rest(cfg_yaml['VC_HOST'],cfg_yaml['VC_SSO_USER'],cfg_yaml['VC_SSO_PWD'] )

    ## DEBUG AND TEST BELOW
    datacenter_object = vc_session.get('https://' + cfg_yaml['VC_HOST'] + '/rest/vcenter/datacenter?filter.names=' + cfg_yaml['VC_DATACENTER'])
    if len(json.loads(datacenter_object.text)["value"]) == 0:
        logger.error("---ERROR - No datacenter found, please enter valid datacenter name")
    else:
        datacenter_id = json.loads(datacenter_object.text)["value"][0].get("datacenter")
        logger.debug("---Datacenter ID is {}".format(datacenter_id))

    # Check NTP Time settings on vCenter
    logger.info("--vCenter TEST 11 - Checking time accuracy/synchronization in environment")

    # Check NTP Time settings on vCenter
    logger.debug("--vCenter TEST 11 - Checking time on vCenter Appliance")
    host_times = get_vc_time( vc_session, cfg_yaml['VC_HOST'])

    # Check Time settings on ESXi hosts
    logger.debug("--vCenter TEST 11 - Checking time on ESXi hosts")
    # First return all the ESXi hosts in the cluster
    host_times = get_host_times(esx_hosts,host_times)

    # Detect variances in the times among all the objects ESXi and vCenter
    logger.info("----------------------- Checking max time deltas on ESXi and vCenter hosts is less than 30")
    detect_time_drift(host_times)
   
    # Check existent of a Content Library
    logger.info("--vCenter TEST 12 - Checking for existence and configuration of Content Library")
    content_library_id = get_content_library(vc_session,cfg_yaml['VC_HOST'])

    # Check Status of WCP Service
    # Set REST VC Variables
    logger.info("--vCenter TEST 13 - Checking Status of WCP Service on vCenter")
    service_status = get_vc_svc_status(s,cfg_yaml['VC_HOST'],"wcp",sessionId)

    # Check for the Primary Workload Network 
    logger.info("--vCenter TEST 16 - Checking for the Primary Workload Network PortGroup")
    prim_wkld_pg = get_obj(vc_content, [vim.Network], cfg_yaml['VDS_PRIMARY_WKLD_PG'])

    # Check for the Workload Network 
    logger.info("--vCenter TEST 17 - Checking for the Workload Network PortGroup")
    wkld_pg = get_obj(vc_content, [vim.Network], cfg_yaml['VDS_WKLD_PG'])

     ## Check on vSphere Clsuter WCP Status and return SC API Server Ednpoint
    logger.info("--vCenter TEST 18 - Checking on cluster {} WCP Health".format(cluster.name))
    wcp_endpoint = check_wcp_cluster_status(s, cfg_yaml['VC_IP'], cluster_id, session_id)
    logger.debug("--WCP Endpoint for SC is ".format(wcp_endpoint))

    logger.info("************ Completed vCenter Environment Testing ************\n")

    ###### If networking type is vSphere  ######
    if network_type=='vsphere':

        logger.info("************ Beginning AVI Environment Testing ************")

        logger.info("--AVI TEST 1 - Checking AVI Controller Health")
        avi_sessionid, avi_version = avi_login(cfg_yaml['ALB_CTLR_IP'] ,cfg_yaml['ALB_CTLR_USER'] ,cfg_yaml['ALB_CTLR_PW'])
        logger.info(CGRN +'Avi controller {} running version {} has sessionid {}'.format(cfg_yaml['ALB_CTLR_IP'],avi_version,avi_sessionid )+ CEND)
        resp = requests.get('https://'+cfg_yaml['ALB_CTLR_IP']+'/api/cluster/version', verify=False, cookies=dict(sessionid= avi_sessionid))
        logger.info(CGRN +'Full AVI Version = {} '.format(json.loads(resp.text)['Tag'])+ CEND)

        # Get all Avi SE's
        logger.info("--AVI TEST 2 - Checking health of all Service Engines")
        avi_ses = get_avi_objects(cfg_yaml['ALB_CTLR_IP'], avi_sessionid,'serviceengine')
        # Get Health Scores
        logger.info('---- Found {} Service Engines'.format(str(len(avi_ses))))
        for se in avi_ses:
            se_health = get_avi_object_health(cfg_yaml['ALB_CTLR_IP'], avi_sessionid,'serviceengine',se['uuid'])
            health_score = se_health['series'][0]['data'][0]['value']    # Type is Float 
            logger.debug('---- Health Score for Service Engine {} is...{}'.format(se['name'],health_score))
            if health_score <= 75:
                logger.info(CRED +"ERROR - Low Health score of {} for SE {}".format(str(health_score),format(se['name']) + CEND))
            else:
                logger.info(CGRN +"SUCCESS - High Health score of {} for SE, {}".format(str(health_score),format(se['name']) + CEND))

        # Get all Avi Pool's
        logger.info("--AVI TEST 3 - Checking health of AVI Pools ")
        avi_pools = get_avi_objects(cfg_yaml['ALB_CTLR_IP'], avi_sessionid,'pool')
        # Get Health Scores for each Pool
        logger.info('---- Found {} Avi Pools'.format(str(len(avi_pools))))
        for pool in avi_pools:
            pool_health = get_avi_object_health(cfg_yaml['ALB_CTLR_IP'], avi_sessionid,'pool',pool['uuid'])
            health_score = pool_health['series'][0]['data'][0]['value']   # Type is Float 
            logger.debug('---- Health Score for Pool {} is...{}'.format(pool['name'],health_score))
            if health_score <= 75:
                logger.info(CRED +"ERROR - Low Health score of {} for Pool, {}".format(str(health_score),format(pool['name']) + CEND))
            else:
                logger.info(CGRN +"SUCCESS - High Health score of {} for Pool, {}".format(str(health_score),format(pool['name']) + CEND))

        # Get all Avi Virtual Services
        logger.info("--AVI TEST 4 - Checking health of all Virtual Services ")
        avi_vs = get_avi_objects(cfg_yaml['ALB_CTLR_IP'], avi_sessionid,'virtualservice')
        # Get Health Scores for each VS
        logger.info('---- Found {} Virtual Services'.format(str(len(avi_vs))))
        for vs in avi_vs:
            vs_health = get_avi_object_health(cfg_yaml['ALB_CTLR_IP'], avi_sessionid,'virtualservice',vs['uuid'])
            health_score = vs_health['series'][0]['data'][0]['value']  # Type is Float 
            logger.debug('---- Health Score for Virtual Service {} is...{}'.format(vs['name'],health_score))
            if health_score <= 75:
                logger.info(CRED +"ERROR - Low Health score of {} for Virtual Service, {}".format(str(health_score),format(vs['name']) + CEND))
            else:
                logger.info(CGRN +"SUCCESS - High Health score of {} for Virtual Service, {}".format(str(health_score),format(vs['name']) + CEND))

   

            
    # If networking type is NSX-T
    if network_type == 'nsxt':
        logger.info("NSX-T is not currrently supported for Supervisor Networking !")


    logger.info("************ Completed AVI Environment Testing ************\n")
    
    logger.info("************ Beginning K8s Environment Testing ************")
  
    #### INSERT CODE HERE for SC Checks.
    ## Log into the Supervisor Cluster to create kubeconfig contexts
    logger.info("--K8s TEST 1 - Logging into Supervisor Control Plane kube-api server")
    try:
        output=subprocess.check_output(['kubectl', 'vsphere', 'login', '--insecure-skip-tls-verify', '--server', wcp_endpoint, '-u', cfg_yaml['VC_SSO_USER']]).decode("utf-8")
        if output.startswith("Welcome"):
            logger.info(CGRN +"---- SUCCESS - Logged into Supervisor Control Plane kube api-server" + CEND) 
            # Create k8s client for CustomObjects
            client2=client.CustomObjectsApi(api_client=config.new_client_from_config(context=wcp_endpoint))
        else:
            logger.error(CRED +"---- ERROR - Could not login to WCP SC Endpoint.  Is WCP Service running ? " + CEND)
    except subprocess.CalledProcessError as e:
        print(e.output)

    # Create k8s client for CustomObjects
    # client2=client.CustomObjectsApi(api_client=config.new_client_from_config(context=wcp_endpoint))

    ## Find 3 SC CP VMs and ESXi hosts they are running on.
    logger.info("--K8s TEST 2 - Verifying health of all Supervisor Control Plane VMs ")
    for vmobject in vmList:
        if "SupervisorControlPlaneVM" in vmobject.summary.config.name:
            logger.debug("-Found Supervisor Control Plane VM %s. " % vmobject.summary.config.name)
            logger.info(CGRN +"---- SUCCESS - Found SC VM {} running on ESX host {}".format(vmobject.summary.config.name,vmobject.runtime.host.name)+ CEND) 

    logger.info("--K8s TEST 3 - Verifying health of VM's matching CAPI Virtual Machines on Supervisor Cluster. ")
    wkld_cluster_vms = []

    # Return Cluster API "Machine" objects
    # This builds a list of every Guest Cluster VM (Not including SC VMs)
    try:
        machine_list_dict=client2.list_namespaced_custom_object("cluster.x-k8s.io","v1alpha3","","machines",pretty="True")
        logger.info("---- Found {} kubernetes Workload Cluster VMs".format(str(len(machine_list_dict)-1)))
    except Exception as e:
        print("Exception when calling CustomObjectsApi->list_namespaced_custom_object: %s\n" % e)

    for machine in machine_list_dict["items"]:
        logger.debug('-Found CAPI Machine Object in Supervisor Cluster . VM Name = {0}'.format(machine['metadata']['name']))
        #print(' -Machine Namespace - {0}'.format(machine['metadata']['namespace']))
        #print(' -Machine Cluster - {0}'.format(machine['metadata']['labels']['cluster.x-k8s.io/cluster-name']))
        # Search pyVmomi all VMs by DNSName
        vm=search_index.FindByDnsName(None, machine['metadata']['name'],True)
        
        if vm is None:
            logger.debug("-Could not find a matching VM with VC API ")
  
        else:
            #print("-Found VM matching CAPI Machine Name in VC API. VM=%s. " % vm.summary.config.name)
            logger.info(CGRN +"---- SUCCESS - Found running VM {} on ESX {} matching CAPI Machine from a TKC".format(vm.summary.config.name,vm.runtime.host.name)+ CEND) 

            wkld_cluster_vms.append(vm)

    logger.info("************ Completed K8s Environment Testing ************")
    # Clean up and exit...
    session_delete = s.delete('https://' + cfg_yaml['VC_HOST'] + '/rest/com/vmware/cis/session', auth=(cfg_yaml['VC_SSO_USER'], cfg_yaml['VC_SSO_PWD'] ))
    print("\n - Successfully Completed Script - Cleaning up REST Session to VC.")

''' 
logger.info("************************************************")
logger.info("** All checks were run. Validation Complete.  **")
logger.info("************************************************")
'''


# Start program
if __name__ == '__main__':
    main()
