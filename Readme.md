# Description
This script will crawl a cumulus vxlan environment for things like mac address and interface configuration. 
The Script looks at the ```hosts.yaml``` file to determine the inventory. The script will look at the ```cumulus``` group.
This script is multithreaded. 
 
# Compatibility
Python 3.6+ 

# Crawl Cumulus Environment for mac address

```python parser.py search -m 00:50:56:9e:2b:c4```

Essentially, this will log in via SSH and run the following command:
```
cumulus-switch01:~$ net show bridge macs dynamic
```

