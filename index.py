import os
import time
from dotenv import load_dotenv
from circle.web3 import utils, developer_controlled_wallets

load_dotenv()

# Circle client başlat
circle_client = utils.init_developer_controlled_wallets_client(
    api_key=os.getenv("CIRCLE_API_KEY"),
    entity_secret=os.getenv("CIRCLE_ENTITY_SECRET"),
)

print("✓ Circle client bağlantısı başarılı")

# Wallet set oluştur
wallet_sets_api = developer_controlled_wallets.WalletSetsApi(circle_client)
wallets_api = developer_controlled_wallets.WalletsApi(circle_client)

wallet_set = wallet_sets_api.create_wallet_set(
    developer_controlled_wallets.CreateWalletSetRequest.from_dict({
        "name": "ARC Agent Wallets",
    })
)
wallet_set_id = wallet_set.data.wallet_set.actual_instance.id
print(f"✓ Wallet set oluşturuldu: {wallet_set_id}")

# 2 wallet oluştur (owner + validator)
wallets_response = wallets_api.create_wallet(
    developer_controlled_wallets.CreateWalletRequest.from_dict({
        "blockchains": ["ARC-TESTNET"],
        "count": 2,
        "walletSetId": wallet_set_id,
        "accountType": "SCA",
    })
)

owner_wallet = wallets_response.data.wallets[0].actual_instance
validator_wallet = wallets_response.data.wallets[1].actual_instance

print(f"✓ Owner wallet:     {owner_wallet.address}")
print(f"✓ Validator wallet: {validator_wallet.address}")
