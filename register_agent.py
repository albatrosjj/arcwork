import os
from dotenv import load_dotenv
from circle.web3 import utils, developer_controlled_wallets

load_dotenv()

circle_client = utils.init_developer_controlled_wallets_client(
    api_key=os.getenv("CIRCLE_API_KEY"),
    entity_secret=os.getenv("CIRCLE_ENTITY_SECRET"),
)

transactions_api = developer_controlled_wallets.TransactionsApi(circle_client)

IDENTITY_REGISTRY = "0x8004A818BFB912233c491871b3d84c89A494BD9e"
OWNER_WALLET_ID = "40dc1d67-2d3b-5ec0-9465-a29d6e084547"

response = transactions_api.create_developer_transaction_contract_execution(
    developer_controlled_wallets.CreateContractExecutionTransactionForDeveloperRequest.from_dict({
        "walletId": OWNER_WALLET_ID,
        "contractAddress": IDENTITY_REGISTRY,
        "abiFunctionSignature": "registerAgent(string,string)",
        "abiParameters": ["ArcAgent", "{\"description\":\"My first Arc AI agent\"}"],
        "feeLevel": "MEDIUM",
    })
)

print("✓ Agent kaydedildi!")
print("Response:", response.data)
