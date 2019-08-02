import paramiko
import json
import time
import logging
import os
import yaml
from textfsm import clitable
from paramiko import ssh_exception as pexception
from exceptions import InventoryFileNotFound, \
    CannotParseOutputWithTextFSM
from multiprocessing .dummy import Pool as Threadpool


HOSTS_FILENAME = 'hosts.yaml'
POOL = Threadpool(4)
WAIT_FOR_COMMAND_IN_SECONDS = 4
TEMPLATE_DIR = './templates/'



show_version = \
"""NCLU_VERSION=1.0
DISTRIB_ID="Cumulus Linux"
DISTRIB_RELEASE=3.7.6
DISTRIB_DESCRIPTION="Cumulus Linux 3.7.6"
"""
show_bridge_macs_dynamic = \
"""

VLAN      Master  Interface     MAC                TunnelDest  State  Flags  LastSeen
--------  ------  ------------  -----------------  ----------  -----  -----  --------
1         bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
1         bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:16
1         bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:00:16
1         bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:00:16
1         bridge  vni-1003      00:00:5e:00:01:64                            00:01:28
1         bridge  vni-1003      00:07:b4:00:01:01                            00:00:16
1         bridge  vni-1003      00:07:b4:00:01:02                            00:01:28
1         bridge  vni-1003      00:50:56:91:18:1f                            00:01:28
1         bridge  vni-1003      00:50:56:a8:24:07                            00:01:28
1         bridge  vni-1003      00:d6:fe:76:69:30                            00:08:18
1         bridge  vni-1003      1a:8c:47:4e:6c:d1                            00:00:46
1         bridge  vni-1003      1e:04:0c:74:51:51                            00:00:46
1         bridge  vni-1003      02:3f:a4:4c:5e:ab                            00:00:16
1         bridge  vni-1003      2a:b5:97:bb:90:44                            00:01:28
1         bridge  vni-1003      2a:f6:dd:86:73:66                            00:00:16
1         bridge  vni-1003      2a:ff:90:b2:e4:46                            00:01:28
1         bridge  vni-1003      3e:70:dc:6a:5e:03                            00:01:28
1         bridge  vni-1003      4a:91:22:96:d9:16                            00:01:28
1         bridge  vni-1003      4a:c3:fe:6e:38:e7                            00:01:28
1         bridge  vni-1003      4e:5c:fe:db:1b:e8                            00:01:28
1         bridge  vni-1003      4e:19:0c:ba:0b:b3                            00:00:16
1         bridge  vni-1003      5e:73:17:5d:8b:17                            00:00:46
1         bridge  vni-1003      6a:43:08:21:90:3b                            00:01:28
1         bridge  vni-1003      6e:1a:15:c4:a0:dd                            00:01:28
1         bridge  vni-1003      7a:dc:7e:9d:0c:04                            00:00:46
1         bridge  vni-1003      7e:83:0d:5f:32:bd                            00:01:28
1         bridge  vni-1003      7e:88:b4:84:dc:d0                            00:00:46
1         bridge  vni-1003      8a:2f:a7:f4:02:02                            00:00:46
1         bridge  vni-1003      8e:a7:45:1d:eb:a1                            00:00:46
1         bridge  vni-1003      9a:9a:e6:82:ed:5d                            00:01:28
1         bridge  vni-1003      9a:be:b2:fe:b6:5e                            00:01:16
1         bridge  vni-1003      9a:e3:01:87:cf:05                            00:00:46
1         bridge  vni-1003      10:98:36:b5:ad:cb                            00:00:16
1         bridge  vni-1003      10:98:36:b5:ad:cd                            00:00:16
1         bridge  vni-1003      12:5e:35:c4:5a:1c                            00:01:28
1         bridge  vni-1003      12:c4:09:c3:2d:21                            00:00:46
1         bridge  vni-1003      16:0f:13:7c:9f:d0                            00:01:16
1         bridge  vni-1003      16:b2:8e:1b:84:44                            00:00:46
1         bridge  vni-1003      16:f2:83:e4:de:0a                            00:01:28
1         bridge  vni-1003      22:41:08:b9:83:a0                            00:00:46
1         bridge  vni-1003      26:6e:fe:a7:be:e7                            00:01:16
1         bridge  vni-1003      26:44:07:f0:44:bb                            00:00:46
1         bridge  vni-1003      32:06:87:12:58:30                            00:01:28
1         bridge  vni-1003      32:a9:f8:52:25:d6                            00:01:28
1         bridge  vni-1003      50:9a:4c:80:93:ef                            00:01:28
1         bridge  vni-1003      50:9a:4c:80:95:ef                            00:01:28
1         bridge  vni-1003      52:90:f4:62:55:42                            00:01:28
1         bridge  vni-1003      56:4b:ce:34:0c:c4                            00:00:46
1         bridge  vni-1003      62:25:45:36:45:ea                            00:01:16
1         bridge  vni-1003      66:65:7c:53:7f:27                            00:01:28
1         bridge  vni-1003      70:35:09:8c:cf:8f                            00:01:28
1         bridge  vni-1003      72:45:49:27:68:c3                            00:00:16
1         bridge  vni-1003      72:74:2b:c9:70:c3                            00:01:28
1         bridge  vni-1003      76:28:39:c8:43:34                            00:01:16
1         bridge  vni-1003      76:43:b8:58:ce:ae                            00:00:16
1         bridge  vni-1003      82:60:e6:b8:de:77                            00:00:16
1         bridge  vni-1003      82:ec:20:b2:1b:43                            00:00:16
1         bridge  vni-1003      86:83:9f:dd:a0:d0                            00:01:28
1         bridge  vni-1003      86:f9:40:71:52:02                            00:01:28
1         bridge  vni-1003      92:0d:ef:47:6e:cf                            00:01:28
1         bridge  vni-1003      96:cc:54:61:46:47                            00:00:46
1         bridge  vni-1003      a2:b6:0b:df:c2:62                            00:01:28
1         bridge  vni-1003      aa:7a:b6:9c:5f:fd                            00:01:28
1         bridge  vni-1003      aa:8d:20:38:f2:bd                            00:00:46
1         bridge  vni-1003      ae:59:b7:7b:ef:ce                            00:01:28
1         bridge  vni-1003      ae:ba:83:75:1a:8d                            00:01:28
1         bridge  vni-1003      be:91:f6:83:b3:a9                            00:01:28
1         bridge  vni-1003      c6:35:9e:2e:18:74                            00:00:46
1         bridge  vni-1003      ca:cc:f7:3c:a5:65                            00:01:28
1         bridge  vni-1003      d0:67:e5:dc:e3:b3                            00:01:28
1         bridge  vni-1003      d0:67:e5:dc:e5:0b                            00:00:16
1         bridge  vni-1003      d6:4c:d0:79:bd:63                            00:00:46
1         bridge  vni-1003      d6:16:3b:63:ea:ef                            00:08:18
1         bridge  vni-1003      d6:88:d6:f9:08:bf                            00:01:28
1         bridge  vni-1003      de:94:a5:5f:0b:b3                            00:01:16
1         bridge  vni-1003      de:d9:46:d1:53:d3                            00:00:16
1         bridge  vni-1003      e2:4a:80:22:bd:bc                            00:00:16
1         bridge  vni-1003      ee:2b:fe:a3:d7:6f                            00:01:28
1         bridge  vni-1003      f2:ff:b6:2d:2c:13                            00:00:16
1         bridge  vni-1003      f4:8e:38:1f:a2:87                            00:01:28
1         bridge  vni-1003      f6:77:66:42:25:db                            00:00:46
4         bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
4         bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:01:28
4         bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:01:28
4         bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:03:05
4         bridge  vni-1004      00:50:56:91:0f:12                            00:00:16
4         bridge  vni-1004      00:50:56:91:40:9b                            00:01:28
4         bridge  vni-1004      00:50:56:91:52:dc                            00:01:28
4         bridge  vni-1004      00:50:56:91:65:48                            00:01:28
4         bridge  vni-1004      00:50:56:a8:d6:c4                            00:00:16
4         bridge  vni-1004      1e:3a:77:dd:dc:53                            00:00:46
4         bridge  vni-1004      2e:97:f0:16:a4:e1                            00:00:46
4         bridge  vni-1004      3e:56:23:f7:63:6a                            00:01:16
4         bridge  vni-1004      5a:13:13:5b:b3:c0                            00:01:28
4         bridge  vni-1004      9e:9d:ac:f3:a5:e6                            00:00:46
4         bridge  vni-1004      82:94:21:99:fb:88                            00:01:28
4         bridge  vni-1004      92:42:b0:0d:b6:a0                            00:01:28
4         bridge  vni-1004      a2:05:6d:a7:d0:85                            00:01:28
4         bridge  vni-1004      d6:06:2b:04:52:07                            00:01:28
12        bridge  CSS-SGR-BOND  f8:ca:b8:f1:5d:45                            00:00:16
12        bridge  CSS-SGR-BOND  f8:ca:b8:f1:5d:52                            00:00:16
12        bridge  CSS-SGR-BOND  f8:ca:b8:f1:5d:64                            00:00:16
12        bridge  vni-602       00:00:5e:00:01:96                            00:01:28
12        bridge  vni-602       00:15:5d:0b:16:16                            00:01:16
12        bridge  vni-602       5c:f9:dd:ef:ab:82                            00:01:28
12        bridge  vni-602       24:8a:07:88:d9:ba                            00:01:28
12        bridge  vni-602       24:8a:07:ad:6d:3a                            00:00:46
12        bridge  vni-602       b0:83:fe:d7:4e:ca                            00:01:28
15        bridge  CSS-SGR-BOND  00:0c:29:1b:0d:88                            00:00:16
15        bridge  CSS-SGR-BOND  00:0c:29:71:d9:8e                            00:00:16
15        bridge  CSS-SGR-BOND  00:0c:29:d4:e1:07                            00:00:16
15        bridge  CSS-SGR-BOND  00:0c:29:ff:90:26                            00:00:16
15        bridge  CSS-SGR-BOND  00:15:5d:82:22:07                            00:00:16
15        bridge  CSS-SGR-BOND  00:15:5d:82:22:08                            00:00:16
15        bridge  CSS-SGR-BOND  00:15:5d:82:23:13                            00:00:16
15        bridge  CSS-SGR-BOND  00:50:56:9e:4a:87                            00:01:16
15        bridge  CSS-SGR-BOND  00:50:56:9e:6e:9f                            00:00:16
15        bridge  CSS-SGR-BOND  00:50:56:9e:9b:43                            00:00:46
15        bridge  CSS-SGR-BOND  00:50:56:9e:74:a4                            00:01:28
15        bridge  CSS-SGR-BOND  00:50:56:9e:81:4f                            00:00:16
15        bridge  CSS-SGR-BOND  00:50:56:9e:bb:e6                            00:00:16
15        bridge  CSS-SGR-BOND  00:50:56:9e:bc:df                            00:00:16
15        bridge  CSS-SGR-BOND  00:50:56:9e:ee:ae                            00:04:46
15        bridge  CSS-SGR-BOND  00:50:56:90:5b:72                            00:02:05
15        bridge  CSS-SGR-BOND  00:50:56:90:6b:4f                            00:01:16
15        bridge  CSS-SGR-BOND  00:50:56:90:7a:ec                            00:01:16
15        bridge  CSS-SGR-BOND  00:50:56:90:e8:ad                            00:00:16
15        bridge  CSS-SGR-BOND  00:50:56:91:31:3a                            00:00:16
15        bridge  CSS-SGR-BOND  00:50:56:b4:1f:38                            00:00:16
15        bridge  CSS-SGR-BOND  00:50:56:b4:22:73                            00:00:16
15        bridge  CSS-SGR-BOND  00:50:56:b4:37:65                            00:04:46
15        bridge  CSS-SGR-BOND  00:50:56:b4:84:cc                            00:01:16
15        bridge  CSS-SGR-BOND  00:50:56:b4:c0:e8                            00:02:46
15        bridge  CSS-SGR-BOND  00:50:56:b4:e4:66                            00:00:16
15        bridge  CSS-SGR-BOND  00:50:56:bc:2c:41                            00:00:16
15        bridge  CSS-SGR-BOND  00:50:56:bc:48:6a                            00:00:16
15        bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
15        bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:16
15        bridge  CSS-SGR-BOND  b0:83:fe:d7:59:6b                            00:00:16
15        bridge  CSS-SGR-BOND  b0:83:fe:e1:b3:4e                            00:00:16
15        bridge  CSS-SGR-BOND  f4:52:14:3a:22:c0                            00:00:16
15        bridge  vni-501       00:00:5e:00:01:0f                            00:01:28
15        bridge  vni-501       00:0c:29:03:a5:09                            00:00:16
15        bridge  vni-501       00:0c:29:62:29:41                            00:00:16
15        bridge  vni-501       00:0c:29:66:77:63                            00:00:46
15        bridge  vni-501       00:15:5d:0b:15:02                            00:00:16
15        bridge  vni-501       00:15:5d:0b:15:04                            00:01:16
15        bridge  vni-501       00:15:5d:0b:15:06                            00:00:16
15        bridge  vni-501       00:15:5d:0b:16:06                            00:01:28
15        bridge  vni-501       00:15:5d:0b:16:12                            00:00:16
15        bridge  vni-501       00:15:5d:0b:16:13                            00:00:46
15        bridge  vni-501       00:50:56:9e:2b:c4                            00:00:16
15        bridge  vni-501       00:50:56:9e:93:64                            00:00:16
15        bridge  vni-501       00:50:56:9e:ed:88                            00:00:16
15        bridge  vni-501       00:50:56:90:00:c2                            00:00:16
15        bridge  vni-501       00:50:56:90:1c:d6                            00:00:16
15        bridge  vni-501       00:50:56:90:1e:33                            00:01:28
15        bridge  vni-501       00:50:56:90:4f:dc                            00:01:28
15        bridge  vni-501       00:50:56:90:06:5c                            00:00:16
15        bridge  vni-501       00:50:56:90:6d:8b                            00:01:28
15        bridge  vni-501       00:50:56:90:8f:f1                            00:01:28
15        bridge  vni-501       00:50:56:90:09:bc                            00:00:16
15        bridge  vni-501       00:50:56:90:19:1a                            00:00:16
15        bridge  vni-501       00:50:56:90:19:59                            00:01:28
15        bridge  vni-501       00:50:56:90:19:d1                            00:00:46
15        bridge  vni-501       00:50:56:90:35:a5                            00:00:16
15        bridge  vni-501       00:50:56:90:37:d1                            00:00:16
15        bridge  vni-501       00:50:56:90:41:70                            00:00:46
15        bridge  vni-501       00:50:56:90:56:92                            00:00:46
15        bridge  vni-501       00:50:56:90:63:fd                            00:00:16
15        bridge  vni-501       00:50:56:90:66:e3                            00:01:28
15        bridge  vni-501       00:50:56:90:66:f4                            00:01:16
15        bridge  vni-501       00:50:56:90:79:f8                            00:00:16
15        bridge  vni-501       00:50:56:90:86:97                            00:01:28
15        bridge  vni-501       00:50:56:90:96:ca                            00:00:16
15        bridge  vni-501       00:50:56:90:b0:31                            00:18:16
15        bridge  vni-501       00:50:56:90:b1:44                            00:00:46
15        bridge  vni-501       00:50:56:90:b5:8c                            00:01:16
15        bridge  vni-501       00:50:56:90:b6:d8                            00:23:46
15        bridge  vni-501       00:50:56:90:b8:6d                            00:01:28
15        bridge  vni-501       00:50:56:90:cd:25                            00:02:46
15        bridge  vni-501       00:50:56:90:cf:00                            00:00:16
15        bridge  vni-501       00:50:56:90:db:c8                            00:00:16
15        bridge  vni-501       00:50:56:90:dc:49                            00:00:16
15        bridge  vni-501       00:50:56:90:de:16                            00:01:16
15        bridge  vni-501       00:50:56:90:e1:95                            00:01:16
15        bridge  vni-501       00:50:56:90:e1:b9                            00:01:28
15        bridge  vni-501       00:50:56:90:e3:aa                            00:10:16
15        bridge  vni-501       00:50:56:90:e6:a5                            00:01:28
15        bridge  vni-501       00:50:56:90:eb:79                            00:00:46
15        bridge  vni-501       00:50:56:90:f3:12                            00:03:05
15        bridge  vni-501       00:50:56:90:f3:fb                            00:00:16
15        bridge  vni-501       00:50:56:90:f4:72                            00:00:46
15        bridge  vni-501       00:50:56:91:0d:a7                            00:00:16
15        bridge  vni-501       00:50:56:91:0e:98                            00:00:16
15        bridge  vni-501       00:50:56:91:1a:fd                            00:00:16
15        bridge  vni-501       00:50:56:91:1b:6e                            00:00:16
15        bridge  vni-501       00:50:56:91:1c:b0                            00:01:28
15        bridge  vni-501       00:50:56:91:1c:dd                            00:04:46
15        bridge  vni-501       00:50:56:91:1f:7a                            00:01:28
15        bridge  vni-501       00:50:56:91:02:70                            00:01:28
15        bridge  vni-501       00:50:56:91:02:e1                            00:10:51
15        bridge  vni-501       00:50:56:91:2d:6a                            00:00:16
15        bridge  vni-501       00:50:56:91:2d:e0                            00:01:16
15        bridge  vni-501       00:50:56:91:2f:a2                            00:01:28
15        bridge  vni-501       00:50:56:91:03:de                            00:00:16
15        bridge  vni-501       00:50:56:91:3d:2e                            00:01:28
15        bridge  vni-501       00:50:56:91:3e:16                            00:00:46
15        bridge  vni-501       00:50:56:91:04:60                            00:01:28
15        bridge  vni-501       00:50:56:91:4f:88                            00:01:28
15        bridge  vni-501       00:50:56:91:05:b4                            00:00:16
15        bridge  vni-501       00:50:56:91:5a:fa                            00:00:46
15        bridge  vni-501       00:50:56:91:5c:06                            00:01:28
15        bridge  vni-501       00:50:56:91:06:44                            00:10:51
15        bridge  vni-501       00:50:56:91:6a:75                            00:00:16
15        bridge  vni-501       00:50:56:91:6e:c5                            00:01:28
15        bridge  vni-501       00:50:56:91:7c:60                            00:00:16
15        bridge  vni-501       00:50:56:91:7c:e0                            00:01:28
15        bridge  vni-501       00:50:56:91:7d:0d                            00:00:46
15        bridge  vni-501       00:50:56:91:7d:7f                            00:00:16
15        bridge  vni-501       00:50:56:91:7d:d6                            00:01:28
15        bridge  vni-501       00:50:56:91:13:21                            00:01:28
15        bridge  vni-501       00:50:56:91:15:0b                            00:01:28
15        bridge  vni-501       00:50:56:91:17:ec                            00:01:28
15        bridge  vni-501       00:50:56:91:18:10                            00:00:16
15        bridge  vni-501       00:50:56:91:18:95                            00:00:16
15        bridge  vni-501       00:50:56:91:22:3d                            00:01:28
15        bridge  vni-501       00:50:56:91:25:86                            00:01:28
15        bridge  vni-501       00:50:56:91:25:ee                            00:00:16
15        bridge  vni-501       00:50:56:91:26:ab                            00:06:45
15        bridge  vni-501       00:50:56:91:34:f9                            00:00:16
15        bridge  vni-501       00:50:56:91:37:9b                            00:01:16
15        bridge  vni-501       00:50:56:91:40:52                            00:00:16
15        bridge  vni-501       00:50:56:91:42:7c                            00:00:16
15        bridge  vni-501       00:50:56:91:46:f3                            00:01:28
15        bridge  vni-501       00:50:56:91:51:4e                            00:01:16
15        bridge  vni-501       00:50:56:91:52:48                            00:00:16
15        bridge  vni-501       00:50:56:91:59:4e                            00:00:16
15        bridge  vni-501       00:50:56:91:59:ef                            00:01:28
15        bridge  vni-501       00:50:56:91:61:63                            00:00:16
15        bridge  vni-501       00:50:56:91:61:64                            00:00:16
15        bridge  vni-501       00:50:56:91:62:61                            00:00:16
15        bridge  vni-501       00:50:56:91:63:97                            00:01:16
15        bridge  vni-501       00:50:56:91:67:7c                            00:00:46
15        bridge  vni-501       00:50:56:91:68:c3                            00:01:28
15        bridge  vni-501       00:50:56:91:69:5e                            00:02:46
15        bridge  vni-501       00:50:56:91:70:53                            00:01:16
15        bridge  vni-501       00:50:56:91:70:be                            00:00:16
15        bridge  vni-501       00:50:56:91:74:83                            00:00:16
15        bridge  vni-501       00:50:56:91:75:c0                            00:00:16
15        bridge  vni-501       00:50:56:91:76:80                            00:01:28
15        bridge  vni-501       00:50:56:91:79:23                            00:00:16
15        bridge  vni-501       00:50:56:93:1b:e9                            00:01:28
15        bridge  vni-501       00:50:56:93:24:43                            00:00:46
15        bridge  vni-501       00:50:56:bc:7f:07                            00:01:28
15        bridge  vni-501       00:50:56:bc:12:6a                            00:01:16
15        bridge  vni-501       00:50:56:bc:47:cc                            00:00:16
15        bridge  vni-501       00:50:56:bc:60:6d                            00:01:28
15        bridge  vni-501       00:50:56:bc:66:57                            00:01:16
15        bridge  vni-501       00:50:56:bc:77:1c                            00:00:16
15        bridge  vni-501       00:50:cc:7f:0b:d4                            00:01:28
15        bridge  vni-501       00:50:cc:7f:0b:d6                            00:00:16
15        bridge  vni-501       00:50:cc:7f:0c:1c                            00:01:28
15        bridge  vni-501       00:50:cc:7f:0c:1e                            00:01:28
15        bridge  vni-501       5c:f9:dd:ef:ab:82                            00:01:28
15        bridge  vni-501       24:8a:07:88:d9:ba                            00:00:16
15        bridge  vni-501       24:8a:07:ad:6d:3a                            00:01:16
15        bridge  vni-501       50:9a:4c:76:6b:89                            00:00:16
15        bridge  vni-501       b0:83:fe:d7:4e:ca                            00:00:16
15        bridge  vni-501       ec:f4:bb:c1:8f:04                            00:00:46
15        bridge  vni-501       ec:f4:bb:f1:86:34                            00:00:16
15        bridge  vni-501       ec:f4:bb:f1:95:f4                            00:01:28
15        bridge  vni-501       ec:f4:bb:f1:a7:3c                            00:18:30
100       bridge  CSS-SGR-BOND  00:15:5d:82:23:0d                            00:00:16
100       bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
100       bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:01:16
100       bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:00:46
100       bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:01:16
100       bridge  CSS-SGR-BOND  b0:83:fe:e1:b3:4e                            00:00:16
100       bridge  vni-504       00:00:5e:00:01:0f                            00:01:28
100       bridge  vni-504       00:15:5d:0b:16:10                            00:00:16
100       bridge  vni-504       00:50:56:91:0b:fd                            00:00:16
100       bridge  vni-504       00:50:56:91:6a:f5                            00:01:28
100       bridge  vni-504       00:50:56:91:7e:d3                            00:03:45
100       bridge  vni-504       00:50:56:91:08:c3                            00:01:28
100       bridge  vni-504       00:50:56:91:19:57                            00:01:28
100       bridge  vni-504       00:50:56:91:26:7f                            00:05:16
100       bridge  vni-504       00:50:56:91:30:bd                            00:01:28
100       bridge  vni-504       00:50:56:91:39:8b                            00:04:16
100       bridge  vni-504       00:50:56:91:50:d0                            00:02:05
100       bridge  vni-504       00:50:56:91:64:e3                            00:06:45
100       bridge  vni-504       00:50:56:91:71:68                            00:00:16
100       bridge  vni-504       00:50:56:93:1c:14                            00:00:16
100       bridge  vni-504       00:50:56:93:58:ed                            00:00:16
100       bridge  vni-504       00:50:56:a8:3f:dc                            00:01:28
100       bridge  vni-504       00:50:56:a8:7f:01                            00:01:28
100       bridge  vni-504       00:50:56:a8:ea:ef                            00:00:16
100       bridge  vni-504       5c:f9:dd:ef:ab:82                            00:01:28
100       bridge  vni-504       24:8a:07:88:d9:ba                            00:00:16
100       bridge  vni-504       24:8a:07:ad:6d:3a                            00:00:16
100       bridge  vni-504       b0:83:fe:d7:4e:ca                            00:05:46
101       bridge  CSS-SGR-BOND  00:15:5d:82:22:0c                            00:00:16
101       bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
101       bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:01:16
101       bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:02:46
101       bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:01:28
101       bridge  CSS-SGR-BOND  b0:83:fe:d7:59:6b                            00:00:16
101       bridge  vni-505       00:00:5e:00:01:0f                            00:01:28
101       bridge  vni-505       00:15:5d:0b:15:12                            00:00:16
101       bridge  vni-505       00:50:56:90:d7:d2                            00:07:46
101       bridge  vni-505       00:50:56:91:4d:01                            00:00:16
101       bridge  vni-505       00:50:56:91:11:9f                            00:05:46
101       bridge  vni-505       00:50:56:91:25:43                            00:03:05
101       bridge  vni-505       00:50:56:91:32:3d                            00:00:16
101       bridge  vni-505       00:50:56:91:44:c5                            00:00:16
101       bridge  vni-505       00:50:56:91:45:c9                            00:02:05
101       bridge  vni-505       00:50:56:91:63:0e                            00:01:28
101       bridge  vni-505       00:50:56:91:63:49                            00:00:16
101       bridge  vni-505       00:50:56:a8:f0:a3                            00:00:16
101       bridge  vni-505       b0:83:fe:d7:4e:ca                            00:00:16
102       bridge  CSS-SGR-BOND  00:15:5d:82:23:0c                            00:00:16
102       bridge  CSS-SGR-BOND  00:50:56:9e:1b:82                            00:00:46
102       bridge  CSS-SGR-BOND  00:50:56:9e:9e:f2                            00:00:16
102       bridge  CSS-SGR-BOND  00:50:56:9e:41:fa                            00:00:16
102       bridge  CSS-SGR-BOND  00:50:56:9e:42:b6                            00:01:28
102       bridge  CSS-SGR-BOND  00:50:56:9e:c0:66                            00:00:16
102       bridge  CSS-SGR-BOND  00:50:56:b4:3b:8a                            00:00:16
102       bridge  CSS-SGR-BOND  00:50:56:b4:26:d5                            00:01:16
102       bridge  CSS-SGR-BOND  00:50:56:b4:51:f2                            00:00:16
102       bridge  CSS-SGR-BOND  00:50:56:b4:57:a2                            00:00:16
102       bridge  CSS-SGR-BOND  00:50:56:b4:82:31                            00:00:16
102       bridge  CSS-SGR-BOND  00:50:56:b4:a5:6a                            00:00:16
102       bridge  CSS-SGR-BOND  00:50:56:b4:d7:cc                            00:00:46
102       bridge  CSS-SGR-BOND  00:50:56:b4:d9:3e                            00:00:16
102       bridge  CSS-SGR-BOND  00:50:56:b4:f8:59                            00:00:16
102       bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
102       bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:16
102       bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:01:16
102       bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:01:16
102       bridge  CSS-SGR-BOND  b0:83:fe:e1:b3:4e                            00:00:16
102       bridge  vni-506       00:00:5e:00:01:0f                            00:01:28
102       bridge  vni-506       00:15:5d:0b:16:0e                            00:00:16
102       bridge  vni-506       00:50:56:91:6b:c7                            00:00:46
102       bridge  vni-506       00:50:56:91:7d:b0                            00:01:28
102       bridge  vni-506       00:50:56:91:48:50                            00:01:28
102       bridge  vni-506       00:50:56:93:1e:be                            00:00:16
102       bridge  vni-506       00:50:56:93:4d:a9                            00:00:16
102       bridge  vni-506       00:50:56:93:4f:fd                            00:00:16
102       bridge  vni-506       00:50:56:93:12:cc                            00:00:46
102       bridge  vni-506       00:50:56:93:35:7f                            00:00:16
102       bridge  vni-506       00:50:56:a8:d8:ba                            00:00:16
102       bridge  vni-506       00:50:56:bc:0a:45                            00:01:16
102       bridge  vni-506       00:50:56:bc:0b:55                            00:00:16
102       bridge  vni-506       00:50:56:bc:0c:51                            00:01:16
102       bridge  vni-506       00:50:56:bc:0d:50                            00:01:16
102       bridge  vni-506       00:50:56:bc:1b:cd                            00:01:16
102       bridge  vni-506       00:50:56:bc:1c:88                            00:00:16
102       bridge  vni-506       00:50:56:bc:1d:bd                            00:00:46
102       bridge  vni-506       00:50:56:bc:1f:73                            00:00:16
102       bridge  vni-506       00:50:56:bc:2f:fa                            00:01:16
102       bridge  vni-506       00:50:56:bc:3a:ae                            00:00:16
102       bridge  vni-506       00:50:56:bc:3a:da                            00:00:16
102       bridge  vni-506       00:50:56:bc:04:b3                            00:01:16
102       bridge  vni-506       00:50:56:bc:4b:15                            00:00:16
102       bridge  vni-506       00:50:56:bc:05:82                            00:01:16
102       bridge  vni-506       00:50:56:bc:05:90                            00:00:16
102       bridge  vni-506       00:50:56:bc:5b:07                            00:01:16
102       bridge  vni-506       00:50:56:bc:5c:7a                            00:00:16
102       bridge  vni-506       00:50:56:bc:5c:f9                            00:00:16
102       bridge  vni-506       00:50:56:bc:5d:d9                            00:00:16
102       bridge  vni-506       00:50:56:bc:6c:27                            00:00:46
102       bridge  vni-506       00:50:56:bc:6f:03                            00:00:46
102       bridge  vni-506       00:50:56:bc:07:87                            00:00:46
102       bridge  vni-506       00:50:56:bc:7a:ce                            00:02:05
102       bridge  vni-506       00:50:56:bc:7f:d7                            00:00:46
102       bridge  vni-506       00:50:56:bc:08:4f                            00:00:46
102       bridge  vni-506       00:50:56:bc:09:00                            00:01:28
102       bridge  vni-506       00:50:56:bc:13:04                            00:00:16
102       bridge  vni-506       00:50:56:bc:13:67                            00:01:28
102       bridge  vni-506       00:50:56:bc:14:4f                            00:00:46
102       bridge  vni-506       00:50:56:bc:15:6c                            00:00:16
102       bridge  vni-506       00:50:56:bc:19:7b                            00:01:16
102       bridge  vni-506       00:50:56:bc:20:16                            00:00:46
102       bridge  vni-506       00:50:56:bc:26:14                            00:00:16
102       bridge  vni-506       00:50:56:bc:27:67                            00:01:16
102       bridge  vni-506       00:50:56:bc:32:9e                            00:01:28
102       bridge  vni-506       00:50:56:bc:36:da                            00:01:28
102       bridge  vni-506       00:50:56:bc:37:20                            00:01:16
102       bridge  vni-506       00:50:56:bc:42:a8                            00:00:46
102       bridge  vni-506       00:50:56:bc:45:14                            00:00:16
102       bridge  vni-506       00:50:56:bc:46:8f                            00:00:16
102       bridge  vni-506       00:50:56:bc:47:31                            00:01:28
102       bridge  vni-506       00:50:56:bc:47:da                            00:01:16
102       bridge  vni-506       00:50:56:bc:48:a5                            00:00:16
102       bridge  vni-506       00:50:56:bc:48:f2                            00:00:46
102       bridge  vni-506       00:50:56:bc:49:11                            00:01:16
102       bridge  vni-506       00:50:56:bc:56:09                            00:01:28
102       bridge  vni-506       00:50:56:bc:58:5a                            00:00:16
102       bridge  vni-506       00:50:56:bc:58:6c                            00:01:28
102       bridge  vni-506       00:50:56:bc:63:64                            00:00:46
102       bridge  vni-506       00:50:56:bc:64:44                            00:01:16
102       bridge  vni-506       00:50:56:bc:65:60                            00:00:16
102       bridge  vni-506       00:50:56:bc:66:38                            00:00:46
102       bridge  vni-506       00:50:56:bc:72:9c                            00:00:46
102       bridge  vni-506       00:50:56:bc:73:09                            00:00:16
102       bridge  vni-506       00:50:56:bc:77:25                            00:00:46
102       bridge  vni-506       00:50:56:bc:79:4c                            00:00:16
102       bridge  vni-506       5c:f9:dd:ef:ab:82                            00:01:28
102       bridge  vni-506       24:8a:07:88:d9:ba                            00:00:16
102       bridge  vni-506       24:8a:07:ad:6d:3a                            00:00:16
102       bridge  vni-506       b0:83:fe:d7:4e:ca                            00:01:16
103       bridge  CSS-SGR-BOND  00:15:5d:82:23:0a                            00:00:16
103       bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
103       bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:46
103       bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:02:46
103       bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:03:05
103       bridge  CSS-SGR-BOND  b0:83:fe:e1:b3:4e                            00:00:16
103       bridge  vni-507       00:00:5e:00:01:0f                            00:01:28
103       bridge  vni-507       00:15:5d:0b:16:11                            00:00:16
103       bridge  vni-507       00:50:56:90:3a:46                            00:01:28
103       bridge  vni-507       00:50:56:90:7c:12                            00:03:05
103       bridge  vni-507       00:50:56:91:1a:3c                            00:01:28
103       bridge  vni-507       00:50:56:91:02:a3                            00:10:16
103       bridge  vni-507       00:50:56:91:2c:29                            00:00:46
103       bridge  vni-507       00:50:56:91:3f:97                            00:01:28
103       bridge  vni-507       00:50:56:91:04:42                            00:01:28
103       bridge  vni-507       00:50:56:91:5a:ec                            00:00:16
103       bridge  vni-507       00:50:56:91:5e:d8                            00:00:16
103       bridge  vni-507       00:50:56:91:5f:cf                            00:02:46
103       bridge  vni-507       00:50:56:91:7e:1e                            00:07:10
103       bridge  vni-507       00:50:56:91:7e:05                            00:01:28
103       bridge  vni-507       00:50:56:91:11:78                            00:04:46
103       bridge  vni-507       00:50:56:91:28:70                            00:00:16
103       bridge  vni-507       00:50:56:91:32:2a                            00:01:28
103       bridge  vni-507       00:50:56:91:42:eb                            00:01:16
103       bridge  vni-507       00:50:56:91:49:cc                            00:00:46
103       bridge  vni-507       00:50:56:91:51:4c                            00:01:28
103       bridge  vni-507       00:50:56:91:58:f8                            00:04:46
103       bridge  vni-507       00:50:56:91:60:87                            00:05:46
103       bridge  vni-507       00:50:56:91:77:92                            00:01:28
103       bridge  vni-507       00:50:56:a8:f9:39                            00:00:16
103       bridge  vni-507       5c:f9:dd:ef:ab:82                            00:01:28
103       bridge  vni-507       24:8a:07:88:d9:ba                            00:00:16
103       bridge  vni-507       24:8a:07:ad:6d:3a                            00:01:16
104       bridge  CSS-SGR-BOND  00:15:5d:82:23:0b                            00:00:16
104       bridge  CSS-SGR-BOND  00:50:56:9e:4e:bd                            00:00:46
104       bridge  CSS-SGR-BOND  00:50:56:9e:58:cb                            00:01:16
104       bridge  CSS-SGR-BOND  00:50:56:9e:60:83                            00:03:45
104       bridge  CSS-SGR-BOND  00:50:56:9e:91:c7                            00:02:05
104       bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
104       bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:16
104       bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:00:46
104       bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:01:28
104       bridge  CSS-SGR-BOND  b0:83:fe:e1:b3:4e                            00:00:16
104       bridge  vni-508       00:00:5e:00:01:0f                            00:01:28
104       bridge  vni-508       00:15:5d:0b:16:0c                            00:00:16
104       bridge  vni-508       00:50:56:91:1f:53                            00:01:16
104       bridge  vni-508       00:50:56:91:4a:53                            00:02:46
104       bridge  vni-508       00:50:56:91:5c:11                            00:00:16
104       bridge  vni-508       00:50:56:91:6d:ef                            00:00:16
104       bridge  vni-508       00:50:56:91:7c:01                            00:07:46
104       bridge  vni-508       00:50:56:91:17:83                            00:07:10
104       bridge  vni-508       00:50:56:91:25:80                            00:00:16
104       bridge  vni-508       00:50:56:91:45:bd                            00:00:46
104       bridge  vni-508       00:50:56:91:58:c5                            00:03:45
104       bridge  vni-508       00:50:56:91:76:05                            00:00:46
104       bridge  vni-508       00:50:56:91:78:0d                            00:00:16
104       bridge  vni-508       00:50:56:91:79:0b                            00:00:16
104       bridge  vni-508       00:50:56:a8:8b:14                            00:00:16
104       bridge  vni-508       24:8a:07:88:d9:ba                            00:00:16
104       bridge  vni-508       24:8a:07:ad:6d:3a                            00:00:16
104       bridge  vni-508       b0:83:fe:d7:4e:ca                            00:00:16
107       bridge  CSS-SGR-BOND  00:50:56:91:24:0a                            00:00:16
107       bridge  CSS-SGR-BOND  00:50:56:91:47:7d                            00:01:16
107       bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
107       bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:16
107       bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:03:05
107       bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:00:16
107       bridge  vni-517       00:00:5e:00:01:0f                            00:01:28
107       bridge  vni-517       5c:f9:dd:ef:ab:82                            00:01:28
113       bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
113       bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:46
113       bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:00:16
113       bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:01:16
113       bridge  vni-521       00:0a:f7:e3:16:06                            00:00:16
113       bridge  vni-521       00:15:5d:71:0f:00                            00:03:45
113       bridge  vni-521       00:15:5d:71:0f:0e                            00:00:46
113       bridge  vni-521       00:15:5d:71:0f:19                            00:01:28
113       bridge  vni-521       00:15:5d:71:0f:21                            00:04:16
113       bridge  vni-521       00:15:5d:71:0f:22                            00:01:28
113       bridge  vni-521       00:15:5d:71:0f:25                            00:01:28
113       bridge  vni-521       00:15:5d:71:10:14                            00:07:46
113       bridge  vni-521       00:15:5d:71:10:15                            00:00:16
113       bridge  vni-521       00:15:5d:71:12:0c                            00:00:16
113       bridge  vni-521       00:15:5d:71:12:1b                            00:00:46
113       bridge  vni-521       00:15:5d:71:12:1c                            00:00:46
113       bridge  vni-521       00:15:5d:71:12:1d                            00:00:46
113       bridge  vni-521       00:15:5d:a8:22:08                            00:00:16
113       bridge  vni-521       00:15:5d:c8:f4:00                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f4:01                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f4:02                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f4:03                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f4:04                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f4:05                            00:00:16
113       bridge  vni-521       00:15:5d:c8:f4:06                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f4:07                            00:00:16
113       bridge  vni-521       00:15:5d:c8:f5:00                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:0a                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:0b                            00:01:16
113       bridge  vni-521       00:15:5d:c8:f5:0c                            00:05:46
113       bridge  vni-521       00:15:5d:c8:f5:0d                            00:10:16
113       bridge  vni-521       00:15:5d:c8:f5:0e                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:0f                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:01                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:1a                            00:10:16
113       bridge  vni-521       00:15:5d:c8:f5:1b                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:1c                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:1d                            00:00:46
113       bridge  vni-521       00:15:5d:c8:f5:1e                            00:00:16
113       bridge  vni-521       00:15:5d:c8:f5:1f                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:02                            00:01:16
113       bridge  vni-521       00:15:5d:c8:f5:2a                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:2b                            00:10:16
113       bridge  vni-521       00:15:5d:c8:f5:2c                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:2d                            00:00:46
113       bridge  vni-521       00:15:5d:c8:f5:2e                            00:00:46
113       bridge  vni-521       00:15:5d:c8:f5:2f                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:03                            00:08:11
113       bridge  vni-521       00:15:5d:c8:f5:04                            00:10:16
113       bridge  vni-521       00:15:5d:c8:f5:05                            00:08:18
113       bridge  vni-521       00:15:5d:c8:f5:06                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:07                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:08                            00:10:16
113       bridge  vni-521       00:15:5d:c8:f5:09                            00:01:16
113       bridge  vni-521       00:15:5d:c8:f5:10                            00:10:16
113       bridge  vni-521       00:15:5d:c8:f5:11                            00:01:16
113       bridge  vni-521       00:15:5d:c8:f5:12                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:13                            00:00:46
113       bridge  vni-521       00:15:5d:c8:f5:14                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:15                            00:10:16
113       bridge  vni-521       00:15:5d:c8:f5:16                            00:00:46
113       bridge  vni-521       00:15:5d:c8:f5:17                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:18                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:19                            00:01:16
113       bridge  vni-521       00:15:5d:c8:f5:20                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:21                            00:03:05
113       bridge  vni-521       00:15:5d:c8:f5:22                            00:10:16
113       bridge  vni-521       00:15:5d:c8:f5:23                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:24                            00:00:46
113       bridge  vni-521       00:15:5d:c8:f5:25                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:26                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:27                            00:10:16
113       bridge  vni-521       00:15:5d:c8:f5:28                            00:00:46
113       bridge  vni-521       00:15:5d:c8:f5:29                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:30                            00:01:28
113       bridge  vni-521       00:15:5d:c8:f5:31                            00:00:16
113       bridge  vni-521       00:15:5d:c8:f5:32                            00:10:16
113       bridge  vni-521       00:15:5d:c8:f6:00                            00:01:28
113       bridge  vni-521       00:15:7f:0c:f2:9f                            00:01:28
113       bridge  vni-521       00:50:56:90:ee:1a                            00:01:16
113       bridge  vni-521       00:50:56:a8:7c:fd                            00:01:28
113       bridge  vni-521       f8:bc:12:05:b4:c0                            00:02:05
113       bridge  vni-521       f8:bc:12:05:b5:00                            00:00:16
113       bridge  vni-521       fa:16:3e:7d:e4:86                            00:00:16
114       bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
114       bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:01:28
114       bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:00:16
114       bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:00:46
114       bridge  vni-525       00:00:5e:00:01:0f                            00:01:28
120       bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
120       bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:16
120       bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:01:28
120       bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:00:16
150       bridge  CSS-SGR-BOND  00:0c:29:bf:de:e3                            00:00:16
150       bridge  CSS-SGR-BOND  00:50:56:b4:72:e8                            00:03:45
150       bridge  CSS-SGR-BOND  00:50:56:b4:c7:ab                            00:00:16
150       bridge  vni-600       00:00:5e:00:01:96                            00:01:28
150       bridge  vni-600       00:50:56:90:43:ed                            00:01:28
150       bridge  vni-600       00:50:56:91:41:10                            00:01:28
150       bridge  vni-600       5c:f9:dd:ef:ab:82                            00:01:28
174       bridge  CSS-SGR-BOND  00:07:43:0b:74:8e                            00:00:16
174       bridge  CSS-SGR-BOND  00:07:43:0b:75:06                            00:00:16
174       bridge  CSS-SGR-BOND  00:07:43:0b:75:12                            00:00:16
174       bridge  CSS-SGR-BOND  00:07:43:0b:75:c2                            00:00:16
174       bridge  CSS-SGR-BOND  00:07:43:0b:ff:8f                            00:05:16
174       bridge  CSS-SGR-BOND  00:07:43:0b:ff:a7                            00:01:28
174       bridge  CSS-SGR-BOND  00:07:43:0b:ff:ab                            00:05:16
174       bridge  CSS-SGR-BOND  00:07:43:0c:00:c6                            00:07:46
174       bridge  CSS-SGR-BOND  00:50:56:6a:d5:e8                            00:05:16
174       bridge  CSS-SGR-BOND  00:50:56:6b:24:34                            00:01:28
174       bridge  CSS-SGR-BOND  00:50:56:6c:1a:f4                            00:08:18
174       bridge  CSS-SGR-BOND  00:50:56:6d:4b:6b                            00:01:28
174       bridge  CSS-SGR-BOND  00:50:56:6f:28:bd                            00:01:28
174       bridge  CSS-SGR-BOND  00:50:56:6f:bd:43                            00:04:16
174       bridge  CSS-SGR-BOND  00:50:56:60:51:1a                            00:01:28
174       bridge  CSS-SGR-BOND  00:50:56:66:1a:65                            00:01:16
174       bridge  CSS-SGR-BOND  00:50:56:67:50:4a                            00:01:28
174       bridge  CSS-SGR-BOND  00:50:56:68:32:30                            00:01:28
174       bridge  CSS-SGR-BOND  00:50:56:69:e8:5f                            00:01:28
174       bridge  CSS-SGR-BOND  00:50:56:a8:18:87                            00:01:28
174       bridge  CSS-SGR-BOND  f8:ca:b8:f1:5c:a5                            00:08:11
174       bridge  CSS-SGR-BOND  f8:ca:b8:f1:5c:b2                            00:01:28
174       bridge  CSS-SGR-BOND  f8:ca:b8:f1:5c:bf                            00:01:28
174       bridge  CSS-SGR-BOND  f8:ca:b8:f1:5c:cc                            00:06:45
174       bridge  CSS-SGR-BOND  f8:ca:b8:f1:5c:d9                            00:01:28
174       bridge  CSS-SGR-BOND  f8:ca:b8:f1:5c:e6                            00:00:46
174       bridge  CSS-SGR-BOND  f8:ca:b8:f1:5c:f3                            00:05:16
174       bridge  CSS-SGR-BOND  f8:ca:b8:f1:5d:00                            00:01:28
174       bridge  CSS-SGR-BOND  f8:ca:b8:f1:5d:0d                            00:06:45
174       bridge  CSS-SGR-BOND  f8:ca:b8:f1:5d:1a                            00:01:28
174       bridge  CSS-SGR-BOND  f8:ca:b8:f1:5d:27                            00:06:45
174       bridge  CSS-SGR-BOND  f8:ca:b8:f1:5d:34                            00:01:28
174       bridge  CSS-SGR-BOND  f8:ca:b8:f2:e4:a5                            00:01:28
174       bridge  CSS-SGR-BOND  f8:ca:b8:f2:e4:b2                            00:05:16
174       bridge  CSS-SGR-BOND  f8:ca:b8:f2:e4:bf                            00:01:28
174       bridge  CSS-SGR-BOND  f8:ca:b8:f2:e4:cc                            00:05:16
174       bridge  CSS-SGR-BOND  f8:ca:b8:f2:e4:d9                            00:07:46
174       bridge  CSS-SGR-BOND  f8:ca:b8:f2:e4:e6                            00:08:11
174       bridge  CSS-SGR-BOND  f8:ca:b8:f2:e4:f3                            00:07:46
174       bridge  CSS-SGR-BOND  f8:ca:b8:f2:e5:00                            00:01:16
174       bridge  CSS-SGR-BOND  f8:ca:b8:f2:e5:0d                            00:01:28
174       bridge  CSS-SGR-BOND  f8:ca:b8:f2:e5:1a                            00:01:28
174       bridge  CSS-SGR-BOND  f8:ca:b8:f2:e5:27                            00:08:18
174       bridge  CSS-SGR-BOND  f8:ca:b8:f2:e5:34                            00:01:28
174       bridge  vni-604       00:00:5e:00:01:ae                            00:01:28
174       bridge  vni-604       00:50:56:90:52:d8                            00:00:16
174       bridge  vni-604       5c:f9:dd:ef:ab:82                            00:01:28
175       bridge  CSS-SGR-BOND  00:07:43:0b:74:8f                            00:00:16
175       bridge  CSS-SGR-BOND  00:07:43:0b:75:07                            00:00:16
175       bridge  CSS-SGR-BOND  00:07:43:0b:75:13                            00:00:16
175       bridge  CSS-SGR-BOND  00:07:43:0b:75:c3                            00:00:16
175       bridge  CSS-SGR-BOND  00:07:43:0b:ff:90                            00:10:16
175       bridge  CSS-SGR-BOND  00:07:43:0b:ff:a8                            00:01:28
175       bridge  CSS-SGR-BOND  00:07:43:0b:ff:ac                            00:01:28
175       bridge  CSS-SGR-BOND  00:07:43:0c:00:c7                            00:01:28
175       bridge  CSS-SGR-BOND  00:50:56:6a:04:8e                            00:01:28
175       bridge  CSS-SGR-BOND  00:50:56:6b:3e:d7                            00:07:46
175       bridge  CSS-SGR-BOND  00:50:56:6b:18:a4                            00:01:28
175       bridge  CSS-SGR-BOND  00:50:56:6b:19:75                            00:01:28
175       bridge  CSS-SGR-BOND  00:50:56:6b:d3:06                            00:00:16
175       bridge  CSS-SGR-BOND  00:50:56:6c:26:66                            00:01:28
175       bridge  CSS-SGR-BOND  00:50:56:6c:39:ef                            00:02:05
175       bridge  CSS-SGR-BOND  00:50:56:6d:0b:08                            00:01:28
175       bridge  CSS-SGR-BOND  00:50:56:6d:64:bd                            00:01:28
175       bridge  CSS-SGR-BOND  00:50:56:6d:77:3f                            00:01:28
175       bridge  CSS-SGR-BOND  00:50:56:6e:8a:3d                            00:01:28
175       bridge  CSS-SGR-BOND  00:50:56:6e:50:d1                            00:12:19
175       bridge  CSS-SGR-BOND  00:50:56:6e:90:31                            00:05:46
175       bridge  CSS-SGR-BOND  00:50:56:6f:12:3a                            00:11:57
175       bridge  CSS-SGR-BOND  00:50:56:6f:bd:be                            00:02:05
175       bridge  CSS-SGR-BOND  00:50:56:6f:d0:b1                            00:12:19
175       bridge  CSS-SGR-BOND  00:50:56:6f:eb:7a                            00:12:19
175       bridge  CSS-SGR-BOND  00:50:56:60:41:00                            00:01:28
175       bridge  CSS-SGR-BOND  00:50:56:61:58:58                            00:01:28
175       bridge  CSS-SGR-BOND  00:50:56:61:ac:03                            00:01:28
175       bridge  CSS-SGR-BOND  00:50:56:62:0b:0e                            00:01:28
175       bridge  CSS-SGR-BOND  00:50:56:62:0c:34                            00:01:28
175       bridge  CSS-SGR-BOND  00:50:56:62:b5:5a                            00:11:57
175       bridge  CSS-SGR-BOND  00:50:56:64:c4:28                            00:04:16
175       bridge  CSS-SGR-BOND  00:50:56:64:d4:cd                            00:11:57
175       bridge  CSS-SGR-BOND  00:50:56:65:23:58                            00:10:51
175       bridge  CSS-SGR-BOND  00:50:56:65:53:7c                            00:01:28
175       bridge  CSS-SGR-BOND  00:50:56:66:18:b8                            00:01:28
175       bridge  CSS-SGR-BOND  00:50:56:66:73:db                            00:01:28
175       bridge  CSS-SGR-BOND  00:50:56:67:93:8e                            00:08:11
175       bridge  CSS-SGR-BOND  00:50:56:67:d4:07                            00:00:16
175       bridge  CSS-SGR-BOND  00:50:56:67:f9:ee                            00:01:28
175       bridge  CSS-SGR-BOND  00:50:56:68:6a:8a                            00:02:05
175       bridge  CSS-SGR-BOND  00:50:56:68:9e:02                            00:09:13
175       bridge  CSS-SGR-BOND  00:50:56:69:63:3d                            00:03:05
175       bridge  CSS-SGR-BOND  00:50:56:69:a5:50                            00:01:28
175       bridge  CSS-SGR-BOND  f4:8e:38:0e:47:5e                            00:01:28
175       bridge  vni-605       00:00:5e:00:01:af                            00:01:28
175       bridge  vni-605       00:50:56:90:52:d8                            00:00:16
175       bridge  vni-605       5c:f9:dd:ef:ab:82                            00:01:28
200       bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
200       bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:01:28
200       bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:02:46
200       bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:01:16
200       bridge  vni-511       00:50:56:91:28:3b                            00:00:46
200       bridge  vni-511       00:50:56:a8:d3:cb                            00:10:51
201       bridge  CSS-SGR-BOND  14:18:77:36:37:27                            00:00:16
201       bridge  vni-512       00:00:5e:00:01:96                            00:01:28
201       bridge  vni-512       5c:f9:dd:ef:ab:82                            00:01:28
205       bridge  vni-522       00:50:56:91:0a:a4                            00:08:18
205       bridge  vni-522       00:50:56:91:1a:22                            00:03:05
205       bridge  vni-522       00:50:56:91:1d:e6                            00:01:28
205       bridge  vni-522       00:50:56:91:1f:ba                            00:01:28
205       bridge  vni-522       00:50:56:91:5d:00                            00:02:05
205       bridge  vni-522       00:50:56:91:10:37                            00:01:28
205       bridge  vni-522       00:50:56:91:31:3d                            00:01:28
205       bridge  vni-522       00:50:56:91:73:bf                            00:01:28
205       bridge  vni-522       00:50:56:91:75:9d                            00:01:28
205       bridge  vni-522       00:50:56:a8:9f:c1                            00:01:28
230       bridge  CSS-SGR-BOND  00:00:5e:00:01:e6                            00:00:16
230       bridge  CSS-SGR-BOND  00:0e:1e:eb:da:90                            00:00:16
230       bridge  CSS-SGR-BOND  00:07:43:0b:f0:3e                            00:00:16
230       bridge  CSS-SGR-BOND  00:07:43:0b:f0:36                            00:00:16
230       bridge  CSS-SGR-BOND  00:15:5d:e6:64:00                            00:00:16
230       bridge  CSS-SGR-BOND  00:15:5d:e6:64:01                            00:00:16
230       bridge  CSS-SGR-BOND  00:15:5d:e6:64:02                            00:00:16
230       bridge  CSS-SGR-BOND  00:15:5d:e6:64:03                            00:00:16
230       bridge  CSS-SGR-BOND  00:15:5d:e6:64:04                            00:00:16
230       bridge  CSS-SGR-BOND  00:15:5d:e6:64:05                            00:00:16
230       bridge  CSS-SGR-BOND  00:15:5d:e6:64:06                            00:00:16
230       bridge  CSS-SGR-BOND  00:24:50:30:f3:4b                            00:00:16
230       bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
230       bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:16
230       bridge  CSS-SGR-BOND  74:2b:0f:0a:3e:f3                            00:01:28
230       bridge  CSS-SGR-BOND  74:2b:0f:0a:3e:f4                            00:01:28
230       bridge  CSS-SGR-BOND  74:2b:0f:0a:3e:f5                            00:01:28
230       bridge  CSS-SGR-BOND  74:2b:0f:0a:3e:f9                            00:00:16
230       bridge  CSS-SGR-BOND  74:2b:0f:0a:3e:fa                            00:00:16
230       bridge  CSS-SGR-BOND  74:2b:0f:0a:3e:fb                            00:00:16
230       bridge  CSS-SGR-BOND  74:2b:0f:0a:3e:fc                            00:00:16
230       bridge  CSS-SGR-BOND  74:2b:0f:0a:3e:fd                            00:01:28
230       bridge  CSS-SGR-BOND  74:2b:0f:0a:3e:fe                            00:01:28
230       bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:00:46
230       bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:01:28
230       bridge  CSS-SGR-BOND  ec:f4:bb:ff:2b:b3                            00:00:16
230       bridge  CSS-SGR-BOND  ec:f4:bb:ff:36:48                            00:01:28
230       bridge  vni-1001      00:00:0c:9f:f0:e6                            00:00:16
230       bridge  vni-1001      00:0e:1e:eb:ec:b0                            00:00:16
230       bridge  vni-1001      00:0e:1e:eb:ec:b2                            00:00:16
230       bridge  vni-1001      00:07:43:0a:26:c5                            00:00:16
230       bridge  vni-1001      00:07:43:0a:26:cd                            00:00:16
230       bridge  vni-1001      00:07:43:46:af:c8                            00:00:16
230       bridge  vni-1001      00:07:43:46:af:e8                            00:00:16
230       bridge  vni-1001      00:15:5d:e6:12:00                            00:00:16
230       bridge  vni-1001      00:15:5d:e6:12:01                            00:00:16
230       bridge  vni-1001      00:15:5d:e6:12:02                            00:00:46
230       bridge  vni-1001      00:15:5d:e6:12:03                            00:00:16
230       bridge  vni-1001      00:15:5d:e6:12:04                            00:00:16
230       bridge  vni-1001      00:15:5d:e6:12:05                            00:00:16
230       bridge  vni-1001      00:15:5d:e6:12:06                            00:00:16
230       bridge  vni-1001      00:15:5d:e6:12:07                            00:00:16
230       bridge  vni-1001      64:a0:e7:40:b4:c2                            00:00:16
230       bridge  vni-1001      64:a0:e7:43:1b:c2                            00:00:16
230       bridge  vni-1001      74:2b:0f:09:a1:ed                            00:00:16
230       bridge  vni-1001      74:2b:0f:09:a1:ee                            00:00:16
230       bridge  vni-1001      74:2b:0f:09:a1:ef                            00:00:16
230       bridge  vni-1001      74:2b:0f:09:a1:f0                            00:00:16
230       bridge  vni-1001      f4:8e:38:2d:ee:fa                            00:00:16
250       bridge  vni-250       00:50:56:a8:f6:e9                            00:01:28
253       bridge  vni-520       00:00:5e:00:01:0f                            00:01:28
1000      bridge  CSS-SGR-BOND  00:15:5d:82:22:0a                            00:00:16
1000      bridge  CSS-SGR-BOND  00:15:5d:82:23:12                            00:00:16
1000      bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
1000      bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:46
1000      bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:01:28
1000      bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:02:46
1000      bridge  CSS-SGR-BOND  b0:83:fe:d7:59:6b                            00:00:16
1000      bridge  CSS-SGR-BOND  b0:83:fe:e1:b3:4e                            00:00:16
1000      bridge  vni-1000      00:00:5e:00:01:64                            00:01:28
1000      bridge  vni-1000      00:15:5d:0b:16:07                            00:01:16
1000      bridge  vni-1000      00:15:5d:0b:16:14                            00:00:16
1000      bridge  vni-1000      00:50:56:90:77:5b                            00:01:16
1000      bridge  vni-1000      00:50:56:90:c6:dc                            00:01:16
1000      bridge  vni-1000      00:50:56:91:01:f4                            00:01:28
1000      bridge  vni-1000      00:50:56:91:1e:49                            00:00:16
1000      bridge  vni-1000      00:50:56:91:3d:ab                            00:01:16
1000      bridge  vni-1000      00:50:56:91:3e:d8                            00:09:13
1000      bridge  vni-1000      00:50:56:91:4f:7e                            00:01:28
1000      bridge  vni-1000      00:50:56:91:5a:2d                            00:01:16
1000      bridge  vni-1000      00:50:56:91:5e:4f                            00:01:28
1000      bridge  vni-1000      00:50:56:91:6e:60                            00:02:46
1000      bridge  vni-1000      00:50:56:91:07:ed                            00:01:28
1000      bridge  vni-1000      00:50:56:91:7a:11                            00:03:45
1000      bridge  vni-1000      00:50:56:91:7b:d2                            00:01:28
1000      bridge  vni-1000      00:50:56:91:7d:b0                            00:01:28
1000      bridge  vni-1000      00:50:56:91:11:0b                            00:01:28
1000      bridge  vni-1000      00:50:56:91:11:58                            00:02:05
1000      bridge  vni-1000      00:50:56:91:12:62                            00:00:16
1000      bridge  vni-1000      00:50:56:91:16:77                            00:01:28
1000      bridge  vni-1000      00:50:56:91:16:e2                            00:01:28
1000      bridge  vni-1000      00:50:56:91:22:17                            00:01:28
1000      bridge  vni-1000      00:50:56:91:22:f6                            00:02:46
1000      bridge  vni-1000      00:50:56:91:37:cc                            00:01:28
1000      bridge  vni-1000      00:50:56:91:39:59                            00:03:45
1000      bridge  vni-1000      00:50:56:91:47:69                            00:00:16
1000      bridge  vni-1000      00:50:56:91:47:cb                            00:01:28
1000      bridge  vni-1000      00:50:56:91:62:88                            00:00:46
1000      bridge  vni-1000      00:50:56:91:71:8c                            00:01:28
1000      bridge  vni-1000      00:50:56:91:74:bc                            00:00:46
1000      bridge  vni-1000      24:8a:07:88:d9:ba                            00:00:16
1000      bridge  vni-1000      24:8a:07:ad:6d:3a                            00:00:46
1000      bridge  vni-1000      b0:83:fe:d7:4e:ca                            00:00:46
1000      bridge  vni-1000      d0:67:e5:dc:e3:b3                            00:01:28
1000      bridge  vni-1000      d0:67:e5:dc:e5:0b                            00:00:16
1002      bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
1002      bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:46
1002      bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:01:28
1002      bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:02:46
1002      bridge  CSS-SGR-BOND  f8:ca:b8:f2:e4:ab                            00:00:16
1002      bridge  vni-1002      00:00:5e:00:01:64                            00:00:16
1002      bridge  vni-1002      d0:67:e5:dc:e3:b3                            00:00:16
1002      bridge  vni-1002      d0:67:e5:dc:e5:0b                            00:00:16
1003      bridge  CSS-SGR-BOND  00:0c:29:e3:08:b7                            00:00:16
1003      bridge  CSS-SGR-BOND  00:0c:29:f7:f3:15                            00:00:16
1003      bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
1003      bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:02:46
1003      bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:00:16
1003      bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:02:46
1003      bridge  vni-513       00:00:5e:00:01:96                            00:01:28
1003      bridge  vni-513       5c:f9:dd:ef:ab:82                            00:01:28
1004      bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
1004      bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:46
1004      bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:02:46
1004      bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:01:28
1004      bridge  vni-514       00:00:5e:00:01:0f                            00:01:28
1004      bridge  vni-514       00:50:56:9e:00:f3                            00:01:28
1004      bridge  vni-514       00:50:56:9e:0a:32                            00:02:05
1004      bridge  vni-514       00:50:56:9e:0d:45                            00:01:28
1004      bridge  vni-514       00:50:56:9e:0f:58                            00:02:46
1004      bridge  vni-514       00:50:56:9e:01:7d                            00:01:28
1004      bridge  vni-514       00:50:56:9e:01:d3                            00:01:28
1004      bridge  vni-514       00:50:56:9e:1a:15                            00:01:28
1004      bridge  vni-514       00:50:56:9e:1b:f8                            00:01:28
1004      bridge  vni-514       00:50:56:9e:1d:75                            00:01:28
1004      bridge  vni-514       00:50:56:9e:1d:f0                            00:01:28
1004      bridge  vni-514       00:50:56:9e:1f:ef                            00:01:28
1004      bridge  vni-514       00:50:56:9e:2e:17                            00:01:28
1004      bridge  vni-514       00:50:56:9e:03:93                            00:01:28
1004      bridge  vni-514       00:50:56:9e:03:b0                            00:01:28
1004      bridge  vni-514       00:50:56:9e:3a:12                            00:01:16
1004      bridge  vni-514       00:50:56:9e:4b:bb                            00:01:16
1004      bridge  vni-514       00:50:56:9e:4c:70                            00:02:05
1004      bridge  vni-514       00:50:56:9e:4d:d3                            00:01:28
1004      bridge  vni-514       00:50:56:9e:4d:d9                            00:00:16
1004      bridge  vni-514       00:50:56:9e:4e:6d                            00:01:28
1004      bridge  vni-514       00:50:56:9e:4e:ac                            00:01:28
1004      bridge  vni-514       00:50:56:9e:4f:5a                            00:02:05
1004      bridge  vni-514       00:50:56:9e:05:b1                            00:01:28
1004      bridge  vni-514       00:50:56:9e:5a:a5                            00:01:28
1004      bridge  vni-514       00:50:56:9e:5e:7b                            00:01:28
1004      bridge  vni-514       00:50:56:9e:5f:61                            00:01:28
1004      bridge  vni-514       00:50:56:9e:5f:77                            00:01:28
1004      bridge  vni-514       00:50:56:9e:5f:b6                            00:01:28
1004      bridge  vni-514       00:50:56:9e:6a:1b                            00:01:28
1004      bridge  vni-514       00:50:56:9e:6a:58                            00:01:28
1004      bridge  vni-514       00:50:56:9e:6b:32                            00:01:28
1004      bridge  vni-514       00:50:56:9e:6f:15                            00:01:28
1004      bridge  vni-514       00:50:56:9e:6f:35                            00:10:16
1004      bridge  vni-514       00:50:56:9e:07:03                            00:00:16
1004      bridge  vni-514       00:50:56:9e:07:e7                            00:01:28
1004      bridge  vni-514       00:50:56:9e:7b:94                            00:03:05
1004      bridge  vni-514       00:50:56:9e:8a:e9                            00:01:28
1004      bridge  vni-514       00:50:56:9e:8c:a5                            00:03:45
1004      bridge  vni-514       00:50:56:9e:8d:86                            00:01:28
1004      bridge  vni-514       00:50:56:9e:09:50                            00:01:28
1004      bridge  vni-514       00:50:56:9e:09:68                            00:01:28
1004      bridge  vni-514       00:50:56:9e:9b:db                            00:00:16
1004      bridge  vni-514       00:50:56:9e:9b:ed                            00:01:28
1004      bridge  vni-514       00:50:56:9e:9c:3a                            00:01:28
1004      bridge  vni-514       00:50:56:9e:9d:e4                            00:02:05
1004      bridge  vni-514       00:50:56:9e:9e:38                            00:01:16
1004      bridge  vni-514       00:50:56:9e:9f:68                            00:01:28
1004      bridge  vni-514       00:50:56:9e:9f:e6                            00:01:28
1004      bridge  vni-514       00:50:56:9e:11:64                            00:01:28
1004      bridge  vni-514       00:50:56:9e:12:2a                            00:00:16
1004      bridge  vni-514       00:50:56:9e:13:82                            00:01:28
1004      bridge  vni-514       00:50:56:9e:17:f5                            00:01:28
1004      bridge  vni-514       00:50:56:9e:20:78                            00:01:28
1004      bridge  vni-514       00:50:56:9e:22:91                            00:01:28
1004      bridge  vni-514       00:50:56:9e:23:80                            00:01:28
1004      bridge  vni-514       00:50:56:9e:28:73                            00:01:16
1004      bridge  vni-514       00:50:56:9e:33:19                            00:01:28
1004      bridge  vni-514       00:50:56:9e:33:cb                            00:01:28
1004      bridge  vni-514       00:50:56:9e:34:cf                            00:01:16
1004      bridge  vni-514       00:50:56:9e:39:d8                            00:10:16
1004      bridge  vni-514       00:50:56:9e:39:e8                            00:01:28
1004      bridge  vni-514       00:50:56:9e:40:b7                            00:10:16
1004      bridge  vni-514       00:50:56:9e:42:ea                            00:01:28
1004      bridge  vni-514       00:50:56:9e:43:0e                            00:01:28
1004      bridge  vni-514       00:50:56:9e:43:ca                            00:01:28
1004      bridge  vni-514       00:50:56:9e:46:8e                            00:01:28
1004      bridge  vni-514       00:50:56:9e:47:a6                            00:01:28
1004      bridge  vni-514       00:50:56:9e:48:6b                            00:01:28
1004      bridge  vni-514       00:50:56:9e:49:57                            00:08:18
1004      bridge  vni-514       00:50:56:9e:54:4e                            00:09:20
1004      bridge  vni-514       00:50:56:9e:56:f5                            00:05:16
1004      bridge  vni-514       00:50:56:9e:61:ba                            00:04:46
1004      bridge  vni-514       00:50:56:9e:63:e7                            00:01:28
1004      bridge  vni-514       00:50:56:9e:64:50                            00:01:28
1004      bridge  vni-514       00:50:56:9e:66:76                            00:01:28
1004      bridge  vni-514       00:50:56:9e:68:95                            00:01:28
1004      bridge  vni-514       00:50:56:9e:70:ea                            00:01:28
1004      bridge  vni-514       00:50:56:9e:75:83                            00:00:46
1004      bridge  vni-514       00:50:56:9e:77:05                            00:02:05
1004      bridge  vni-514       00:50:56:9e:77:09                            00:01:28
1004      bridge  vni-514       00:50:56:9e:80:cb                            00:01:28
1004      bridge  vni-514       00:50:56:9e:84:8a                            00:10:16
1004      bridge  vni-514       00:50:56:9e:85:51                            00:01:28
1004      bridge  vni-514       00:50:56:9e:86:f1                            00:00:16
1004      bridge  vni-514       00:50:56:9e:87:ce                            00:01:28
1004      bridge  vni-514       00:50:56:9e:90:65                            00:01:28
1004      bridge  vni-514       00:50:56:9e:91:20                            00:01:16
1004      bridge  vni-514       00:50:56:9e:93:1a                            00:01:28
1004      bridge  vni-514       00:50:56:9e:93:76                            00:01:28
1004      bridge  vni-514       00:50:56:9e:98:2e                            00:01:28
1004      bridge  vni-514       00:50:56:9e:99:97                            00:00:46
1004      bridge  vni-514       00:50:56:9e:a0:33                            00:01:28
1004      bridge  vni-514       00:50:56:9e:a3:30                            00:01:28
1004      bridge  vni-514       00:50:56:9e:a4:9b                            00:01:28
1004      bridge  vni-514       00:50:56:9e:a4:a3                            00:10:16
1004      bridge  vni-514       00:50:56:9e:a5:2d                            00:01:16
1004      bridge  vni-514       00:50:56:9e:a7:9a                            00:01:28
1004      bridge  vni-514       00:50:56:9e:a8:5c                            00:01:28
1004      bridge  vni-514       00:50:56:9e:ae:52                            00:01:28
1004      bridge  vni-514       00:50:56:9e:af:28                            00:01:28
1004      bridge  vni-514       00:50:56:9e:b0:c9                            00:00:46
1004      bridge  vni-514       00:50:56:9e:b1:06                            00:01:28
1004      bridge  vni-514       00:50:56:9e:b3:12                            00:02:05
1004      bridge  vni-514       00:50:56:9e:b4:5c                            00:01:16
1004      bridge  vni-514       00:50:56:9e:b5:c7                            00:01:28
1004      bridge  vni-514       00:50:56:9e:b7:f3                            00:01:16
1004      bridge  vni-514       00:50:56:9e:b8:8e                            00:00:16
1004      bridge  vni-514       00:50:56:9e:ba:94                            00:00:46
1004      bridge  vni-514       00:50:56:9e:ba:fe                            00:10:16
1004      bridge  vni-514       00:50:56:9e:bb:81                            00:01:28
1004      bridge  vni-514       00:50:56:9e:bd:8b                            00:10:51
1004      bridge  vni-514       00:50:56:9e:c4:1f                            00:01:16
1004      bridge  vni-514       00:50:56:9e:c6:0f                            00:02:46
1004      bridge  vni-514       00:50:56:9e:c7:c9                            00:10:16
1004      bridge  vni-514       00:50:56:9e:cd:f4                            00:01:28
1004      bridge  vni-514       00:50:56:9e:cf:fb                            00:01:16
1004      bridge  vni-514       00:50:56:9e:d0:ae                            00:02:46
1004      bridge  vni-514       00:50:56:9e:d4:c7                            00:01:28
1004      bridge  vni-514       00:50:56:9e:d6:de                            00:01:28
1004      bridge  vni-514       00:50:56:9e:d9:25                            00:00:46
1004      bridge  vni-514       00:50:56:9e:d9:ef                            00:01:28
1004      bridge  vni-514       00:50:56:9e:da:76                            00:01:28
1004      bridge  vni-514       00:50:56:9e:da:fd                            00:01:28
1004      bridge  vni-514       00:50:56:9e:dc:e6                            00:01:28
1004      bridge  vni-514       00:50:56:9e:de:06                            00:01:28
1004      bridge  vni-514       00:50:56:9e:df:a6                            00:00:46
1004      bridge  vni-514       00:50:56:9e:e3:6e                            00:01:28
1004      bridge  vni-514       00:50:56:9e:e6:06                            00:01:28
1004      bridge  vni-514       00:50:56:9e:e7:b7                            00:02:05
1004      bridge  vni-514       00:50:56:9e:e8:7d                            00:01:28
1004      bridge  vni-514       00:50:56:9e:e9:6d                            00:07:46
1004      bridge  vni-514       00:50:56:9e:ea:71                            00:01:28
1004      bridge  vni-514       00:50:56:9e:eb:6f                            00:01:28
1004      bridge  vni-514       00:50:56:9e:eb:8a                            00:01:28
1004      bridge  vni-514       00:50:56:9e:ee:c4                            00:01:28
1004      bridge  vni-514       00:50:56:9e:ef:74                            00:01:28
1004      bridge  vni-514       00:50:56:9e:ef:a2                            00:01:28
1004      bridge  vni-514       00:50:56:9e:f6:cc                            00:01:28
1004      bridge  vni-514       00:50:56:9e:f8:f9                            00:00:16
1004      bridge  vni-514       00:50:56:9e:fa:a6                            00:05:16
1004      bridge  vni-514       00:50:56:9e:fb:35                            00:01:28
1004      bridge  vni-514       00:50:56:9e:fd:00                            00:01:28
1004      bridge  vni-514       00:50:56:90:a9:75                            00:02:05
1004      bridge  vni-514       5c:f9:dd:ef:ab:82                            00:01:28
1005      bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
1005      bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:02:05
1005      bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:02:05
1005      bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:01:16
1005      bridge  vni-523       00:50:56:90:97:d4                            00:00:16
1006      bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
1006      bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:16
1006      bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:01:16
1006      bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:01:28
1006      bridge  vni-524       00:50:56:91:7b:75                            00:01:28
1006      bridge  vni-524       00:50:56:91:25:bd                            00:02:46
1006      bridge  vni-524       00:50:56:91:40:a6                            00:00:16
1006      bridge  vni-524       00:50:56:91:54:48                            00:01:28
1007      bridge  CSS-SGR-BOND  00:15:5d:82:22:0b                            00:00:16
1007      bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
1007      bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:46
1007      bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:01:28
1007      bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:00:46
1007      bridge  CSS-SGR-BOND  b0:83:fe:d7:59:6b                            00:00:16
1007      bridge  CSS-SGR-BOND  f8:ca:b8:f2:e4:a9                            00:07:10
1007      bridge  CSS-SGR-BOND  f8:ca:b8:f2:e4:ac                            00:03:05
1007      bridge  vni-519       00:00:5e:00:01:0f                            00:01:28
1007      bridge  vni-519       00:15:5d:0b:15:13                            00:00:16
1007      bridge  vni-519       00:15:5d:6d:19:0a                            00:01:28
1007      bridge  vni-519       00:15:5d:6d:19:05                            00:00:46
1007      bridge  vni-519       00:15:5d:6d:19:06                            00:01:16
1007      bridge  vni-519       00:15:5d:6d:19:07                            00:01:16
1007      bridge  vni-519       00:15:5d:6d:19:10                            00:01:16
1007      bridge  vni-519       00:15:5d:6d:19:11                            00:01:16
1007      bridge  vni-519       00:15:5d:6d:19:12                            00:00:46
1007      bridge  vni-519       00:15:5d:6d:19:13                            00:01:16
1007      bridge  vni-519       00:50:56:a8:3e:15                            00:00:16
1007      bridge  vni-519       24:8a:07:55:4b:b4                            00:00:46
1007      bridge  vni-519       24:8a:07:91:5a:4c                            00:01:28
1007      bridge  vni-519       b0:83:fe:d7:4e:ca                            00:00:16
1102      bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
1102      bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:16
1102      bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:01:28
1102      bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:01:28
1102      bridge  CSS-SGR-BOND  f8:ca:b8:f2:e4:a5                            00:01:16
1102      bridge  vni-1102      00:00:5e:00:01:66                            00:01:28
1102      bridge  vni-1102      5c:f9:dd:ef:ab:82                            00:01:28
1102      bridge  vni-1102      24:8a:07:91:5a:4d                            00:01:28
1103      bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
1103      bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:46
1103      bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:01:28
1103      bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:00:16
1103      bridge  CSS-SGR-BOND  f8:ca:b8:f2:e4:a8                            00:01:16
1103      bridge  vni-1103      00:00:5e:00:01:67                            00:01:28
1103      bridge  vni-1103      24:8a:07:55:4b:b5                            00:00:16
1200      bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
1200      bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:16
1200      bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:01:28
1200      bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:01:16
1200      bridge  vni-1200      00:15:5d:0b:16:00                            00:01:28
1200      bridge  vni-1200      00:15:5d:0b:16:01                            00:01:28
1200      bridge  vni-1200      00:50:56:a8:fe:c0                            00:01:28
1200      bridge  vni-1200      24:8a:07:88:d9:ba                            00:01:28
1200      bridge  vni-1200      24:8a:07:ad:6d:3a                            00:00:16
1201      bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
1201      bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:16
1201      bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:01:28
1201      bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:02:46
1201      bridge  vni-1201      00:15:5d:0b:16:03                            00:01:28
1201      bridge  vni-1201      00:50:56:a8:43:7a                            00:13:46
1201      bridge  vni-1201      24:8a:07:88:d9:ba                            00:01:16
1201      bridge  vni-1201      24:8a:07:ad:6d:3a                            00:00:16
1202      bridge  CSS-SGR-BOND  00:15:5d:82:23:0e                            00:01:28
1202      bridge  CSS-SGR-BOND  00:15:5d:82:23:0f                            00:20:46
1202      bridge  CSS-SGR-BOND  00:15:5d:82:23:10                            00:01:16
1202      bridge  CSS-SGR-BOND  00:15:5d:82:23:11                            00:26:46
1202      bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
1202      bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:16
1202      bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:00:46
1202      bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:00:46
1202      bridge  CSS-SGR-BOND  b0:83:fe:e1:b3:4e                            00:01:28
1251      bridge  CSS-SGR-BOND  00:50:56:a8:2e:e0                            00:00:16
1251      bridge  vni-1251      00:00:5e:00:01:0f                            00:01:28
1251      bridge  vni-1251      5c:f9:dd:ef:ab:82                            00:01:28
1998      bridge  CSS-SGR-BOND  00:50:56:a8:15:42                            00:00:16
1998      bridge  CSS-SGR-BOND  00:50:56:a8:75:18                            00:00:16
1998      bridge  CSS-SGR-BOND  7c:fe:90:fb:d1:dc                            00:00:16
1998      bridge  CSS-SGR-BOND  b8:59:9f:6a:5f:dc                            00:00:16
1998      bridge  vni-1998      00:00:5e:00:01:64                            00:00:16
1998      bridge  vni-1998      00:50:56:a8:0e:e0                            00:01:28
1998      bridge  vni-1998      00:50:56:a8:1f:90                            00:00:46
1998      bridge  vni-1998      00:50:56:a8:3b:5c                            00:01:28
1998      bridge  vni-1998      00:50:56:a8:9d:93                            00:00:46
1998      bridge  vni-1998      00:50:56:a8:10:80                            00:00:46
1998      bridge  vni-1998      00:50:56:a8:25:65                            00:01:28
1998      bridge  vni-1998      00:50:56:a8:34:c8                            00:01:28
1998      bridge  vni-1998      00:50:56:a8:a3:e4                            00:02:05
1998      bridge  vni-1998      00:50:56:a8:a4:6f                            00:00:16
1998      bridge  vni-1998      00:50:56:a8:b6:6a                            00:00:16
1998      bridge  vni-1998      00:50:56:a8:cf:fe                            00:01:16
1998      bridge  vni-1998      00:50:56:a8:fe:30                            00:01:28
1998      bridge  vni-1998      e4:f0:04:5b:c8:43                            00:01:28
1998      bridge  vni-1998      e4:f0:04:58:9c:c3                            00:00:16
1999      bridge  CSS-SGR-BOND  7c:fe:90:fb:d1:dc                            00:01:28
1999      bridge  CSS-SGR-BOND  b8:59:9f:6a:5f:dc                            00:01:28
1999      bridge  vni-1999      00:00:5e:00:01:65                            00:01:28
1999      bridge  vni-1999      00:50:56:a8:33:ad                            00:01:28
1999      bridge  vni-1999      00:50:56:a8:ce:e4                            00:07:10
1999      bridge  vni-1999      e4:f0:04:5b:c8:43                            00:01:28
1999      bridge  vni-1999      e4:f0:04:58:9c:c3                            00:00:16
2000      bridge  vni-100       5c:f9:dd:ef:ab:82                            00:01:28
2100      bridge  vni-2100      00:00:5e:00:01:0f                            00:01:28
2511      bridge  CSS-SGR-BOND  00:15:5d:82:22:0d                            00:01:28
2511      bridge  CSS-SGR-BOND  00:15:5d:82:23:14                            00:01:28
2511      bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
2511      bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:16
2511      bridge  CSS-SGR-BOND  98:03:9b:61:9c:f8                            00:00:16
2511      bridge  CSS-SGR-BOND  98:03:9b:61:27:18                            00:00:16
2511      bridge  CSS-SGR-BOND  98:03:9b:61:bc:b8                            00:00:16
2511      bridge  CSS-SGR-BOND  98:03:9b:b4:5f:6a                            00:00:16
2511      bridge  CSS-SGR-BOND  98:03:9b:b4:5f:8a                            00:02:05
2511      bridge  CSS-SGR-BOND  98:03:9b:b4:60:92                            00:10:16
2511      bridge  CSS-SGR-BOND  98:03:9b:b4:60:a2                            00:00:16
2511      bridge  CSS-SGR-BOND  98:03:9b:b4:60:b2                            00:00:16
2511      bridge  CSS-SGR-BOND  98:03:9b:b4:61:b2                            00:00:16
2511      bridge  CSS-SGR-BOND  98:03:9b:b4:63:5a                            00:08:18
2511      bridge  CSS-SGR-BOND  98:03:9b:b4:66:22                            00:03:05
2511      bridge  CSS-SGR-BOND  98:03:9b:b4:67:9a                            00:00:16
2511      bridge  CSS-SGR-BOND  98:03:9b:b4:67:a2                            00:00:16
2511      bridge  CSS-SGR-BOND  98:03:9b:b4:67:b2                            00:00:16
2511      bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:00:16
2511      bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:00:46
2511      bridge  CSS-SGR-BOND  b0:83:fe:d7:59:6b                            00:01:16
2511      bridge  CSS-SGR-BOND  b0:83:fe:e1:b3:4e                            00:00:16
2511      bridge  CSS-SGR-BOND  f4:52:14:3a:22:c0                            00:01:16
2511      bridge  CSS-SGR-BOND  f4:52:14:33:2d:c0                            00:00:16
2511      bridge  vni-2511      00:00:5e:00:01:0f                            00:01:28
2511      bridge  vni-2511      5c:f9:dd:ef:ab:82                            00:01:28
2520      bridge  CSS-SGR-BOND  00:00:5e:00:01:01                            00:00:16
2520      bridge  CSS-SGR-BOND  00:ec:ac:ce:b2:bb                            00:01:28
2520      bridge  CSS-SGR-BOND  3c:2c:30:68:08:02                            00:00:16
2520      bridge  CSS-SGR-BOND  24:6e:96:cc:2e:7c                            00:01:28
2520      bridge  CSS-SGR-BOND  24:8a:07:2c:43:16                            00:01:28
2520      bridge  CSS-SGR-BOND  24:8a:07:53:3a:5e                            00:01:28
2520      bridge  CSS-SGR-BOND  24:8a:07:56:2e:b4                            00:01:28
2520      bridge  CSS-SGR-BOND  24:8a:07:92:fd:3c                            00:15:25
2520      bridge  CSS-SGR-BOND  24:8a:07:92:ff:44                            00:01:28
2520      bridge  CSS-SGR-BOND  24:8a:07:a8:07:ec                            00:01:28
2520      bridge  CSS-SGR-BOND  50:6b:4b:cb:bc:80                            00:02:46
2520      bridge  CSS-SGR-BOND  98:03:9b:80:31:28                            00:01:28
2520      bridge  CSS-SGR-BOND  b8:59:9f:27:c0:04                            00:01:28
2520      bridge  CSS-SGR-BOND  e4:43:4b:02:f1:0c                            00:01:28
2520      bridge  CSS-SGR-BOND  ec:f4:bb:ff:36:48                            00:07:46
2520      bridge  vni-2520      5c:f9:dd:ef:ab:82                            00:01:28
2521      bridge  CSS-SGR-BOND  4c:d9:8f:1f:4f:a0                            00:01:16
2521      bridge  CSS-SGR-BOND  4c:d9:8f:1f:4f:ca                            00:00:46
2521      bridge  CSS-SGR-BOND  4c:d9:8f:1f:52:28                            00:01:16
2521      bridge  CSS-SGR-BOND  4c:d9:8f:40:39:6c                            00:01:28
2521      bridge  CSS-SGR-BOND  4c:d9:8f:43:8a:b1                            00:04:46
2521      bridge  CSS-SGR-BOND  4c:d9:8f:43:9b:03                            00:03:05
2521      bridge  CSS-SGR-BOND  4c:d9:8f:43:9b:5b                            00:00:16
2521      bridge  CSS-SGR-BOND  4c:d9:8f:43:9b:43                            00:01:16
2521      bridge  CSS-SGR-BOND  4c:d9:8f:43:84:c8                            00:01:28
2521      bridge  CSS-SGR-BOND  4c:d9:8f:43:86:e9                            00:01:16
2521      bridge  CSS-SGR-BOND  4c:d9:8f:48:62:d4                            00:00:16
2521      bridge  CSS-SGR-BOND  4c:d9:8f:48:63:2c                            00:00:46
2521      bridge  CSS-SGR-BOND  4c:d9:8f:48:63:cc                            00:01:16
2521      bridge  CSS-SGR-BOND  4c:d9:8f:48:65:c4                            00:04:46
2521      bridge  CSS-SGR-BOND  14:18:77:59:5a:fe                            00:01:28
2521      bridge  CSS-SGR-BOND  14:18:77:59:70:d2                            00:00:16
2521      bridge  CSS-SGR-BOND  18:fb:7b:9a:97:13                            00:01:28
2521      bridge  CSS-SGR-BOND  18:fb:7b:99:df:97                            00:01:28
2521      bridge  CSS-SGR-BOND  18:fb:7b:99:e0:59                            00:01:28
2521      bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
2521      bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:02:05
2521      bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:00:16
2521      bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:00:16
2521      bridge  CSS-SGR-BOND  d0:94:66:3c:9b:20                            00:00:46
2521      bridge  CSS-SGR-BOND  d0:94:66:3c:a0:60                            00:07:10
2521      bridge  CSS-SGR-BOND  f4:8e:38:0e:45:d6                            00:01:28
2521      bridge  CSS-SGR-BOND  f4:8e:38:0e:47:02                            00:01:28
2521      bridge  CSS-SGR-BOND  f4:8e:38:0e:47:5e                            00:00:16
2521      bridge  CSS-SGR-BOND  f4:8e:38:0e:47:76                            00:00:16
2521      bridge  CSS-SGR-BOND  f4:8e:38:0e:47:ca                            00:01:28
2521      bridge  CSS-SGR-BOND  f4:8e:38:0e:48:2a                            00:01:28
2521      bridge  CSS-SGR-BOND  f4:8e:38:0e:48:3a                            00:01:28
2521      bridge  CSS-SGR-BOND  f4:8e:38:0e:48:66                            00:01:28
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f1:5c:a0                            00:04:46
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f1:5c:ad                            00:00:16
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f1:5c:ba                            00:12:19
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f1:5c:c7                            00:14:16
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f1:5c:d4                            00:15:25
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f1:5c:e1                            00:01:28
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f1:5c:ee                            00:01:16
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f1:5c:fb                            00:13:16
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f1:5d:2f                            00:01:28
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f1:5d:3c                            00:02:46
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f1:5d:08                            00:00:46
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f1:5d:15                            00:01:28
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f1:5d:22                            00:09:20
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f1:5d:49                            00:02:46
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f1:5d:56                            00:01:28
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f1:5d:63                            00:01:28
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f2:e4:a0                            00:01:28
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f2:e4:ad                            00:00:46
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f2:e4:ba                            00:01:16
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f2:e4:c7                            00:02:05
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f2:e4:d4                            00:08:11
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f2:e4:e1                            00:01:28
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f2:e4:fb                            00:14:16
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f2:e5:2f                            00:01:28
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f2:e5:3c                            00:09:20
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f2:e5:08                            00:00:16
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f2:e5:15                            00:06:45
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f2:e5:22                            00:05:16
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f2:e5:49                            00:05:46
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f2:e5:56                            00:02:05
2521      bridge  CSS-SGR-BOND  f8:ca:b8:f2:e5:63                            00:03:45
2521      bridge  vni-2521      00:00:5e:00:01:0f                            00:01:28
2521      bridge  vni-2521      5c:f9:dd:ef:ab:82                            00:01:28
2522      bridge  CSS-SGR-BOND  00:50:cc:7d:73:e0                            00:00:16
2522      bridge  CSS-SGR-BOND  00:50:cc:7d:73:e2                            00:01:28
2522      bridge  CSS-SGR-BOND  00:50:cc:7d:88:c8                            00:02:46
2522      bridge  CSS-SGR-BOND  00:50:cc:7d:88:ca                            00:01:28
2522      bridge  CSS-SGR-BOND  00:50:cc:7d:96:dc                            00:00:16
2522      bridge  CSS-SGR-BOND  00:50:cc:7d:96:de                            00:01:28
2522      bridge  CSS-SGR-BOND  00:50:cc:7d:98:2c                            00:01:28
2522      bridge  CSS-SGR-BOND  00:50:cc:7d:98:2e                            00:01:28
2522      bridge  CSS-SGR-BOND  ec:f4:bb:d2:fd:84                            00:00:16
2522      bridge  CSS-SGR-BOND  ec:f4:bb:d3:03:44                            00:00:46
2522      bridge  CSS-SGR-BOND  ec:f4:bb:f1:77:6c                            00:00:16
2522      bridge  CSS-SGR-BOND  ec:f4:bb:f1:78:84                            00:00:16
2522      bridge  vni-2522      00:00:5e:00:01:0f                            00:01:28
2522      bridge  vni-2522      5c:f9:dd:ef:ab:82                            00:01:28
2577      bridge  CSS-SGR-BOND  00:50:56:6c:24:cc                            00:01:28
2577      bridge  CSS-SGR-BOND  00:50:56:6e:5d:3a                            00:00:16
2577      bridge  CSS-SGR-BOND  00:50:56:6f:d1:aa                            00:00:16
2577      bridge  CSS-SGR-BOND  00:50:56:60:94:41                            00:01:16
2577      bridge  CSS-SGR-BOND  00:50:56:63:31:85                            00:03:05
2577      bridge  CSS-SGR-BOND  00:50:56:63:85:47                            00:01:28
2577      bridge  CSS-SGR-BOND  00:50:56:65:3f:bd                            00:05:16
2577      bridge  CSS-SGR-BOND  00:50:56:66:43:55                            00:02:05
2577      bridge  CSS-SGR-BOND  00:50:56:67:54:c4                            00:13:46
2577      bridge  CSS-SGR-BOND  00:50:56:67:74:e3                            00:03:45
2577      bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
2577      bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:01:28
2577      bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:00:46
2577      bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:00:46
2577      bridge  CSS-SGR-BOND  b0:83:fe:d7:59:6d                            00:03:05
2577      bridge  CSS-SGR-BOND  b0:83:fe:e1:b3:50                            00:05:16
2578      bridge  CSS-SGR-BOND  00:50:56:6a:57:8d                            00:00:16
2578      bridge  CSS-SGR-BOND  00:50:56:6b:41:dc                            00:05:46
2578      bridge  CSS-SGR-BOND  00:50:56:6d:50:5d                            00:00:16
2578      bridge  CSS-SGR-BOND  00:50:56:6e:f3:d4                            00:03:05
2578      bridge  CSS-SGR-BOND  00:50:56:6f:4b:2f                            00:01:28
2578      bridge  CSS-SGR-BOND  00:50:56:6f:ad:95                            00:01:28
2578      bridge  CSS-SGR-BOND  00:50:56:60:db:6a                            00:02:46
2578      bridge  CSS-SGR-BOND  00:50:56:61:ba:44                            00:01:28
2578      bridge  CSS-SGR-BOND  00:50:56:62:24:73                            00:01:28
2578      bridge  CSS-SGR-BOND  00:50:56:67:a0:f9                            00:01:28
2578      bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
2578      bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:46
2578      bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:00:46
2578      bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:00:46
2578      bridge  CSS-SGR-BOND  f4:52:14:33:2d:c1                            00:05:16
2579      bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
2579      bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:16
2579      bridge  CSS-SGR-BOND  74:2b:0f:0a:3e:e0                            00:00:16
2579      bridge  CSS-SGR-BOND  74:2b:0f:0a:3e:e1                            00:00:16
2579      bridge  CSS-SGR-BOND  74:2b:0f:0a:3e:e2                            00:07:10
2579      bridge  CSS-SGR-BOND  74:2b:0f:0a:3e:e3                            00:02:05
2579      bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:00:46
2579      bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:01:28
2579      bridge  vni-2579      00:00:5e:00:01:0f                            00:01:28
2579      bridge  vni-2579      5c:f9:dd:ef:ab:82                            00:01:28
2902      bridge  CSS-SGR-BOND  00:07:43:0b:74:8e                            00:00:16
2902      bridge  CSS-SGR-BOND  00:07:43:0b:75:06                            00:00:16
2902      bridge  CSS-SGR-BOND  00:07:43:0b:75:12                            00:00:46
2902      bridge  CSS-SGR-BOND  00:07:43:0b:75:c2                            00:00:16
2902      bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
2902      bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:00:16
2902      bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:01:16
2902      bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:00:16
2902      bridge  vni-2902      00:00:5e:00:01:ca                            00:01:28
2902      bridge  vni-2902      24:8a:07:9b:0d:6b                            00:00:46
2902      bridge  vni-2902      24:8a:07:a4:64:f1                            00:01:28
2903      bridge  CSS-SGR-BOND  00:07:43:0b:74:8f                            00:00:16
2903      bridge  CSS-SGR-BOND  00:07:43:0b:75:07                            00:01:28
2903      bridge  CSS-SGR-BOND  00:07:43:0b:75:13                            00:01:28
2903      bridge  CSS-SGR-BOND  00:07:43:0b:75:c3                            00:01:28
2903      bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
2903      bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:02:05
2903      bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:03:05
2903      bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:03:05
2903      bridge  vni-2903      00:00:5e:00:01:cb                            00:01:28
2903      bridge  vni-2903      24:8a:07:91:5a:25                            00:00:16
2903      bridge  vni-2903      24:8a:07:99:c3:7b                            00:00:46
2904      bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
2904      bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:01:28
2904      bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:01:16
2904      bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:01:28
2905      bridge  CSS-SGR-BOND  50:6b:4b:97:1b:01                            00:01:28
2905      bridge  CSS-SGR-BOND  50:6b:4b:97:1d:81                            00:01:16
2905      bridge  CSS-SGR-BOND  98:03:9b:f0:c7:a1                            00:02:05
2905      bridge  CSS-SGR-BOND  98:03:9b:f2:cd:a1                            00:02:46
untagged          vni-100       5c:f9:dd:ef:ab:82  10.35.0.12         self   19:07:39
untagged          vni-250       00:50:56:a8:f6:e9  10.35.0.12         self   00:27:24
untagged          vni-501       00:00:5e:00:01:0f  10.35.0.12         self   19:07:39
untagged          vni-501       00:0c:29:03:a5:09  10.35.0.12         self   19:06:27
untagged          vni-501       00:0c:29:62:29:41  10.35.0.12         self   19:07:40
untagged          vni-501       00:0c:29:66:77:63  10.35.0.12         self   19:07:26
untagged          vni-501       00:15:5d:0b:15:02  10.35.0.12         self   19:07:39
untagged          vni-501       00:15:5d:0b:15:04  10.35.0.12         self   19:06:53
untagged          vni-501       00:15:5d:0b:15:06  10.35.0.12         self   19:07:40
untagged          vni-501       00:15:5d:0b:16:06  10.35.0.12         self   19:06:11
untagged          vni-501       00:15:5d:0b:16:12  10.35.0.12         self   19:07:39
untagged          vni-501       00:15:5d:0b:16:13  10.35.0.12         self   19:07:13
untagged          vni-501       00:50:56:9e:2b:c4  10.35.0.12         self   19:07:26
untagged          vni-501       00:50:56:9e:93:64  10.35.0.12         self   19:07:39
untagged          vni-501       00:50:56:9e:ed:88  10.35.0.12         self   19:07:19
untagged          vni-501       00:50:56:90:00:c2  10.35.0.12         self   19:07:22
untagged          vni-501       00:50:56:90:1c:d6  10.35.0.12         self   19:07:39
untagged          vni-501       00:50:56:90:1e:33  10.35.0.12         self   00:14:16
untagged          vni-501       00:50:56:90:4f:dc  10.35.0.12         self   00:16:50
untagged          vni-501       00:50:56:90:06:5c  10.35.0.12         self   19:07:40
untagged          vni-501       00:50:56:90:6d:8b  10.35.0.12         self   00:26:58
untagged          vni-501       00:50:56:90:8f:f1  10.35.0.12         self   00:19:34
untagged          vni-501       00:50:56:90:09:bc  10.35.0.12         self   19:07:01
untagged          vni-501       00:50:56:90:19:1a  10.35.0.12         self   19:04:40
untagged          vni-501       00:50:56:90:19:59  10.35.0.12         self   19:07:26
untagged          vni-501       00:50:56:90:19:d1  10.35.0.12         self   19:07:39
untagged          vni-501       00:50:56:90:35:a5  10.35.0.12         self   19:01:14
untagged          vni-501       00:50:56:90:37:d1  10.35.0.12         self   19:07:22
untagged          vni-501       00:50:56:90:41:70  10.35.0.12         self   18:09:08
untagged          vni-501       00:50:56:90:56:92  10.35.0.12         self   19:07:39
untagged          vni-501       00:50:56:90:63:fd  10.35.0.12         self   19:07:32
untagged          vni-501       00:50:56:90:66:e3  10.35.0.12         self   19:05:52
untagged          vni-501       00:50:56:90:66:f4  10.35.0.12         self   19:05:24
untagged          vni-501       00:50:56:90:79:f8  10.35.0.12         self   19:02:13
untagged          vni-501       00:50:56:90:86:97  10.35.0.12         self   19:06:53
untagged          vni-501       00:50:56:90:96:ca  10.35.0.12         self   19:02:03
untagged          vni-501       00:50:56:90:b0:31  10.35.0.12         self   00:18:30
untagged          vni-501       00:50:56:90:b1:44  10.35.0.12         self   19:07:25
untagged          vni-501       00:50:56:90:b5:8c  10.35.0.12         self   19:06:33
untagged          vni-501       00:50:56:90:b6:d8  10.35.0.12         self   00:24:57
untagged          vni-501       00:50:56:90:b8:6d  10.35.0.12         self   18:59:18
untagged          vni-501       00:50:56:90:cd:25  10.35.0.12         self   19:06:14
untagged          vni-501       00:50:56:90:cf:00  10.35.0.12         self   19:07:40
untagged          vni-501       00:50:56:90:db:c8  10.35.0.12         self   19:07:40
untagged          vni-501       00:50:56:90:dc:49  10.35.0.12         self   19:04:38
untagged          vni-501       00:50:56:90:de:16  10.35.0.12         self   19:06:34
untagged          vni-501       00:50:56:90:e1:95  10.35.0.12         self   19:07:05
untagged          vni-501       00:50:56:90:e1:b9  10.35.0.12         self   19:03:44
untagged          vni-501       00:50:56:90:e3:aa  10.35.0.12         self   00:12:30
untagged          vni-501       00:50:56:90:e6:a5  10.35.0.12         self   19:05:02
untagged          vni-501       00:50:56:90:eb:79  10.35.0.12         self   19:07:26
untagged          vni-501       00:50:56:90:f3:12  10.35.0.12         self   19:03:13
untagged          vni-501       00:50:56:90:f3:fb  10.35.0.12         self   19:07:26
untagged          vni-501       00:50:56:90:f4:72  10.35.0.12         self   19:07:01
untagged          vni-501       00:50:56:91:0d:a7  10.35.0.12         self   19:06:08
untagged          vni-501       00:50:56:91:0e:98  10.35.0.12         self   19:07:40
untagged          vni-501       00:50:56:91:1a:fd  10.35.0.12         self   19:05:30
untagged          vni-501       00:50:56:91:1b:6e  10.35.0.12         self   19:01:49
untagged          vni-501       00:50:56:91:1c:b0  10.35.0.12         self   19:06:16
untagged          vni-501       00:50:56:91:1c:dd  10.35.0.12         self   19:06:17
untagged          vni-501       00:50:56:91:1f:7a  10.35.0.12         self   19:07:40
untagged          vni-501       00:50:56:91:02:70  10.35.0.12         self   19:04:23
untagged          vni-501       00:50:56:91:02:e1  10.35.0.12         self   18:54:11
untagged          vni-501       00:50:56:91:2d:6a  10.35.0.12         self   19:07:39
untagged          vni-501       00:50:56:91:2d:e0  10.35.0.12         self   19:05:15
untagged          vni-501       00:50:56:91:2f:a2  10.35.0.12         self   19:05:50
untagged          vni-501       00:50:56:91:03:de  10.35.0.12         self   19:06:51
untagged          vni-501       00:50:56:91:3d:2e  10.35.0.12         self   19:02:32
untagged          vni-501       00:50:56:91:3e:16  10.35.0.12         self   19:04:02
untagged          vni-501       00:50:56:91:04:60  10.35.0.12         self   19:07:39
untagged          vni-501       00:50:56:91:4f:88  10.35.0.12         self   19:07:24
untagged          vni-501       00:50:56:91:05:b4  10.35.0.12         self   19:07:39
untagged          vni-501       00:50:56:91:5a:fa  10.35.0.12         self   19:07:20
untagged          vni-501       00:50:56:91:5c:06  10.35.0.12         self   19:04:49
untagged          vni-501       00:50:56:91:06:44  10.35.0.12         self   13:12:16
untagged          vni-501       00:50:56:91:6a:75  10.35.0.12         self   19:07:40
untagged          vni-501       00:50:56:91:6e:c5  10.35.0.12         self   19:05:54
untagged          vni-501       00:50:56:91:7c:60  10.35.0.12         self   19:05:03
untagged          vni-501       00:50:56:91:7c:e0  10.35.0.12         self   19:03:54
untagged          vni-501       00:50:56:91:7d:0d  10.35.0.12         self   19:07:10
untagged          vni-501       00:50:56:91:7d:7f  10.35.0.12         self   19:06:52
untagged          vni-501       00:50:56:91:7d:d6  10.35.0.12         self   19:07:39
untagged          vni-501       00:50:56:91:13:21  10.35.0.12         self   19:03:16
untagged          vni-501       00:50:56:91:15:0b  10.35.0.12         self   19:01:58
untagged          vni-501       00:50:56:91:17:ec  10.35.0.12         self   19:06:15
untagged          vni-501       00:50:56:91:18:10  10.35.0.12         self   19:06:05
untagged          vni-501       00:50:56:91:18:95  10.35.0.12         self   19:07:40
untagged          vni-501       00:50:56:91:22:3d  10.35.0.12         self   19:07:18
untagged          vni-501       00:50:56:91:25:86  10.35.0.12         self   19:06:26
untagged          vni-501       00:50:56:91:25:ee  10.35.0.12         self   19:07:40
untagged          vni-501       00:50:56:91:26:ab  10.35.0.12         self   00:07:10
untagged          vni-501       00:50:56:91:34:f9  10.35.0.12         self   18:58:04
untagged          vni-501       00:50:56:91:37:9b  10.35.0.12         self   19:05:53
untagged          vni-501       00:50:56:91:40:52  10.35.0.12         self   19:04:38
untagged          vni-501       00:50:56:91:42:7c  10.35.0.12         self   19:07:40
untagged          vni-501       00:50:56:91:46:f3  10.35.0.12         self   19:05:47
untagged          vni-501       00:50:56:91:51:4e  10.35.0.12         self   19:07:14
untagged          vni-501       00:50:56:91:52:48  10.35.0.12         self   19:07:40
untagged          vni-501       00:50:56:91:59:4e  10.35.0.12         self   19:06:09
untagged          vni-501       00:50:56:91:59:ef  10.35.0.12         self   19:03:44
untagged          vni-501       00:50:56:91:61:63  10.35.0.12         self   19:05:30
untagged          vni-501       00:50:56:91:61:64  10.35.0.12         self   19:07:39
untagged          vni-501       00:50:56:91:62:61  10.35.0.12         self   19:05:59
untagged          vni-501       00:50:56:91:63:97  10.35.0.12         self   19:07:12
untagged          vni-501       00:50:56:91:67:7c  10.35.0.12         self   19:07:15
untagged          vni-501       00:50:56:91:68:c3  10.35.0.12         self   19:07:13
untagged          vni-501       00:50:56:91:69:5e  10.35.0.12         self   19:01:06
untagged          vni-501       00:50:56:91:70:53  10.35.0.12         self   19:06:51
untagged          vni-501       00:50:56:91:70:be  10.35.0.12         self   19:07:40
untagged          vni-501       00:50:56:91:74:83  10.35.0.12         self   19:07:20
untagged          vni-501       00:50:56:91:75:c0  10.35.0.12         self   19:07:39
untagged          vni-501       00:50:56:91:76:80  10.35.0.12         self   19:07:40
untagged          vni-501       00:50:56:91:79:23  10.35.0.12         self   19:06:50
untagged          vni-501       00:50:56:93:1b:e9  10.35.0.12         self   19:06:28
untagged          vni-501       00:50:56:93:24:43  10.35.0.12         self   19:07:40
untagged          vni-501       00:50:56:bc:7f:07  10.35.0.12         self   19:07:39
untagged          vni-501       00:50:56:bc:12:6a  10.35.0.12         self   19:03:15
untagged          vni-501       00:50:56:bc:47:cc  10.35.0.12         self   19:07:40
untagged          vni-501       00:50:56:bc:60:6d  10.35.0.12         self   19:04:54
untagged          vni-501       00:50:56:bc:66:57  10.35.0.12         self   19:00:11
untagged          vni-501       00:50:56:bc:77:1c  10.35.0.12         self   19:07:40
untagged          vni-501       00:50:cc:7f:0b:d4  10.35.0.12         self   19:07:03
untagged          vni-501       00:50:cc:7f:0b:d6  10.35.0.12         self   19:06:04
untagged          vni-501       00:50:cc:7f:0c:1c  10.35.0.12         self   00:15:25
untagged          vni-501       00:50:cc:7f:0c:1e  10.35.0.12         self   19:06:01
untagged          vni-501       5c:f9:dd:ef:ab:82  10.35.0.12         self   19:07:40
untagged          vni-501       24:8a:07:88:d9:ba  10.35.0.12         self   19:07:40
untagged          vni-501       24:8a:07:ad:6d:3a  10.35.0.12         self   19:06:05
untagged          vni-501       50:9a:4c:76:6b:89  10.35.0.12         self   18:08:43
untagged          vni-501       b0:83:fe:d7:4e:ca  10.35.0.12         self   19:07:40
untagged          vni-501       ec:f4:bb:c1:8f:04  10.35.0.12         self   19:02:27
untagged          vni-501       ec:f4:bb:f1:86:34  10.35.0.12         self   19:06:01
untagged          vni-501       ec:f4:bb:f1:95:f4  10.35.0.12         self   19:05:27
untagged          vni-501       ec:f4:bb:f1:a7:3c  10.35.0.12         self   19:07:20
untagged          vni-504       00:00:5e:00:01:0f  10.35.0.12         self   19:07:40
untagged          vni-504       00:15:5d:0b:16:10  10.35.0.12         self   19:07:40
untagged          vni-504       00:50:56:91:0b:fd  10.35.0.12         self   19:01:01
untagged          vni-504       00:50:56:91:6a:f5  10.35.0.12         self   19:01:12
untagged          vni-504       00:50:56:91:7e:d3  10.35.0.12         self   19:07:09
untagged          vni-504       00:50:56:91:08:c3  10.35.0.12         self   19:02:40
untagged          vni-504       00:50:56:91:19:57  10.35.0.12         self   19:06:00
untagged          vni-504       00:50:56:91:26:7f  10.35.0.12         self   19:05:46
untagged          vni-504       00:50:56:91:30:bd  10.35.0.12         self   19:02:57
untagged          vni-504       00:50:56:91:39:8b  10.35.0.12         self   19:05:49
untagged          vni-504       00:50:56:91:50:d0  10.35.0.12         self   19:03:30
untagged          vni-504       00:50:56:91:64:e3  10.35.0.12         self   03:36:15
untagged          vni-504       00:50:56:91:71:68  10.35.0.12         self   19:07:26
untagged          vni-504       00:50:56:93:1c:14  10.35.0.12         self   19:07:40
untagged          vni-504       00:50:56:93:58:ed  10.35.0.12         self   19:06:17
untagged          vni-504       00:50:56:a8:3f:dc  10.35.0.12         self   18:59:24
untagged          vni-504       00:50:56:a8:7f:01  10.35.0.12         self   17:30:45
untagged          vni-504       00:50:56:a8:ea:ef  10.35.0.12         self   19:07:39
untagged          vni-504       5c:f9:dd:ef:ab:82  10.35.0.12         self   00:16:06
untagged          vni-504       24:8a:07:88:d9:ba  10.35.0.12         self   19:07:40
untagged          vni-504       24:8a:07:ad:6d:3a  10.35.0.12         self   19:03:21
untagged          vni-504       b0:83:fe:d7:4e:ca  10.35.0.12         self   19:06:41
untagged          vni-505       00:00:5e:00:01:0f  10.35.0.12         self   19:07:40
untagged          vni-505       00:15:5d:0b:15:12  10.35.0.12         self   19:07:40
untagged          vni-505       00:50:56:90:d7:d2  10.35.0.12         self   18:55:41
untagged          vni-505       00:50:56:91:4d:01  10.35.0.12         self   19:07:40
untagged          vni-505       00:50:56:91:11:9f  10.35.0.12         self   19:06:38
untagged          vni-505       00:50:56:91:25:43  10.35.0.12         self   19:06:40
untagged          vni-505       00:50:56:91:32:3d  10.35.0.12         self   19:06:28
untagged          vni-505       00:50:56:91:44:c5  10.35.0.12         self   19:07:40
untagged          vni-505       00:50:56:91:45:c9  10.35.0.12         self   19:02:11
untagged          vni-505       00:50:56:91:63:0e  10.35.0.12         self   19:07:04
untagged          vni-505       00:50:56:91:63:49  10.35.0.12         self   19:07:26
untagged          vni-505       00:50:56:a8:f0:a3  10.35.0.12         self   19:07:40
untagged          vni-505       b0:83:fe:d7:4e:ca  10.35.0.12         self   19:07:23
untagged          vni-506       00:00:5e:00:01:0f  10.35.0.12         self   19:07:40
untagged          vni-506       00:15:5d:0b:16:0e  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:91:6b:c7  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:91:7d:b0  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:91:48:50  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:93:1e:be  10.35.0.12         self   19:07:39
untagged          vni-506       00:50:56:93:4d:a9  10.35.0.12         self   19:07:39
untagged          vni-506       00:50:56:93:4f:fd  10.35.0.12         self   19:07:39
untagged          vni-506       00:50:56:93:12:cc  10.35.0.12         self   17:45:06
untagged          vni-506       00:50:56:93:35:7f  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:a8:d8:ba  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:bc:0a:45  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:bc:0b:55  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:bc:0c:51  10.35.0.12         self   19:06:02
untagged          vni-506       00:50:56:bc:0d:50  10.35.0.12         self   19:03:22
untagged          vni-506       00:50:56:bc:1b:cd  10.35.0.12         self   19:02:11
untagged          vni-506       00:50:56:bc:1c:88  10.35.0.12         self   19:07:39
untagged          vni-506       00:50:56:bc:1d:bd  10.35.0.12         self   19:07:39
untagged          vni-506       00:50:56:bc:1f:73  10.35.0.12         self   19:07:39
untagged          vni-506       00:50:56:bc:2f:fa  10.35.0.12         self   19:07:39
untagged          vni-506       00:50:56:bc:3a:ae  10.35.0.12         self   19:07:39
untagged          vni-506       00:50:56:bc:3a:da  10.35.0.12         self   19:07:39
untagged          vni-506       00:50:56:bc:04:b3  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:bc:4b:15  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:bc:05:82  10.35.0.12         self   19:07:39
untagged          vni-506       00:50:56:bc:05:90  10.35.0.12         self   19:07:16
untagged          vni-506       00:50:56:bc:5b:07  10.35.0.12         self   19:07:39
untagged          vni-506       00:50:56:bc:5c:7a  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:bc:5c:f9  10.35.0.12         self   19:07:39
untagged          vni-506       00:50:56:bc:5d:d9  10.35.0.12         self   19:07:39
untagged          vni-506       00:50:56:bc:6c:27  10.35.0.12         self   19:07:18
untagged          vni-506       00:50:56:bc:6f:03  10.35.0.12         self   19:05:24
untagged          vni-506       00:50:56:bc:07:87  10.35.0.12         self   19:06:58
untagged          vni-506       00:50:56:bc:7a:ce  10.35.0.12         self   19:04:03
untagged          vni-506       00:50:56:bc:7f:d7  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:bc:08:4f  10.35.0.12         self   19:07:33
untagged          vni-506       00:50:56:bc:09:00  10.35.0.12         self   19:07:04
untagged          vni-506       00:50:56:bc:13:04  10.35.0.12         self   19:03:45
untagged          vni-506       00:50:56:bc:13:67  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:bc:14:4f  10.35.0.12         self   19:07:39
untagged          vni-506       00:50:56:bc:15:6c  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:bc:19:7b  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:bc:20:16  10.35.0.12         self   19:07:10
untagged          vni-506       00:50:56:bc:26:14  10.35.0.12         self   19:04:45
untagged          vni-506       00:50:56:bc:27:67  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:bc:32:9e  10.35.0.12         self   19:07:38
untagged          vni-506       00:50:56:bc:36:da  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:bc:37:20  10.35.0.12         self   19:05:52
untagged          vni-506       00:50:56:bc:42:a8  10.35.0.12         self   19:07:11
untagged          vni-506       00:50:56:bc:45:14  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:bc:46:8f  10.35.0.12         self   19:03:03
untagged          vni-506       00:50:56:bc:47:31  10.35.0.12         self   19:03:38
untagged          vni-506       00:50:56:bc:47:da  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:bc:48:a5  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:bc:48:f2  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:bc:49:11  10.35.0.12         self   19:04:59
untagged          vni-506       00:50:56:bc:56:09  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:bc:58:5a  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:bc:58:6c  10.35.0.12         self   19:07:39
untagged          vni-506       00:50:56:bc:63:64  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:bc:64:44  10.35.0.12         self   19:03:07
untagged          vni-506       00:50:56:bc:65:60  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:bc:66:38  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:bc:72:9c  10.35.0.12         self   19:07:40
untagged          vni-506       00:50:56:bc:73:09  10.35.0.12         self   19:04:07
untagged          vni-506       00:50:56:bc:77:25  10.35.0.12         self   19:07:31
untagged          vni-506       00:50:56:bc:79:4c  10.35.0.12         self   19:07:40
untagged          vni-506       5c:f9:dd:ef:ab:82  10.35.0.12         self   00:22:05
untagged          vni-506       24:8a:07:88:d9:ba  10.35.0.12         self   19:07:40
untagged          vni-506       24:8a:07:ad:6d:3a  10.35.0.12         self   19:06:35
untagged          vni-506       b0:83:fe:d7:4e:ca  10.35.0.12         self   19:05:38
untagged          vni-507       00:00:5e:00:01:0f  10.35.0.12         self   19:07:39
untagged          vni-507       00:15:5d:0b:16:11  10.35.0.12         self   19:07:40
untagged          vni-507       00:50:56:90:3a:46  10.35.0.12         self   18:59:29
untagged          vni-507       00:50:56:90:7c:12  10.35.0.12         self   19:04:18
untagged          vni-507       00:50:56:91:1a:3c  10.35.0.12         self   19:06:44
untagged          vni-507       00:50:56:91:02:a3  10.35.0.12         self   18:59:19
untagged          vni-507       00:50:56:91:2c:29  10.35.0.12         self   19:06:55
untagged          vni-507       00:50:56:91:3f:97  10.35.0.12         self   19:04:09
untagged          vni-507       00:50:56:91:04:42  10.35.0.12         self   19:06:36
untagged          vni-507       00:50:56:91:5a:ec  10.35.0.12         self   19:06:55
untagged          vni-507       00:50:56:91:5e:d8  10.35.0.12         self   19:06:30
untagged          vni-507       00:50:56:91:5f:cf  10.35.0.12         self   19:03:03
untagged          vni-507       00:50:56:91:7e:1e  10.35.0.12         self   18:55:46
untagged          vni-507       00:50:56:91:7e:05  10.35.0.12         self   19:03:39
untagged          vni-507       00:50:56:91:11:78  10.35.0.12         self   19:05:42
untagged          vni-507       00:50:56:91:28:70  10.35.0.12         self   19:07:23
untagged          vni-507       00:50:56:91:32:2a  10.35.0.12         self   19:07:40
untagged          vni-507       00:50:56:91:42:eb  10.35.0.12         self   19:06:07
untagged          vni-507       00:50:56:91:49:cc  10.35.0.12         self   19:07:39
untagged          vni-507       00:50:56:91:51:4c  10.35.0.12         self   19:05:20
untagged          vni-507       00:50:56:91:58:f8  10.35.0.12         self   19:05:12
untagged          vni-507       00:50:56:91:60:87  10.35.0.12         self   19:06:38
untagged          vni-507       00:50:56:91:77:92  10.35.0.12         self   19:07:23
untagged          vni-507       00:50:56:a8:f9:39  10.35.0.12         self   19:07:39
untagged          vni-507       5c:f9:dd:ef:ab:82  10.35.0.12         self   01:06:05
untagged          vni-507       24:8a:07:88:d9:ba  10.35.0.12         self   19:07:39
untagged          vni-507       24:8a:07:ad:6d:3a  10.35.0.12         self   19:03:49
untagged          vni-508       00:00:5e:00:01:0f  10.35.0.12         self   19:07:39
untagged          vni-508       00:15:5d:0b:16:0c  10.35.0.12         self   19:07:39
untagged          vni-508       00:50:56:91:1f:53  10.35.0.12         self   19:05:55
untagged          vni-508       00:50:56:91:4a:53  10.35.0.12         self   19:06:18
untagged          vni-508       00:50:56:91:5c:11  10.35.0.12         self   19:07:40
untagged          vni-508       00:50:56:91:6d:ef  10.35.0.12         self   19:07:39
untagged          vni-508       00:50:56:91:7c:01  10.35.0.12         self   19:07:04
untagged          vni-508       00:50:56:91:17:83  10.35.0.12         self   19:03:45
untagged          vni-508       00:50:56:91:25:80  10.35.0.12         self   19:07:40
untagged          vni-508       00:50:56:91:45:bd  10.35.0.12         self   19:07:18
untagged          vni-508       00:50:56:91:58:c5  10.35.0.12         self   19:03:50
untagged          vni-508       00:50:56:91:76:05  10.35.0.12         self   19:07:40
untagged          vni-508       00:50:56:91:78:0d  10.35.0.12         self   19:06:59
untagged          vni-508       00:50:56:91:79:0b  10.35.0.12         self   19:07:39
untagged          vni-508       00:50:56:a8:8b:14  10.35.0.12         self   19:07:40
untagged          vni-508       24:8a:07:88:d9:ba  10.35.0.12         self   19:07:39
untagged          vni-508       24:8a:07:ad:6d:3a  10.35.0.12         self   19:03:38
untagged          vni-508       b0:83:fe:d7:4e:ca  10.35.0.12         self   19:07:17
untagged          vni-511       00:50:56:91:28:3b  10.35.0.12         self   19:06:26
untagged          vni-511       00:50:56:a8:d3:cb  10.35.0.12         self   01:51:58
untagged          vni-512       00:00:5e:00:01:96  10.35.0.12         self   19:07:39
untagged          vni-512       5c:f9:dd:ef:ab:82  10.35.0.12         self   19:07:39
untagged          vni-513       00:00:5e:00:01:96  10.35.0.12         self   19:07:40
untagged          vni-513       5c:f9:dd:ef:ab:82  10.35.0.12         self   19:07:40
untagged          vni-514       00:00:5e:00:01:0f  10.35.0.12         self   19:07:39
untagged          vni-514       00:50:56:9e:00:f3  10.35.0.12         self   04:35:35
untagged          vni-514       00:50:56:9e:0a:32  10.35.0.12         self   02:38:45
untagged          vni-514       00:50:56:9e:0d:45  10.35.0.12         self   04:35:50
untagged          vni-514       00:50:56:9e:0f:58  10.35.0.12         self   03:17:26
untagged          vni-514       00:50:56:9e:01:7d  10.35.0.12         self   13:18:54
untagged          vni-514       00:50:56:9e:01:d3  10.35.0.12         self   01:14:10
untagged          vni-514       00:50:56:9e:1a:15  10.35.0.12         self   01:38:24
untagged          vni-514       00:50:56:9e:1b:f8  10.35.0.12         self   03:38:21
untagged          vni-514       00:50:56:9e:1d:75  10.35.0.12         self   04:38:05
untagged          vni-514       00:50:56:9e:1d:f0  10.35.0.12         self   04:37:16
untagged          vni-514       00:50:56:9e:1f:ef  10.35.0.12         self   02:36:32
untagged          vni-514       00:50:56:9e:2e:17  10.35.0.12         self   03:38:18
untagged          vni-514       00:50:56:9e:03:93  10.35.0.12         self   19:06:19
untagged          vni-514       00:50:56:9e:03:b0  10.35.0.12         self   03:16:22
untagged          vni-514       00:50:56:9e:3a:12  10.35.0.12         self   02:16:23
untagged          vni-514       00:50:56:9e:4b:bb  10.35.0.12         self   04:37:36
untagged          vni-514       00:50:56:9e:4c:70  10.35.0.12         self   02:17:15
untagged          vni-514       00:50:56:9e:4d:d3  10.35.0.12         self   11:22:28
untagged          vni-514       00:50:56:9e:4d:d9  10.35.0.12         self   03:15:27
untagged          vni-514       00:50:56:9e:4e:6d  10.35.0.12         self   04:13:09
untagged          vni-514       00:50:56:9e:4e:ac  10.35.0.12         self   11:44:06
untagged          vni-514       00:50:56:9e:4f:5a  10.35.0.12         self   03:17:27
untagged          vni-514       00:50:56:9e:05:b1  10.35.0.12         self   01:37:35
untagged          vni-514       00:50:56:9e:5a:a5  10.35.0.12         self   05:15:25
untagged          vni-514       00:50:56:9e:5e:7b  10.35.0.12         self   03:17:27
untagged          vni-514       00:50:56:9e:5f:61  10.35.0.12         self   10:06:26
untagged          vni-514       00:50:56:9e:5f:77  10.35.0.12         self   05:14:21
untagged          vni-514       00:50:56:9e:5f:b6  10.35.0.12         self   03:16:27
untagged          vni-514       00:50:56:9e:6a:1b  10.35.0.12         self   04:35:41
untagged          vni-514       00:50:56:9e:6a:58  10.35.0.12         self   05:17:24
untagged          vni-514       00:50:56:9e:6b:32  10.35.0.12         self   02:38:11
untagged          vni-514       00:50:56:9e:6f:15  10.35.0.12         self   02:38:21
untagged          vni-514       00:50:56:9e:6f:35  10.35.0.12         self   04:35:41
untagged          vni-514       00:50:56:9e:07:03  10.35.0.12         self   02:36:36
untagged          vni-514       00:50:56:9e:07:e7  10.35.0.12         self   05:57:31
untagged          vni-514       00:50:56:9e:7b:94  10.35.0.12         self   05:40:10
untagged          vni-514       00:50:56:9e:8a:e9  10.35.0.12         self   01:38:27
untagged          vni-514       00:50:56:9e:8c:a5  10.35.0.12         self   03:30:28
untagged          vni-514       00:50:56:9e:8d:86  10.35.0.12         self   19:04:11
untagged          vni-514       00:50:56:9e:09:50  10.35.0.12         self   02:15:21
untagged          vni-514       00:50:56:9e:09:68  10.35.0.12         self   04:11:39
untagged          vni-514       00:50:56:9e:9b:db  10.35.0.12         self   02:36:31
untagged          vni-514       00:50:56:9e:9b:ed  10.35.0.12         self   04:38:17
untagged          vni-514       00:50:56:9e:9c:3a  10.35.0.12         self   05:17:23
untagged          vni-514       00:50:56:9e:9d:e4  10.35.0.12         self   03:15:28
untagged          vni-514       00:50:56:9e:9e:38  10.35.0.12         self   05:15:28
untagged          vni-514       00:50:56:9e:9f:68  10.35.0.12         self   03:38:20
untagged          vni-514       00:50:56:9e:9f:e6  10.35.0.12         self   05:14:21
untagged          vni-514       00:50:56:9e:11:64  10.35.0.12         self   04:37:13
untagged          vni-514       00:50:56:9e:12:2a  10.35.0.12         self   04:38:14
untagged          vni-514       00:50:56:9e:13:82  10.35.0.12         self   03:16:27
untagged          vni-514       00:50:56:9e:17:f5  10.35.0.12         self   04:17:25
untagged          vni-514       00:50:56:9e:20:78  10.35.0.12         self   12:25:34
untagged          vni-514       00:50:56:9e:22:91  10.35.0.12         self   04:17:23
untagged          vni-514       00:50:56:9e:23:80  10.35.0.12         self   04:36:23
untagged          vni-514       00:50:56:9e:28:73  10.35.0.12         self   04:37:25
untagged          vni-514       00:50:56:9e:33:19  10.35.0.12         self   19:03:02
untagged          vni-514       00:50:56:9e:33:cb  10.35.0.12         self   02:17:19
untagged          vni-514       00:50:56:9e:34:cf  10.35.0.12         self   05:15:28
untagged          vni-514       00:50:56:9e:39:d8  10.35.0.12         self   18:58:58
untagged          vni-514       00:50:56:9e:39:e8  10.35.0.12         self   05:14:20
untagged          vni-514       00:50:56:9e:40:b7  10.35.0.12         self   05:13:24
untagged          vni-514       00:50:56:9e:42:ea  10.35.0.12         self   03:38:12
untagged          vni-514       00:50:56:9e:43:0e  10.35.0.12         self   02:17:21
untagged          vni-514       00:50:56:9e:43:ca  10.35.0.12         self   03:38:20
untagged          vni-514       00:50:56:9e:46:8e  10.35.0.12         self   04:35:44
untagged          vni-514       00:50:56:9e:47:a6  10.35.0.12         self   05:13:29
untagged          vni-514       00:50:56:9e:48:6b  10.35.0.12         self   04:17:25
untagged          vni-514       00:50:56:9e:49:57  10.35.0.12         self   04:35:17
untagged          vni-514       00:50:56:9e:54:4e  10.35.0.12         self   19:06:46
untagged          vni-514       00:50:56:9e:56:f5  10.35.0.12         self   08:53:55
untagged          vni-514       00:50:56:9e:61:ba  10.35.0.12         self   02:55:27
untagged          vni-514       00:50:56:9e:63:e7  10.35.0.12         self   19:02:42
untagged          vni-514       00:50:56:9e:64:50  10.35.0.12         self   05:15:28
untagged          vni-514       00:50:56:9e:66:76  10.35.0.12         self   03:15:30
untagged          vni-514       00:50:56:9e:68:95  10.35.0.12         self   02:15:14
untagged          vni-514       00:50:56:9e:70:ea  10.35.0.12         self   02:46:23
untagged          vni-514       00:50:56:9e:75:83  10.35.0.12         self   01:12:57
untagged          vni-514       00:50:56:9e:77:05  10.35.0.12         self   01:38:37
untagged          vni-514       00:50:56:9e:77:09  10.35.0.12         self   02:07:32
untagged          vni-514       00:50:56:9e:80:cb  10.35.0.12         self   01:39:14
untagged          vni-514       00:50:56:9e:84:8a  10.35.0.12         self   04:35:28
untagged          vni-514       00:50:56:9e:85:51  10.35.0.12         self   04:17:29
untagged          vni-514       00:50:56:9e:86:f1  10.35.0.12         self   02:15:25
untagged          vni-514       00:50:56:9e:87:ce  10.35.0.12         self   04:37:16
untagged          vni-514       00:50:56:9e:90:65  10.35.0.12         self   03:38:17
untagged          vni-514       00:50:56:9e:91:20  10.35.0.12         self   01:37:31
untagged          vni-514       00:50:56:9e:93:1a  10.35.0.12         self   02:16:23
untagged          vni-514       00:50:56:9e:93:76  10.35.0.12         self   02:39:16
untagged          vni-514       00:50:56:9e:98:2e  10.35.0.12         self   19:01:43
untagged          vni-514       00:50:56:9e:99:97  10.35.0.12         self   01:36:53
untagged          vni-514       00:50:56:9e:a0:33  10.35.0.12         self   03:15:29
untagged          vni-514       00:50:56:9e:a3:30  10.35.0.12         self   04:38:15
untagged          vni-514       00:50:56:9e:a4:9b  10.35.0.12         self   18:59:16
untagged          vni-514       00:50:56:9e:a4:a3  10.35.0.12         self   18:59:49
untagged          vni-514       00:50:56:9e:a5:2d  10.35.0.12         self   02:16:15
untagged          vni-514       00:50:56:9e:a7:9a  10.35.0.12         self   04:38:04
untagged          vni-514       00:50:56:9e:a8:5c  10.35.0.12         self   01:38:13
untagged          vni-514       00:50:56:9e:ae:52  10.35.0.12         self   05:15:27
untagged          vni-514       00:50:56:9e:af:28  10.35.0.12         self   05:16:22
untagged          vni-514       00:50:56:9e:b0:c9  10.35.0.12         self   01:01:24
untagged          vni-514       00:50:56:9e:b1:06  10.35.0.12         self   11:14:56
untagged          vni-514       00:50:56:9e:b3:12  10.35.0.12         self   02:38:47
untagged          vni-514       00:50:56:9e:b4:5c  10.35.0.12         self   05:15:29
untagged          vni-514       00:50:56:9e:b5:c7  10.35.0.12         self   04:36:24
untagged          vni-514       00:50:56:9e:b7:f3  10.35.0.12         self   05:15:16
untagged          vni-514       00:50:56:9e:b8:8e  10.35.0.12         self   02:15:14
untagged          vni-514       00:50:56:9e:ba:94  10.35.0.12         self   02:15:14
untagged          vni-514       00:50:56:9e:ba:fe  10.35.0.12         self   05:13:31
untagged          vni-514       00:50:56:9e:bb:81  10.35.0.12         self   02:14:52
untagged          vni-514       00:50:56:9e:bd:8b  10.35.0.12         self   04:36:19
untagged          vni-514       00:50:56:9e:c4:1f  10.35.0.12         self   01:37:41
untagged          vni-514       00:50:56:9e:c6:0f  10.35.0.12         self   03:17:20
untagged          vni-514       00:50:56:9e:c7:c9  10.35.0.12         self   05:13:29
untagged          vni-514       00:50:56:9e:cd:f4  10.35.0.12         self   05:17:21
untagged          vni-514       00:50:56:9e:cf:fb  10.35.0.12         self   02:16:23
untagged          vni-514       00:50:56:9e:d0:ae  10.35.0.12         self   05:39:06
untagged          vni-514       00:50:56:9e:d4:c7  10.35.0.12         self   05:17:17
untagged          vni-514       00:50:56:9e:d6:de  10.35.0.12         self   03:16:25
untagged          vni-514       00:50:56:9e:d9:25  10.35.0.12         self   02:38:18
untagged          vni-514       00:50:56:9e:d9:ef  10.35.0.12         self   02:17:19
untagged          vni-514       00:50:56:9e:da:76  10.35.0.12         self   02:36:39
untagged          vni-514       00:50:56:9e:da:fd  10.35.0.12         self   02:21:15
untagged          vni-514       00:50:56:9e:dc:e6  10.35.0.12         self   04:38:14
untagged          vni-514       00:50:56:9e:de:06  10.35.0.12         self   01:12:52
untagged          vni-514       00:50:56:9e:df:a6  10.35.0.12         self   02:15:22
untagged          vni-514       00:50:56:9e:e3:6e  10.35.0.12         self   02:17:11
untagged          vni-514       00:50:56:9e:e6:06  10.35.0.12         self   05:16:29
untagged          vni-514       00:50:56:9e:e7:b7  10.35.0.12         self   19:02:43
untagged          vni-514       00:50:56:9e:e8:7d  10.35.0.12         self   01:37:30
untagged          vni-514       00:50:56:9e:e9:6d  10.35.0.12         self   05:16:28
untagged          vni-514       00:50:56:9e:ea:71  10.35.0.12         self   05:16:28
untagged          vni-514       00:50:56:9e:eb:6f  10.35.0.12         self   03:16:23
untagged          vni-514       00:50:56:9e:eb:8a  10.35.0.12         self   01:38:12
untagged          vni-514       00:50:56:9e:ee:c4  10.35.0.12         self   02:38:17
untagged          vni-514       00:50:56:9e:ef:74  10.35.0.12         self   04:38:13
untagged          vni-514       00:50:56:9e:ef:a2  10.35.0.12         self   03:16:22
untagged          vni-514       00:50:56:9e:f6:cc  10.35.0.12         self   19:07:40
untagged          vni-514       00:50:56:9e:f8:f9  10.35.0.12         self   02:36:39
untagged          vni-514       00:50:56:9e:fa:a6  10.35.0.12         self   13:10:32
untagged          vni-514       00:50:56:9e:fb:35  10.35.0.12         self   02:15:14
untagged          vni-514       00:50:56:9e:fd:00  10.35.0.12         self   03:15:29
untagged          vni-514       00:50:56:90:a9:75  10.35.0.12         self   19:07:01
untagged          vni-514       5c:f9:dd:ef:ab:82  10.35.0.12         self   19:07:40
untagged          vni-517       00:00:5e:00:01:0f  10.35.0.12         self   19:07:39
untagged          vni-517       5c:f9:dd:ef:ab:82  10.35.0.12         self   19:07:40
untagged          vni-519       00:00:5e:00:01:0f  10.35.0.12         self   19:07:40
untagged          vni-519       00:15:5d:0b:15:13  10.35.0.12         self   19:07:39
untagged          vni-519       00:15:5d:6d:19:0a  10.35.0.12         self   19:06:08
untagged          vni-519       00:15:5d:6d:19:05  10.35.0.12         self   19:06:44
untagged          vni-519       00:15:5d:6d:19:06  10.35.0.12         self   19:07:39
untagged          vni-519       00:15:5d:6d:19:07  10.35.0.12         self   19:07:13
untagged          vni-519       00:15:5d:6d:19:10  10.35.0.12         self   19:06:08
untagged          vni-519       00:15:5d:6d:19:11  10.35.0.12         self   19:04:06
untagged          vni-519       00:15:5d:6d:19:12  10.35.0.12         self   19:07:39
untagged          vni-519       00:15:5d:6d:19:13  10.35.0.12         self   19:02:14
untagged          vni-519       00:50:56:a8:3e:15  10.35.0.12         self   19:07:40
untagged          vni-519       24:8a:07:55:4b:b4  10.35.0.12         self   19:05:44
untagged          vni-519       24:8a:07:91:5a:4c  10.35.0.12         self   18:07:10
untagged          vni-519       b0:83:fe:d7:4e:ca  10.35.0.12         self   19:07:40
untagged          vni-520       00:00:5e:00:01:0f  10.35.0.12         self   19:07:39
untagged          vni-521       00:0a:f7:e3:16:06  10.35.0.12         self   19:07:24
untagged          vni-521       00:15:5d:71:0f:00  10.35.0.12         self   19:03:46
untagged          vni-521       00:15:5d:71:0f:0e  10.35.0.12         self   19:07:23
untagged          vni-521       00:15:5d:71:0f:19  10.35.0.12         self   19:01:44
untagged          vni-521       00:15:5d:71:0f:21  10.35.0.12         self   19:07:20
untagged          vni-521       00:15:5d:71:0f:22  10.35.0.12         self   19:07:39
untagged          vni-521       00:15:5d:71:0f:25  10.35.0.12         self   19:01:26
untagged          vni-521       00:15:5d:71:10:14  10.35.0.12         self   19:04:54
untagged          vni-521       00:15:5d:71:10:15  10.35.0.12         self   19:07:33
untagged          vni-521       00:15:5d:71:12:0c  10.35.0.12         self   19:00:10
untagged          vni-521       00:15:5d:71:12:1b  10.35.0.12         self   19:01:10
untagged          vni-521       00:15:5d:71:12:1c  10.35.0.12         self   19:02:24
untagged          vni-521       00:15:5d:71:12:1d  10.35.0.12         self   19:01:12
untagged          vni-521       00:15:5d:a8:22:08  10.35.0.12         self   19:07:40
untagged          vni-521       00:15:5d:c8:f4:00  10.35.0.12         self   19:01:28
untagged          vni-521       00:15:5d:c8:f4:01  10.35.0.12         self   19:02:25
untagged          vni-521       00:15:5d:c8:f4:02  10.35.0.12         self   19:02:27
untagged          vni-521       00:15:5d:c8:f4:03  10.35.0.12         self   19:07:40
untagged          vni-521       00:15:5d:c8:f4:04  10.35.0.12         self   19:01:46
untagged          vni-521       00:15:5d:c8:f4:05  10.35.0.12         self   19:00:14
untagged          vni-521       00:15:5d:c8:f4:06  10.35.0.12         self   19:03:29
untagged          vni-521       00:15:5d:c8:f4:07  10.35.0.12         self   19:07:09
untagged          vni-521       00:15:5d:c8:f5:00  10.35.0.12         self   18:58:01
untagged          vni-521       00:15:5d:c8:f5:0a  10.35.0.12         self   19:00:22
untagged          vni-521       00:15:5d:c8:f5:0b  10.35.0.12         self   19:01:14
untagged          vni-521       00:15:5d:c8:f5:0c  10.35.0.12         self   19:06:39
untagged          vni-521       00:15:5d:c8:f5:0d  10.35.0.12         self   18:59:36
untagged          vni-521       00:15:5d:c8:f5:0e  10.35.0.12         self   18:57:03
untagged          vni-521       00:15:5d:c8:f5:0f  10.35.0.12         self   19:06:43
untagged          vni-521       00:15:5d:c8:f5:01  10.35.0.12         self   18:59:46
untagged          vni-521       00:15:5d:c8:f5:1a  10.35.0.12         self   18:59:31
untagged          vni-521       00:15:5d:c8:f5:1b  10.35.0.12         self   19:01:07
untagged          vni-521       00:15:5d:c8:f5:1c  10.35.0.12         self   18:59:27
untagged          vni-521       00:15:5d:c8:f5:1d  10.35.0.12         self   19:01:06
untagged          vni-521       00:15:5d:c8:f5:1e  10.35.0.12         self   19:03:46
untagged          vni-521       00:15:5d:c8:f5:1f  10.35.0.12         self   19:01:02
untagged          vni-521       00:15:5d:c8:f5:02  10.35.0.12         self   19:01:18
untagged          vni-521       00:15:5d:c8:f5:2a  10.35.0.12         self   18:59:22
untagged          vni-521       00:15:5d:c8:f5:2b  10.35.0.12         self   18:59:23
untagged          vni-521       00:15:5d:c8:f5:2c  10.35.0.12         self   18:59:23
untagged          vni-521       00:15:5d:c8:f5:2d  10.35.0.12         self   19:00:53
untagged          vni-521       00:15:5d:c8:f5:2e  10.35.0.12         self   19:00:50
untagged          vni-521       00:15:5d:c8:f5:2f  10.35.0.12         self   18:59:22
untagged          vni-521       00:15:5d:c8:f5:03  10.35.0.12         self   18:56:35
untagged          vni-521       00:15:5d:c8:f5:04  10.35.0.12         self   18:59:41
untagged          vni-521       00:15:5d:c8:f5:05  10.35.0.12         self   18:57:01
untagged          vni-521       00:15:5d:c8:f5:06  10.35.0.12         self   19:01:13
untagged          vni-521       00:15:5d:c8:f5:07  10.35.0.12         self   18:59:42
untagged          vni-521       00:15:5d:c8:f5:08  10.35.0.12         self   18:59:42
untagged          vni-521       00:15:5d:c8:f5:09  10.35.0.12         self   19:01:10
untagged          vni-521       00:15:5d:c8:f5:10  10.35.0.12         self   18:59:37
untagged          vni-521       00:15:5d:c8:f5:11  10.35.0.12         self   19:01:10
untagged          vni-521       00:15:5d:c8:f5:12  10.35.0.12         self   19:00:20
untagged          vni-521       00:15:5d:c8:f5:13  10.35.0.12         self   19:01:05
untagged          vni-521       00:15:5d:c8:f5:14  10.35.0.12         self   19:01:06
untagged          vni-521       00:15:5d:c8:f5:15  10.35.0.12         self   18:59:35
untagged          vni-521       00:15:5d:c8:f5:16  10.35.0.12         self   19:01:04
untagged          vni-521       00:15:5d:c8:f5:17  10.35.0.12         self   18:59:35
untagged          vni-521       00:15:5d:c8:f5:18  10.35.0.12         self   18:59:27
untagged          vni-521       00:15:5d:c8:f5:19  10.35.0.12         self   19:01:11
untagged          vni-521       00:15:5d:c8:f5:20  10.35.0.12         self   18:59:31
untagged          vni-521       00:15:5d:c8:f5:21  10.35.0.12         self   19:04:13
untagged          vni-521       00:15:5d:c8:f5:22  10.35.0.12         self   18:59:30
untagged          vni-521       00:15:5d:c8:f5:23  10.35.0.12         self   19:00:55
untagged          vni-521       00:15:5d:c8:f5:24  10.35.0.12         self   19:01:04
untagged          vni-521       00:15:5d:c8:f5:25  10.35.0.12         self   19:01:14
untagged          vni-521       00:15:5d:c8:f5:26  10.35.0.12         self   18:59:27
untagged          vni-521       00:15:5d:c8:f5:27  10.35.0.12         self   18:59:29
untagged          vni-521       00:15:5d:c8:f5:28  10.35.0.12         self   19:01:00
untagged          vni-521       00:15:5d:c8:f5:29  10.35.0.12         self   18:59:23
untagged          vni-521       00:15:5d:c8:f5:30  10.35.0.12         self   18:59:16
untagged          vni-521       00:15:5d:c8:f5:31  10.35.0.12         self   19:00:52
untagged          vni-521       00:15:5d:c8:f5:32  10.35.0.12         self   18:59:15
untagged          vni-521       00:15:5d:c8:f6:00  10.35.0.12         self   19:06:20
untagged          vni-521       00:15:7f:0c:f2:9f  10.35.0.12         self   19:01:43
untagged          vni-521       00:50:56:90:ee:1a  10.35.0.12         self   19:07:01
untagged          vni-521       00:50:56:a8:7c:fd  10.35.0.12         self   19:05:38
untagged          vni-521       f8:bc:12:05:b4:c0  10.35.0.12         self   19:07:07
untagged          vni-521       f8:bc:12:05:b5:00  10.35.0.12         self   19:07:40
untagged          vni-521       fa:16:3e:7d:e4:86  10.35.0.12         self   18:59:38
untagged          vni-522       00:50:56:91:0a:a4  10.35.0.12         self   18:57:11
untagged          vni-522       00:50:56:91:1a:22  10.35.0.12         self   17:28:08
untagged          vni-522       00:50:56:91:1d:e6  10.35.0.12         self   19:07:39
untagged          vni-522       00:50:56:91:1f:ba  10.35.0.12         self   19:07:39
untagged          vni-522       00:50:56:91:5d:00  10.35.0.12         self   18:06:48
untagged          vni-522       00:50:56:91:10:37  10.35.0.12         self   19:07:40
untagged          vni-522       00:50:56:91:31:3d  10.35.0.12         self   19:07:39
untagged          vni-522       00:50:56:91:73:bf  10.35.0.12         self   19:07:40
untagged          vni-522       00:50:56:91:75:9d  10.35.0.12         self   19:07:40
untagged          vni-522       00:50:56:a8:9f:c1  10.35.0.12         self   19:07:40
untagged          vni-523       00:50:56:90:97:d4  10.35.0.12         self   19:07:40
untagged          vni-524       00:50:56:91:7b:75  10.35.0.12         self   19:07:40
untagged          vni-524       00:50:56:91:25:bd  10.35.0.12         self   19:04:21
untagged          vni-524       00:50:56:91:40:a6  10.35.0.12         self   19:07:40
untagged          vni-524       00:50:56:91:54:48  10.35.0.12         self   19:05:15
untagged          vni-525       00:00:5e:00:01:0f  10.35.0.12         self   19:07:40
untagged          vni-600       00:00:5e:00:01:96  10.35.0.12         self   19:07:39
untagged          vni-600       00:50:56:90:43:ed  10.35.0.12         self   19:07:39
untagged          vni-600       00:50:56:91:41:10  10.35.0.12         self   18:59:15
untagged          vni-600       5c:f9:dd:ef:ab:82  10.35.0.12         self   19:07:40
untagged          vni-602       00:00:5e:00:01:96  10.35.0.12         self   19:07:40
untagged          vni-602       00:15:5d:0b:16:16  10.35.0.12         self   19:07:40
untagged          vni-602       5c:f9:dd:ef:ab:82  10.35.0.12         self   19:07:39
untagged          vni-602       24:8a:07:88:d9:ba  10.35.0.12         self   19:07:39
untagged          vni-602       24:8a:07:ad:6d:3a  10.35.0.12         self   19:04:27
untagged          vni-602       b0:83:fe:d7:4e:ca  10.35.0.12         self   19:06:41
untagged          vni-604       00:00:5e:00:01:ae  10.35.0.12         self   19:07:39
untagged          vni-604       00:50:56:90:52:d8  10.35.0.12         self   19:07:39
untagged          vni-604       5c:f9:dd:ef:ab:82  10.35.0.12         self   19:07:40
untagged          vni-605       00:00:5e:00:01:af  10.35.0.12         self   19:07:40
untagged          vni-605       00:50:56:90:52:d8  10.35.0.12         self   19:07:39
untagged          vni-605       5c:f9:dd:ef:ab:82  10.35.0.12         self   19:07:40
untagged          vni-1000      00:00:5e:00:01:64  10.35.0.12         self   19:07:40
untagged          vni-1000      00:15:5d:0b:16:07  10.35.0.12         self   19:07:17
untagged          vni-1000      00:15:5d:0b:16:14  10.35.0.12         self   19:07:09
untagged          vni-1000      00:50:56:90:77:5b  10.35.0.12         self   19:01:49
untagged          vni-1000      00:50:56:90:c6:dc  10.35.0.12         self   19:02:01
untagged          vni-1000      00:50:56:91:01:f4  10.35.0.12         self   19:04:04
untagged          vni-1000      00:50:56:91:1e:49  10.35.0.12         self   19:07:40
untagged          vni-1000      00:50:56:91:3d:ab  10.35.0.12         self   19:02:02
untagged          vni-1000      00:50:56:91:3e:d8  10.35.0.12         self   19:05:59
untagged          vni-1000      00:50:56:91:4f:7e  10.35.0.12         self   15:36:34
untagged          vni-1000      00:50:56:91:5a:2d  10.35.0.12         self   15:39:06
untagged          vni-1000      00:50:56:91:5e:4f  10.35.0.12         self   15:08:46
untagged          vni-1000      00:50:56:91:6e:60  10.35.0.12         self   19:03:45
untagged          vni-1000      00:50:56:91:07:ed  10.35.0.12         self   18:57:31
untagged          vni-1000      00:50:56:91:7a:11  10.35.0.12         self   19:04:23
untagged          vni-1000      00:50:56:91:7b:d2  10.35.0.12         self   19:02:33
untagged          vni-1000      00:50:56:91:7d:b0  10.35.0.12         self   19:02:05
untagged          vni-1000      00:50:56:91:11:0b  10.35.0.12         self   08:52:47
untagged          vni-1000      00:50:56:91:11:58  10.35.0.12         self   19:06:19
untagged          vni-1000      00:50:56:91:12:62  10.35.0.12         self   19:07:19
untagged          vni-1000      00:50:56:91:16:77  10.35.0.12         self   19:06:26
untagged          vni-1000      00:50:56:91:16:e2  10.35.0.12         self   19:00:42
untagged          vni-1000      00:50:56:91:22:17  10.35.0.12         self   19:04:46
untagged          vni-1000      00:50:56:91:22:f6  10.35.0.12         self   19:06:45
untagged          vni-1000      00:50:56:91:37:cc  10.35.0.12         self   19:07:40
untagged          vni-1000      00:50:56:91:39:59  10.35.0.12         self   19:06:15
untagged          vni-1000      00:50:56:91:47:69  10.35.0.12         self   19:05:03
untagged          vni-1000      00:50:56:91:47:cb  10.35.0.12         self   06:09:19
untagged          vni-1000      00:50:56:91:62:88  10.35.0.12         self   07:57:00
untagged          vni-1000      00:50:56:91:71:8c  10.35.0.12         self   00:05:56
untagged          vni-1000      00:50:56:91:74:bc  10.35.0.12         self   19:05:02
untagged          vni-1000      24:8a:07:88:d9:ba  10.35.0.12         self   19:07:14
untagged          vni-1000      24:8a:07:ad:6d:3a  10.35.0.12         self   19:07:40
untagged          vni-1000      b0:83:fe:d7:4e:ca  10.35.0.12         self   19:07:40
untagged          vni-1000      d0:67:e5:dc:e3:b3  10.35.0.12         self   01:45:32
untagged          vni-1000      d0:67:e5:dc:e5:0b  10.35.0.12         self   19:07:40
untagged          vni-1001      00:00:0c:9f:f0:e6  10.35.0.10         self   19:07:25
untagged          vni-1001      00:0e:1e:eb:ec:b0  10.35.0.10         self   18:09:24
untagged          vni-1001      00:0e:1e:eb:ec:b2  10.35.0.10         self   19:07:26
untagged          vni-1001      00:07:43:0a:26:c5  10.35.0.10         self   18:09:24
untagged          vni-1001      00:07:43:0a:26:cd  10.35.0.10         self   18:09:24
untagged          vni-1001      00:07:43:46:af:c8  10.35.0.10         self   18:09:24
untagged          vni-1001      00:07:43:46:af:e8  10.35.0.10         self   18:09:24
untagged          vni-1001      00:15:5d:e6:12:00  10.35.0.10         self   19:07:25
untagged          vni-1001      00:15:5d:e6:12:01  10.35.0.10         self   19:07:26
untagged          vni-1001      00:15:5d:e6:12:02  10.35.0.10         self   19:07:26
untagged          vni-1001      00:15:5d:e6:12:03  10.35.0.10         self   19:07:26
untagged          vni-1001      00:15:5d:e6:12:04  10.35.0.10         self   19:07:26
untagged          vni-1001      00:15:5d:e6:12:05  10.35.0.10         self   19:07:21
untagged          vni-1001      00:15:5d:e6:12:06  10.35.0.10         self   19:07:26
untagged          vni-1001      00:15:5d:e6:12:07  10.35.0.10         self   19:07:20
untagged          vni-1001      64:a0:e7:40:b4:c2  10.35.0.10         self   18:09:24
untagged          vni-1001      64:a0:e7:43:1b:c2  10.35.0.10         self   18:09:24
untagged          vni-1001      74:2b:0f:09:a1:ed  10.35.0.10         self   19:06:48
untagged          vni-1001      74:2b:0f:09:a1:ee  10.35.0.10         self   18:09:24
untagged          vni-1001      74:2b:0f:09:a1:ef  10.35.0.10         self   18:09:24
untagged          vni-1001      74:2b:0f:09:a1:f0  10.35.0.10         self   18:09:24
untagged          vni-1001      f4:8e:38:2d:ee:fa  10.35.0.10         self   19:07:22
untagged          vni-1002      00:00:5e:00:01:64  10.35.0.12         self   18:09:23
untagged          vni-1002      d0:67:e5:dc:e3:b3  10.35.0.12         self   19:07:26
untagged          vni-1002      d0:67:e5:dc:e5:0b  10.35.0.12         self   19:07:24
untagged          vni-1003      00:00:5e:00:01:64  10.35.0.12         self   19:07:39
untagged          vni-1003      00:07:b4:00:01:01  10.35.0.12         self   18:09:22
untagged          vni-1003      00:07:b4:00:01:02  10.35.0.12         self   19:07:39
untagged          vni-1003      00:50:56:91:18:1f  10.35.0.12         self   19:07:39
untagged          vni-1003      00:50:56:a8:24:07  10.35.0.12         self   19:07:40
untagged          vni-1003      00:d6:fe:76:69:30  10.35.0.12         self   18:57:58
untagged          vni-1003      1a:8c:47:4e:6c:d1  10.35.0.12         self   19:07:40
untagged          vni-1003      1e:04:0c:74:51:51  10.35.0.12         self   19:07:40
untagged          vni-1003      02:3f:a4:4c:5e:ab  10.35.0.12         self   19:07:39
untagged          vni-1003      2a:b5:97:bb:90:44  10.35.0.12         self   19:07:40
untagged          vni-1003      2a:f6:dd:86:73:66  10.35.0.12         self   19:07:40
untagged          vni-1003      2a:ff:90:b2:e4:46  10.35.0.12         self   19:07:40
untagged          vni-1003      3e:70:dc:6a:5e:03  10.35.0.12         self   19:07:40
untagged          vni-1003      4a:91:22:96:d9:16  10.35.0.12         self   19:07:40
untagged          vni-1003      4a:c3:fe:6e:38:e7  10.35.0.12         self   19:07:40
untagged          vni-1003      4e:5c:fe:db:1b:e8  10.35.0.12         self   19:07:40
untagged          vni-1003      4e:19:0c:ba:0b:b3  10.35.0.12         self   19:07:39
untagged          vni-1003      5e:73:17:5d:8b:17  10.35.0.12         self   19:07:40
untagged          vni-1003      6a:43:08:21:90:3b  10.35.0.12         self   19:07:40
untagged          vni-1003      6e:1a:15:c4:a0:dd  10.35.0.12         self   19:07:40
untagged          vni-1003      7a:dc:7e:9d:0c:04  10.35.0.12         self   19:07:40
untagged          vni-1003      7e:83:0d:5f:32:bd  10.35.0.12         self   18:02:11
untagged          vni-1003      7e:88:b4:84:dc:d0  10.35.0.12         self   19:07:40
untagged          vni-1003      8a:2f:a7:f4:02:02  10.35.0.12         self   19:07:40
untagged          vni-1003      8e:a7:45:1d:eb:a1  10.35.0.12         self   19:07:40
untagged          vni-1003      9a:9a:e6:82:ed:5d  10.35.0.12         self   19:07:40
untagged          vni-1003      9a:be:b2:fe:b6:5e  10.35.0.12         self   19:07:39
untagged          vni-1003      9a:e3:01:87:cf:05  10.35.0.12         self   19:07:40
untagged          vni-1003      10:98:36:b5:ad:cb  10.35.0.12         self   19:07:40
untagged          vni-1003      10:98:36:b5:ad:cd  10.35.0.12         self   18:08:51
untagged          vni-1003      12:5e:35:c4:5a:1c  10.35.0.12         self   19:07:39
untagged          vni-1003      12:c4:09:c3:2d:21  10.35.0.12         self   19:07:40
untagged          vni-1003      16:0f:13:7c:9f:d0  10.35.0.12         self   19:07:39
untagged          vni-1003      16:b2:8e:1b:84:44  10.35.0.12         self   19:07:40
untagged          vni-1003      16:f2:83:e4:de:0a  10.35.0.12         self   19:07:39
untagged          vni-1003      22:41:08:b9:83:a0  10.35.0.12         self   19:07:40
untagged          vni-1003      26:6e:fe:a7:be:e7  10.35.0.12         self   19:07:40
untagged          vni-1003      26:44:07:f0:44:bb  10.35.0.12         self   19:07:40
untagged          vni-1003      32:06:87:12:58:30  10.35.0.12         self   19:07:39
untagged          vni-1003      32:a9:f8:52:25:d6  10.35.0.12         self   19:07:40
untagged          vni-1003      50:9a:4c:80:93:ef  10.35.0.12         self   19:07:40
untagged          vni-1003      50:9a:4c:80:95:ef  10.35.0.12         self   19:07:39
untagged          vni-1003      52:90:f4:62:55:42  10.35.0.12         self   19:07:40
untagged          vni-1003      56:4b:ce:34:0c:c4  10.35.0.12         self   08:07:11
untagged          vni-1003      62:25:45:36:45:ea  10.35.0.12         self   19:07:40
untagged          vni-1003      66:65:7c:53:7f:27  10.35.0.12         self   19:07:39
untagged          vni-1003      70:35:09:8c:cf:8f  10.35.0.12         self   18:07:49
untagged          vni-1003      72:45:49:27:68:c3  10.35.0.12         self   19:07:39
untagged          vni-1003      72:74:2b:c9:70:c3  10.35.0.12         self   19:07:40
untagged          vni-1003      76:28:39:c8:43:34  10.35.0.12         self   19:07:39
untagged          vni-1003      76:43:b8:58:ce:ae  10.35.0.12         self   19:07:40
untagged          vni-1003      82:60:e6:b8:de:77  10.35.0.12         self   19:07:39
untagged          vni-1003      82:ec:20:b2:1b:43  10.35.0.12         self   19:07:40
untagged          vni-1003      86:83:9f:dd:a0:d0  10.35.0.12         self   07:24:01
untagged          vni-1003      86:f9:40:71:52:02  10.35.0.12         self   19:07:40
untagged          vni-1003      92:0d:ef:47:6e:cf  10.35.0.12         self   19:07:39
untagged          vni-1003      96:cc:54:61:46:47  10.35.0.12         self   19:07:39
untagged          vni-1003      a2:b6:0b:df:c2:62  10.35.0.12         self   19:07:40
untagged          vni-1003      aa:7a:b6:9c:5f:fd  10.35.0.12         self   19:07:40
untagged          vni-1003      aa:8d:20:38:f2:bd  10.35.0.12         self   19:07:40
untagged          vni-1003      ae:59:b7:7b:ef:ce  10.35.0.12         self   19:07:40
untagged          vni-1003      ae:ba:83:75:1a:8d  10.35.0.12         self   19:07:40
untagged          vni-1003      be:91:f6:83:b3:a9  10.35.0.12         self   19:07:40
untagged          vni-1003      c6:35:9e:2e:18:74  10.35.0.12         self   19:07:39
untagged          vni-1003      ca:cc:f7:3c:a5:65  10.35.0.12         self   19:07:39
untagged          vni-1003      d0:67:e5:dc:e3:b3  10.35.0.12         self   19:07:40
untagged          vni-1003      d0:67:e5:dc:e5:0b  10.35.0.12         self   19:07:40
untagged          vni-1003      d6:4c:d0:79:bd:63  10.35.0.12         self   09:20:23
untagged          vni-1003      d6:16:3b:63:ea:ef  10.35.0.12         self   18:57:39
untagged          vni-1003      d6:88:d6:f9:08:bf  10.35.0.12         self   19:07:40
untagged          vni-1003      de:94:a5:5f:0b:b3  10.35.0.12         self   19:07:40
untagged          vni-1003      de:d9:46:d1:53:d3  10.35.0.12         self   19:07:40
untagged          vni-1003      e2:4a:80:22:bd:bc  10.35.0.12         self   18:48:26
untagged          vni-1003      ee:2b:fe:a3:d7:6f  10.35.0.12         self   19:07:39
untagged          vni-1003      f2:ff:b6:2d:2c:13  10.35.0.12         self   19:07:40
untagged          vni-1003      f4:8e:38:1f:a2:87  10.35.0.12         self   19:07:39
untagged          vni-1003      f6:77:66:42:25:db  10.35.0.12         self   19:07:39
untagged          vni-1004      00:50:56:91:0f:12  10.35.0.12         self   19:07:40
untagged          vni-1004      00:50:56:91:40:9b  10.35.0.12         self   17:43:29
untagged          vni-1004      00:50:56:91:52:dc  10.35.0.12         self   19:07:40
untagged          vni-1004      00:50:56:91:65:48  10.35.0.12         self   19:07:39
untagged          vni-1004      00:50:56:a8:d6:c4  10.35.0.12         self   19:07:40
untagged          vni-1004      1e:3a:77:dd:dc:53  10.35.0.12         self   18:59:46
untagged          vni-1004      2e:97:f0:16:a4:e1  10.35.0.12         self   19:07:39
untagged          vni-1004      3e:56:23:f7:63:6a  10.35.0.12         self   19:07:40
untagged          vni-1004      5a:13:13:5b:b3:c0  10.35.0.12         self   19:07:40
untagged          vni-1004      9e:9d:ac:f3:a5:e6  10.35.0.12         self   19:07:39
untagged          vni-1004      82:94:21:99:fb:88  10.35.0.12         self   18:06:32
untagged          vni-1004      92:42:b0:0d:b6:a0  10.35.0.12         self   19:07:40
untagged          vni-1004      a2:05:6d:a7:d0:85  10.35.0.12         self   19:07:39
untagged          vni-1004      d6:06:2b:04:52:07  10.35.0.12         self   04:22:35
untagged          vni-1102      00:00:5e:00:01:66  10.35.0.12         self   19:07:40
untagged          vni-1102      5c:f9:dd:ef:ab:82  10.35.0.12         self   00:21:05
untagged          vni-1102      24:8a:07:91:5a:4d  10.35.0.12         self   19:07:39
untagged          vni-1103      00:00:5e:00:01:67  10.35.0.12         self   17:39:37
untagged          vni-1103      24:8a:07:55:4b:b5  10.35.0.12         self   18:04:49
untagged          vni-1200      00:15:5d:0b:16:00  10.35.0.12         self   01:03:25
untagged          vni-1200      00:15:5d:0b:16:01  10.35.0.12         self   02:40:26
untagged          vni-1200      00:50:56:a8:fe:c0  10.35.0.12         self   01:24:28
untagged          vni-1200      24:8a:07:88:d9:ba  10.35.0.12         self   19:07:40
untagged          vni-1200      24:8a:07:ad:6d:3a  10.35.0.12         self   19:07:40
untagged          vni-1201      00:15:5d:0b:16:03  10.35.0.12         self   01:00:36
untagged          vni-1201      00:50:56:a8:43:7a  10.35.0.12         self   01:19:39
untagged          vni-1201      24:8a:07:88:d9:ba  10.35.0.12         self   16:02:36
untagged          vni-1201      24:8a:07:ad:6d:3a  10.35.0.12         self   19:07:37
untagged          vni-1251      00:00:5e:00:01:0f  10.35.0.12         self   19:07:40
untagged          vni-1251      5c:f9:dd:ef:ab:82  10.35.0.12         self   19:07:40
untagged          vni-1998      00:00:5e:00:01:64  10.35.0.12         self   18:09:24
untagged          vni-1998      00:50:56:a8:0e:e0  10.35.0.12         self   19:07:40
untagged          vni-1998      00:50:56:a8:1f:90  10.35.0.12         self   19:05:41
untagged          vni-1998      00:50:56:a8:3b:5c  10.35.0.12         self   19:07:38
untagged          vni-1998      00:50:56:a8:9d:93  10.35.0.12         self   19:06:31
untagged          vni-1998      00:50:56:a8:10:80  10.35.0.12         self   19:06:53
untagged          vni-1998      00:50:56:a8:25:65  10.35.0.12         self   19:07:39
untagged          vni-1998      00:50:56:a8:34:c8  10.35.0.12         self   19:07:10
untagged          vni-1998      00:50:56:a8:a3:e4  10.35.0.12         self   19:06:55
untagged          vni-1998      00:50:56:a8:a4:6f  10.35.0.12         self   19:05:57
untagged          vni-1998      00:50:56:a8:b6:6a  10.35.0.12         self   19:07:26
untagged          vni-1998      00:50:56:a8:cf:fe  10.35.0.12         self   19:05:51
untagged          vni-1998      00:50:56:a8:fe:30  10.35.0.12         self   19:06:52
untagged          vni-1998      e4:f0:04:5b:c8:43  10.35.0.12         self   19:07:40
untagged          vni-1998      e4:f0:04:58:9c:c3  10.35.0.12         self   18:09:24
untagged          vni-1999      00:00:5e:00:01:65  10.35.0.12         self   19:07:39
untagged          vni-1999      00:50:56:a8:33:ad  10.35.0.12         self   19:07:15
untagged          vni-1999      00:50:56:a8:ce:e4  10.35.0.12         self   19:03:47
untagged          vni-1999      e4:f0:04:5b:c8:43  10.35.0.12         self   19:07:40
untagged          vni-1999      e4:f0:04:58:9c:c3  10.35.0.12         self   18:09:24
untagged          vni-2100      00:00:5e:00:01:0f  10.35.0.12         self   19:07:39
untagged          vni-2511      00:00:5e:00:01:0f  10.35.0.12         self   19:07:40
untagged          vni-2511      5c:f9:dd:ef:ab:82  10.35.0.12         self   19:07:40
untagged          vni-2520      5c:f9:dd:ef:ab:82  10.35.0.12         self   19:07:40
untagged          vni-2521      00:00:5e:00:01:0f  10.35.0.12         self   19:07:40
untagged          vni-2521      5c:f9:dd:ef:ab:82  10.35.0.12         self   19:07:40
untagged          vni-2522      00:00:5e:00:01:0f  10.35.0.12         self   19:07:39
untagged          vni-2522      5c:f9:dd:ef:ab:82  10.35.0.12         self   19:07:39
untagged          vni-2579      00:00:5e:00:01:0f  10.35.0.12         self   19:07:39
untagged          vni-2579      5c:f9:dd:ef:ab:82  10.35.0.12         self   19:07:40
untagged          vni-2902      00:00:5e:00:01:ca  10.35.0.12         self   19:07:40
untagged          vni-2902      24:8a:07:9b:0d:6b  10.35.0.12         self   19:07:40
untagged          vni-2902      24:8a:07:a4:64:f1  10.35.0.12         self   19:07:39
untagged          vni-2903      00:00:5e:00:01:cb  10.35.0.12         self   19:07:39
untagged          vni-2903      24:8a:07:91:5a:25  10.35.0.12         self   19:07:39
untagged          vni-2903      24:8a:07:99:c3:7b  10.35.0.12         self   19:07:39
"""

