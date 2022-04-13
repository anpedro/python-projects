import json
from napalm import get_network_driver
#Author: Andre Pedro

def interface_counters(all_hosts,host):
    """Getting all the non-zero interface counters"""
    print(f"hostname is {host}")
    int_counters = all_hosts.get_interfaces_counters()
    for key,values in int_counters.items(): #Getting key/values on the dict of dict.
        for name,counters in values.items(): # Getting key/value of the second dict (counter name + number)
                if counters != 0:
                    print(f"Interface:{key} {name} : {counters}")


def interface_details(all_hosts,host):
    """Getting the interface that are up + mac_address and speed/MTU"""
    print(f"hostname is {host}")
    gi = all_hosts.get_interfaces()
    for key,values in gi.items():
        if values['is_up'] :
            print(f"Interfaces is {key} and mac_address is {values['mac_address']} and speed is {values['speed']} - MTU:{values['mtu']}")


def interface_errors():
    """Getting only the interface errors"""



def main():

    xr_supported_models = ['get_bgp_config', 'get_bgp_neighbors', 'get_bgp_neighbors_detail', 'get_config', 'get_environment', 'get_facts', 'get_interfaces', 'get_interfaces_counters','get_interfaces_ip','get_lldp_neighbors','get_lldp_neighbors_detail','get_mac_address_table','get_ntp_peers','get_ntp_servers','get_ntp_stats','get_probes_config','get_probes_results','get_route_to','get_snmp_information','get_users','is_alive']
    """Getting Interface non-zero counters/mac-address/mtu/speed on the entire A-MSW-Testbed"""
    list_of_hosts = ['10.8.70.12', '10.8.70.13', '10.8.70.14', '10.8.70.15', '10.8.70.22', '10.8.70.23', '10.8.70.25', '10.8.70.26']

    for host in list_of_hosts:
        driver = get_network_driver('iosxr_netconf')
        all_hosts = driver(host, 'cisco','lab123')
        all_hosts.open() #open connections to all hosts
        interface_counters(all_hosts,host)
        interface_details(all_hosts,host)


if __name__ == '__main__':
    main()


        
