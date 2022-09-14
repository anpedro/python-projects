from os import remove
import time
from traceback import print_tb
from netmiko import ConnectHandler
import argparse
from paramiko import SSHClient
import paramiko
from scp import SCPClient
import pysftp as sftp
import re
import itertools




def check_sandbox_configured(con):
    '''Checking if sandbox configuration is present, otherwise bail out'''
    command = con.send_command(f"show run sandbox ").strip()
    print(command)
    if 'No such' in command:
        print(f'Sandbox is not configured')
        exit(1)
    else:
        pass


def show_sandbox_detail(con):
    """Checking if show_sandbox_detail is operational"""
    command = con.send_command(f"show sandbox detail | inc \"state|State\"").split()
    state = command[-1]
    if 'Running' in state:
        print('show sandbox detail CLI is verified')
        return True
    else:
        print('show sandbox detail CLI is not working')
        return False
    
        

def show_sandbox_info(con):
    """Checking if show_sandbox_info is operational"""
    command = con.send_command(f"show sandbox info | inc \"state|Image\"").split()
    image = command[6]
    state = command[-1]

    if 'Running' in state:
        print(f'show sandbox info CLI is verified and Image running is {image}')
        return True
    else:
        print(f'show sandbox info CLI is not working')
        return False

def show_sandbox_services(con):
    """Checking sandbox services are running"""
    command = con.send_command(f"show sandbox services | inc systemd-journald.service ").split()
    if len(command) >= 11: ## We are just parsing journald.service here as an example and to make sure the command has an output and matching on the list #11 list len.    
        print('show sandbox services CLI is working')
        return True
    else: 
        print('show sandbox services CLI is NOT working')
        return False

    

def ssh_to_sandbox(ip,username,password):
    """'ssh cisco@2001:10:8:90::111 bash docker exec -it sandbox /bin/bash'       """    
    try:
        #ask if there will be any case where the sandbox will be accessible via inband##
        command = "bash sandbox -c ls"
        port = 22
        ssh = SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port, username, password)
        stdin, stdout, stderr = ssh.exec_command(command)
        lines = stdout.readlines()
        if 'Error response' in lines[3]:
            print('Unable to remote connect to Sandbox')
            return False
        else:
            print('Remote connection to Sandbox Container is working')   
            return True     
    except Exception as e:
            print(f'Exception is {e}')


def copy_file_sandbox(ip,username,password):
    '''copy file to sandbox and make sure file is available in the container'''
    try:
        cnopts = sftp.CnOpts()
        cnopts.hostkeys = None
        s = sftp.Connection(host=ip, username=username, password=password, cnopts=cnopts)
        local_path = '/home/lab/.ssh/id_rsa'
        remote_path = "/misc/disk1/sandbox/id_rsa"
        print(f'Copying {local_path} to sandbox')
        s.put(local_path, remote_path)
        s.close()
    
    except Exception as e:
            print(f'Exception is {e}')


def verify_copied_file(ip,username,password):
    '''verify if the copied file can be accessible from the sandbox'''
    try:
        command = "bash sandbox -c ls /host/id_rsa"
        port = 22
        ssh = SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port, username, password)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.readlines()
        if 'id_rsa' in output[3] and 'cannot' in output[3]:
            print(f'File is not accessible from sandbox')
            return False
        else:
            print(f'File is accessible from sandbox')
            return True
            
    except Exception as e:
        print(f'Exception is {e}')

def sandbox_restart(con):
    '''Verify if sandbox container can be restarted (configuring and un-configuring) '''
    con.send_config_set([f'no sandbox enable'])
    print(f'disabling sandbox container(stopping) and waiting 5 seconds')
    con.commit()
    con.send_command(f'end', expect_string=r"#")
    time.sleep(5)
    command = con.send_command(f"show sandbox detail")
    if 'Sandbox is not Enabled' in command:
        print('enabling sandbox container(starting) and waiting 10 seconds')
        con.send_config_set([f'sandbox enable'])
        con.commit()
        con.send_command(f'end', expect_string=r"#")
    time.sleep(10)
    '''Checking sandbox detail after the re-configuration/reload'''
    command = con.send_command(f"show sandbox detail | inc \"state|State\"").split()
    state = command[-1]
    if 'Running' in state:
        command_1 = con.send_command(f"bash docker ps -a | grep sandbox").split()
        second = command_1[13]
        exact_seconds = command_1[12]
        state = command_1[11]
        if 'seconds' in second and 'Up' in state:
            print(f'sandbox process restart works and container is {state} for {exact_seconds}  {second}')
        return True
    else:
        print('sandbox process restart is NOT working')
        return False
    
