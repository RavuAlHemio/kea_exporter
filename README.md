# kea-exporter
Prometheus exporter for the ISC Kea DHCP Server, written in Python, forked from [kea-exporter](https://github.com/mweinelt/kea-exporter/)

## Features
* DHCP4 metrics
* Querying via RESTful API (allows the exporter to be run remotely)

## Requirements
This exporter has ONLY been tested on Kea 1.4, though any version of Kea that implements the RESTful API should work (> 1.2).

## Known Issues & Limitations
- DHCPv6 metrics not supported (yet)
- Packet statistics are limited to `pkt4-received`, `pkt4-parse-failed`, and `pkt4-receive-drop` - this is a limitation of the API which impacts the metrics the exporter can provide. If more granular detail for packet statistics is needed, the original [kea-exporter](https://github.com/mweinelt/kea-exporter/) would be highly recommended.

## Installation
```
git clone git@github.com:ddericco/kea-exporter.git
cd kea-exporter
pip install -r requirements.txt
```
