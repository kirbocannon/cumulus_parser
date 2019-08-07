# Description
This script will crawl a cumulus vxlan environment for things like mac address and interface configuration. 
The Script looks at the ```hosts.yaml``` file to determine the inventory. The script will look at the ```cumulus``` group.
This script is multithreaded. 
 
# Compatibility
Python 3.6+ 

### Crawl Cumulus Environment for mac address

```python parser.py search -m 00:50:56:9e:2b:c4```

Essentially, this will log in via SSH and run the following command:

```
cumulus-switch01:~$ net show bridge macs dynamic
```

### Check BGP status of environment

#### Define Validation File using YAML in ```./templates/validation/bgp.yaml```
```
---

SFD-C320-BLF-S4048-01:
  bgp_neighbors:
    ipv4 unicast:
      peers:
        peerlink.4094: SFD-C320-BLF-S4048-02
        swp16: CSS1A-105-TBL-01
        swp17: CSSFH-S4048-01

SFD-C320-BLF-S4048-02:
  bgp_neighbors:
    ipv4 unicast:
      peers:
        peerlink.4094: SFD-C320-BLF-S4048-01
        swp16: CSS1A-105-TBL-02
        swp17: CSSFH-S4048-02
```

Then use the following command to validate current BGP state:

```python parser.py check --bgp```

This command will let you know if there is any obvious issue with BGP. In the following
output, two different switches have not met the validation requirements:
```
  --> CSS1A-106-LEF-01's required peer on interface peerlink.4094 to CSS1A-106-LEF-02 failed check because 
      peering is not established!  


  --> CSS1A-106-LEF-02's required peer on interface peerlink.4094 to CSS1A-106-LEF-01 failed check because 
      peering is not established!  

```

You can also see verbose output by adding ```-v``` like so: ```python parser.py check --bgp -v```

And see output like this:

```
 hostname               address family    interface      peer hostname          configured    status
---------------------  ----------------  -------------  ---------------------  ------------  ---------------
CSS1A-105-TBL-01       ipv4 unicast      peerlink.4094  CSS1A-105-TBL-02       yes           Established
CSS1A-105-TBL-01       ipv4 unicast      swp16          SFD-C320-BLF-S4048-01  yes           Established
CSS1A-105-TBL-02       ipv4 unicast      peerlink.4094  CSS1A-105-TBL-01       yes           Established
CSS1A-105-TBL-02       ipv4 unicast      swp16          SFD-C320-BLF-S4048-02  yes           Established
CSS1A-105-BLF-01       l2vpn evpn        peerlink.4094  CSS1A-105-BLF-02       yes           Established
CSS1A-105-BLF-01       l2vpn evpn        swp19          CSS1A-105-SPN-01       yes           Not Established
CSS1A-105-BLF-01       l2vpn evpn        swp20          CSS1A-105-SPN-02       yes           Established
CSS1A-105-BLF-02       ipv4 unicast      peerlink.4094  CSS1A-105-BLF-01       yes           Established
CSS1A-105-BLF-02       ipv4 unicast      swp19          CSS1A-105-SPN-01       yes           Established
CSS1A-105-BLF-02       ipv4 unicast      swp20          CSS1A-105-SPN-02       yes           Established
CSS1A-105-BLF-02       l2vpn evpn        peerlink.4094  CSS1A-105-BLF-01       yes           Established
CSS1A-105-BLF-02       l2vpn evpn        swp19          CSS1A-105-SPN-01       yes           Established
CSS1A-105-BLF-02       l2vpn evpn        swp20          CSS1A-105-SPN-02       yes           Established

```