import pandas as pd
from warnings import filterwarnings
from tqdm import tqdm
import requests
from typing import Optional, Union
import json
from urllib3.exceptions import TimeoutError
from requests.exceptions import ConnectionError, ReadTimeout

from config import logging


filterwarnings('ignore')
tqdm.pandas()


def get_denom_info(denom: str, node_lcd_url: str) -> [str, Optional[str]]:
    """
    Get a base demon and a path for ics20 asset
    :param denom: an asset denom in a network
    :param node_lcd_url: a node LCD url
    :return: a base demon and a path
    """
    if denom[:4] == 'ibc/':
        try:
            _res_json = requests.get(f'{node_lcd_url}/ibc/apps/transfer/v1/denom_traces/{denom[4:]}').json()[
                'denom_trace']
            return _res_json['base_denom'], _res_json['path']
        except Exception as _e:
            logging.error(f'Error: {_e}')
            return denom, 'Not found'
    else:
        return denom, None


def get_type_asset(denom: str) -> str:
    """
    Get an asset type by a denom
    :param denom: an asset denom
    :return: an asset type
    """
    if denom[:4] == 'ibc/':
        return 'ics20'
    if denom[:4] == 'pool' or denom[:10] == 'gamm/pool/':
        return 'pool'
    if denom[:5] == 'cw20:':
        return 'cw20'
    if denom[:9] == 'gravity0x':
        return 'erc20'
    if denom[:8] == 'factory/':
        return 'factory'
    return 'sdk.coin'


def get_assets_supply(node_lcd_url: str,
                      limit: int = 10_000) -> pd.DataFrame:
    """
    Get a dataframe with asset denom and supply
    :param node_lcd_url: node LCD url
    :param limit: max number of query result items
    :return: a dataframe with denom and supply columns
    """
    _assets_supply_json = requests.get(
        url=f'{node_lcd_url}/cosmos/bank/v1beta1/supply?pagination.limit={limit}',
        timeout=5
    ).json()['supply']
    return pd.DataFrame(_assets_supply_json).rename(columns={'amount': 'supply'})


def get_assets_metadata(node_lcd_url: str,
                        limit: int = 10_000) -> pd.DataFrame:
    """
    Get a dataframe with asset metadata
    :param node_lcd_url: node LCD url
    :param limit: max number of query result items
    :return: a dataframe with asset metadata
    """
    _assets_metadata_json = requests.get(
        url=f'{node_lcd_url}/cosmos/bank/v1beta1/denoms_metadata?pagination.limit={limit}'
    ).json()['metadatas']
    return pd.DataFrame(_assets_metadata_json).rename(columns={'base': 'denom'})


def get_channel_id_counterparty_dict(node_lcd_url: str,
                                     limit: int = 10_000) -> dict:
    """
    Get a dictionary from channel id to counterparty channel id
    :param node_lcd_url: node LCD url
    :param limit: max number of query result items
    :return: a dictionary from channel id to counterparty channel id
    """
    _channels_json = requests.get(
        url=f'{node_lcd_url}/ibc/core/channel/v1/channels?pagination.limit={limit}'
    ).json()['channels']
    return {_channel['channel_id']: _channel['counterparty']['channel_id'] for _channel in _channels_json}


def get_chain_id_counterparty_dict(channels: Union[list[str], set[str]],
                                   node_lcd_url: str,
                                   port_id: str = 'transfer') -> dict[str, Optional[str]]:
    """
    Get a dictionary from channel id to counterparty chain id
    :param channels: list of channels
    :param node_lcd_url: node LCD url
    :param port_id: port id
    :return: dictionary from channel id to counterparty chain id
    """
    def _get_counterparty_chain_id(channel: str, port_id: str, node_lcd_url: str) -> Optional[str]:
        try:
            return requests.get(
                url=f'{node_lcd_url}/ibc/core/channel/v1/channels/{channel}/ports/{port_id}/client_state'
                ).json()['identified_client_state']['client_state']['chain_id']
        except KeyError:
            logging.error(f'Key error in get_chain_id_counterparty_dict: '
                          f'channel {channel}, node_lcd_url {node_lcd_url}, port_id {port_id}')
            return None
    return {_channel: _get_counterparty_chain_id(channel=_channel, port_id=port_id, node_lcd_url=node_lcd_url)
            for _channel in tqdm(channels)}


