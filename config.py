import logging
import sys


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%d-%m-%Y %H:%M:%S',
                    handlers=[logging.FileHandler("arbitrage_osmosis.log"),
                              logging.StreamHandler(sys.stdout)])

PUSSY_CHAIN_ID = 'space-pussy'
PUSSY_CHAIN_NAME = 'space-pussy'
PUSSY_NODE_LCD_URL = 'https://lcd.space-pussy.cybernode.ai'

INIT_CHAIN_ID_NAME_DICT = {PUSSY_CHAIN_ID: PUSSY_CHAIN_NAME}
INIT_CHAIN_ID_LCD_DICT = {PUSSY_CHAIN_ID: [PUSSY_NODE_LCD_URL]}

CONTRACTS = {
    'bostrom': 'bostrom1eeahgvdsun8a04rh5vy9je49nllq6nj8ljmaslsvjeyg0j0063mssjcjmt'
}
