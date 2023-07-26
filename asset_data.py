import json
import os
import ast
from argparse import ArgumentParser

import pandas as pd
from warnings import filterwarnings
from tqdm import tqdm
from jsonschema import validate

from config import logging, CONTRACT_ADDRESSES, LCD_CLIENTS, WALLETS, WALLET_ADDRESSES, FEE_DENOMS, EXPORT_CHAINS
from src.lcd_extractor import extract_assets, get_cw20_token_info
from src.chain_registry_extractor import get_chain_names_and_lcd_dicts
from src.json_export import get_asset_json_dict
from src.contract_export import save_to_contract

filterwarnings('ignore')
tqdm.pandas()


def load_intermediate_csv_files(dir_csv: str = 'data_csv') -> pd.DataFrame:
    """
    Load data from intermediate csv files
    :param dir_csv: path of a directory with intermediate csv files
    :return: dataframe with asset metadata
    """
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


def add_cw20(
        assets_df: pd.DataFrame,
        chain_id_lcd_dict: dict[str, list[str]],
        chain_id_name_dict: dict[str, str]) -> pd.DataFrame:
    """
    Add cw20 metadata for cw20 assets transferred by ibc protocol
    :param assets_df: dataframe with asset metadata
    :param chain_id_lcd_dict: dictionary of lcd apis by chain names
    :param chain_id_name_dict: dictionary of chain ids by chain names
    :return: asset metadata dataframe with cw20 assets
    """
    _cw20_token_info_list = []
    for _chain_id, _assets in assets_df[(assets_df.type_asset_base == 'cw20') & (assets_df.one_channel == True)][
        ['chain_id_counterparty', 'denom_base']].drop_duplicates().groupby('chain_id_counterparty'):
        if _chain_id not in chain_id_lcd_dict.keys():
            logging.error(f'{_chain_id} not in chain_id_lcd_dict')
            continue
        logging.info(f'Extract cw20 data for {_chain_id}')
        for _denom in tqdm(_assets['denom_base'].to_list()):
            _contract = _denom[5:]
            _cw20_token_info = None
            for _node_lcd_url in chain_id_lcd_dict[_chain_id]:
                try:
                    _cw20_token_info = get_cw20_token_info(contract_address=_denom[5:], node_lcd_url=_node_lcd_url)
                except KeyError:
                    print(f'KeyError: chain_id {_chain_id}, _node_lcd_url {_node_lcd_url} contract_address {_contract}')
                except Exception as e:
                    print(f'{e}: chain_id {_chain_id}, _node_lcd_url {_node_lcd_url} contract_address {_contract}')
                if _cw20_token_info:
                    break
            if _cw20_token_info and 'code' not in _cw20_token_info.keys():
                _cw20_token_info['denom'] = _denom
                _cw20_token_info['chain_id'] = _chain_id
                _cw20_token_info['chain_name'] = chain_id_name_dict[_chain_id]
                _cw20_token_info['type_asset'] = 'cw20'
                _cw20_token_info_list.append(_cw20_token_info)

    _cw20_token_info_df = pd.DataFrame(_cw20_token_info_list)
    _cw20_token_info_df['denom_units'] = _cw20_token_info_df.apply(
        lambda x: [{
            "denom": x.symbol.lower(),
            "exponent": x.decimals,
            "aliases": [x.symbol]
        }],
        axis=1)
    _cw20_token_info_df = _cw20_token_info_df.rename(columns={'total_supply': 'supply'})[
        ['chain_name', 'chain_id', 'denom', 'type_asset', 'supply', 'denom_units', 'name', 'symbol']]

    return assets_df.append(_cw20_token_info_df)


def enrich_asset_df(
        assets_df: pd.DataFrame,
        chain_id_name_dict: dict[str, str]) -> pd.DataFrame:
    """
    Enrich ics20 asset metadata by adding base asset metadata
    :param assets_df: dataframe with asset metadata
    :param chain_id_name_dict: dictionary of chain ids by chain names
    :return: asset metadata dataframe with ics20 base asset metadata
    """
    _assets_one_channel_df = \
        assets_df[assets_df.one_channel == True][['denom', 'supply', 'chain_id', 'denom_base', 'path', 'channels',
                                                  'chain_id_counterparty', 'channel_id_counterparty', 'type_asset',
                                                  'one_channel', 'type_asset_base']].merge(
            assets_df[
                ['denom', 'supply', 'chain_id', 'description', 'denom_units', 'display', 'name', 'symbol', 'admin']]
            .rename(columns={'supply': 'supply_base', 'chain_id': 'chain_id_base', 'denom': 'denom_base'}),
            how='left',
            left_on=['chain_id_counterparty', 'denom_base'],
            right_on=['chain_id_base', 'denom_base']
        )
    _assets_not_one_channel_df = assets_df[assets_df.one_channel != True]
    _assets_not_one_channel_df['supply_base'] = _assets_not_one_channel_df.apply(
        lambda _row: _row['supply'] if _row['one_channel'] is None else None, axis=1)
    _assets_not_one_channel_df['chain_id_base'] = _assets_not_one_channel_df.apply(
        lambda _row: _row['chain_id'] if _row['one_channel'] == True else None, axis=1)

    _assets_df = pd.concat([
        _assets_one_channel_df,
        _assets_not_one_channel_df]).reset_index(drop=True)

    _assets_df['chain_name'] = _assets_df.chain_id.map(
        lambda _chain_id: chain_id_name_dict[_chain_id] if _chain_id in chain_id_name_dict.keys() else '')

    return _assets_df[[
        'chain_name', 'chain_id', 'denom', 'type_asset', 'supply', 'description', 'denom_units', 'display', 'name',
        'symbol', 'uri', 'denom_base', 'type_asset_base', 'path', 'channels', 'chain_id_counterparty',
        'channel_id_counterparty', 'supply_base', 'chain_id_base', 'one_channel', 'admin']]


