from datetime import datetime
from netmiko import ConnectHandler
import time
import os.path
import subprocess
import argparse



def pre_configure(con):
    """Adding pre-configuration, so we do not have to deal with timestamps matching"""
    configure_list = ['line console timestamp disable','line default timestamp disable']
    for config in configure_list:
        con.send_config_set([f'{config}'])
        con.commit()
        print(f"Pre configuration added {config}")
        time.sleep(5)
        cli = con.send_command(f'end', expect_string=r"#")    


def post_configure(con):
    """Removing pre-configuration after script run"""
    configure_list = ['no line console timestamp disable','no line default timestamp disable']
    for config in configure_list:
        con.send_config_set([f'{config}'])
        con.commit()
        print(f"Pre configuration removed {config}")
        time.sleep(5)
        cli = con.send_command(f'end', expect_string=r"#")

def bgp_before_trigger(con):
    """Collecting BGP snapshot before drain out to check the number of routes """
    command = con.send_command(f"show bgp ipv6 unicast summary")
    print(command)

    
def bgp_after_trigger(con):
        """Collecting BGP snapshot after drain out """
        command = con.send_command(f"show bgp ipv6 unicast summary")
        print(command)


def check_configured_rpl(con):
        """Checking what is the configured RPL per the neighbor groups and gathering the AS number from the BGP router process"""    
        command = con.send_command(f"show bgp neighbor-group all configuration  | inc \"neighbor-group|address-family|policy\" | ex \"default-originate\"")
        command_1 = con.send_command(f"show bgp ipv6 unicast  summary | inc number").split()[-1]
        as_number = command_1
        output_lines = command.split('\n')
        output_lines = [output_line.strip() for output_line in output_lines]
        """Creating empty list to add what is necessary after parsing"""
        neighbor_group_names = []
        rpl_names = []
        safi_names = [] 
        for line in output_lines:
            match = line.strip('[]').strip('policy').strip().split('neighbor-group')
            neighbor_group_rpl_safi = match[-1].split()
            """Checking if the length of the list is == 0 which means, there are no RPLs configured"""
            if len(neighbor_group_rpl_safi) == 0:
                print(f'There are no RPLs configured')
                exit(1)


            if len(neighbor_group_rpl_safi) == 1:
                """Checking if the length of the list is == 1 to gather the neighbor_group name"""
                neighbor_group = neighbor_group_rpl_safi
                neighbor_group_names.append(neighbor_group)

            if len(neighbor_group_rpl_safi) == 2:
                """Checking if the length of the list is == 2 to gather the rpl_name"""
                rpl_name = neighbor_group_rpl_safi
                rpl_names.append(rpl_name)
        
            if len(neighbor_group_rpl_safi) == 3:
                """Checking if the length of the list is == 3 and there is 'string' address inside to gather the rpl_name"""
                safi_name = neighbor_group_rpl_safi
                if 'address' in safi_name[0]:
                    safi_names.append(safi_name)
        
        return neighbor_group_names, rpl_names, safi_names, as_number
   

def remove_rpl_configs(con, neighbor_group_names, rpl_names, safi_names, as_number):

    """Filtering the required info via list List Comprehension  """

    neighbor_group_names_config = [neighbor[0] for neighbor in neighbor_group_names ] #take the first item in the list and loop though
    safi_v4_v6 = [safi_name[1] for safi_name in safi_names ] #take the 2nd item in the list and loop though
    safi_type = [safi_name[2] for safi_name in safi_names] #take the 3rd item in the list and loop though
    rpl_in_list = [rpl_name[0] for rpl_name in rpl_names if rpl_name[1] == "in"] ##take the first item in the list and loop though
    rpl_out_list = [rpl_name[0] for rpl_name in rpl_names if rpl_name[1] == "out"] #take the first item in the list and loop though

    remove_config_list_in = [] # create empty list to add the configs inbound 
    remove_config_list_out = [] # create empty list to add the configs outbound 

    for nei,safi,safi_t,rpl_in,rpl_out in zip(neighbor_group_names_config,safi_v4_v6,safi_type,rpl_in_list,rpl_out_list):
        """Loop through each list comprehension and use zip to 'attach' everything together"""
        remove_config_list_in.append(f"no router bgp {as_number} neighbor-group {nei} address-family {safi} {safi_t} route-policy {rpl_in} in")
        remove_config_list_out.append(f"no router bgp {as_number} neighbor-group {nei} address-family {safi} {safi_t} route-policy {rpl_out} out")

    for config_in,config_out in zip(remove_config_list_in,remove_config_list_out):

        print(config_in)
        con.send_config_set(f'configure terminal')
        con.send_config_set([f'{config_in}'])
        print(config_out)
        con.send_config_set([f'{config_out}'])
    con.commit()
    time.sleep(5)
    cli = con.send_command(f'end', expect_string="#")
    print(f'All current RPLs removed from Neighbors')

    return neighbor_group_names_config, safi_v4_v6, safi_type


def configure_drain_rpl(con,neighbor_group_names_config,as_number,safi_v4_v6,safi_type):
    '''Configure RPL drain'''
    configure_drain_in = []
    configure_drain_out = []

        #Same logic as before
    for nei,safi,safi_t in zip(neighbor_group_names_config,safi_v4_v6,safi_type):
        configure_drain_in.append(f"router bgp {as_number} neighbor-group {nei} address-family {safi} {safi_t} route-policy DRAIN in")
        configure_drain_out.append(f"router bgp {as_number} neighbor-group {nei} address-family {safi} {safi_t} route-policy DRAIN out")

    for config_in,config_out in zip(configure_drain_in,configure_drain_out):
        print(config_in)
        con.send_config_set(f'configure terminal')
        con.send_config_set([f'{config_in}'])
        print(config_out)
        con.send_config_set([f'{config_out}'])
    con.commit()
    time.sleep(5)
    cli = con.send_command(f'end', expect_string="#")
    print(f'All Neighbors have been DRAINED')




def main():

    ##Gathering details of how to connect to router ##
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", '-u', type=str, default="cisco", help="Username. Default is cisco")
    parser.add_argument("--password", '-p', type=str, default="lab123", help="Password. Default is lab123")
    parser.add_argument("--ip", '-i', type=str, help="IP of the host")


    arguments = parser.parse_args()
    #### End of Argparse block ####

    # grabbing all variables from arguments
    username: str = arguments.username
    password: str = arguments.password
    ip: str = arguments.ip


    device = {
        'device_type': 'cisco_xr',
        'ip': ip,
        'username': username,
        'password': password,
        'timeout': 120,
        'global_delay_factor': 5
        }
    
    connection_attempts = 0
    while connection_attempts < 100:
        time.sleep(0.5) 
        try:
            con = ConnectHandler(**device)
        except Exception as e:
            print(f'Attempting to connect {connection_attempts}')
            
        else:
            break
        connection_attempts = connection_attempts + 1
    
    bgp_before_trigger(con)
    pre_configure(con)
    neighbor_group_names, rpl_names, safi_names, as_number  = check_configured_rpl(con)
    neighbor_group_names_config, safi_v4_v6, safi_type = remove_rpl_configs(con, neighbor_group_names, rpl_names,safi_names,as_number)
    configure_drain_rpl(con,neighbor_group_names_config,as_number,safi_v4_v6,safi_type)
    post_configure(con)
    time.sleep(30)
    bgp_after_trigger(con)
    

if __name__ == '__main__':
    main()
