import os
from dotenv import load_dotenv
from circle.web3 import utils, developer_controlled_wallets

load_dotenv()

circle_client = utils.init_developer_controlled_wallets_client(
    api_key=os.getenv("CIRCLE_API_KEY"),
    entity_secret=os.getenv("CIRCLE_ENTITY_SECRET"),
)

transactions_api = developer_controlled_wallets.TransactionsApi(circle_client)

TX_ID = "a0fea4fd-5c41-53db-a992-a768f3889e8a"

response = transactions_api.get_transaction(TX_ID)
tx = response.data.transaction
print("Durum:", tx.state)
print("Hata:", tx.error_reason)
print("Detay:", tx)
