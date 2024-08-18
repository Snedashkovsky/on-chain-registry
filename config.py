import logging
import sys
from dotenv import dotenv_values
import warnings

from cyber_sdk.client.lcd import LCDClient
from cyber_sdk.key.mnemonic import MnemonicKey

# logging config
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%d-%m-%Y %H:%M:%S',
                    handlers=[logging.FileHandler("on-chain-registry.log"),
                              logging.StreamHandler(sys.stdout)])

# extra chains
PUSSY_CHAIN_ID = 'space-pussy'
PUSSY_CHAIN_NAME = 'space-pussy'
PUSSY_NODE_LCD_URL = 'https://lcd.space-pussy.cybernode.ai'
INIT_CHAIN_ID_NAME_DICT = {PUSSY_CHAIN_ID: PUSSY_CHAIN_NAME}
INIT_CHAIN_ID_LCD_DICT = {PUSSY_CHAIN_ID: [PUSSY_NODE_LCD_URL]}

# for contract instantiations
CONTRACT_NAMES = {
    'bostrom': 'on-chain-registry  github.com/Snedashkovsky/on-chain-registry',
    'localbostrom': 'on-chain-registry  github.com/Snedashkovsky/on-chain-registry',
    'osmosis-testnet': 'on-chain-registry  github.com/Snedashkovsky/on-chain-registry'
}
CODE_IDS = {
    'bostrom': '33',
    'localbostrom': '57',
    'osmosis-testnet': '3352'
}

# for export to contracts
EXPORT_CHAINS = ['bostrom', 'osmosis-testnet']
CHAIN_IDS = {
    'bostrom': 'bostrom',
    'localbostrom': 'localbostrom',
    'osmosis-testnet': 'osmo-test-5'
}
PREFIXES = {
    'bostrom': 'bostrom',
    'localbostrom': 'bostrom',
    'osmosis-testnet': 'osmo'
}
FEE_DENOMS = {
    'bostrom': 'boot',
    'localbostrom': 'boot',
    'osmosis-testnet': 'uosmo'
}
NODE_RPC_URLS = {
    'bostrom': 'https://rpc.bostrom.cybernode.ai:443',
    'localbostrom': 'http://localhost:26657',
    'osmosis-testnet': 'https://rpc.testnet.osmosis.zone:443'
}
NODE_LCD_URLS = {
    'bostrom': 'https://lcd.bostrom.cybernode.ai',
    'localbostrom': 'http://localhost:1317',
    'osmosis-testnet': 'https://lcd.testnet.osmosis.zone'
}
CONTRACT_ADDRESSES = {
    'bostrom': 'bostrom1w33tanvadg6fw04suylew9akcagcwngmkvns476wwu40fpq36pms92re6u',
    'localbostrom': 'bostrom1l2rs0hxzfy343z8n6punpj9gwzrsq644nzzls6dql52jjj2nxncqjn5vg3',
    'osmosis-testnet': 'osmo1nwesd2xe6cnvtpqd29xg7qeznlm65x02lfjfg20wlvkdze20hcxsftxtzz'
}

LCD_CLIENTS = {_network: LCDClient(url=NODE_LCD_URLS[_network],
                                   chain_id=CHAIN_IDS[_network],
                                   prefix=PREFIXES[_network])
               for _network in CHAIN_IDS.keys()}
WALLET_SEED = dotenv_values('.env').get('WALLET_SEED', '')
if not WALLET_SEED:
    warnings.warn('WALLET_SEED not set. Please add it to `.env` file')
WALLETS = {_network: LCD_CLIENTS[_network].wallet(MnemonicKey(mnemonic=WALLET_SEED))
           for _network in CHAIN_IDS.keys()}
WALLET_ADDRESSES = {_network: WALLETS[_network].key.acc_address
                    for _network in CHAIN_IDS.keys()}

CSV_INTERMEDIATE_DIR = 'data_csv'
CSV_FILE_PATH = 'data_csv/all_assets.csv'