def verify_tcpdump_sandbox(ip,username,password):
    '''Check ability to run tcpdump within the sandbox container'''
    try:
        results = []
        cli = ['bash sandbox -c rm -rf /tmp/tcpdump-test-case.pcap', 'bash sandbox -c ip netns exec vrf-management /usr/sbin/tcpdump port 22 -i Mg0_RP0_CPU0_0 -c 3 -w /tmp/tcpdump-test-case.pcap \n', 'bash sandbox -c ls -lsrt /tmp/tcpdump-test-case.pcap' ]
        for output in cli:
            port = 22
            ssh = SSHClient()
            ssh.load_system_host_keys()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, port, username, password)
            stdin, stdout, stderr = ssh.exec_command(output)
            output = stdout.readlines()
            results.append(output)

        for result in results:  ## looping through results to get the sweet string##
            if 'tcpdump-test-case' in result[3]:
                print(f'tcpdump originated from sandbox works')
                print(f'{result[3]}')

    except Exception as e:
        print(f'Exception is {e}')
    
    
def verify_package_install_sandbox(ip,username,password):
    '''Verify if RPM package can be installed in the sandbox'''
    try:
        ##copying target RPM to the harddisk###
        cnopts = sftp.CnOpts()
        cnopts.hostkeys = None
        s = sftp.Connection(host=ip, username=username, password=password, cnopts=cnopts)
        local_path = '/home/lab/chef-17.10.3-1.el7.x86_64.rpm'
        remote_path = "/misc/disk1/sandbox/chef-17.10.3-1.el7.x86_64.rpm"
        print(f'Copying {local_path} to sandbox')
        s.put(local_path, remote_path)
        s.close()

        ##installing copied RPM###

        cli = ['bash sandbox -c rpm -ivh /host/chef-17.10.3-1.el7.x86_64.rpm','bash sandbox -c rpm -qa | grep chef ' ]
        results = []
        for output in cli:
            port = 22
            ssh = SSHClient()
            ssh.load_system_host_keys()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, port, username, password)
            stdin, stdout, stderr = ssh.exec_command(output)
            output = stdout.readlines()
            results.append(output)
        if 'chef' in output[3] or 'already installed' in output[3]:
            print(f'RPM install inside sandbox works {output[3]}')
    
    except Exception as e:
        print(f'Exception is {e}')
        print(f'Sandbox RPM install failed')

def verify_iperf(ip,username,password):
    try:
        '''Verify if IPERF works via management and default vrf'''
        results = []
        cli = ['bash sandbox -c  ip netns exec vrf-default  /usr/bin/iperf3 -c 2001:10:80:70::80 -f K', 'bash sandbox -c  ip netns exec vrf-management /usr/bin/iperf3 -c 2001:10:8:90::119 -f K']
        for output in cli:
            port = 22
            ssh = SSHClient()
            ssh.load_system_host_keys()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, port, username, password)
            print(f'Verifying IPERF3 via mgmt & default')
            stdin, stdout, stderr = ssh.exec_command(output)
            output = stdout.readlines()
            if 'unable to connect' in output[3]: ## checking if iperf is running and able to connect to server
                print(output[3])
            else:
                results.append(output)

        for result in results:
            if 'Done' in result[21]:
                print(f'{result[3]}')
                print(f'{result[21]}')
    
    except Exception as e:
        print(f'Exception is {e}')


def verify_grpc(ip,username,password):

    '''Verify if GRPC capabilities work originated from sandbox'''
    try:
    ##copying gnmic to sandbox accessible folder###
        cnopts = sftp.CnOpts()
        cnopts.hostkeys = None
        s = sftp.Connection(host=ip, username=username, password=password, cnopts=cnopts)
        local_path = '/home/lab/gnmic'
        remote_path = "/misc/disk1/sandbox/gnmic"
        print(f'Copying {local_path} to sandbox')
        s.put(local_path, remote_path)
        s.close()
        cli = f"bash sandbox -c ip netns exec vrf-management /host/gnmic capabilities --skip-verify --address  {ip}  --port 57400  -u {username} --password {password}"
        port = 22
        ssh = SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port, username, password)
        stdin, stdout, stderr = ssh.exec_command(cli)
        output = stdout.readlines()
        if 'gNMI version' in output[3]:
            print(f'gNMI capabilities collected from sandbox successfully')

    except Exception as e:
        print(f'Exception is {e}')
        print(f'gNMI capabilities NOT collected from sandbox')


