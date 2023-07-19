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

# for export to a contract
CHAIN_ID = 'bostrom'
NODE_RPC_URL = 'https://rpc.bostrom.cybernode.ai:443'
NODE_LCD_URL = 'https://lcd.bostrom.cybernode.ai'
CONTRACT_ADDRESS = 'bostrom1eeahgvdsun8a04rh5vy9je49nllq6nj8ljmaslsvjeyg0j0063mssjcjmt'
LCD_CLIENT = LCDClient(url=NODE_LCD_URL, chain_id=CHAIN_ID)
WALLET_SEED = dotenv_values('.env')['WALLET_SEED']
WALLET = LCD_CLIENT.wallet(MnemonicKey(mnemonic=WALLET_SEED))
WALLET_ADDRESS = WALLET.key.acc_address
