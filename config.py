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
    'bostrom': 'on-chain-registry',
    'localbostrom': 'on-chain-registry',
    'osmosis-testnet': 'on-chain-registry'
}
CODE_IDS = {
    'bostrom': '32',
    'localbostrom': '46',
    'osmosis-testnet': '3281'
}

# for export to contracts
EXPORT_CHAINS = ['bostrom', 'osmo-test-5']
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
    'bostrom': 'bostrom1t33kxpypdlnp28fl4sttj59jj6e5tg6sxl3423s6sjp79ldqaucqzf6y3v',
    'localbostrom': 'bostrom1jskphr9zxs2yp3e9vwamyeqwxkfkg5zghyv52qcy4tlql3qjjwgsk2d9vp',
    'osmosis-testnet': 'osmo1me45lxajuhe5g0rqqwsn4rw4hm26d05q5f395742ztngu647yy2qrqwxq7'
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
