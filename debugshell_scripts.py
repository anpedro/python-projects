from netmiko import ConnectHandler
from time import sleep
import re
import argparse
import datetime

def print_get_counters(ip,username,password):
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
        print(f'Connected to {hostname}, collecting print_get_counters') ##connecting to the device
        check_chassis_type = con.send_command(f'show inventory chassis',read_timeout=120) ##checking the chassis type
        check_code_version = con.send_command(f'show version | inc Version',read_timeout=120) ##checking the code version
        check_lc_command = con.send_command(f'show platform | inc XR',read_timeout=120) ##checking the line card available in the system        
        lc_pattern = re.compile(r'0/\d+/CPU0') ##regex to match the line card
        version_pattern = re.compile(r"Version\s+([\d.]+)") ##regex to match the version
        match_version = version_pattern.search(check_code_version) ##searching the version
        
        ## This is just for the filename as on the LC .. there will always be 0-3 NPUs.
        if '8808' in check_chassis_type: ##checking the chassis type
            chassis_type = '8808'
        elif '8804' in check_chassis_type: ##checking the chassis type
            chassis_type = '8804'
        
        if match_version: ##checking the version
            version = match_version.group(1) ##getting the version
            
        for line in check_lc_command.strip().split('\n'): ##looping through the line card (up in the system)
            start_time = datetime.datetime.now()
            match_lc = lc_pattern.search(line) ##
            if match_lc: ##checking the line card
                lc_location = match_lc.group(0)  # Get the whole LC matched string
                for npu_number in range(3):  # Loop through NPU numbers 0, 1, and 2
                    if version.startswith('24.2'):
                        execute_sf_debug_fabric = con.send_command(f'show controllers npu debugshell {npu_number} "script print_get_counters" location {lc_location}',read_timeout=120)
                        end_time = datetime.datetime.now()
                        execution_time = end_time - start_time
                        print(f"print_get_counters-np-{npu_number}-lc-{lc_location} took {execution_time} seconds to execute")

                    else:    
                        execute_sf_debug_fabric = con.send_command(f'show controllers npu debugshell {npu_number} "script print_get_counters" location {lc_location}',read_timeout=120)
                        end_time = datetime.datetime.now()
                        execution_time = end_time - start_time
                        print(f"print_get_counters-np-{npu_number}-lc-{lc_location} took {execution_time} seconds to execute")

                    with open(f'print_get_counters-{hostname}-{chassis_type}-lc-{version}.txt', 'a') as file:
                        file.write(execute_sf_debug_fabric)
                        print(f'Output saved to print_get_counters-{hostname}-{chassis_type}-lc-{version}-np-{npu_number}-linecard-{lc_location}.txt')
        

    

def sf_fabric_debug_lc(ip, username, password):
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
        print(f'Connected to {hostname}, collecting fabric_debug LC side') ##connecting to the device
        check_chassis_type = con.send_command(f'show inventory chassis',read_timeout=120) ##checking the chassis type
        check_code_version = con.send_command(f'show version | inc Version',read_timeout=120) ##checking the code version
        check_lc_command = con.send_command(f'show platform | inc XR',read_timeout=120) ##checking the line card available in the system        
        lc_pattern = re.compile(r'0/\d+/CPU0') ##regex to match the line card
        version_pattern = re.compile(r"Version\s+([\d.]+)") ##regex to match the version
        match_version = version_pattern.search(check_code_version) ##searching the version
        
        ## This is just for the filename as on the LC .. there will always be 0-3 NPUs.
        if '8808' in check_chassis_type: ##checking the chassis type
            chassis_type = '8808'
        elif '8804' in check_chassis_type: ##checking the chassis type
            chassis_type = '8804'
        
        if match_version: ##checking the version
            version = match_version.group(1) ##getting the version
            
        for line in check_lc_command.strip().split('\n'): ##looping through the line card (up in the system)
            start_time = datetime.datetime.now()
            match_lc = lc_pattern.search(line) ##
            if match_lc: ##checking the line card
                lc_location = match_lc.group(0)  # Get the whole LC matched string
                for npu_number in range(3):  # Loop through NPU numbers 0, 1, and 2
                    if version.startswith('24.2'):
                        execute_sf_debug_fabric = con.send_command(f'show controllers npu debugshell {npu_number} "script exec_sdk_api fabric_debug" location {lc_location}',read_timeout=120)
                        end_time = datetime.datetime.now()
                        execution_time = end_time - start_time
                        print(f"sf_fabric_debug_lc-np-{npu_number}-lc-{lc_location} took {execution_time} seconds to execute")

                    else:    
                        execute_sf_debug_fabric = con.send_command(f'show controllers npu debugshell {npu_number} "script sf_fabric_debug" location {lc_location}',read_timeout=120)
                        end_time = datetime.datetime.now()
                        execution_time = end_time - start_time
                        print(f"sf_fabric_debug_lc-np-{npu_number}-lc-{lc_location} took {execution_time} seconds to execute")

                    with open(f'sf_fabric_debug-{hostname}-{chassis_type}-lc-{version}.txt', 'a') as file:
                        file.write(execute_sf_debug_fabric)
                        print(f'Output saved to sf_fabric_debug-{hostname}-{chassis_type}-lc-{version}-np-{npu_number}-linecard-{lc_location}.txt')
        


                        
