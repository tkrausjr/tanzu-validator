# WCP-precheck
WCP-Precheck project aims to make POC's and vSphere with Tanzu installations less painful for customers and overall more successful by quickly indentifying common misconfigurations and errors that would prevent a successful installation of WCP .  The WCP-precheck team is constantly incorporating field feedback to enhance the test coverage. Please open a Gitlab Issue with a FR to add a test that is missing.

## Test Coverage
  ### General
  - [x] The Tag-based storage policy specified exists the vCenter.
  - [x] DNS forward and reverse resolution should work for vCenter and NSX Manager.
  - [x] Ping/curl various network end points that they are reachable (DNS, NTP, VCenter, NSX Manager, )
  - [x] Validate vSphere API is accessible and provided credentials are valid.
  - [x] Validate existence of vSphere cluster specified in configuration YAML is valid.
  - [x] Validate existence of VDS specified in configuration YAML is valid.
  - [x] Validate existence of Datacenter specified in configuration YAML is valid.
  - [x] Validate existence of Cluster specified in configuration YAML is valid.
  - [x] Validate that vLCM (Personality Manager) is not enabled on the specified cluster if vSphere <= 7.0 U1.
  - [x] Validate that HA is enabled on the specified cluster.
  - [x] Validate that DRS is enabled and set to Fully Automated Mode on the specified cluster.
  - [x] Validate that a compatible NSX-T VDS exists.
  - [x] Validate that at leaset one content library is created on the vCenter.
  - [x] NTP driff between vCenter and ESXi hosts in Cluster
  ---
  ### NSX based networking
  - [x] Validate required VDS Port Groups(Management, Edge TEP, Uplink) specified in configuration YAML is valid.
  - [x] DNS forward and reverse resolution should work for NSX Manager.
  - [x] Validate we can communicate with NSX Manager on network and NSX Management Node and Cluster is Healthy.
  - [x] Validate NSX-T API is accessible and provided credentials are valid.
  - [x] Validate Health of ESXi Transport Nodes(NSX-T Agent Install and Status) in vSphere Cluster.
  - [x] Validate Health of Edge Transport Nodes(Status) in vSphere Cluster.
  - [ ] Ingress and Egress network is routed
  - [ ] Heartbeat ping to the uplink IP (T0 interface) is working. 
  - [ ] 1600 byte ping with no fragmentation between ESXi TEPs
  - [ ] 1600 byte ping with no fragmentation between ESXi TEPs to Edge TEPs.   
  - [x] Validate EDGE VMs are deployed as at least large.
  - [x] NTP driff between EDGE, vCenter and ESXi
  - [ ] Depending on NSX version, EDGE vTEP and ESX vTEP are on different VLANs
  - [x] Validate existence of a T0 router.
  - [ ] T0 router can access DNS and NTP
  ---
  ### (COMING SOON) VDS based AVI Lite config
  - [ ] AVI Controller liveness probes that check each network connectivity and the frontend VIP IP's
  - [ ] AVI Service Engine Health.

  ---
  ### VDS based HAProxy config
  - [x] HA proxy liveness probes that check each network connectivity and the frontend VIP IP's
  - [ ] The HA Proxy Load-Balancer IP Range and WCP Workload Network Range must not include the Gateway address for the overall Workload Network.
  - [ ] The HA Proxy Workload IP should be in the overall Workload network, but outside of the Load-Balancer IP Range and the WCP Workload Network Range.
  - [ ] The IP ranges for the OVA and the WCP enablement should be checked to be the same
  - [ ] The WCP Range for Virtual Servers must be exactly the range defined by the Load-Balancer IP Range in HA Proxy.  
  - [x] Validate successful login access to HAProxy VM's API endpoint.

