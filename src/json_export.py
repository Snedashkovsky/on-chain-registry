import pandas as pd
import json
import os
from jsonschema import validate

from config import logging


def get_asset_json(
        row: pd.Series,
        save_supply: bool = False) -> dict:
    """
    Get json for asset
    :param row: an asset row
    :param save_supply: save or not `supply` and `base_supply`
    :return: an asset json
    """
    _asset_json = {
        "base": row['denom'],
        "type_asset": row['type_asset']
    }

    if save_supply:
        _asset_json['supply'] = int(row['supply']) if row['supply'] and not pd.isna(row['supply']) else 0

    if row['traces']:
        if save_supply:
            _asset_json['traces'] = row['traces']
        else:
            _traces = row['traces'].copy()
            for _trace in _traces:
                _trace['counterparty'].pop('base_supply', None)
            _asset_json['traces'] = _traces

    if row['denom_units']:
        _asset_json['denom_units'] = [dict(sorted(_denom_unit.items())) for _denom_unit in row['denom_units']]

    for _field in ['description', 'denom_units', 'display', 'name', 'symbol', 'ibc']:
        if row[_field]:
            _asset_json[_field] = row[_field]

    if row['type_asset'] == 'cw20':
        _asset_json['address'] = row['denom_base'][5:]

    if row['type_asset'] == 'erc20' and row['denom'][:9] == 'gravity0x':
        _asset_json['address'] = row['denom_base'][7:]

    if row['type_asset'] == 'snip20':
        # asset_json['address'] =   # Add
        pass

    if row['type_asset'] == 'factory':
        _asset_json['address'] = row['denom']
        _asset_json['admin'] = row['admin']

    return dict(sorted(_asset_json.items()))


def get_asset_json_dict(
        assets_df: pd.DataFrame,
        chain_id_name_dict: dict[str, str],
        save_supply: bool = False) -> dict[str, dict]:
    """
    Get json with all assets
    :param assets_df: an assets dataframe
    :param chain_id_name_dict: dictionary of chain ids by chain names
    :param save_supply: save or not `supply` and `base_supply`
    :return: json with all assets
    """
    _assets_json = {}
    for _chain_id, _assets_item_df in assets_df.groupby('chain_id'):
        _asset_json_list = [get_asset_json(row=row, save_supply=save_supply) for _, row in
                            _assets_item_df.iterrows()]
        try:
            _assets_json[_chain_id] = {
                "chain_name": chain_id_name_dict[_chain_id],
                "chain_id": _chain_id,
                "assets": _asset_json_list
            }
        except KeyError:
            logging.info(f'! no have chain_id {_chain_id}, assets in on-chain registry {_asset_json_list}')
    return _assets_json


def save_to_json(
        assets_df: pd.DataFrame,
        chain_id_name_dict: dict[str, str],
        save_supply: bool = False) -> None:
    """
    Save an assets metadata dataframe to a json files
    :param assets_df: an assets metadata dataframe
    :param chain_id_name_dict: dictionary of chain ids by chain names
    :param save_supply: save or not `supply` and `base_supply`
    :return: none
    """
    _assets_json = get_asset_json_dict(
        assets_df=assets_df,
        chain_id_name_dict=chain_id_name_dict,
        save_supply=save_supply)
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
