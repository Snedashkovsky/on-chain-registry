import logging
import sys
from dotenv import dotenv_values

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
    'bostrom': 'test-on-chain-registry',
    'localbostrom': 'test-on-chain-registry'
}
CODE_IDS = {
    'bostrom': '28',
    'localbostrom': '46'
}

# for export to contracts
EXPORT_CHAINS = ['bostrom']
CHAIN_IDS = {
    'bostrom': 'bostrom',
    'localbostrom': 'localbostrom'
}
PREFIXES = {
    'bostrom': 'bostrom',
    'localbostrom': 'bostrom'
}
FEE_DENOMS = {
    'bostrom': 'boot',
    'localbostrom': 'boot'
}
NODE_RPC_URLS = {
    'bostrom': 'https://rpc.bostrom.cybernode.ai:443',
    'localbostrom': 'http://localhost:26657'
}
NODE_LCD_URLS = {
    'bostrom': 'https://lcd.bostrom.cybernode.ai',
    'localbostrom': 'http://localhost:1317'
}
CONTRACT_ADDRESSES = {
    'bostrom': 'bostrom1eeahgvdsun8a04rh5vy9je49nllq6nj8ljmaslsvjeyg0j0063mssjcjmt',
    'localbostrom': 'bostrom1jskphr9zxs2yp3e9vwamyeqwxkfkg5zghyv52qcy4tlql3qjjwgsk2d9vp'
}

LCD_CLIENTS = {_network: LCDClient(url=NODE_LCD_URLS[_network],
                                   chain_id=CHAIN_IDS[_network],
                                   prefix=PREFIXES[_network])
               for _network in CHAIN_IDS.keys()}
WALLET_SEED = dotenv_values('.env')['WALLET_SEED']
WALLETS = {_network: LCD_CLIENTS[_network].wallet(MnemonicKey(mnemonic=WALLET_SEED))
           for _network in CHAIN_IDS.keys()}
WALLET_ADDRESSES = {_network: WALLETS[_network].key.acc_address
                    for _network in CHAIN_IDS.keys()}