def save_to_csv(
        assets_df: pd.DataFrame,
        file_path: str = 'data_csv/all_assets.csv') -> None:
    """
    Save an assets metadata dataframe to a csv file
    :param assets_df: an assets metadata dataframe
    :param file_path: csv file path
    :return: none
    """
    assets_df.to_csv(file_path)


def save_to_json(
        assets_df: pd.DataFrame,
        chain_id_name_dict: dict[str, str]) -> None:
    """
    Save an assets metadata dataframe to a json files
    :param assets_df: an assets metadata dataframe
    :param chain_id_name_dict: dictionary of chain ids by chain names
    :return: none
    """
    _assets_json = get_asset_json_dict(assets_df=assets_df, chain_id_name_dict=chain_id_name_dict)
    logging.info(f'chains in chain-registry: {len(chain_id_name_dict.keys())}, '
                 f'chain indexed: {len(_assets_json.keys())}')

    with open('assetlist.schema.json', 'r') as asset_list_schema_file:
        _assetlist_schema_json = json.load(asset_list_schema_file)
    for _chain_id in _assets_json.keys():
        validate(instance=_assets_json[_chain_id], schema=_assetlist_schema_json)

    for _chain_id in _assets_json.keys():
        try:
            os.mkdir(
                path=f'data_json/'
                     f'{chain_id_name_dict[_chain_id] if _chain_id in chain_id_name_dict.keys() else _chain_id}')
        except FileExistsError:
            pass
        with open(
                f'data_json/{chain_id_name_dict[_chain_id] if _chain_id in chain_id_name_dict.keys() else _chain_id}'
                f'/assetlist.json',
                'w') as _assetlist_file:
            json.dump(obj=_assets_json[_chain_id], fp=_assetlist_file, ensure_ascii=False, indent=4)
    with open(f'data_json/all_assets.json', 'w') as all_assets_file:
        json.dump(obj=[_assets_json[chain_id] for chain_id in _assets_json.keys()],
                  fp=all_assets_file, ensure_ascii=False, indent=4)


def run_extract() -> None:
    """
    Extract asset metadata and store it to intermediate csv files
    :return: none
    """
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


def run_export() -> None:
    """
    Export asset metadata to the csv file, json files and contracts
    :return: none
    """
    _chain_id_name_dict, chain_id_lcd_dict, _ = get_chain_names_and_lcd_dicts()
    _assets_df = load_intermediate_csv_files()
    _assets_df = add_cw20(assets_df=_assets_df, chain_id_lcd_dict=chain_id_lcd_dict,
                          chain_id_name_dict=_chain_id_name_dict)
    _assets_df = enrich_asset_df(assets_df=_assets_df, chain_id_name_dict=_chain_id_name_dict)
    _assets_df = _assets_df.fillna(
        value={'description': '', 'denom_units': '', 'display': '', 'name': '', 'symbol': '', 'admin': '',
               'denom_base': ''})
    save_to_csv(assets_df=_assets_df)
    save_to_json(assets_df=_assets_df, chain_id_name_dict=_chain_id_name_dict)
    for _chain_name in EXPORT_CHAINS:
        save_to_contract(
            contract_address=CONTRACT_ADDRESSES[_chain_name],
            lcd_client=LCD_CLIENTS[_chain_name],
            wallet=WALLETS[_chain_name],
            wallet_address=WALLET_ADDRESSES[_chain_name],
            fee_denom=FEE_DENOMS[_chain_name],
        )
    logging.info(msg=f'exported {len(_assets_df):>,} assets for {len(set(_assets_df.chain_id.to_list()))} chains')


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("--extract", default=True)
    parser.add_argument("--export", default=True)
    args = parser.parse_args()

    extract_bool = bool(args.extract)
    export_bool = bool(args.export)

    if extract_bool:
        run_extract()
    if export_bool:
        run_export()
