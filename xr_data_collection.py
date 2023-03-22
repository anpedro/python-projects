from datetime import datetime
import os
from netmiko import ConnectHandler
import time
from time import sleep, perf_counter
from threading import Thread
import os.path
import hashlib
import pysftp as sftp
import subprocess
import threading
import traceback


def copy_files(host):
    device = {
        'device_type': 'cisco_xr',
        'ip': host,
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
            get_hostname = con.send_command_timing(f'bash hostname').splitlines()
            print(f'Connected to {get_hostname[-1]}')
        except Exception as e:
            print(f'Attempting to connect to {connection_attempts}')
            connection_attempts = connection_attempts + 1

        copy_show_techs(con,host)
        copy_corefile(con,host)
        logging_file(con,host)
        break



def copy_show_techs(con,host):
    """Function to collect any show techs from the box """
    show_techs = [f'show tech qos pi', 'show tech qos platform']
    for line in show_techs:
        print(f'Collecting {line}')
        output = con.send_command(f'{line}',read_timeout=600,expect_string=r"#").strip('\n')
        print(f'Collection {line} completed')
        ls_files = con.send_command(f'run ls -lsrt /misc/disk1/showtech/',read_timeout=600,expect_string=r"#").strip('\n').split(' ')
        filename =(ls_files[-1])
        cnopts = sftp.CnOpts()
        cnopts.hostkeys = None
        s = sftp.Connection(host=host, username='cisco', password='lab123', cnopts=cnopts)
        print(f'Copying {filename} to local directory')
        s.get(f'/misc/disk1/showtech/{filename}', preserve_mtime=True)

def copy_corefile(con,host):
    """Function to collect latest core file """
    corefiles = [f'dumpcore running bgp']
    for line in corefiles:
        print(f'Dumping {line}')
        output = con.send_command(f'{line}',read_timeout=600,expect_string=r"#").strip('\n')
        print(f'Collection {line} completed')
        ls_files = con.send_command(f'run ls -lsrt /misc/disk1/*.core.gz',read_timeout=600,expect_string=r"#").strip('\n').split(' ')
        filename =(ls_files[-1])
        print(filename)
        cnopts = sftp.CnOpts()
        cnopts.hostkeys = None
        s = sftp.Connection(host=host, username='cisco', password='lab123', cnopts=cnopts)
        print(f'Copying {filename} to local directory')
        s.get(f'{filename}', preserve_mtime=True)


def logging_file(con,host):
    """Function to collect latest show logging """
    get_hostname_time = con.send_command_timing(f'bash hostname').splitlines()
    get_hostname_time.reverse()
    time_hostname = (f'{get_hostname_time[0]} {get_hostname_time[1]}')
    formatting = str(time_hostname).replace(' ','-').replace(':','-').replace('.','-')
    sh_logging = f'show logging | file harddisk:show_logging_{formatting}'
    print(f'Collecting {sh_logging}')
    output = con.send_command(f'{sh_logging}',read_timeout=600,expect_string=r"#").strip('\n')
    print(f'Collection {sh_logging} completed')
    ls_files = con.send_command(f'run ls -lsrt /misc/disk1/*show_logging*',read_timeout=600,expect_string=r"#").strip('\n').split(' ')
    filename =(ls_files[-1])
    print(filename)
    cnopts = sftp.CnOpts()
    cnopts.hostkeys = None
    s = sftp.Connection(host=host, username='cisco', password='lab123', cnopts=cnopts)
    print(f'Copying {filename} to local directory')
    s.get(f'{filename}', preserve_mtime=True)
    

def main():

    list_of_hosts = ['10.8.90.98'] 
    
    thread_list = []
    for host in list_of_hosts:
        t1 = threading.Thread(target=copy_files, args=(host,))
        thread_list.append(t1)
        print()
    
    for t in thread_list:
        t.start()
    
    for t in thread_list:
        t.join()
    
        

if __name__ == '__main__':
    main()
