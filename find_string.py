import re

def opening_file(filename):
    with open(filename, "r") as f:
        lines = f.readlines()
    patterns = '%ROUTING-BGP-5-ADJCHANGE'
    line = str(lines)

    matches = re.findall(patterns,line)
    
    matches_list = []
    counter = 0 
    for match in matches:
        match_list = list(match)
        if len(match_list) == 0:
            print(f'Match not found')
            exit(1)

        else:

            print(f'Match found appending to new list, {match_list}')
            matches_list.append(match_list)

    print (len(matches_list))

        
    

def main():
    filename = '/home/lab/devbox/playground/sh_logging.txt'
    opening_file(filename)




if __name__ == '__main__':
    main()
