from datetime import datetime
start_time = datetime.now()
import os
import paramiko
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoTimeoutException
import logging
import time
from time import sleep, perf_counter
from threading import Thread
import os.path
import hashlib
import pysftp as sftp
import subprocess

#Author: Andre Pedro

def check_if_file_already_exists(con, filename, host):
    check_file = con.send_command(f'run ls -lsrt /misc/disk1/{filename}').split()
    filter_output = check_file[-1]
    remove_unwanted = filter_output.strip('/misc/disk1')
    if remove_unwanted == filename:
        print(f'file found in {host}, {filename }')
        return False
    else:
        print(f'file not found in {host} {filename}')
        return True


def check_if_upgrade_is_require(con,filename_no_iso):
    check_sh_ver = con.send_command(f'show ver | inc Label')
    split_sh_ver = check_sh_ver.split(':')
    final_output = split_sh_ver[1]

    if filename_no_iso not in final_output:
        print(f'Upgrade required, upgrading to {filename_no_iso}')
        return True
    else: 
        print(f'Upgrade not required')
        return False

def check_rw_file(con,filename):
    check_rw = con.send_command(f'run ls -lsrt /misc/disk1/{filename}').split()
    filter_rw = check_rw[1]
    if 'rw' not in filter_rw:
        print('File is not writtable')
        exit(4)


def giso_error_handling(con,filename,localpath):
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
    if readable_hash != md5_remote:
        print(f'MD5 does not match, {filename}')
        exit(2)
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
    # Check disk space:
    check_diskspace = con.send_command(f'run df /misc/disk1/')
    disk_space_split = check_diskspace.split(" ")
    disk_space_percentage = int(disk_space_split[-2].strip('%'))
    if disk_space_percentage > 90:
        print(f'Not enough disk space, currently on /misc/disk1/ {disk_space_percentage}% utilized, copy of {filename} to {host} will fail, aborting') 
        exit(5)    
        #need to check how to skip failed host only and move on


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

def remote_device_image_verify(con,filename_no_iso):
    check_sh_ver = con.send_command(f'show ver | inc Label')
    split_sh_ver = check_sh_ver.split(':')
    final_output = split_sh_ver[1]
    if filename_no_iso in final_output:
        print(f'Upgrade succesfully {filename_no_iso} ')
    else:
        print(f'Upgrade failed {final_output} is not the same as {filename_no_iso} ')
        pass
#        exit(6)


def upgrade_devices(host,con,filename):
    formatting = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logger = logging.basicConfig(format=formatting, level=logging.INFO)
    log = logging.getLogger('Golden ISO copy and Install')
    hostname = con.find_prompt().split(':')[-1]
    log.info(f'Connected to {hostname}')
    cli_clear_config = con.send_command(f'clear configuration inconsistency')
    print(f'clearing configuration inconsistency , {cli_clear_config}')
    time.sleep(30)
    cli_commit = con.send_command(f'install commit')
    print(f'Commiting software, {cli_commit}')
    time.sleep(30)
    cli = con.send_command(f'install replace /harddisk:/{filename} noprompt commit reload', expect_string=r"#")
    print(cli)


def main():
    formatting = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logger = logging.basicConfig(format=formatting, level=logging.INFO)
    log = logging.getLogger('Golden ISO copy and Install')
    
    list_of_hosts = ['10.8.70.12','10.8.70.13','10.8.70.14', '10.8.70.15', '10.8.70.16', '10.8.70.22', '10.8.70.23']
    #list_of_hosts = ['10.8.70.15']
    localpath = input(f'Enter Local Path along with file name: ')
    split_string = localpath.split("/")
    filename = split_string[-1]
    filename_no_iso = filename.strip('8000-goldenk9-x64- .iso')
    
    for host in list_of_hosts:
        control_the_while_loop = False
        while control_the_while_loop == False :
            if remote_device_check(host):
                control_the_while_loop = True
                time.sleep(1)

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
            except NetMikoTimeoutException:
                print(f'device is not reachable via ssh, Attempting connection {connection_attempts}')
            else:
                break

            connection_attempts = connection_attempts + 1

        check_disk_space(host,filename,con)   
        file_exists = check_if_file_already_exists(con, filename, host)
        upgrade_required = check_if_upgrade_is_require(con,filename_no_iso)

        if file_exists :
            push_file_to_routers(host,localpath,filename)
 
        if upgrade_required :

#            print(f'Upgrading to, {filename_no_iso} ')
#            push_file_to_routers(host,localpath,filename)
            giso_error_handling(con,filename,localpath)        
            check_rw_file(con,filename)
            upgrade_devices(host,con,filename)

        #t1 = threading.Thread(target=push_file_to_routers(host,localpath,filename))
        #t2 = threading.Thread(target=push_file_to_routers(host,localpath,filename))
        #t1.start()
        #t2.start()

    for x in list_of_hosts:
        control_the_while_loop = False
        while control_the_while_loop == False :
            if remote_device_check(x):
                control_the_while_loop = True
                time.sleep(5)


        device = {
            'device_type': 'cisco_xr',
            'ip': x,
            'username': 'cisco',
            'password': 'lab123',
            'timeout': 120,
            'global_delay_factor': 5
        }

        connection_attempts = 0
        while connection_attempts < 100:
            time.sleep(0.5)
            try:
                con = ConnectHandler(**device)
            except NetMikoTimeoutException:
                print(f'device is not reachable via ssh, Attempting connection {connection_attempts}')
            else:
                remote_device_image_verify(con,filename_no_iso)
                break
            connection_attempts = connection_attempts + 1


if __name__ == '__main__':
    main()

end_time = datetime.now()
delta_time = end_time - start_time


print()
print(f"---------------------------------------------------------")
print(f"#DEBUG: start_time = {start_time}")
print(f"#DEBUG:   end_time = {end_time}")
print(f"#DEBUG:  exec_time = {delta_time.days} days, {delta_time.seconds // 3600} hours, {delta_time.seconds // 60 % 60} mins, {delta_time.seconds % 60} secs")
print(f"---------------------------------------------------------")
print()
