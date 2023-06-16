import json
import os
import ast
import sys

import pandas as pd
from warnings import filterwarnings
from tqdm import tqdm
from jsonschema import validate

from config import logging
from src.lcd_extractor import extract_assets
from src.chain_registry_extractor import get_chain_names_and_lcd_dicts
from src.json_export import get_asset_json_dict

filterwarnings('ignore')
tqdm.pandas()


def load_csv_files(dir_csv: str = 'data_csv') -> pd.DataFrame:
    _assets_df = pd.DataFrame(columns=['denom', 'supply', 'denom_base', 'path', 'channels', 'one_channel',
                                       'chain_id_counterparty', 'channel_id_counterparty', 'type_asset',
                                       'type_asset_base', 'chain_id'])

    _asset_raw_file_names = [f.path for f in os.scandir(dir_csv)
                             if not f.is_dir() if
                             f.path.split('/')[1][0] not in ('_', '.') and f.path.split('/')[1] != 'all_assets.csv']
    for _asset_raw_file_name in _asset_raw_file_names:
        _asset_df = pd.read_csv(_asset_raw_file_name)
        _asset_df = _asset_df.drop_duplicates()
        if 'channels' in _asset_df.columns:
            _asset_df['channels'] = _asset_df.channels.map(lambda x: ast.literal_eval(x) if type(x) == str else None)
        if 'denom_units' in _asset_df.columns:
            _asset_df['denom_units'] = _asset_df.denom_units.map(
                lambda x: ast.literal_eval(x) if type(x) == str else None)
        _assets_df = pd.concat([_assets_df, _asset_df])
    return _assets_df


def enrich_asset_df(assets_df: pd.DataFrame) -> pd.DataFrame:
    _assets_one_channel_df = \
        assets_df[assets_df.one_channel == True][['denom', 'supply', 'chain_id', 'denom_base', 'path', 'channels',
                                                  'chain_id_counterparty', 'channel_id_counterparty', 'type_asset',
                                                  'one_channel', 'type_asset_base']].merge(
            assets_df[['denom', 'supply', 'chain_id', 'description', 'denom_units', 'display', 'name', 'symbol']].rename(
                columns={'supply': 'supply_base', 'chain_id': 'chain_id_base', 'denom': 'denom_base'}),
            how='left',
            left_on=['chain_id_counterparty', 'denom_base'],
            right_on=['chain_id_base', 'denom_base']
        )
    _assets_not_one_channel_df = assets_df[assets_df.one_channel != True]
    _assets_not_one_channel_df['supply_base'] = _assets_not_one_channel_df.apply(
        lambda _row: _row['supply'] if _row['one_channel'] is None else None, axis=1)
    _assets_not_one_channel_df['chain_id_base'] = _assets_not_one_channel_df.apply(
        lambda _row: _row['chain_id'] if _row['one_channel'] == True else None, axis=1)

    return pd.concat([
        _assets_one_channel_df,
        _assets_not_one_channel_df]).reset_index(drop=True)[[
            'chain_id', 'denom', 'type_asset', 'supply', 'description', 'denom_units', 'display', 'name', 'symbol', 'uri',
            'denom_base', 'type_asset_base', 'path', 'channels', 'chain_id_counterparty', 'channel_id_counterparty',
            'supply_base', 'chain_id_base', 'one_channel']]


def save_to_csv(assets_df: pd.DataFrame) -> None:
    assets_df.to_csv('data_csv/all_assets.csv')


def save_to_json(assets_df: pd.DataFrame) -> None:
    _chain_id_name_dict, _, _ = get_chain_names_and_lcd_dicts()
    _assets_json = get_asset_json_dict(assets_df=assets_df, chain_id_name_dict=_chain_id_name_dict)
    logging.info(f'chains in chain-registry: {len(_chain_id_name_dict.keys())}, '
                 f'chain indexed: {len(_assets_json.keys())}')

    with open('assetlist.schema.json', 'r') as asset_list_schema_file:
        _assetlist_schema_json = json.load(asset_list_schema_file)
    for _chain_id in _assets_json.keys():
        validate(instance=_assets_json[_chain_id], schema=_assetlist_schema_json)

    for _chain_id in _assets_json.keys():
        try:
            os.mkdir(path=f'data_json/{_chain_id_name_dict[_chain_id]}')
        except FileExistsError:
            pass
        with open(f'data_json/{_chain_id_name_dict[_chain_id]}/assetlist.json', 'w') as _assetlist_file:
            json.dump(obj=_assets_json[_chain_id], fp=_assetlist_file, ensure_ascii=False, indent=4)
    with open(f'data_json/all_assets.json', 'w') as all_assets_file:
        json.dump(obj=[_assets_json[chain_id] for chain_id in _assets_json.keys()],
                  fp=all_assets_file, ensure_ascii=False, indent=4)


def run_extract():
    # extract chain names and lcd paths from chain-registry
    _chain_id_name_dict, _chain_id_lcd_dict, _ = get_chain_names_and_lcd_dicts()
    logging.info(msg=f'start extraction {len(_chain_id_name_dict.keys()):>,} chains')

    # extract asset data from lcd apis
    for _chain_id, _node_lcd_url_list in list(_chain_id_lcd_dict.items()):
        logging.info(_chain_id)
        _asset_df = extract_assets(_chain_id, _node_lcd_url_list)
        if _asset_df is None:
            logging.info(f'data has not been loaded for {_chain_id}, lcd apis not work')
            continue
        _asset_df.to_csv(f'data_csv/assets_{_chain_id}.csv')
        logging.info(msg=f'extract {len(_asset_df):>,} assets for `{_chain_id}` chain_id')


def run_export():
    assets_df = load_csv_files()
    assets_df = enrich_asset_df(assets_df=assets_df)
    assets_df = assets_df.fillna(value={'description': '', 'denom_units': '', 'display': '', 'name': '', 'symbol': ''})
    save_to_csv(assets_df=assets_df)
    save_to_json(assets_df=assets_df)
    logging.info(msg=f'extracted {len(assets_df):>,} assets for {len(set(assets_df.chain_id.to_list()))} chains')


if __name__ == '__main__':
    if len(sys.argv) == 0:
        run_extract()
        run_export()
    elif 'extract' in sys.argv:
        run_extract()
    elif 'export' in sys.argv:
        run_export()
