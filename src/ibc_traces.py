import pandas as pd
from tqdm import tqdm
from typing import Optional


def get_ibc_asset_section(row: pd.Series) -> dict:
    """
    Get ibc section for an ics20(IBC) asset
    :param row: an asset row
    :return: a value of asset ibc section
    """
    if row['type_asset'] != 'ics20' or type(row['channels']) != list or \
             pd.isna(row['chain_id_counterparty']):
        return {}
    return {
        "source_channel": row['channels'][0],
        "dst_channel": row['channel_id_counterparty'],
        "source_denom": row['denom_source'] if not pd.isna(row['denom_source']) else ''
    }


def get_traces_asset_section(row: pd.Series, chain_id_name_dict: dict) -> Optional[list[dict]]:
    """
    Get traces section for an ics20(IBC) asset
    :param row: an asset row
    :param chain_id_name_dict: dictionary of chain ids by chain names
    :return: a value of asset traces section
    """
    if row['type_asset'] != 'ics20' or type(row['channels']) != list or pd.isna(row['chain_id_counterparty']):
        return []
    _chain_name_counterparty = chain_id_name_dict.get(row['chain_id_counterparty'], None)
    if row['type_asset_source'] in ('sdk.coin', 'pool', 'factory', 'ics20', 'cw20'):
        _traces = [{
            "type": 'ibc' if row['type_asset_source'] in ('sdk.coin', 'pool', 'factory', 'ics20') else 'ibc-cw20',
            "counterparty": {
                "chain_id": row['chain_id_counterparty'],
                "channel_id": row['channel_id_counterparty'],
                "base_denom": row['denom_source'] if not pd.isna(row['denom_source']) else ''
            },
            "chain": {
                "channel_id": row['channels'][0],
                "path": f"{row['path']}/{row['denom_base']}"
            }
        }]
        if _chain_name_counterparty:
            _traces[0]["counterparty"]["chain_name"] = _chain_name_counterparty
        if row['supply_source'] and not pd.isna(row['supply_source']):
            _traces[0]["counterparty"]["base_supply"] = int(row['supply_source'])
        if row['type_asset_source'] == 'cw20':
            _traces[0]["chain"]["port"] = 'transfer'
            _traces[0]["counterparty"]["port"] = 'transfer'
        if type(row['traces_source']) == list:
            _traces.extend(row['traces_source'])
        return _traces


def add_ibc_metadata(
        assets_df: pd.DataFrame,
        chain_id_name_dict: dict) -> pd.DataFrame:
    """
    Add base asset metadata and IBC traces for ics20 assets
    :param assets_df: dataframe with asset metadata
    :param chain_id_name_dict: dictionary of chain ids by chain names
    :return: asset metadata dataframe with ics20 base asset metadata
    """
    _assets_df = assets_df.copy()
    _assets_df.loc[_assets_df.channels_number == 0, 'supply_base'] = _assets_df[_assets_df.channels_number == 0].supply
    _assets_df.loc[_assets_df.channels_number == 0, 'chain_id_base'] = _assets_df[
        _assets_df.channels_number == 0].chain_id
    _assets_df.loc[_assets_df.channels_number > 1, f'path_deep_1'] = \
        _assets_df[_assets_df.channels_number > 1].channels.map(
            lambda _channels: 'transfer/' + '/transfer/'.join(_channels[1:]))
    _assets_df['traces'] = None
    _assets_df['ibc'] = None

    for i in tqdm(range(1, _assets_df.channels_number.max() + 1)):

        _assets_channel_df = _assets_df[_assets_df.channels_number == i][
            ['denom', 'supply', 'chain_id', 'denom_base', 'path', 'path_deep_1', 'channels',
             'chain_id_counterparty', 'channel_id_counterparty', 'type_asset',
             'channels_number', 'type_asset_base']].merge(
            _assets_df[_assets_df.channels_number == i - 1][
                ['denom', 'denom_base', 'supply', 'chain_id', 'path', 'description', 'denom_units', 'display', 'name',
                 'symbol', 'type_asset', 'supply_base', 'chain_id_base', 'admin', 'traces']] \
                .rename(columns={'supply': 'supply_source',
                                 'chain_id': 'chain_id_counterparty',
                                 'denom': 'denom_source',
                                 'type_asset': 'type_asset_source',
                                 'path': 'path_deep_1',
                                 'traces': 'traces_source'}),
            how='left',
            left_on=['chain_id_counterparty', 'denom_base', 'path_deep_1'],
            right_on=['chain_id_counterparty', 'denom_base', 'path_deep_1'])

        _assets_channel_df['ibc'] = _assets_channel_df.apply(get_ibc_asset_section, axis=1)
        _assets_channel_df['traces'] = _assets_channel_df.apply(
            lambda _row: get_traces_asset_section(row=_row, chain_id_name_dict=chain_id_name_dict), axis=1)

        _assets_df = pd.concat([
            _assets_channel_df,
            _assets_df[_assets_df.channels_number != i]
        ]).reset_index(drop=True)

    return _assets_df[[
        'chain_id', 'denom', 'type_asset', 'supply', 'description', 'denom_units', 'display', 'name',
        'symbol', 'uri', 'denom_base', 'type_asset_base', 'type_asset_source', 'path', 'channels',
        'chain_id_counterparty', 'supply_base', 'chain_id_base', 'channels_number', 'admin', 'ibc', 'traces']]
