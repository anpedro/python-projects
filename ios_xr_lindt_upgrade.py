from audioop import add
from datetime import datetime
import os
from netmiko import ConnectHandler
import paramiko
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

#Author: Andre Pedro


def host_handler(host,filename,filename_no_iso,localpath):
    device = {
        'device_type': 'cisco_xr',
        'ip': host,
        'username': 'cisco',
        'password': 'lab123',
        'timeout': 120,
        'global_delay_factor': 10
        }
    connection_attempts = 0
    while connection_attempts < 100:
        time.sleep(0.5) 
        try:
            con = ConnectHandler(**device)
        except Exception as e:
            #print(f'Attempting to connect {connection_attempts} error is {e}')
            print(f'Attempting to connect {connection_attempts}')
            
        else:
            break
        connection_attempts = connection_attempts + 1

    pre_configure(host,con)
    check_disk_space(host,filename,con)
    file_exists = check_if_file_already_exists(con, filename, host)
    upgrade_required = check_if_upgrade_is_require(con,filename_no_iso,host)
    if file_exists : #True means file needs to copied to the router and upgrade will happen #
        push_file_to_routers(host,localpath,filename)
    
    if upgrade_required : #True means upgrade is required 
        giso_error_handling(con,filename,localpath,host)        
        check_rw_file(con,filename)
        upgrade_devices(host,con,filename)
    
    
    ### check if device is still reachable up 
    control_the_while_loop = False
    while control_the_while_loop == False :
        if remote_device_check(host):
            control_the_while_loop = True
            time.sleep(5)


    connection_attempts = 0
    while connection_attempts < 100:
        time.sleep(0.5)
        try:
            con = ConnectHandler(**device)
        except Exception as e:
            #print(e)
            print(f'Attempting to connect {connection_attempts}')

        else:
            check_if_install_still_running(device,filename_no_iso,host)
            break
        connection_attempts = connection_attempts + 1

      
def check_if_install_still_running(device,filename_no_iso,host):
    control = False
    connection_attempts = 0
    while control == False:
        check_install_filtered = ''

        try:
            con = ConnectHandler(**device)
        except Exception as e:
            #print(e)
            print(f'Attempting to connect {connection_attempts}')

        else:
            check_install = con.send_command(f'show install request  | inc State:').split(':')
            check_install_filtered = check_install[1]
        if "Success since" in check_install_filtered:
            remote_device_image_verify(con,filename_no_iso,host) #check this #
            control = True
        else:
            time.sleep(30)
            connection_attempts = connection_attempts + 1
            print(f'Upgrade still in progress ...{host}....attempt {connection_attempts}')
      
#

def check_if_file_already_exists(con, filename, host):
    check_file = con.send_command(f'run ls -lsrt /misc/disk1/{filename}').split()
    filter_output = check_file[-1]
    remove_unwanted = filter_output.strip('/misc/disk1')
    if remove_unwanted == filename:
        print(f'file {filename } found in {host} ')
        return False
    else:
        print(f'file {filename } not found in {host} ')
        return True


def check_if_upgrade_is_require(con,filename_no_iso,host):
    check_sh_ver = con.send_command(f'show ver | inc Label')
    split_sh_ver = check_sh_ver.split(':')
    final_output = split_sh_ver[1]

    if filename_no_iso not in final_output:
        print(f'Upgrade required, upgrading to {filename_no_iso} in {host}')
        return True
    else: 
        print(f'Upgrade not required in {host}')
        return False

def check_rw_file(con,filename):
    check_rw = con.send_command(f'run ls -lsrt /misc/disk1/{filename}').split()
    filter_rw = check_rw[1]
    if 'rw' not in filter_rw:
        print('File is not writtable')
        exit(4)


def giso_error_handling(con,filename,localpath,host):
    """This function will perform bunch of GISO handling"""
    #check if the file exists
    if not os.path.exists(localpath):
        print(f'File does not exist, {localpath}')
        exit(1)
    #check the md5 from local and remote
    with open(localpath, "rb") as f:
        bytes = f.read()
        readable_hash = hashlib.md5(bytes).hexdigest()
    check_md5 = con.send_command(f'run md5sum /misc/disk1/{filename}')
    split_md5_string = check_md5.split()
    md5_remote = split_md5_string[0]
    print(f"Local MD5 is {readable_hash} / remote MD5 is  {md5_remote}")
    if readable_hash != md5_remote:
        delete_remote_iso = con.send_command(f'run rm -rf /misc/disk1/{filename}')
        print(f'MD5 does not match,host {host}, filename {filename}, deleting remote file and resending {delete_remote_iso}')
        push_file_to_routers(host,localpath,filename)

    #check if the local file is an iso:
    cmd = f"file {localpath}"
    cmd_list = cmd.split() #change string to list so the subprocess popen works.. it takes a list as argument
    temp = subprocess.Popen(cmd_list, stdout = subprocess.PIPE).communicate() # execute the command in linux
    new_temp = temp[0] #filter the tuple taking 1st position
    final_temp = new_temp.decode("utf-8") #convert from bytes to regular string 
    if "ISO" not in final_temp:
        print(f'Not an ISO file')
        exit(3)
    