def get_assets(chain_id: str,
               node_lcd_url: str,
               port_id: str = 'transfer',
               limit: int = 10_000) -> pd.DataFrame:
    """
    Get dataframe with assets data for a given network and a given network lcd
    :param chain_id: chain id
    :param node_lcd_url: node LCD url
    :param port_id: connection port id
    :param limit: maximum amount of assets
    :return: dataframe with asset data
    """
    _assets_supply_df = get_assets_supply(node_lcd_url=node_lcd_url, limit=limit)
    _asset_metadata_df = get_assets_metadata(node_lcd_url=node_lcd_url)

    if not _asset_metadata_df.empty:
        _assets_df = _assets_supply_df.merge(_asset_metadata_df,
                                             on='denom',
                                             how='left')
    else:
        _assets_df = _assets_supply_df

    _assets_df.loc[:, ['denom_base', 'path']] = \
        _assets_df.progress_apply(
            lambda row: pd.Series(
                data=get_denom_info(
                    denom=row['denom'],
                    node_lcd_url=node_lcd_url)),
            axis=1).to_numpy()

    _assets_df['channels'] = \
        _assets_df.path.map(
            lambda path: path.replace('/transfer/', 'transfer/').split('transfer/')[1:] if path is not None else None)
    _assets_df['one_channel'] = \
        _assets_df.channels.map(
            lambda _channels: len(_channels) == 1 if _channels is not None else None)

    _channel_set = set([item[0] for item in _assets_df.channels.to_list() if item is not None and len(item) > 0])
    _channel_chain_id_dict = get_chain_id_counterparty_dict(channels=_channel_set,
                                                            node_lcd_url=node_lcd_url,
                                                            port_id=port_id)
    _channel_id_counterparty_dict = get_channel_id_counterparty_dict(node_lcd_url=node_lcd_url)
    _assets_df['chain_id_counterparty'] = \
        _assets_df.channels.map(
            lambda _channels: _channel_chain_id_dict[_channels[0]] if _channels is not None and len(
                _channels) > 0 else None)
    _assets_df['channel_id_counterparty'] = \
        _assets_df.channels.map(
            lambda _channels: _channel_id_counterparty_dict[_channels[0]] if _channels is not None and len(
                _channels) > 0 else None)
    _assets_df['type_asset'] = _assets_df.denom.map(get_type_asset)
    _assets_df['type_asset_base'] = _assets_df.denom_base.map(get_type_asset)
    _assets_df['chain_id'] = chain_id
    return _assets_df


def extract_assets(chain_id: str, node_lcd_url_list: list[str]) -> Optional[pd.DataFrame]:
    """
    Get dataframe with assets data for a given network by lcd list
    :param chain_id: network chain id
    :param node_lcd_url_list: list of node lcd urls
    :return: dataframe with asset data
    """
    _asset_df = None
    for _node_lcd_url in node_lcd_url_list[::-1]:
        try:
            logging.info(f'node lcd url:  {_node_lcd_url}')
            _asset_df = get_assets(chain_id=chain_id, node_lcd_url=_node_lcd_url)
            break
        except (ConnectionError, ReadTimeout, TimeoutError, json.JSONDecodeError):
            logging.error(f'no connection for {chain_id} to lcd {_node_lcd_url}')
        except Exception as e:
            logging.error(f'no connection for {chain_id} to lcd {_node_lcd_url}. Error: {e}')
    return _asset_df
