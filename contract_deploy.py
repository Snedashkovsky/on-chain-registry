import json
from typing import Optional
from argparse import ArgumentParser

from cyberutils.bash import execute_bash

from config import logging, CHAIN_IDS, NODE_RPC_URLS, WALLET_ADDRESSES, CONTRACT_NAMES, CODE_IDS


def build_code(
        contract_code_path: str = './cw-on-chain-registry/contracts/on-chain-registry'
) -> tuple[Optional[str], Optional[str]]:
    """
    Build code by cw-optimizoor
    :param contract_code_path: source code path
    :return: none
    """
    return execute_bash(
        bash_command=f"cd {contract_code_path} && cargo cw-optimizoor",
        shell=True)


def store_code(
        wallet_address: str,
        chain_id: str,
        note: str,
        node_rpc_url: str,
        cli_name: str = 'cyber',
        gas: int = 20_000_000) -> Optional[str]:
    """
    Store a code to a chain by a cli
    :param wallet_address: sender address
    :param chain_id: chain id
    :param note: transaction note
    :param node_rpc_url: node rpc url
    :param cli_name: cli name for bash query
    :param gas: gas limit
    :return: code id
    """
    print(f"{cli_name} tx wasm store ./cw-on-chain-registry/artifacts/on_chain_registry-aarch64.wasm "
          f"--from={wallet_address} --chain-id={chain_id} --broadcast-mode=block --note='{note}' "
          f"--gas={gas} -y -o=json --node={node_rpc_url}")
    _res, _ = execute_bash(
        bash_command=f"{cli_name} tx wasm store ./cw-on-chain-registry/artifacts/on_chain_registry-aarch64.wasm "
                     f"--from={wallet_address} --chain-id={chain_id} --broadcast-mode=block --note='{note}' "
                     f"--gas={gas} -y -o=json --node={node_rpc_url}",
        shell=True)
    try:
        _code_id = json.loads(_res)['logs'][0]['events'][-1]['attributes'][0]['value']
        return _code_id
    except IndexError:
        logging.error(_res)


def instantiate_contract(
        init_query: str,
        code_id: str,
        contract_label: str,
        from_address: str,
        chain_id: str,
        node_rpc_url: str,
        gas: int,
        cli_name: str = 'cyber',
        contract_admin: Optional[str] = None,
        amount: str = '',
        display_data: bool = False) -> str:
    """
    Instantiate a contract by a cli
    :param init_query: Instantiate query
    :param code_id: code id
    :param contract_label: contract label
    :param from_address: sender address
    :param chain_id: chain id
    :param node_rpc_url: node rpc url
    :param cli_name: cli name
    :param gas: gas limit
    :param contract_admin: address of a contract admin
    :param amount: coins to send to a contract during instantiation
    :param display_data: display transaction data or not
    :return: contract address
    """
    _init_output, _init_error = execute_bash(
        f'''INIT='{init_query}' \
            && {cli_name} tx wasm instantiate {code_id} "$INIT" --from={from_address} \
            {'--amount=' + amount if amount else ''} --label="{contract_label}" \
            {'--admin=' + contract_admin if contract_admin else '--no-admin'} \
            -y --gas={gas} --broadcast-mode=block -o=json --chain-id={chain_id} --node={node_rpc_url}''',
        shell=True)
    if display_data:
        try:
            logging.info(json.dumps(json.loads(_init_output), indent=4, sort_keys=True))
        except json.JSONDecodeError:
            logging.error(_init_output)
    if _init_error:
        logging.error(_init_error)
    _init_json = json.loads(_init_output)
    return [event['attributes'][0]['value']
            for event in _init_json['logs'][0]['events']
            if event['type'] == 'instantiate'][0]


def init_on_chain_registry_contract(
        executors_addresses: list[str],
        admins_addresses: list[str],
        wallet_address: str,
        code_id: str,
        contract_label: str,
        chain_id: str,
        node_rpc_url: str,
        gas: int = 4_000_000,
        cli_name: str = 'cyber',
        contract_admin: Optional[str] = None,
        display_data: bool = True) -> str:
    """
    Instantiate an `on-chain registry` contract by a cli
    :param executors_addresses: addresses of contract executors is specific to `on-chain registry` contract
    :param admins_addresses: addresses of contract admins is specific to `on-chain registry` contract
    :param wallet_address: address of a transaction sender
    :param code_id: code id
    :param contract_label: contract label
    :param chain_id: chain id
    :param node_rpc_url: node rpc url
    :param gas: gas limit
    :param cli_name: cli name
    :param contract_admin: address of a contract admin
    :param display_data: display transaction data or not
    :return: contract address
    """
    _init_query = \
        f'''{{"executors":["{'", "'.join(executors_addresses)}"], "admins":["{'", "'.join(admins_addresses)}"]}}'''
    _contract_address = \
        instantiate_contract(
            init_query=_init_query,
            code_id=code_id,
            contract_label=contract_label,
            from_address=wallet_address,
            chain_id=chain_id,
            node_rpc_url=node_rpc_url,
            gas=gas,
            cli_name=cli_name,
            contract_admin=contract_admin,
            display_data=display_data)
    return _contract_address


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("--chain_name", default='bostrom')
    parser.add_argument("--build_code", default=False)
    parser.add_argument("--store_code", default=False)
    parser.add_argument("--init_contract", default=False)
    args = parser.parse_args()

    chain_name = args.chain_name if args.chain_name else 'bostrom'
    build_code_bool = bool(args.build_code)
    store_code_bool = bool(args.store_code)
    init_contract_bool = bool(args.init_contract)

    assert chain_name in CHAIN_IDS.keys()

    if build_code_bool:
        build_code()
        logging.info(f'the code has been built')

    if store_code_bool:
        code_id = store_code(
            wallet_address=WALLET_ADDRESSES[chain_name],
            note=CONTRACT_NAMES[chain_name],
            chain_id=CHAIN_IDS[chain_name],
            node_rpc_url=NODE_RPC_URLS[chain_name]
        )
        if code_id:
            logging.info(f'the code has been stored in {chain_name}, code id {code_id}.\nplease update `config.py`')
    else:
        code_id = CODE_IDS[chain_name]

    if init_contract_bool:
        contract_address = init_on_chain_registry_contract(
            executors_addresses=[WALLET_ADDRESSES[chain_name]],
            admins_addresses=[WALLET_ADDRESSES[chain_name]],
            wallet_address=WALLET_ADDRESSES[chain_name],
            code_id=code_id,
            contract_label=CONTRACT_NAMES[chain_name],
            chain_id=CHAIN_IDS[chain_name],
            node_rpc_url=NODE_RPC_URLS[chain_name]
        )
        if contract_address:
            logging.info(f'the contract has been instantiated in {chain_name} network, '
                         f'contract address {contract_address}.\nplease update `config.py`')