def sf_fabric_debug_fc(ip, username, password):
        device = {
        'device_type': 'cisco_xr',
        'ip': ip,
        'username': username,
        'password': password,
        'timeout': 5000,
        }
        con = ConnectHandler(**device)
        hostname = con.find_prompt().split(':')[-1][:-1]
        print(f'Connected to {hostname}, collecting fabric_debug FC side')
        start_time = datetime.datetime.now()
 
        check_chassis_type = con.send_command(f'show inventory chassis',read_timeout=120) ##checking the chassis type
        check_code_version = con.send_command(f'show version | inc Version',read_timeout=120) ##checking the code version
        version_pattern = re.compile(r"Version\s+([\d.]+)") ##regex to match the version
        match_version = version_pattern.search(check_code_version) ##searching the version
        
        
        #chassis type check is needed to count the number of available FEs and execute the CLI properly.
        
        if '8808' in check_chassis_type: ##checking the chassis type
            chassis_type = '8808'
        elif '8804' in check_chassis_type: ##checking the chassis type
            chassis_type = '8804'
        
        #version check is needed to see which CLI will be executed as the CLI have been changed by SDK team on the later releases
        if match_version: ##checking the version
            version = match_version.group(1) ##getting the version
            
            
        if '8808' in check_chassis_type:
            for fe_number in range(15):  # Loop through FE elements numbers 0, 15 since 8808 has 15 FEs
                if version.startswith('24.2'):
                    execute_sf_debug_fabric = con.send_command(f'show controllers npu debugshell {fe_number} "script exec_sdk_api fabric_debug" location 0/RP0/CPU0',read_timeout=120)
                else:    
                    execute_sf_debug_fabric = con.send_command(f'show controllers npu debugshell {fe_number} "script sf_fabric_debug" location 0/RP0/CPU0',read_timeout=120)
                sleep(5)
                with open(f'sf_fabric_debug-{hostname}-{chassis_type}-fc-{version}.txt', 'a') as file:
                    file.write(execute_sf_debug_fabric)
                    print(f'Output saved to sf_fabric_debug-{hostname}-{chassis_type}-fc-{version}.txt')
        else:
            for fe_number in range(7):  # Loop through NPU numbers 0, 7 since 8804 has 7 FEs
                if version.startswith('24.2'):
                    execute_sf_debug_fabric = con.send_command(f'show controllers npu debugshell {fe_number} "script exec_sdk_api fabric_debug" location 0/RP0/CPU0',read_timeout=120)
                else:    
                    execute_sf_debug_fabric = con.send_command(f'show controllers npu debugshell {fe_number} "script sf_fabric_debug" location 0/RP0/CPU0',read_timeout=120)
                sleep(5)
                with open(f'sf_fabric_debug-{hostname}-{chassis_type}-fc-{version}.txt', 'a') as file:
                    file.write(execute_sf_debug_fabric)
                    print(f'Output saved to sf_fabric_debug-{hostname}-{chassis_type}-fc-{version}.txt')
        
        end_time = datetime.datetime.now()
        execution_time = end_time - start_time
        print(f"sf_fabric_debug_fc took {execution_time.total_seconds()} seconds to execute")

        

                
