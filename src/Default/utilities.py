import json

def util_read_modules(address: str = None) -> dict:
    """Read the module information of the application

    Args:
        address (str): The address in hex string format. Send None to get all the modules

    Returns:
        dict: The parameters of the application
    """
    f = open('TinyCTRL/modules.json')
    try:
        data = json.load(f)
    except Exception as e:
        return {}

    if address != None:
        if address in data:
            data = data[address]
        else:
            data = {}
    f.close()

    return data


def util_write_modules(address: str, data: dict):
    """ Write the modules information of the application

    Args:
        data (dict): The new parameters to write
        address (str): The address in hex string format
    """
    f = open('TinyCTRL/modules.json')
    try:
        current_info = json.load(f)
    except Exception as e:
        return {}
    f.close()

    f = open('TinyCTRL/modules.json', "w")
    current_info[address] = data
    json.dump(current_info, f)
    f.close()
