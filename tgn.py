from netmiko import ConnectHandler
import time
from time import sleep, perf_counter
from threading import Thread
import threading
import re
import json
import argparse

def tgn(host):
    device = {
        
        'device_type': 'cisco_xr',
        'ip': host,
        'username': 'lab',
        'password': 'lab123',
        'timeout': 120,
        'global_delay_factor': 5
        }
    connection_attempts = 0
    while connection_attempts < 100:
        time.sleep(0.5) 
        try:
            con = ConnectHandler(**device)
            get_hostname = con.send_command_timing(f'bash hostname').splitlines()
            print(f'Connected to {get_hostname[-1]}')
        except Exception as e:
            print(f'Attempting to connect to {connection_attempts}')
            
        else:
            break
        connection_attempts = connection_attempts + 1

    
    raw_lldp_output = show_lldp_nei(con, host)
    lldp_data = collect_lldp(con, host)
    lldp_data = json.dumps(lldp_data, indent=4)
    all_data = f"{raw_lldp_output}\n{lldp_data}" 
    
    with open(f'output{host}.json', 'w') as file:
        file.write(all_data)

def collect_lldp(con, host):
    """Function to collect lldp neighbors up and its bia"""
    check_lldp = f'show lldp neighbors | inc FourHu '
    output = con.send_command(f'{check_lldp}', read_timeout=600, expect_string=r"#").strip()

    if len(output) == 0:
        print(f'There are no interfaces up')
    else:
        output_list = output.strip().split('\n')
        pattern = re.compile(r'([A-Z])\w+/././..') #<-- regex to match FourHundred interfaces
        intf_matched = []
        for line in output_list:
            string_to_match = line
            match_object = pattern.search(string_to_match)
            if match_object:
                matched_string = match_object.group()
                intf_matched.append(matched_string)
        
        data = []
        for interface in intf_matched:
            output_v6_address = con.send_command(f'show run interface {interface} | inc ipv6 address', read_timeout=600, expect_string=r"#").strip()
            ipv6_pattern = r'ipv6 address\s+([0-9a-fA-F:]+(?:/\d+)?)'#<-- regex to match only ipv6 interfaces addresses
            ipv6_addresses = re.findall(ipv6_pattern, output_v6_address)
            
            output_bia_address = con.send_command(f'show interface {interface} | inc bia', read_timeout=600, expect_string=r"#").strip()           
            mac_pattern = r'address is ([0-9a-fA-F\.]+) \(bia' #<-- regex to match only mac interfaces addresses
            mac_addresses = re.findall(mac_pattern, output_bia_address)

            print(f"IPv6 addresses for {interface}:")
            for address in ipv6_addresses:
                print(address)
            print(f"Mac addresses for {interface}:")
            for mac in mac_addresses:
                print(mac)

            data.append({
                "int": interface,
                "addr": address,
                "mac_addr": mac
                })
                
        return data



def show_lldp_nei(con, host):
        check_lldp_full = f'show lldp neighbors'
        output_lldp = con.send_command(f'{check_lldp_full}', read_timeout=600, expect_string=r"#").strip()
        print(output_lldp)
        
        return output_lldp
        

        
def main():

    #### Argparse block ####
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", '-u', type=str,default="lab",  help="Username. Default is cisco")
    parser.add_argument("--password", '-p', type=str,default="lab123", help="Password. Default is lab123")
    parser.add_argument("--sip",       '-sip', type=str, help="IP of the host")
    parser.add_argument("--dip",       '-dip', type=str, help="IP of the host")
    
    arguments = parser.parse_args()
    #### End of Argparse block ####

    # grabbing all variables from arguments
    username: str = arguments.username
    password: str = arguments.password
    sip: str = arguments.sip
    dip: str = arguments.dip
    
    

    list_of_hosts = [f'{sip}', f'{dip}'] 
    thread_list = []
    for host in list_of_hosts:
        t1 = threading.Thread(target=tgn, args=(host,))
        thread_list.append(t1)
        print()
    
    for t in thread_list:
        t.start()
    
    for t in thread_list:
        t.join()
    
        

if __name__ == '__main__':
    main()
