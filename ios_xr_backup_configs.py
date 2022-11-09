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



def backup_config(host):
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
            
        else:
            break
        connection_attempts = connection_attempts + 1
    generate_backup_file(con)


def generate_backup_file(con):
       get_hostname_time = con.send_command_timing(f'bash hostname').splitlines()
       get_hostname_time.reverse()
       time_hostname = (f'{get_hostname_time[0]} {get_hostname_time[1]}')
       formatting = str(time_hostname).replace(' ','-').replace(':','-').replace('.','-')
       copy = con.send_command_timing(f'copy running-config ftp://lab:cisco123@10.8.70.80/home/lab/devbox/x/backup/{formatting}.cfg vrf management')
       copy = con.send_command_timing("\n")
       copy = con.send_command_timing("\n")
       print(copy)
       print(f'File copied to x-devbox/home/lab/devbox/x/backup/ and filename is {formatting}.cfg')

def main():

    list_of_hosts = ['10.8.90.1','10.8.90.2','10.8.90.11','10.8.90.12', '10.8.90.13', '10.8.90.14', '10.8.90.15', '10.8.90.16','10.8.90.17','10.8.90.18'] 
    
    thread_list = []
    for host in list_of_hosts:
        t1 = threading.Thread(target=backup_config, args=(host,))
        thread_list.append(t1)
        print()
    
    for t in thread_list:
        t.start()
    
    for t in thread_list:
        t.join()
    
        

if __name__ == '__main__':
    main()
