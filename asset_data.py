import os
import ast
from argparse import ArgumentParser
from multiprocessing import Pool
import pandas as pd
from warnings import filterwarnings
from tqdm import tqdm

from config import logging, CSV_INTERMEDIATE_DIR
from src.lcd_extractor import extract_assets_star, add_cw20
from src.chain_registry_extractor import get_chain_names_and_lcd_dicts
from src.json_export import save_to_json
from src.contract_export import save_to_contracts
from src.csv_export import save_to_csv
from src.ibc_traces import add_ibc_metadata

filterwarnings('ignore')
tqdm.pandas()


def run_extract(number_of_treads: int = 25) -> None:
    """
    Extract asset metadata and store it to intermediate csv files
    :return: none
    """
    # extract chain names and lcd paths from chain-registry
    _chain_id_name_dict, _chain_id_lcd_dict, _ = get_chain_names_and_lcd_dicts()
    logging.info(msg=f'start extraction {len(_chain_id_name_dict.keys()):>,} chains')

    # extract asset data from lcd apis
    _tasks = [[_chain_id, _node_lcd_url_list] for _chain_id, _node_lcd_url_list in _chain_id_lcd_dict.items()]
    logging.info(f'lcd extract. first task: {_tasks[0][0]}  last task: {_tasks[-1][0]}  total tasks: {len(_tasks)}  '
                 f'threads: {number_of_treads:>,}')
    with Pool(processes=number_of_treads) as pool:
        _res = list(tqdm(pool.imap(extract_assets_star, _tasks, 1), total=len(_tasks)))
    logging.info(
        f'! extracted chains {sum(_res)} not extracted {len(_tasks) - sum(_res)} total {len(_tasks)}.'
        f'not extracted: {", ".join([_item[0] for _i, _item in enumerate(_tasks) if _res[_i] == False])}'
    )


def load_intermediate_csv_files(
        chain_id_name_dict: dict[str, str],
        dir_csv: str = CSV_INTERMEDIATE_DIR) -> pd.DataFrame:
    """
    Load data from intermediate csv files
    :param chain_id_name_dict: dictionary of chain ids by chain names
    :param dir_csv: path of a directory with intermediate csv files
    :return: dataframe with asset metadata
    """
    _assets_df = pd.DataFrame(columns=['denom', 'supply', 'denom_base', 'path', 'channels', 'channels_number',
                                       'chain_id_counterparty', 'channel_id_counterparty', 'type_asset',
                                       'type_asset_base', 'chain_id'])

    _asset_raw_file_names = [f.path for f in os.scandir(dir_csv)
                             if not f.is_dir() if
                             f.path.split('/')[1][0] not in ('_', '.') and f.path.split('/')[1] != 'all_assets.csv']
    _asset_filtered_file_names = [_item for _item in _asset_raw_file_names
                                  if _item.split('/')[1][7:-4] in chain_id_name_dict.keys()]
    if len(_asset_raw_file_names) > len(_asset_filtered_file_names):
        logging.info(f'! please remove deprecated files: '
                     f'{", ".join([_item for _item in _asset_raw_file_names if _item not in _asset_filtered_file_names])}')
    for _asset_filtered_file_name in _asset_filtered_file_names:
        _asset_df = pd.read_csv(_asset_filtered_file_name)
        _asset_df = _asset_df.drop_duplicates()
        if 'channels' in _asset_df.columns:
            _asset_df['channels'] = _asset_df.channels.map(lambda x: ast.literal_eval(x) if type(x) == str else None)
            _asset_df['channels_number'] = _asset_df.channels.map(lambda x: len(x) if x is not None else 0)
        if 'denom_units' in _asset_df.columns:
            _asset_df['denom_units'] = _asset_df.denom_units.map(
                lambda x: ast.literal_eval(x) if type(x) == str else None)
        if 'one_channel' in _asset_df.columns:
            _asset_df.drop(columns=['one_channel'])
        _assets_df = pd.concat([_assets_df, _asset_df])
    return _assets_df


def run_export() -> None:
    """
    Export asset metadata to the csv file and json files
    :return: none
    """
    _chain_id_name_dict, chain_id_lcd_dict, _ = get_chain_names_and_lcd_dicts()
    _assets_df = load_intermediate_csv_files(chain_id_name_dict=_chain_id_name_dict)
    _assets_df = add_cw20(assets_df=_assets_df, chain_id_lcd_dict=chain_id_lcd_dict,
                          chain_id_name_dict=_chain_id_name_dict)
    _assets_df = add_ibc_metadata(assets_df=_assets_df, chain_id_name_dict=_chain_id_name_dict)
    _assets_df['chain_name'] = _assets_df.chain_id.map(
        lambda _chain_id: _chain_id_name_dict.get(_chain_id, ''))
    _assets_df = _assets_df.fillna(
        value={'description': '', 'denom_units': '', 'display': '', 'name': '', 'symbol': '', 'admin': '',
               'denom_base': ''})
    save_to_csv(assets_df=_assets_df)
    save_to_json(assets_df=_assets_df, chain_id_name_dict=_chain_id_name_dict)
    logging.info(msg=f'! exported {len(_assets_df):>,} assets for {len(set(_assets_df.chain_id.to_list()))} chains')


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("--extract", action='store_true')
    parser.add_argument("--export", action='store_true')
    parser.add_argument("--export_to_contracts", action='store_true')
    args = parser.parse_args()

    if args.extract:
        logging.info('! start extraction')
        run_extract()
    if args.export:
        logging.info('! start export to the csv file and json files')
        run_export()
    if args.export_to_contracts:
        logging.info('! start export to contracts')
        save_to_contracts()