class CumulusDevice(object):
    def __init__(self, hostname, username, password):
        self.hostname = hostname
        self.username = username
        self.password = password

    def _open_connection(self):
        ssh_client = None

        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(
                               hostname=self.hostname,
                               username=self.username,
                               password=self.password,
                               look_for_keys=False,
                               allow_agent=False, timeout=5)

            print("SSH connection established to {0}".format(self.hostname))

        except (pexception.BadHostKeyException,
                pexception.AuthenticationException,
                pexception.SSHException,
                pexception.socket.error) as e:
                    print(e)

        return ssh_client

    def _close_connection(self, client):
        return client.close()

    def send_command(self, command):
        """Wrapper for self.device.send.command().
        If command is a list will iterate through commands until valid command.
        """

        ssh_client = self._open_connection()
        _, stdout, stderr = ssh_client.exec_command(command, timeout=10)
        output = stdout.read().decode('utf-8')
        _ = self._close_connection(ssh_client)

        return output

    @staticmethod
    def _clitable_to_dict(cli_table):
        """Convert TextFSM cli_table object to list of dictionaries."""
        objs = []
        for row in cli_table:
            temp_dict = {}
            for index, element in enumerate(row):
                temp_dict[cli_table.header[index].lower()] = element
            objs.append(temp_dict)

        return objs

    def parse_output(self, platform=None, command=None, data=None):
        """Return the structured data based on the output from a network device."""
        cli_table = clitable.CliTable('index', TEMPLATE_DIR)

        attrs = dict(
            Command=command,
            Platform=platform
        )
        try:
            cli_table.ParseCmd(data, attrs)
            structured_data = self._clitable_to_dict(cli_table)
        except clitable.CliTableError as e:
            raise CannotParseOutputWithTextFSM

        return structured_data

    def show_version(self):
        #output = self.send_command('net show version')
        structured_output = device.parse_output(
            command="net show version",
            platform="cumulus_clos",
            data=show_version)

        return structured_output

    def show_bridge_macs(self, state='dynamic'):
        state = state.lower()
        command = f"net show bridge macs {state}"
        #output = self.send_command(command)
        structured_output = device.parse_output(
            command=command,
            platform="cumulus_clos",
            data=show_bridge_macs_dynamic)

        return structured_output


def get_inventory():

    if os.path.isfile(HOSTS_FILENAME):
        inventory = read_yaml_file(HOSTS_FILENAME)
    else:
        raise InventoryFileNotFound

    return inventory


def read_yaml_file(filepath):
    """ Read YAML file """

    with open(filepath, 'r') as stream:
        data = yaml.safe_load(stream)

    return data


def get_inventory_by_group(group):
    inventory = get_inventory()
    group_inventory = inventory[group]['hosts']

    for k, v in group_inventory.items():
        for _, i in inventory.items():
            if i.get('hosts'):
                caw = i['hosts']
                if caw.get(k) and isinstance(caw.get(k), dict):
                    if caw[k].get('ansible_host'):
                        group_inventory[k] = caw[k]['ansible_host']

    return group_inventory


if __name__ == '__main__':
    # get host inventory
    hosts = get_inventory_by_group('cumulus')

    device = CumulusDevice(
        hostname="10.30.20.82",
        username="cumulus",
        password="T0dayweride!"
    )

    show_version = device.show_version()
    print(show_version)

    macs = device.show_bridge_macs()
    for mac in macs:
        print(mac)
    print(len(macs))





    #
    # #show_version = device.show_version()



    #print(show_version)












