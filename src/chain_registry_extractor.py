import os
import json

from config import INIT_CHAIN_ID_NAME_DICT, INIT_CHAIN_ID_LCD_DICT


def get_chain_names_and_lcd_dicts(directory: str = 'chain-registry',
                                  chain_file_name: str = 'chain.json') -> [dict[str:str], dict[str:list[str]], list[str]]:
    """
    Get dictionaries from chain ids to chain names and lcd api lists
    :param directory: a chain registry directory
    :param chain_file_name: file name with `chain_id` property
    :return: dictionary from chain ids to chain names, dictionary from chain ids to and lcd api lists,
    list of chain registry subdirectories
    """
    chain_directories = \
        [f.path for f in os.scandir(directory)
         if f.is_dir() if f.path.split('/')[1][0] not in ('_', '.') and f.path.split('/')[1] != 'testnets']
    chain_id_name_dict = INIT_CHAIN_ID_NAME_DICT if INIT_CHAIN_ID_NAME_DICT else {}
    chain_id_lcd_dict = INIT_CHAIN_ID_LCD_DICT if INIT_CHAIN_ID_LCD_DICT else {}
    for chain_directory in chain_directories:
        with open(f'{chain_directory}/{chain_file_name}') as chain_json_file:
            chain_json = json.load(chain_json_file)
        try:
            chain_id_lcd_dict[chain_json['chain_id']] = \
                [rest_api['address'][:-1] if rest_api['address'].endswith('/') else rest_api['address']
                 for rest_api in chain_json['apis']['rest']]
            chain_id_name_dict[chain_json['chain_id']] = chain_json['chain_name']
        except KeyError:
            print(f'no lcd api for {chain_directory.split("/")[1]}')
    return chain_id_name_dict, chain_id_lcd_dict, chain_directories
