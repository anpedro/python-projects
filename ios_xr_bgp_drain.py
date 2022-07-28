from datetime import datetime
from black import out
from netmiko import ConnectHandler
import time
from threading import Thread
import os.path
import subprocess
import argparse
from datetime import date
from difflib import Differ




def main():
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


    def pre_configure(con):
        configure_list = ['line console timestamp disable','line default timestamp disable']
        for config in configure_list:
            con.send_config_set([f'{config}'])
            con.commit()
            print(f"Pre configuration added {config}")
            time.sleep(5)
            cli = con.send_command(f'end', expect_string=r"#")    


    def post_configure(con):
        configure_list = ['no line console timestamp disable','no line default timestamp disable']
        for config in configure_list:
            con.send_config_set([f'{config}'])
            con.commit()
            print(f"Pre configuration removed {config}")
            time.sleep(5)
            cli = con.send_command(f'end', expect_string=r"#")

    def bgp_before_trigger(con):
        """Collecting BGP snapshot before drain out """
        command = con.send_command(f"show bgp ipv6 unicast summary")
        print(command)

    
    def bgp_after_trigger(con):
        """Collecting BGP snapshot before drain out """
        command = con.send_command(f"show bgp ipv6 unicast summary")
        print(command)


    def check_configured_rpl(con):
        """Checking what is the configured RPL in the neighbor groups"""    
        command = con.send_command(f"show bgp neighbor-group all configuration  | inc \"neighbor-group|address-family|policy\" | ex \"default-originate\"")
        command_1 = con.send_command(f"show bgp summary  | inc number").split()[-1]
        as_number = command_1

        output_lines = command.split('\n')
        output_lines = [output_line.strip() for output_line in output_lines]

        neighbor_group_names = []
        rpl_names = []
        safi_names = [] 
        for line in output_lines:
           match = line.strip('[]').strip('policy').strip().split('neighbor-group')
           neighbor_group_rpl_safi = match[-1].split()
           print(neighbor_group_rpl_safi)

           if len(neighbor_group_rpl_safi) == 0:
            print(f'There are no RPLs configured')
            exit(1)

         
           if len(neighbor_group_rpl_safi) == 1:
            neighbor_group = neighbor_group_rpl_safi
            neighbor_group_names.append(neighbor_group)

           if len(neighbor_group_rpl_safi) == 2:
            rpl_name = neighbor_group_rpl_safi
            rpl_names.append(rpl_name)
        
           if len(neighbor_group_rpl_safi) == 3:
                safi_name = neighbor_group_rpl_safi
                if 'address' in safi_name[0]:
                    safi_names.append(safi_name)
        
        print(neighbor_group_names)
        print(rpl_names)

        return neighbor_group_names, rpl_names, safi_names, as_number
   

    def remove_rpl_configs(con, neighbor_group_names, rpl_names, safi_names, as_number):
        """Remove old RPL and apply drain"""
        neighbor_group_names_config = [neighbor[0] for neighbor in neighbor_group_names ]
        safi_v4_v6 = [safi_name[1] for safi_name in safi_names ]        
        safi_type = [safi_name[2] for safi_name in safi_names]
        rpl_in_list = [rpl_name[0] for rpl_name in rpl_names if rpl_name[1] == "in"]
        rpl_out_list = [rpl_name[0] for rpl_name in rpl_names if rpl_name[1] == "out"]

        remove_config_list_in = []
        remove_config_list_out = []
        for nei,safi,safi_t,rpl_in,rpl_out in zip(neighbor_group_names_config,safi_v4_v6,safi_type,rpl_in_list,rpl_out_list):
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
