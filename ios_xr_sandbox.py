##Still under construction###



import time
from netmiko import ConnectHandler
import argparse
from paramiko import SSHClient
import paramiko
import traceback



def show_sandbox_detail(con):
    """Checking if show_sandbox_detail is operational"""
    command = con.send_command(f"show sandbox detail | inc \"state|State\"").split()
    status = command[3]
    config = command[6]
    state = command[-1]

    if 'Enabled' in status and 'Activated' in config and 'Running' in state:
        print('show sandbox detail is verified')
        return True
    else:
        print('show sandbox detail is not working')
        return False
        

def show_sandbox_info(con):
    """Checking if show_sandbox_info is operational"""
    command = con.send_command(f"show sandbox info | inc \"state|Image\"").split()
    image = command[1]
    config = command[4]
    state = command[-1]

    if 'Activated' in config and 'Running' in state:
        print(f'Image running is {image} and show sandbox info is verified')
        return True
    else:
        print(f'show sandbox info is not working')
        return False

def show_sandbox_services(con):
    """Checking sandbox services are running"""
    ##check with Suresh what needs to be parsed###

    command = con.send_command(f"show sandbox services")


def ssh_to_sandbox(ip,username,password):
    """'ssh cisco@2001:10:8:90::111 bash docker exec -it sandbox /bin/bash'       """    
    try:
        command = "bash docker exec -it sandbox /bin/bash ls"
        #command = 'run ls /misc/disk1/'
        port = 22
        ssh = SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port, username, password)
        stdin, stdout, stderr = ssh.exec_command(command)
        lines = stdout.readlines()
        print(lines)


    except Exception as e:
            print(f'Exception is {e}')
    


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

#    show_sandbox_detail(con)
#    show_sandbox_info(con)
    ssh_to_sandbox(ip,username,password)
    


if __name__ == '__main__':
    main()