def verify_namespaces_vrf(ip,username,password):
    '''verify namespaces/vrfs were replicated into the container'''
    try:
        port = 22
        ssh = SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port, username, password)

        results = []
        results_1 = []
        cli = ['show run formal vrf  | ex "address"']
        cli_1 = ['bash sandbox -c ip netns']

        for output in cli: ## how do I accomplish this with list compreehsion?
            stdin, stdout, stderr = ssh.exec_command(output)
            output = stdout.readlines()
            results.append(output)
        
        for output in cli_1:
            stdin, stdout, stderr = ssh.exec_command(output)
            output = stdout.readlines()
            results_1.append(output)


        for xrcli, bashcli in zip(results,results_1):
            ''' going through the difference between what is configured in xr vs sandbox  '''
            remove_date_xr_cli = (xrcli[3::])
            remove_date_bashcli =(bashcli[3::])
            result = [line.strip().replace(' ','-') for line in remove_date_xr_cli]
            result_1 = [line.rstrip() for line in remove_date_bashcli]
            trimming_xrcli = result[:-1]
            trimming_bashcli = result_1[:-5]

            if len(trimming_xrcli) == len(trimming_bashcli):
                print(f'VRFs from XR replicated to namespaces in linux(sandbox) correctly, VRF names are:  \n {trimming_xrcli}')

    except Exception as e:
        print(f'Exception is {e}')
        print(f'VRFs from XR replicated to namespaces in linux(sandbox) failed')


def verify_int_replication(con,ip,username,password):
    '''Verify if interfaces created in XR are replicated to sandbox'''        
    #defining 3 empty lists for xr,vrf and vrf-default collection#
    iosxr_interfaces = []
    vrfs = []
    vrf_default =  []
    
    xr_interfaces = con.send_command(f"show ipv6 vrf all interface  brief | utility egrep -E 'GigE|Mgm'").strip().split() ### Acquiring interfaces in XR (FourHun/Hun/Mgmt)
    for xr_interface in xr_interfaces:
        if 'GigE' in xr_interface and not '.' in xr_interface:
            iosxr_interfaces.append(xr_interface)
        elif 'Mg' in xr_interface:
            iosxr_interfaces.append(xr_interface)


    namespaces = con.send_command(f"bash sandbox -c ip netns").split() #gathering namespaces / vrfs in linux#
    only_vrfs = namespaces[5::]
    del only_vrfs[-4:]

    for output in only_vrfs: # counting number of interfaces per vrf/namespace and add to the empty list##
        cli = con.send_command(f"bash sandbox -c ip netns exec {output} ip link | grep -E 'FH|Mg'").split()
        cli = [segment for segment in cli if segment.startswith('FH0_') or segment.startswith('Mg') or segment.startswith('Hu')]        
        for segment in cli: 
            vrfs.append(segment)
    

    cli_vrf_default = con.send_command(f"bash sandbox -c ip netns exec vrf-default ip link | grep -E 'FH|Hu|Mg'").split() ###counting number of interfaces in vrf-default and add to empty list##
    output = [segment for segment in cli_vrf_default if segment.startswith('FH0_') or segment.startswith('Hu')]
    for segment in output:
        vrf_default.append(segment)
    
    if len(vrfs) + len(vrf_default) == len(iosxr_interfaces):
        print(f'Interface replication from XR to sandbox worked')
    else:
        print(f'Interface replication failed')

    

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
    
    check_sandbox_configured(con)
    show_sandbox_detail(con)
    show_sandbox_info(con)
    show_sandbox_services(con)
    ssh_to_sandbox(ip,username,password)
    copy_file_sandbox(ip,username,password)
    verify_copied_file(ip,username,password)
    sandbox_restart(con)
    verify_tcpdump_sandbox(ip,username,password)
    verify_package_install_sandbox(ip,username,password)
    verify_iperf(ip,username,password)
    verify_grpc(ip,username,password)
    verify_namespaces_vrf(ip,username,password)
    verify_int_replication(con,ip,username,password)  
    

    


if __name__ == '__main__':
    main()