def sf_rate_checker_detailed(ip, username, password):

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
    print(f'Connected to {hostname}, collecting rate_checker_detailed') ##connecting to the device
    start_time = datetime.datetime.now()
    check_chassis_type = con.send_command(f'show inventory chassis',read_timeout=120) ##checking the chassis type
    check_code_version = con.send_command(f'show version | inc Version',read_timeout=120) ##checking the code version
    check_lc_command = con.send_command(f'show platform | inc XR',read_timeout=120) ##checking the line card available in the system        
    lc_pattern = re.compile(r'0/\d+/CPU0') ##regex to match the line card
    version_pattern = re.compile(r"Version\s+([\d.]+)") ##regex to match the version
    match_version = version_pattern.search(check_code_version) ##searching the version
    
        ## This is just for the filename as on the LC .. there will always be 0-3 NPUs.
    if '8808' in check_chassis_type: ##checking the chassis type
        chassis_type = '8808'
    elif '8804' in check_chassis_type: ##checking the chassis type
        chassis_type = '8804'
        
    if match_version: ##checking the version
        version = match_version.group(1) ##getting the version
            
        for line in check_lc_command.strip().split('\n'): ##looping through the line card (up in the system)
            match_lc = lc_pattern.search(line) ##
            if match_lc: ##checking the line card
                lc_location = match_lc.group(0)  # Get the whole LC matched string
                for npu_number in range(3):  # Loop through NPU numbers 0, 1, and 2
                    if version.startswith('24.2'):
                        execute_rate_checker_detailed = con.send_command(f'show controllers npu debugshell {npu_number} "script exec_sdk_api rate_checker_detailed" location {lc_location}',read_timeout=120)
                        with open(f'rate_checker_detailed-{hostname}-{chassis_type}-lc-{version}.txt', 'a') as file:
                            file.write(execute_rate_checker_detailed)
                            print(f'Output saved to rate_checker_detailed-{hostname}-{chassis_type}-lc-{version}.txt')
                    else:
                        print(f'rate_checker_detailed does not apply for  {hostname} {chassis_type} {version} {lc_location} {npu_number}')  
        end_time = datetime.datetime.now()
        execution_time = end_time - start_time
        print(f"sf_rate_checker_detailed took {execution_time.total_seconds()} seconds to execute")


def sf_rate_checker(ip, username, password):
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
    print(f'Connected to {hostname}, collecting rate_checker') ##connecting to the device
    start_time = datetime.datetime.now()
    check_chassis_type = con.send_command(f'show inventory chassis',read_timeout=120) ##checking the chassis type
    check_code_version = con.send_command(f'show version | inc Version',read_timeout=120) ##checking the code version
    check_lc_command = con.send_command(f'show platform | inc XR',read_timeout=120) ##checking the line card available in the system        
    lc_pattern = re.compile(r'0/\d+/CPU0') ##regex to match the line card
    version_pattern = re.compile(r"Version\s+([\d.]+)") ##regex to match the version
    match_version = version_pattern.search(check_code_version) ##searching the version
    
        ## This is just for the filename as on the LC .. there will always be 0-3 NPUs.
    if '8808' in check_chassis_type: ##checking the chassis type
        chassis_type = '8808'
    elif '8804' in check_chassis_type: ##checking the chassis type
        chassis_type = '8804'
        
    if match_version: ##checking the version
        version = match_version.group(1) ##getting the version
            
        for line in check_lc_command.strip().split('\n'): ##looping through the line card (up in the system)
            match_lc = lc_pattern.search(line) ##
            if match_lc: ##checking the line card
                lc_location = match_lc.group(0)  # Get the whole LC matched string
                for npu_number in range(3):  # Loop through NPU numbers 0, 1, and 2
                    if version.startswith('24.2'):
                        execute_rate_checker = con.send_command(f'show controllers npu debugshell {npu_number} "script exec_sdk_api rate_checker" location {lc_location}',read_timeout=120)
                        with open(f'rate_checker-{hostname}-{chassis_type}-lc-{version}.txt', 'a') as file:
                            file.write(execute_rate_checker)
                            print(f'Output saved to rate_checker-{hostname}-{chassis_type}-lc-{version}.txt')
                    else:
                        execute_rate_checker = con.send_command(f'show controllers npu debugshell {npu_number} "script sf_rate_checker" location {lc_location}',read_timeout=120)
                        with open(f'rate_checker-{hostname}-{chassis_type}-lc-{version}.txt', 'a') as file:
                            file.write(execute_rate_checker)
                            print(f'Output saved to rate_checker-{hostname}-{chassis_type}-lc-{version}.txt')
    end_time = datetime.datetime.now()
    execution_time = end_time - start_time
    print(f"sf_rate_checker took {execution_time.total_seconds()} seconds to execute")



