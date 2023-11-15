import json
import pandas as pd
from tqdm import tqdm
import requests
import base64
from time import sleep

from cyber_sdk.client.lcd import LCDClient, Wallet
from cyber_sdk.client.lcd.api.tx import BlockTxBroadcastResult
from cyberutils.contract import execute_contract

from config import logging, CONTRACT_ADDRESSES, LCD_CLIENTS, WALLETS, WALLET_ADDRESSES, FEE_DENOMS, EXPORT_CHAINS


def batch(x: list, batch_size: int) -> list[list]:
    return [x[_i: _i + batch_size] for _i in range(0, len(x), batch_size)]


def contract_query(
        contract_address: str,
        query: dict,
        node_lcd_url: str,
        display_query: bool = False) -> dict:
    """
    Query contract
    :param contract_address: contract address
    :param query: contract query
    :param node_lcd_url: node lcd url
    :param display_query: display a query url or not
    :return: query result
    """
    _query_msg = base64.b64encode(json.dumps(query).encode("utf-8")).decode("utf-8")
    _query = f'{node_lcd_url}/cosmwasm/wasm/v1/contract/{contract_address}/smart/{_query_msg}'
    if display_query:
        logging.info(_query)
    return requests.get(_query).json()


def get_asset_json_list(
        all_asset_path: str = 'data_json/all_assets.json',
        save_supply: bool = False) -> list[dict]:
    """
    Get list of asset data
    :param all_asset_path: path of file with all assets
    :param save_supply: save or not `supply` and `base_supply`
    :return: list of asset jsons
    """
    with open(all_asset_path, 'r') as _all_assets_file:
        _all_assets_json = json.load(_all_assets_file)

    _assets_list = []
    for _assets_json in tqdm(_all_assets_json):
        _assets = _assets_json['assets']
        for i in range(len(_assets)):
            _assets[i]['supply'] = str(_assets[i]['supply']) if save_supply else None
            _assets[i]['chain_name'] = _assets_json['chain_name']
            _assets[i]['chain_id'] = _assets_json['chain_id']
            if 'traces' in _assets[i].keys():
                for _trace in _assets[i]['traces']:
                    if 'base_supply' in _trace.keys() and save_supply:
                        _trace['base_supply'] = str(_trace['base_supply'])
                    if 'counterparty' in _trace.keys() and 'base_supply' in _trace['counterparty'].keys():
                        _trace['counterparty']['base_supply'] = \
                            str(_trace['counterparty']['base_supply']) if save_supply else None
                    if 'type' in _trace.keys():
                        _trace['trace_type'] = _trace.pop('type')
        _assets_list.extend(_assets)
    return _assets_list


def save_to_contract(
        contract_address: str,
        lcd_client: LCDClient,
        wallet: Wallet,
        wallet_address: str,
        fee_denom: str,
        all_asset_path: str = 'data_json/all_assets.json',
        batch_size: int = 128,
        gas: int = 24_000_000,
        memo: str = 'update assets in on-chain registry  github.com/Snedashkovsky/on-chain-registry',
        save_supply: bool = False) -> list[BlockTxBroadcastResult]:
    """
    Save asset data to a contract
    :param all_asset_path: path of file with all assets
    :param batch_size: number of updated assets in one transaction
    :param contract_address: contract address
    :param lcd_client: LCD client
    :param wallet: sender wallet
    :param wallet_address: sender address
    :param fee_denom: transaction fee denom
    :param gas: gas amount
    :param memo: transaction memo
    :param save_supply: save or not `supply` and `base_supply`
    :return: list of transaction results
    """

    _assets_list = get_asset_json_list(all_asset_path=all_asset_path, save_supply=save_supply)

    _res_list = []
    for _assets_batch in tqdm(batch(_assets_list, batch_size)):
        logging.info(
            'Export to contract   ' + ', '.join(
                [f'{k} {v:>,}'
                 for k, v in
                 pd.DataFrame(_assets_batch).groupby('chain_name')['chain_name'].agg(pd.value_counts).to_dict().items()]
            )
        )
        _res = execute_contract(
            execute_msgs=[{'UpdateAssets': {
                'assets': _assets_batch}}],
            contract_address=contract_address,
            lcd_client=lcd_client,
            fee_denom=fee_denom,
            wallet=wallet,
            sender=wallet_address,
            memo=memo,
            gas=gas,
            fee_amount=int(gas * 0.0025) if wallet_address[:4] == 'osmo' else 0
        )
        if _res is None:
            sleep(10)
        _res_list.append(_res)
        if len(str(_res)) < 500:
            logging.error(_res)

    return _res_list


def save_to_contracts(save_supply: bool = False) -> None:
    """
    Save metadata to OCR contracts
    :param save_supply: save or not `supply` and `base_supply`
    :return: none
    """
    for _chain_name in EXPORT_CHAINS:
        logging.info(f'Export to {_chain_name} contract')
        save_to_contract(
            contract_address=CONTRACT_ADDRESSES[_chain_name],
            lcd_client=LCD_CLIENTS[_chain_name],
            wallet=WALLETS[_chain_name],
            wallet_address=WALLET_ADDRESSES[_chain_name],
            fee_denom=FEE_DENOMS[_chain_name],
            save_supply=save_supply
        )
