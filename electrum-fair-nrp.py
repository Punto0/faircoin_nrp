#!/usr/bin/env python
#
# Electrum - lightweight Bitcoin client
# Copyright (C) 2011 thomasv@gitorious
#
# Faircoin Payment For NRP
# Copyright (C) 2015-2016 santi@punto0.org -- FairCoop 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import time, sys, os
import logging

import electrum_fair
from electrum_fair import util
from electrum_fair.util import NotEnoughFunds
electrum_fair.set_verbosity(True)

import ConfigParser
config = ConfigParser.ConfigParser()
config.read("electrum-fair-nrp.conf")

wallet_path = config.get('electrum','wallet_path')

seed = config.get('electrum','seed')
password = config.get('electrum', 'password')
network_fee = config.get('network','fee')

logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)s %(message)s')

def do_stop():
    network.stop_daemon()
    if network.is_connected():
        time.sleep(1) 
    logging.debug("Stopping")    
    return "ok"

def process_request(amount, faircoin_address):
    logging.debug("New payment request received. Amount : %s -- To address : %s" %(amount, faircoin_address))
    try:
        amount = float(amount)
    except Exception:
        return "incorrect parameters"
    # Perhaps here we should validate the faircoin address more properly 
    if not faircoin_address:
         logging.error("We have not the faircoin address")
         return 0
  
    amount_total = ( 1.e6 * float(amount) ) - float(network_fee)
    amount_total = int(amount_total)

    if amount_total > 0:
        output = [('address', faircoin_address, int(amount_total))] 
    else:
        logging.error("Amount negative: %s" %(amount_total) )
        return 0
    # Create the transaction
    try:  
        tx = wallet.mktx(output, password)
    except NotEnoughFunds:	
	logging.error("Not enough funds confirmed to make the transactions.")
        return 2
    
    # Here we go...
    rec_tx_state, rec_tx_out = wallet.sendtx(tx)
    if rec_tx_state:
         logging.info("SUCCES. The transaction has been broadcasted.")
    else:
         logging.error("Sending %s fairs to the address %s" %(amount_total, faircoin_address ) )
         return 0 

    return 1

def getbalance():
    return wallet.get_balance()

def make_transaction_from_address(address_origin, address_end, amount):
    coins = wallet.get_spendable_coins()
    print coins
    amount_total = ( 1.e6 * float(amount) ) - float(network_fee)
    amount_total = int(amount_total)

    if amount_total > 0:
        output = [('address', address_end, int(amount_total))] 
    else:
        logging.error("Amount negative: %s" %(amount_total) )
        return 0
    try:
        tx = wallet.make_unsigned_transaction(coins, output, change_addr=address_origin)
    except NotEnoughFunds:
	        print "Not enough funds confirmed to make the transaction. Delaying..."
                print wallet.get_balance()
                print wallet.get_balance('fYvakbTMSVJqv2gvMoyCMeeZTiidjWvDNq')
                exit(1)    
    wallet.sign_transaction(tx, password)
    rec_tx_state, rec_tx_out = wallet.sendtx(tx)
    if rec_tx_state:
         logging.info("SUCCESS. The transaction has been broadcasted.")
    else:
         logging.error("Sending %s fairs to the address %s" %(amount_total, address_end ) )
         

def new_fair_address(id, entity = 'generic'):
    """ Return a new address labeled or False if there's no network connection. 
    The label is for debugging proposals. It's like 'entity: id'
    We can label like "user: 213" or "user: pachamama" or "order: 67".
    """
    while network.is_connected():
        new_address = wallet.create_new_address()
        check_label = wallet.get_label(new_address)
        check_history = cmd_wallet.getaddresshistory(new_address)
        # It checks if address is labeled or has history yet, a gap limit protection. 
        # This can be removed when we have good control of gap limit.     
        if not check_label[0] and not check_history:
            wallet.set_label(new_address, entity + ': ' + str(id))
            return new_address
    return False

if __name__ == '__main__':
    logging.debug("---------------------------------")
    logging.debug("Starting payment daemon")
    # start network
    c = electrum_fair.SimpleConfig({'wallet_path':wallet_path})
    daemon_socket = electrum_fair.daemon.get_daemon(c, True)
    network = electrum_fair.NetworkProxy(daemon_socket, config)
    network.start()
    n = 0
    # wait until connected
    while (network.is_connecting() and (n < 100)):
        time.sleep(0.5)
        n = n + 1

    if not network.is_connected():
        logging.error("Can not init Electrum Network. Exiting.")
        sys.exit(1)

    # create wallet
    storage = electrum_fair.WalletStorage(wallet_path)
    if not storage.file_exists:
        logging.debug("creating wallet file")
        wallet = electrum_fair.wallet.Wallet.from_seed(seed, password, storage)
    else:
        wallet = electrum_fair.wallet.Wallet(storage)
    #wallet.use_change = False
    #wallet.synchronize = lambda: None # prevent address creation by the wallet
    wallet.start_threads(network)
    wallet.add_address('fHddAEGtTtv1YrxyvguoCatvNkKiDWNnkR')
    #print wallet.check_history()
    wallet.load_accounts()
    wallet.synchronize()
    wallet.update()
    #cmd_wallet = electrum_fair.commands.Commands(c, wallet, network)
    print wallet.is_mine('fHddAEGtTtv1YrxyvguoCatvNkKiDWNnkR')
    print wallet.is_used('fHddAEGtTtv1YrxyvguoCatvNkKiDWNnkR')
    print wallet.get_addr_received('fHddAEGtTtv1YrxyvguoCatvNkKiDWNnkR')
    #print wallet.get_account_addresses('fYvakbTMSVJqv2gvMoyCMeeZTiidjWvDNq')
    make_transaction_from_address('fHddAEGtTtv1YrxyvguoCatvNkKiDWNnkR','fT6fArCWPKv8skvaV5QnvZKYhksEhfYJsn',1)    
    