def dvoq_qsm(ip, username, password):
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
    print(f'Connected to {hostname}, collecting dvoq_qsm') ##connecting to the device
    start_time = datetime.datetime.now()
    check_chassis_type = con.send_command(f'show inventory chassis',read_timeout=120) ##checking the chassis type
    check_code_version = con.send_command(f'show version | inc Version',read_timeout=120) ##checking the code version
    check_lc_command = con.send_command(f'show platform | inc XR',read_timeout=120) ##checking the line card available in the system        
    lc_pattern = re.compile(r'0/\d+/CPU0') ##regex to match the line card
    version_pattern = re.compile(r"Version\s+([\d.]+)") ##regex to match the version
    match_version = version_pattern.search(check_code_version) ##searching the version
    
        ## This is just for the filename as on the LC .. there will always be 0-3 NPUs.
    if '8808' in check_chassis_type: ##checking the chassis type
        chassis_type = '8808'
    elif '8804' in check_chassis_type: ##checking the chassis type
        chassis_type = '8804'
        
    if match_version: ##checking the version
        version = match_version.group(1) ##getting the version
            
        for line in check_lc_command.strip().split('\n'): ##looping through the line card (up in the system)
            match_lc = lc_pattern.search(line) ##
            if match_lc: ##checking the line card
                lc_location = match_lc.group(0)  # Get the whole LC matched string
                for npu_number in range(3):  # Loop through NPU numbers 0, 1, and 2
                    if version.startswith('24.2'):
                        execute_dvoq_qsm = con.send_command(f'show controllers npu debugshell {npu_number} "script exec_sdk_api dvoq_qsm" location {lc_location}',read_timeout=120)
                        with open(f'dvoq_qsm-{hostname}-{chassis_type}-lc-{version}.txt', 'a') as file:
                            file.write(execute_dvoq_qsm)
                            print(f'Output saved to dvoq_qsm-{hostname}-{chassis_type}-lc-{version}.txt')
                    else:
                        execute_dvoq_qsm = con.send_command(f'show controllers npu debugshell {npu_number} "script read_dvoq_qsm" location {lc_location}',read_timeout=120)
                        with open(f'dvoq_qsm-{hostname}-{chassis_type}-lc-{version}.txt', 'a') as file:
                            file.write(execute_dvoq_qsm)
                            print(f'Output saved to dvoq_qsm-{hostname}-{chassis_type}-lc-{version}.txt')
    end_time = datetime.datetime.now()
    execution_time = end_time - start_time
    print(f"dvoq_qsm took {execution_time.total_seconds()} seconds to execute")



def hbm_error_counters(ip, username, password):
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
    print(f'Connected to {hostname}, collecting hbm_error_counters') ##connecting to the device
    start_time = datetime.datetime.now()
    check_chassis_type = con.send_command(f'show inventory chassis',read_timeout=120) ##checking the chassis type
    check_code_version = con.send_command(f'show version | inc Version',read_timeout=120) ##checking the code version
    check_lc_command = con.send_command(f'show platform | inc XR',read_timeout=120) ##checking the line card available in the system        
    lc_pattern = re.compile(r'0/\d+/CPU0') ##regex to match the line card
    version_pattern = re.compile(r"Version\s+([\d.]+)") ##regex to match the version
    match_version = version_pattern.search(check_code_version) ##searching the version
    
        ## This is just for the filename as on the LC .. there will always be 0-3 NPUs.
    if '8808' in check_chassis_type: ##checking the chassis type
        chassis_type = '8808'
    elif '8804' in check_chassis_type: ##checking the chassis type
        chassis_type = '8804'
        
    if match_version: ##checking the version
        version = match_version.group(1) ##getting the version
            
        for line in check_lc_command.strip().split('\n'): ##looping through the line card (up in the system)
            match_lc = lc_pattern.search(line) ##
            if match_lc: ##checking the line card
                lc_location = match_lc.group(0)  # Get the whole LC matched string
                for npu_number in range(3):  # Loop through NPU numbers 0, 1, and 2
                    if version.startswith('24.2'):
                        execute_hbm_error_counters = con.send_command(f'show controllers npu debugshell {npu_number} "script exec_sdk_api hbm_error_counters" location {lc_location}',read_timeout=120)
                        with open(f'hbm_error_counters-{hostname}-{chassis_type}-lc-{version}.txt', 'a') as file:
                            file.write(execute_hbm_error_counters)
                            print(f'Output saved to hbm_error_counters-{hostname}-{chassis_type}-lc-{version}.txt')
                    else:
                        execute_hbm_error_counters = con.send_command(f'show controllers npu debugshell {npu_number} "script script hbm_error_counters" location {lc_location}',read_timeout=120)
                        with open(f'hbm_error_counters-{hostname}-{chassis_type}-lc-{version}.txt', 'a') as file:
                            file.write(execute_hbm_error_counters)
                            print(f'Output saved to hbm_error_counters-{hostname}-{chassis_type}-lc-{version}.txt')
    end_time = datetime.datetime.now()
    execution_time = end_time - start_time
    print(f"hbm_error_counters took {execution_time.total_seconds()} seconds to execute")


