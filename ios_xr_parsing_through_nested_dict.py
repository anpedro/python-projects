import json
import sys
sys.path.append('/home/lab/anpedro/scripts/playground/')
from recursive_dict_search import find_keys


def parsing_to_dict(filename):
    dict = {}
    f = open(filename)
    data = json.load(f)

    targets = ['receive-window-size']
    found_values = find_keys(data, targets)
    print(found_values)
        

def main():

    filename = '/home/lab/devbox/playground/tcp.json'

    parsing_to_dict(filename)



if __name__ == '__main__':
    main()
