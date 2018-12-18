import os
import re
import sys
import requests
import json
from prometheus_client import Gauge



class KeaExporter():
    subnet_pattern = re.compile(
        r"subnet\[(?P<subnet_idx>[\d]+)\]\.(?P<metric>[\w-]+)")

    def __init__(self, target):

        self._target = target

        # prometheus
        self.prefix = 'kea'
        self.prefix_dhcp4 = '{0}_dhcp4'.format(self.prefix)
        self.prefix_dhcp6 = '{0}_dhcp6'.format(self.prefix)

        self.metrics_dhcp4 = None
        self.metrics_dhcp4_map = None
        self.metrics_dhcp4_ignore = None
        self.setup_dhcp4_metrics()

        self.metrics_dhcp6 = None
        self.metrics_dhcp6_map = None
        self.metrics_dhcp6_ignore = None
        self.setup_dhcp6_metrics()

        self.Modules = []
        self.subnets = {}

        self.load_modules()
        self.load_subnets()


    def load_modules(self):
        r = requests.post(self._target, json = {'command': 'config-get'},
            headers={'Content-Type': 'application/json'})
        config= r.json()
        for module in (config[0]['arguments']['Control-agent']
            ['control-sockets']):
            self.Modules.append(module)


    def load_subnets(self):
        r = requests.post(self._target, json = {'command': 'config-get',
            'service': self.Modules },
            headers={'Content-Type': 'application/json'})
        config = r.json()
        for subnet in (config[0]['arguments']['Dhcp4']['subnet4']):
            self.subnets.update( {subnet['id']: subnet['subnet']} )


    def setup_dhcp4_metrics(self):
        self.metrics_dhcp4 = {
            # Packets
            'received_packets': Gauge(
                '{0}_packets_received'.format(self.prefix_dhcp4),
                'Number of DHCPv4 packets received',
                ['operation']),

            # per Subnet
            'addresses_assigned_total': Gauge(
                '{0}_addresses_assigned_total'.format(self.prefix_dhcp4),
                'Assigned addresses',
                ['id', 'subnet']),
            'addresses_declined_total': Gauge(
                '{0}_addresses_declined_total'.format(self.prefix_dhcp4),
                'Declined counts',
                ['id', 'subnet']),
            'addresses_declined_reclaimed_total': Gauge(
                '{0}_addresses_declined_reclaimed_total'.format(
                    self.prefix_dhcp4),
                'Declined addresses that were reclaimed',
                ['id', 'subnet']),
            'addresses_reclaimed_total': Gauge(
                '{0}_addresses_reclaimed_total'.format(self.prefix_dhcp4),
                'Expired addresses that were reclaimed',
                ['id', 'subnet']),
            'addresses_total': Gauge(
                '{0}_addresses_total'.format(self.prefix_dhcp4),
                'Size of subnet address pool',
                ['id', 'subnet']
            )
        }

        self.metrics_dhcp4_map = {
            # received_packets
            'pkt4-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'all'}
            },
            'pkt4-parse-failed': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'parse-failed'}
            },
            'pkt4-receive-drop': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'dropped'}
            },

            # per Subnet
            'assigned-addresses': {
                'metric': 'addresses_assigned_total',
            },
            'declined-addresses': {
                'metric': 'addresses_declined_total',
            },
            'declined-reclaimed-addresses': {
                'metric': 'addresses_declined_reclaimed_total',
            },
            'reclaimed-declined-addresses': {
                'metric': 'addresses_declined_reclaimed_total',
            },
            'reclaimed-leases': {
                'metric': 'addresses_reclaimed_total',
            },
            'total-addresses': {
                'metric': 'addresses_total',
            }
        }

        self.metrics_dhcp4_ignore = [
            # sums of subnet values
            'declined-addresses',
            'declined-reclaimed-addresses',
            'reclaimed-declined-addresses',
            'reclaimed-leases'
        ]


    def setup_dhcp6_metrics(self):
        self.metrics_dhcp6 = {
            # Packets sent/received
            'sent_packets': Gauge(
                '{0}_packets_sent_total'.format(self.prefix_dhcp6),
                'Packets sent',
                ['operation']),
            'received_packets': Gauge(
                '{0}_packets_received_total'.format(self.prefix_dhcp6),
                'Packets received',
                ['operation']),

            # DHCPv4-over-DHCPv6
            'sent_dhcp4_packets': Gauge(
                '{0}_packets_sent_dhcp4_total'.format(self.prefix_dhcp6),
                'DHCPv4-over-DHCPv6 Packets received',
                ['operation']
            ),
            'received_dhcp4_packets': Gauge(
                '{0}_packets_received_dhcp4_total'.format(self.prefix_dhcp6),
                'DHCPv4-over-DHCPv6 Packets received',
                ['operation']
            ),

            # per Subnet
            'addresses_declined_total': Gauge(
                '{0}_addresses_declined_total'.format(self.prefix_dhcp6),
                'Declined addresses',
                ['subnet']),
            'addresses_declined_reclaimed_total': Gauge(
                '{0}_addresses_declined_reclaimed_total'.format(
                    self.prefix_dhcp6),
                'Declined addresses that were reclaimed',
                ['subnet']),
            'addresses_reclaimed_total': Gauge(
                '{0}_addresses_reclaimed_total'.format(self.prefix_dhcp6),
                'Expired addresses that were reclaimed',
                ['subnet']),

            # IA_NA
            'na_assigned_total': Gauge(
                '{0}_na_assigned_total'.format(self.prefix_dhcp6),
                'Assigned non-temporary addresses (IA_NA)',
                ['subnet']),
            'na_total': Gauge(
                '{0}_na_total'.format(self.prefix_dhcp6),
                'Size of non-temporary address pool',
                ['subnet']
            ),

            # IA_PD
            'pd_assigned_total': Gauge(
                '{0}_pd_assigned_total'.format(self.prefix_dhcp6),
                'Assigned prefix delegations (IA_PD)',
                ['subnet']),
            'pd_total': Gauge(
                '{0}_pd_total'.format(self.prefix_dhcp6),
                'Size of prefix delegation pool',
                ['subnet']
            ),

        }

        self.metrics_dhcp6_map = {
            # sent_packets
            'pkt6-advertise-sent': {
                'metric': 'sent_packets',
                'labels': {
                    'operation': 'advertise'
                },
            },
            'pkt6-reply-sent': {
                'metric': 'sent_packets',
                'labels': {
                    'operation': 'reply'
                },
            },

            # received_packets
            'pkt6-receive-drop': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'drop'
                },
            },
            'pkt6-parse-failed': {
                'metric': 'receoved_packets',
                'labels': {
                    'operation': 'parse-failed'
                },
            },
            'pkt6-solicit-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'solicit'
                },
            },
            'pkt6-advertise-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'advertise'
                }
            },
            'pkt6-request-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'request'
                }
            },
            'pkt6-reply-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'reply'
                }
            },
            'pkt6-renew-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'renew'
                }
            },
            'pkt6-rebind-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'rebind'
                }
            },
            'pkt6-release-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'release'
                }
            },
            'pkt6-decline-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'decline'
                }
            },
            'pkt6-infrequest-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'infrequest'
                }
            },
            'pkt6-unknown-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'unknown'
                }
            },

            # DHCPv4-over-DHCPv6
            'pkt6-dhcpv4-response-sent': {
                'metric': 'sent_dhcp4_packets',
                'labels': {
                    'operation': 'response'
                }
            },
            'pkt6-dhcpv4-query-received': {
                'metric': 'received_dhcp4_packets',
                'labels': {
                    'operation': 'query'
                }
            },
            'pkt6-dhcpv4-response-received': {
                'metric': 'received_dhcp4_packets',
                'labels': {
                    'operation': 'response'
                }
            },

            # per Subnet
            'assigned-nas': {
                'metric': 'na_assigned_total',
            },
            'assigned-pds': {
                'metric': 'pd_assigned_total',
            },
            'declined-addresses': {
                'metric': 'addresses_declined_total',
            },
            'declined-reclaimed-addresses': {
                'metric': 'addresses_declined_reclaimed_total',
            },
            'reclaimed-declined-addresses': {
                'metric': 'addresses_declined_reclaimed_total',
            },
            'reclaimed-leases': {
                'metric': 'addresses_reclaimed_total',
            },
            'total-nas': {
                'metric': 'na_total',
            },
            'total-pds': {
                'metric': 'pd_total',
            }
        }

        self.metrics_dhcp6_ignore = [
            # sums of different packet types
            'pkt6-sent',
            'pkt6-received',
            # sums of subnet values
            'declined-addresses',
            'declined-reclaimed-addresses',
            'reclaimed-declined-addresses',
            'reclaimed-leases'
        ]


    def update(self):
        # Note for future testing: pipe curl output to jq for an easier read
        for m in self.Modules:
            list = []
            list.append(m)
            r = requests.post(self._target, json = {'command':
                'statistic-get-all', 'arguments': { }, 'service': list },
                 headers={'Content-Type': 'application/json'})
            self.parse_metrics(r.json(), m)


    def parse_metrics(self, response, module):
        # From the JSON reply, take the first array, index 'arguments'; then
        # return a list of the dictionary's key/values
        for key, data in response[0]['arguments'].items():
            if module == 'dhcp4':
                if key in self.metrics_dhcp4_ignore:
                    continue
            else:
                if key in self.metrics_dhcp6_ignore:
                    continue

            value, timestamp = data[0]
            labels = {}

            if key.startswith('subnet['):
                match = self.subnet_pattern.match(key)

                if match:
                    subnet_idx = int(match.group('subnet_idx'))

                    key = match.group('metric')
                    if module == 'dhcp4':
                        idx = subnet_idx
                        subnet = self.subnets.get(subnet_idx)
                    else:
                        # To-do: add support for DHCPv6
                        pass

                    labels['subnet'] = subnet
                    labels['id'] = idx
                else:
                    print('subnet pattern failed for metric: {0}'.format(
                        key), file=sys.stderr)

            if module == 'dhcp4':
                metric_info = self.metrics_dhcp4_map[key]
                metric = self.metrics_dhcp4[metric_info['metric']]
            else:
                metric_info = self.metrics_dhcp6_map[key]
                metric = self.metrics_dhcp6[metric_info['metric']]

            # merge static and dynamic labels
            labels.update(metric_info.get('labels', {}))

            # export labels and value
            metric.labels(**labels).set(value)