def mmu_error_buffers(ip, username, password):
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
    print(f'Connected to {hostname}, collecting mmu_error_buffers') ##connecting to the device
    start_time = datetime.datetime.now()
    check_chassis_type = con.send_command(f'show inventory chassis',read_timeout=120) ##checking the chassis type
    check_code_version = con.send_command(f'show version | inc Version',read_timeout=120) ##checking the code version
    check_lc_command = con.send_command(f'show platform | inc XR',read_timeout=120) ##checking the line card available in the system        
    lc_pattern = re.compile(r'0/\d+/CPU0') ##regex to match the line card
    version_pattern = re.compile(r"Version\s+([\d.]+)") ##regex to match the version
    match_version = version_pattern.search(check_code_version) ##searching the version
    
        ## This is just for the filename as on the LC .. there will always be 0-3 NPUs.
    if '8808' in check_chassis_type: ##checking the chassis type
        chassis_type = '8808'
    elif '8804' in check_chassis_type: ##checking the chassis type
        chassis_type = '8804'
        
    if match_version: ##checking the version
        version = match_version.group(1) ##getting the version
            
        for line in check_lc_command.strip().split('\n'): ##looping through the line card (up in the system)
            match_lc = lc_pattern.search(line) ##
            if match_lc: ##checking the line card
                lc_location = match_lc.group(0)  # Get the whole LC matched string
                for npu_number in range(3):  # Loop through NPU numbers 0, 1, and 2
                    if version.startswith('24.2'):
                        execute_sf_mmu_error_buffers = con.send_command(f'show controllers npu debugshell {npu_number} "script exec_sdk_api mmu_error_buffers" location {lc_location}',read_timeout=120)
                        with open(f'mmu_error_buffers-{hostname}-{chassis_type}-lc-{version}.txt', 'a') as file:
                            file.write(execute_sf_mmu_error_buffers)
                            print(f'Output saved to mmu_error_buffers-{hostname}-{chassis_type}-lc-{version}.txt')
                    else:
                        execute_sf_mmu_error_buffers = con.send_command(f'show controllers npu debugshell {npu_number} "script script mmu_error_buffers" location {lc_location}',read_timeout=120)
                        with open(f'mmu_error_buffers-{hostname}-{chassis_type}-lc-{version}.txt', 'a') as file:
                            file.write(execute_sf_mmu_error_buffers)
                            print(f'Output saved to mmu_error_buffers-{hostname}-{chassis_type}-lc-{version}.txt')
    end_time = datetime.datetime.now()
    execution_time = end_time - start_time
    print(f"mmu_error_buffers took {execution_time.total_seconds()} seconds to execute")




