from typing import Dict, List, Tuple, Any, Union, Callable
from tabulate import tabulate
from ben_helpers import display_parameters as print_dict


def find_keys(nested_dict:Dict[str, Any], targets:List[str], keep:str="all", verbose:bool=False) -> Dict[str, Any]:
    """
    Given a dictionary with potentially nested dictionaries, recursively go through each layer until we acquire all the targets
    
    Parameters
    ----------
    nested_dict : Dict[str, Any]
        The dictionary to search through
        Each entry's value can be a non-iterable value, a dictionary, or an iterable item
    targets : List[str]
        A list of keys
    keep : str
        Options: "first", "last", "all"
        If multiple entries are found for the same target, which one do we pick?
        Option "first": keep the first value encountered
        Option "last": keep the last value encountered
        Option "all": keep all the values encountered
        Note: if "all", return a dictionary of lists if target values, i.e. Dict[str, List[Any]]
        Note: anything else, and found values are not returned
        Default: "all"
    verbose : bool
        Whether to call out each key-value pair found
        Default: False
     
    Returns
    -------
    type Dict[str, Any]
    A dictionary of target keys and found values
    """

    def iteration_type(item:Any) -> str:
        """
        Determine which kind of iteration to use for the given item
        Excludes strings

        Parameters
        ----------
        item : any
            the item to check
        
        Returns
        -------
        type str
        Options: "dict", "list-like", "not iterable"
        """
        if item is None:
            return "not iterable"
        elif isinstance(item, str):
            return "not iterable"
        elif isinstance(item, Dict):
            return "dict"
        else:
            try:
                item[0]
                return "list-like"
            except TypeError:
                return "not iterable"


    def set_value(found_values:Dict[str, Any], key:str, value:Any, keep:str) -> None:
        """
        Assuming a matching key is already found, set found_values[key] according to keep's setting

        Parameters
        ----------
        found_values : Dict[str, Any]
            A dictionary of target keys and found values
            Note: It is assumed to be configured according to keep. That is, if keep=="all", it is already configured to Dict[str, List[Any]]
        key : str
            The target key
            Note: It is assumed that a match has already been found. That is, found_values has a "key" key
        value:
            The value to be set into found_values
        keep:
            A description of how to handle the new value, should a previous matching value already exist for the same key
            Option "first": the new value is ignored
            Option "last": the new value replaces the old value
            Option "all": the new value is appended
            Note: anything else, and the new value is ignored
        
        Returns
        -------
        type None
        The value is inserted directly into found_values. Nothing is returned.
        """
        if keep=="first":
            if found_values[key] is None:
                found_values[key] = value
        elif keep=="last":
            found_values[key] = value
        elif keep=="all":
            found_values[key].append(value)


    def _find_keys(found_values:Dict[str,Any], nested_dict:Any, targets:List[str], keep:str="all", verbose:bool=False) -> None:
        """
        Given a dictionary with potentially nested dictionaries, recursively go through each layer until we acquire all the targets
        
        Parameters
        ----------
        found_values : Dict[str, Any]
            The place to write the found values into
            Note: It is assumed to be configured according to keep. That is, if keep=="all", it is already configured to Dict[str, List[Any]]
        nested_dict : Any
            The structure that contains the dictionary to search through
            Can be Dict, list-like, or non-iterable
            Note: this does not have to be a dictionary, but we will recursively go through each layer until we hit one of type Dict[str, Any]
        targets : List[str]
            A list of keys
        keep : str
            Options: "first", "last", "all"
            If multiple entries are found for the same target, which one do we pick?
            Option "first": keep the first value encountered
            Option "last": keep the last value encountered
            Option "all": keep all the values encountered
            Note: if "all", return a dictionary of lists if target values, i.e. Dict[str, List[Any]]
            Note: anything else, and found values are not returned
            Default: "all"
        verbose : bool
            Whether to call out each key-value pair found
            Default: False
        
        Returns
        -------
        type None
        The value is inserted directly into found_values. Nothing is returned.
        """

        iteration_to_use = iteration_type(nested_dict)
        if iteration_to_use=="dict":
            for key, value in nested_dict.items():
                if key in targets:
                    if verbose:
                        print(f'key found: "{key}", value found: "{value}"')
                    set_value(found_values, key, value, keep)
                _find_keys(found_values=found_values, nested_dict=value, targets=targets, keep=keep, verbose=verbose)
        
        elif iteration_to_use=="list-like":
            for item in nested_dict:
                _find_keys(found_values=found_values, nested_dict=item, targets=targets, keep=keep, verbose=verbose)
        
        else:
            return


    found_values = dict(zip(targets, [None]*len(targets)))
    if keep=="all":
        for key in found_values.keys():
            found_values[key] = []

    _find_keys(found_values=found_values, nested_dict=nested_dict, targets=targets, keep=keep, verbose=verbose)

    return found_values


def test1():
    my_dict = {
        "ip": "10.8.74.183",
        "content": [
            "ben is cool",
            {
                "address_family": "ipv6",
                "max-reauth-req": 48
            },
            {
                "address_family": {
                    "version": "ipv4",
                    "received_prefixes": "153",
                    "sent_prefixes": 32
                },
                "timestamp": 1651005430248605500, 
                "boundaries": [
                    {
                        "max-reauth-req": 2,
                        "supp-timeout": 30, 
                        "max-req": 4,
                        "auth-period": 34
                    }
                ]
            },
            {
                "auth-period": 58,
                "start-period": 14, 
                "sent_prefixes": 52
            },
            "hello world"
        ],
        "ben is cool": True
    }

    targets = [
        "sent_prefixes",
        "address_family",
        "max-reauth-req",
        "ben is cool",
        "hello world"
    ]

    values = find_keys(my_dict, targets, keep="all", verbose=True)
    print_dict(**values)


if __name__ == "__main__":
    test1()
