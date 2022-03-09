from datetime import datetime
import os
from netmiko import ConnectHandler
import logging
import time
from time import sleep, perf_counter
from threading import Thread
import os.path
import hashlib
import pysftp as sftp
import subprocess
import threading
import traceback
import argparse

def ssh_client(ip,username,password,log) -> None:
    device = {
        'device_type': 'cisco_xr',
        'ip': ip,
        'username': username,
        'password': password,
        'timeout': 120,
        'global_delay_factor': 5
    }
    try:
        con = ConnectHandler(**device)
    except Exception as e:
        log.info(f'#Exeption e={e}')
    else:
        hostname = con.find_prompt().split(':')[-1]
        log.info(f'Connected to {hostname}')
        return con

def check_input_file(filename):
    #check if the file exists
    if not os.path.exists(filename):
        print(f'File does not exist, {filename}')
        exit(1)
    else: 
        print(f'SMU source file exists')


def push_file_to_routers(ip,filename,just_filename):
    cnopts = sftp.CnOpts()
    cnopts.hostkeys = None
    s = sftp.Connection(host=ip, username='cisco', password='lab123', cnopts=cnopts)
    local_path = filename
#    print(local_path)
    remote_path = f"/misc/disk1/install_repo/{just_filename}"
#    print(remote_path)
    print(f'Uploading SMU {just_filename} to {ip}')
    s.put(local_path, remote_path)
    s.close()


def check_file_md5(filename,con,just_filename):
    #check file md5
    with open(filename, "rb") as f:
        bytes = f.read()
    readable_hash = hashlib.md5(bytes).hexdigest()    
    check_md5 = con.send_command(f'run md5sum /misc/disk1/install_repo/{just_filename}')
    split_md5_string = check_md5.split()
    md5_remote = split_md5_string[0]
    if readable_hash != md5_remote:
        print(f'MD5 does not match, {just_filename}')
        exit(2)
    else:
        print(f'MD5 check OK')


def install_add(con,just_filename):
    install_add_cli = con.send_command(f'install package add source /misc/disk1/install_repo/{just_filename}')
    print(install_add_cli)
    while True:
        check_complete_string = con.send_command(f'show install request | inc Current').split(':')
        check_complete_string_sliced = check_complete_string[-1]
        print(f'Current status: {check_complete_string_sliced}')

        if 'Await' in check_complete_string_sliced:
            break
        else:
            print(f'Install still running')

def install_apply(con):
    install_appy_cli = con.send_command(f'install apply noprompt')
    print(f'Install apply executed and going for reload CLI: {install_appy_cli}')
    time.sleep(120)

               
def install_commit(con,just_filename):
    try:
        install_commit = con.send_command(f'install commit')
        print(f'{install_commit}')
        time.sleep(60)
        check_complete_string = con.send_command(f'show install request  | inc State:').split(':')
        check_complete_string_sliced = check_complete_string[1]
        if 'Success' in check_complete_string_sliced:
            print(f'SMU {just_filename} installed & committed' )
            exit(10)
        else:
            print(f'SMU install did not complete due to {check_complete_string_sliced}')
    except Exception as e:
        print(e)
        pass
    
                
def main():
    ############################# INITIALIZATION #############################
    #### Argparse block ####
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", '-u', type=str, default="cisco", help="Username. Default is cisco")
    parser.add_argument("--password", '-p', type=str, default="lab123", help="Password. Default is lab123")
    parser.add_argument("--ip", '-i', type=str, help="IP of the host")
    parser.add_argument("--filename", '-f', type= str, help= "Filename should be provided as whole path")

    arguments = parser.parse_args()
    #### End of Argparse block ####

    # grabbing all variables from arguments
    username: str = arguments.username
    password: str = arguments.password
    ip: str = arguments.ip
    filename: str = arguments.filename
    
    
    # init logger
    formatting = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logger = logging.basicConfig(format=formatting, level=logging.INFO)
    log = logging.getLogger('Lindt SMU Install ')
    

    con = ssh_client(ip, username, password,log)
    hostname = con.find_prompt().split(':')[-1]
    log.info(f'Connected to {hostname}')
    split_filename = filename.split("/")
    just_filename = split_filename[-1]

    check_input_file(filename)
    push_file_to_routers(ip,filename,just_filename)
    check_file_md5(filename,con,just_filename)
    install_add(con,just_filename)
    install_apply(con)
    
    control_the_while_loop = False
    counter = 0
    while control_the_while_loop == False :
        try:
            con = ssh_client(ip,username,password,log)
            check_complete_string = con.send_command(f'show install request  | inc State:').split(':')
            check_complete_string_sliced = check_complete_string[1]
            if 'Success' in check_complete_string_sliced:
                control_the_while_loop = True
        except Exception as e:
            print(f'#Exception counter={counter} e={e}')

        time.sleep(1)
        if counter == 100:
            break
        counter += 1
        #print(f'Attempted to connect {counter}')

    
    install_commit(con,just_filename)
    
    exit()


if __name__ == '__main__':
    main()