def mmu_sms_fifos(ip,username,password):
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
    print(f'Connected to {hostname}, collecting mmu_sms_fifos') ##connecting to the device
    start_time = datetime.datetime.now()

    check_chassis_type = con.send_command(f'show inventory chassis',read_timeout=120) ##checking the chassis type
    check_code_version = con.send_command(f'show version | inc Version',read_timeout=120) ##checking the code version
    check_lc_command = con.send_command(f'show platform | inc XR',read_timeout=120) ##checking the line card available in the system        
    lc_pattern = re.compile(r'0/\d+/CPU0') ##regex to match the line card
    version_pattern = re.compile(r"Version\s+([\d.]+)") ##regex to match the version
    match_version = version_pattern.search(check_code_version) ##searching the version
    
        ## This is just for the filename as on the LC .. there will always be 0-3 NPUs.
    if '8808' in check_chassis_type: ##checking the chassis type
        chassis_type = '8808'
    elif '8804' in check_chassis_type: ##checking the chassis type
        chassis_type = '8804'
        
    if match_version: ##checking the version
        version = match_version.group(1) ##getting the version
            
        for line in check_lc_command.strip().split('\n'): ##looping through the line card (up in the system)
            match_lc = lc_pattern.search(line) ##
            if match_lc: ##checking the line card
                lc_location = match_lc.group(0)  # Get the whole LC matched string
                for npu_number in range(3):  # Loop through NPU numbers 0, 1, and 2
                    if version.startswith('24.2'):
                        execute_mmu_sms_fifos = con.send_command(f'show controllers npu debugshell {npu_number} "script exec_sdk_api mmu_sms_fifos" location {lc_location}',read_timeout=120)
                        with open(f'mmu_sms_fifos-{hostname}-{chassis_type}-lc-{version}.txt', 'a') as file:
                            file.write(execute_mmu_sms_fifos)
                            print(f'Output saved to mmu_sms_fifos-{hostname}-{chassis_type}-lc-{version}.txt')
                    else: ##this is broken for 7552 --- need to find out what is the correct name. 
                        execute_mmu_sms_fifos = con.send_command(f'show controllers npu debugshell {npu_number} "script  read_mmu_sms_fifos" location {lc_location}',read_timeout=120)
                        with open(f'mmu_sms_fifos-{hostname}-{chassis_type}-lc-{version}.txt', 'a') as file:
                            file.write(execute_mmu_sms_fifos)
                            print(f'Output saved to mmu_error_buffers-{hostname}-{chassis_type}-lc-{version}.txt')
    end_time = datetime.datetime.now()
    execution_time = end_time - start_time
    print(f"mmu_sms_fifos took {execution_time.total_seconds()} seconds to execute")



def sms_counters(ip,username,password):
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
    print(f'Connected to {hostname}, collecting sms_counters') ##connecting to the device
    start_time = datetime.datetime.now()    
    check_chassis_type = con.send_command(f'show inventory chassis',read_timeout=120) ##checking the chassis type
    check_code_version = con.send_command(f'show version | inc Version',read_timeout=120) ##checking the code version
    check_lc_command = con.send_command(f'show platform | inc XR',read_timeout=120) ##checking the line card available in the system        
    lc_pattern = re.compile(r'0/\d+/CPU0') ##regex to match the line card
    version_pattern = re.compile(r"Version\s+([\d.]+)") ##regex to match the version
    match_version = version_pattern.search(check_code_version) ##searching the version
    
        ## This is just for the filename as on the LC .. there will always be 0-3 NPUs.
    if '8808' in check_chassis_type: ##checking the chassis type
        chassis_type = '8808'
    elif '8804' in check_chassis_type: ##checking the chassis type
        chassis_type = '8804'
        
    if match_version: ##checking the version
        version = match_version.group(1) ##getting the version
            
        for line in check_lc_command.strip().split('\n'): ##looping through the line card (up in the system)
            match_lc = lc_pattern.search(line) ##
            if match_lc: ##checking the line card
                lc_location = match_lc.group(0)  # Get the whole LC matched string
                for npu_number in range(3):  # Loop through NPU numbers 0, 1, and 2
                    if version.startswith('24.2'):
                        execute_sms_counters = con.send_command(f'show controllers npu debugshell {npu_number} "script exec_sdk_api sms_counters" location {lc_location}',read_timeout=120)
                        with open(f'sms_counters-{hostname}-{chassis_type}-lc-{version}.txt', 'a') as file:
                            file.write(execute_sms_counters)
                            print(f'Output saved to sms_counters-{hostname}-{chassis_type}-lc-{version}.txt')
                    else: ##this is broken for 7552 --- need to find out what is the correct name or file a bug?
                        execute_sms_counters = con.send_command(f'show controllers npu debugshell {npu_number} "script  read_sms_counters" location {lc_location}',read_timeout=120)
                        with open(f'sms_counters-{hostname}-{chassis_type}-lc-{version}.txt', 'a') as file:
                            file.write(execute_sms_counters)
                            print(f'Output saved to sms_counters-{hostname}-{chassis_type}-lc-{version}.txt')    
    end_time = datetime.datetime.now()
    execution_time = end_time - start_time
    print(f"sms_counters took {execution_time.total_seconds()} seconds to execute")
    
    
