from netmiko import ConnectHandler
import re
import argparse
import threading

    
def clear_logs_on_device(device):
    try:
        con = ConnectHandler(**device)
        hostname = con.find_prompt().split(':')[-1][:-1]
        print(f'Connected to {hostname}, clearing logs')
        clearing_logs = con.send_command_expect('clear logging', expect_string=r'\[confirm\]', read_timeout=120)
        clearing_logs += con.send_command_expect('y\n', expect_string=r'#', read_timeout=120)
        print(f'Logs cleared on {hostname}')
    except Exception as e:
        print(f'Failed to clear logs on device {device["ip"]}: {e}')



def collect_reload_data(ip,username,password,lc):
    
    device = {
        'device_type': 'cisco_xr',
        'ip': ip,
        'username': username,
        'password': password,
        'timeout': 5000,
        }
    con = ConnectHandler(**device)
    print(con.find_prompt())
    hostname = con.find_prompt().split(':')[-1][:-1]
    print(f'Connected to {hostname}, collecting card_reload_data') ##
    print(f'Executing card reload {hostname} LC {lc} connecting Leaf-2')
    card_reload = con.send_command(f'reload location {lc} noprompt' ,read_timeout=120)
    getting_timestamp = con.send_command(f'show logging | inc %PLATFORM-SHELFMGR-6-USER_OP',read_timeout=120) ##getting the card reload timestamp from the logs
    #timestamp_pattern = r'\b\w{3}\s\d{2}\s\d{2}:\d{2}:\d{2}\b'
    timestamp_pattern = r'\b[A-Za-z]{3} {1,2}\d{1,2} \d{2}:\d{2}:\d{2}\b'

    match_timestamp = re.search(timestamp_pattern, getting_timestamp)
    if match_timestamp:
        timestamp_str = match_timestamp.group()
        print("Matched timestamp:", timestamp_str)
        timestamp_str_dash = timestamp_str.replace(' ', '-').replace(':', '-')    
        with open(f'output_logs-sdk-{timestamp_str_dash}.txt', 'w') as file:
            collecting_shelf_mgr_logs = con.send_command(f'show shelfmgr history events detail location {lc}/CPU0 | b {timestamp_str}', read_timeout=120)
            file.write(collecting_shelf_mgr_logs + "Trigger Timestamp: " + "\n\n" + getting_timestamp + "\n\n" + card_reload + "\n\n")
            collecting_ifmgr_logs = con.send_command(f'show logging process ifmgr', read_timeout=120)
            print(collecting_ifmgr_logs)    
            file.write("Logs ifmgr interface down:\n")
            file.write(collecting_ifmgr_logs + "\n\n" + "Trigger Timestamp: "  + "\n\n"+ getting_timestamp + "\n\n" + card_reload + "\n\n")
            collecting_ipv6_connected_traces = con.send_command(f'show connected ipv6 trace location all | b {timestamp_str}', read_timeout=120)
            print(collecting_ipv6_connected_traces)    
            file.write("IPv6 Connected Traces:\n")
            file.write(collecting_ipv6_connected_traces + "Trigger Timestamp: " + "\n\n" + getting_timestamp + "\n\n" + card_reload + "\n\n")
            collecting_protected_notif = con.send_command(f'show protection-notif trace location all | b {timestamp_str}', read_timeout=120)
            print(collecting_protected_notif)    
            file.write("Protection Notifications:\n")
            file.write(collecting_protected_notif + "\n\n" + "Trigger Timestamp: "  + "\n\n" + getting_timestamp + "\n\n" + card_reload + "\n\n")
            collecting_bgp_trace = con.send_command(f'show bgp trace location all | b {timestamp_str}', read_timeout=260)
            print(collecting_bgp_trace)    
            file.write("BGP Traces:\n")
            file.write(collecting_bgp_trace + "\n\n" + "Trigger Timestamp: "  + "\n\n" + getting_timestamp + "\n\n" + card_reload + "\n\n")
            collecting_rib_trace = con.send_command(f'show rib ipv6 trace usec | include {timestamp_str}', read_timeout=120)
            print(collecting_rib_trace)
            file.write("RIB Traces:\n")
            file.write(collecting_rib_trace + "\n\n" + " Trigger Timestamp: "  + "\n\n" + getting_timestamp + "\n\n" + card_reload  + "\n\n")        


def collect_reload_data_leaf(ip2,username,password,lc):
    
    device = {
        'device_type': 'cisco_xr',
        'ip': ip2,
        'username': username,
        'password': password,
        'timeout': 5000,
        }
    
    
    con = ConnectHandler(**device)
    print(con.find_prompt())
    hostname = con.find_prompt().split(':')[-1][:-1]
    print(f'Connected to {hostname}, collecting card_reload_data') ##
    getting_timestamp = con.send_command(f'show logging process ifmgr',read_timeout=120) 
    print(getting_timestamp)
    #timestamp_pattern = r'\b\w{3}\s\d{2}\s\d{2}:\d{2}:\d{2}\b'
    timestamp_pattern = r'\b[A-Za-z]{3} {1,2}\d{1,2} \d{2}:\d{2}:\d{2}\b'
    match_timestamp = re.search(timestamp_pattern, getting_timestamp)
    if match_timestamp:    
        timestamp_str = match_timestamp.group()
        print("Matched timestamp:", timestamp_str)
        timestamp_str_dash = timestamp_str.replace(' ', '-').replace(':', '-')
        with open(f'output_logs-sdk-{timestamp_str_dash}-leaf.txt', 'w') as file:
            collecting_ifmgr_logs = con.send_command(f'show logging process ifmgr', read_timeout=120)
            print(collecting_ifmgr_logs)
            collecting_asic_errors = con.send_command(f'show asic-errors all detail location 0/rP0/CPU0 | b {timestamp_str}', read_timeout=120)
            print(collecting_asic_errors)
            file.write(collecting_ifmgr_logs + collecting_asic_errors + "Trigger Timestamp: " + "\n\n" + getting_timestamp + "\n\n")




def main():
    #### Argparse block ####
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", '-u', type=str, default="lab", help="Username. Default is lab")
    parser.add_argument("--password", '-p', type=str, default="lab123", help="Password. Default is lab123")
    parser.add_argument("--ip", '-i', type=str, help="IP of the host")
    parser.add_argument("--lc", '-l', type=str, default="0/1", help="LC to be reloaded")
    parser.add_argument("--ip2", '-ip2', type=str, help="IP of the remote host")
    
    arguments = parser.parse_args()
    
    # grabbing all variables from arguments
    username: str = arguments.username
    password: str = arguments.password
    ip: str = arguments.ip
    lc: str = arguments.lc
    ip2: str = arguments.ip2
    
    devices = [
    {
        'device_type': 'cisco_xr',
        'ip': ip,
        'username': username,
        'password': password,
        'timeout': 5000,
    },
    {
        'device_type': 'cisco_xr',
        'ip': ip2,
        'username': username,
        'password': password,
        'timeout': 5000,
    }
]

    threads = []
    for device in devices:
        thread = threading.Thread(target=clear_logs_on_device, args=(device,))
        threads.append(thread)
        thread.start()
    for thread in threads:      
        thread.join()

    print('All logs cleared on all devices.')

    collect_reload_data(ip,username,password,lc)
    collect_reload_data_leaf(ip2,username,password,lc)
    
    # usage = python card_reload_sre.py -i 2001:10:8:100::1 -ip2 2001:10:8:100::4 -u lab -p lab123 -l 0/1

if __name__ == "__main__":
    main()
    
    
    
    