def check_disk_space(host,filename,con):
    check_diskspace = con.send_command(f'run df /misc/disk1/')
    disk_space_split = check_diskspace.split(" ")
    disk_space_percentage = int(disk_space_split[-2].strip('%'))
    if disk_space_percentage > 90:
        print(f'Not enough disk space, currently on /misc/disk1/ {disk_space_percentage}% utilized, deleting .iso & core.gz files older than 10 days') 
        cmd = f'run find /misc/disk1 -type f -mtime -10 \\( -name "*.core.gz" -o -name "*.core.txt" -o -name "*.iso" \\)'
        list_old_files = con.send_command(cmd)
        print(f' The following files will be deleted to free up disk space {list_old_files} & {host}')
        cmd = f'run find /misc/disk1 -type f -mtime -10 \\( -name "*.core.gz" -o -name "*.core.txt" -o -name "*.iso" \\) -delete'
        find_old_files = con.send_command(cmd)
        print(find_old_files) 


def push_file_to_routers(host,localpath,filename):
    cnopts = sftp.CnOpts()
    cnopts.hostkeys = None
    s = sftp.Connection(host=host, username='cisco', password='lab123', cnopts=cnopts)
    local_path = localpath
    remote_path = f"/misc/disk1/{filename}"
    print(f'Uploading {filename} to {host}')
    s.put(local_path, remote_path)
    s.close()


def remote_device_check(host):

    cmd = f"ping {host} -c 2"
    response = os.popen(f"{cmd}").read().split(",")
    loss = response[2]
    if "0% packet loss" not in loss:
        print(f'host not reachable {host}')
        return False
    else:
        print(f'host is reachable, {host}')
        return True

def remote_device_image_verify(con,filename_no_iso,host):
    check_sh_ver = con.send_command(f'show ver | inc Label')
    split_sh_ver = check_sh_ver.split(':')
    final_output = split_sh_ver[1]
    if filename_no_iso in final_output:
        print(f'Upgrade succesfully {filename_no_iso} at {host} ')
    else:
        print(f'Upgrade failed {final_output} is not the same as {filename_no_iso} at {host} ')
        pass
#        exit(6)


def upgrade_devices(host,con,filename):
    formatting = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    cli_clear_config = con.send_command(f'clear configuration inconsistency')
    print(f'clearing configuration inconsistency  {cli_clear_config} at {host}')
    time.sleep(30)
    cli_clear_install_previous = con.send_command(f'install package abort latest')
    print(f'Aborting latest install operation{cli_clear_install_previous} at {host}')
    time.sleep(180)
    cli_commit = con.send_command(f'install commit')
    print(f'Commiting software, {cli_commit} at {host}')
    time.sleep(30)
    cli = con.send_command(f'install replace /harddisk:/{filename} noprompt commit reload', expect_string=r"#")
    print(f' {cli} at {host}')

def pre_configure(host,con):
    configure_list = ['line console timestamp disable','line default timestamp disable']
    for config in configure_list:
        con.send_config_set([f'{config}'])
        con.commit()
        print(f"Pre configuration added {config} {host}")
        time.sleep(5)
        cli = con.send_command(f'end', expect_string=r"#")
        

def main():

    
    list_of_hosts = ['10.8.70.11','10.8.70.12','10.8.70.13','10.8.70.14', '10.8.70.15', '10.8.70.16', '10.8.70.22', '10.8.70.23'] 
    localpath = input(f'Enter Local Path along with file name: ')
    split_string = localpath.split("/")
    filename = split_string[-1]
    filename_no_iso = filename.strip('8000-goldenk9-x64- .iso')
    
    thread_list = []
    for host in list_of_hosts:
        t1 = threading.Thread(target=host_handler, args=(host,filename,filename_no_iso,localpath,))
        thread_list.append(t1)
        print()
    
    for t in thread_list:
        t.start()
    
    for t in thread_list:
        t.join()
    
        

if __name__ == '__main__':
    main()