def oq_debug(ip,username,password):
    
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
    print(f'Connected to {hostname}, collecting oq_debug') ##connecting to the device

    check_chassis_type = con.send_command(f'show inventory chassis',read_timeout=120) ##checking the chassis type
    check_code_version = con.send_command(f'show version | inc Version',read_timeout=120) ##checking the code version
    check_lc_command = con.send_command(f'show platform | inc XR',read_timeout=120) ##checking the line card available in the system        
    lc_pattern = re.compile(r'0/\d+/CPU0') ##regex to match the line card
    version_pattern = re.compile(r"Version\s+([\d.]+)") ##regex to match the version
    match_version = version_pattern.search(check_code_version) ##searching the version
    
        ## This is just for the filename as on the LC .. there will always be 0-3 NPUs.
    if '8808' in check_chassis_type: ##checking the chassis type
        chassis_type = '8808'
    elif '8804' in check_chassis_type: ##checking the chassis type
        chassis_type = '8804'
        
    if match_version: ##checking the version
        version = match_version.group(1) ##getting the version
            
        for line in check_lc_command.strip().split('\n'): ##looping through the line card (up in the system)
            match_lc = lc_pattern.search(line) ##
            if match_lc: ##checking the line card
                lc_location = match_lc.group(0)  # Get the whole LC matched string
                for npu_number in range(3):  # Loop through NPU numbers 0, 1, and 2
                    start_time = datetime.datetime.now()
                    if version.startswith('24.2'):
                        execute_oq_debug = con.send_command(f'show controllers npu debugshell {npu_number} "script exec_sdk_api oq_debug" location {lc_location}',read_timeout=120)
                        end_time = datetime.datetime.now()
                        execution_time = end_time - start_time
                        print(f'oq_debug-np-{npu_number}-lc-{lc_location} took {execution_time} seconds to execute')
                        with open(f'oq_debug-{hostname}-{chassis_type}-lc-{version}.txt', 'a') as file:
                            file.write(execute_oq_debug)
                            print(f'Output saved to oq_debug-{hostname}-{chassis_type}-lc-{version}.txt')
                    else: 
                        execute_oq_debug = con.send_command(f'show controllers npu debugshell {npu_number} "script sf_oq_debug" location {lc_location}',read_timeout=120)
                        with open(f'oq_debug-{hostname}-{chassis_type}-lc-{version}.txt', 'a') as file:
                            file.write(execute_oq_debug)
                            print(f'Output saved to oq_debug-{hostname}-{chassis_type}-lc-{version}.txt')    





def show_drops(ip,username,password):
    
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
    print(f'Connected to {hostname}, collecting show drops') ##connecting to the device

    check_lc_command = con.send_command(f'show platform | inc XR',read_timeout=120) ##checking the line card available in the system        
    lc_pattern = re.compile(r'0/\d+/CPU0') ##regex to match the line card
        
    for line in check_lc_command.strip().split('\n'): ##looping through the line card (up in the system)
        match_lc = lc_pattern.search(line) ##
        if match_lc: ##checking the line card            
            lc_location = match_lc.group(0)  # Get the whole LC matched string    
            start_time = datetime.datetime.now()
            execute_show_drops = con.send_command(f'show drops all location {lc_location}',read_timeout=120)
#            print(f'{execute_show_drops}')
            end_time = datetime.datetime.now()
            execution_time = end_time - start_time
            print(f'show_drops-lc-{lc_location} took {execution_time} seconds to execute')
            



    

def main():
    #### Argparse block ####
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", '-u', type=str, default="lab", help="Username. Default is lab")
    parser.add_argument("--password", '-p', type=str, default="lab123", help="Password. Default is lab123")
    parser.add_argument("--ip", '-i', type=str, help="IP of the host")


    arguments = parser.parse_args()
    #### End of Argparse block ####

    # grabbing all variables from arguments
    username: str = arguments.username
    password: str = arguments.password
    ip: str = arguments.ip

    print_get_counters(ip,username,password)
    sf_fabric_debug_lc(ip, username, password)
    sf_fabric_debug_fc(ip, username, password)
    sf_rate_checker_detailed(ip, username, password)
    sf_rate_checker(ip, username, password)
    dvoq_qsm(ip, username, password)
    hbm_error_counters(ip, username, password)
    mmu_error_buffers(ip, username, password)
    mmu_sms_fifos(ip, username, password)
    sms_counters(ip, username, password)
    oq_debug(ip, username, password)
    show_drops(ip,username,password)



    
if __name__ == "__main__":
    main()
    
    
    
    
