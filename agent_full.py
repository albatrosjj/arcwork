import os, time
from dotenv import load_dotenv
from circle.web3 import utils, developer_controlled_wallets
from web3 import Web3

load_dotenv()

IDENTITY_REGISTRY   = "0x8004A818BFB912233c491871b3d84c89A494BD9e"
REPUTATION_REGISTRY = "0x8004B663056A597Dffe9eCcC1965A193B7388713"
VALIDATION_REGISTRY = "0x8004Cb1BF31DAf7788923b405b754f57acEB4272"
METADATA_URI = "ipfs://bafkreibdi6623n3xpf7ymk62ckb4bo75o3qemwkpfvp5i25j66itxvsoei"

circle_client = utils.init_developer_controlled_wallets_client(
    api_key=os.getenv("CIRCLE_API_KEY"),
    entity_secret=os.getenv("CIRCLE_ENTITY_SECRET"),
)
transactions_api = developer_controlled_wallets.TransactionsApi(circle_client)
w3 = Web3(Web3.HTTPProvider("https://rpc.testnet.arc.network/"))

OWNER_ADDRESS     = "0xe7faaccb0746dbbc20e250546c28f9f4ca03a100"
VALIDATOR_ADDRESS = "0xbbf0e306276f7ffe9f7d09e7ca33756a3ea844e9"

def send_tx(wallet_address, contract_address, abi_sig, abi_params, label):
    print(f"  Gönderiliyor: {label}...")
    req = developer_controlled_wallets \
        .CreateContractExecutionTransactionForDeveloperRequest.from_dict({
            "walletAddress": wallet_address,
            "blockchain": "ARC-TESTNET",
            "contractAddress": contract_address,
            "abiFunctionSignature": abi_sig,
            "abiParameters": abi_params,
            "feeLevel": "MEDIUM",
        })
    resp = transactions_api.create_developer_transaction_contract_execution(req)
    tx_id = resp.data.id
    for _ in range(30):
        time.sleep(2)
        tx = transactions_api.get_transaction(id=tx_id)
        state = str(tx.data.transaction.state)
        if "COMPLETE" in state:
            print(f"  ✓ {label} tamamlandı: https://testnet.arcscan.app/tx/{tx.data.transaction.tx_hash}")
            return
        if "FAILED" in state:
            raise Exception(f"{label} başarısız oldu")
        print(f"    Bekleniyor... ({state})")
    raise Exception(f"{label} zaman aşımı")

# Step 1: Agent kimliğini kaydet
print("\n── Adım 1: Agent kaydediliyor ──")
send_tx(OWNER_ADDRESS, IDENTITY_REGISTRY, "register(string)", [METADATA_URI], "agent kaydı")

# Step 2: Agent ID bul
print("\n── Adım 2: Agent ID alınıyor ──")
identity_abi = [
    {"anonymous": False, "inputs": [
        {"indexed": True, "name": "from", "type": "address"},
        {"indexed": True, "name": "to", "type": "address"},
        {"indexed": True, "name": "tokenId", "type": "uint256"},
    ], "name": "Transfer", "type": "event"},
    {"inputs": [{"name": "tokenId", "type": "uint256"}], "name": "ownerOf",
     "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "tokenId", "type": "uint256"}], "name": "tokenURI",
     "outputs": [{"name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
]
identity_contract = w3.eth.contract(address=IDENTITY_REGISTRY, abi=identity_abi)
latest_block = w3.eth.block_number
events = identity_contract.events.Transfer.create_filter(
    from_block=max(0, latest_block - 10000),
    to_block=latest_block,
    argument_filters={"to": OWNER_ADDRESS},
).get_all_entries()
agent_id = events[-1]["args"]["tokenId"]
print(f"  Agent ID: {agent_id}")
print(f"  Owner:    {identity_contract.functions.ownerOf(agent_id).call()}")
print(f"  URI:      {identity_contract.functions.tokenURI(agent_id).call()}")

# Step 3: İtibar kaydet
print("\n── Adım 3: İtibar kaydediliyor ──")
tag = "successful_trade"
feedback_hash = "0x" + w3.keccak(text=tag).hex()
send_tx(VALIDATOR_ADDRESS, REPUTATION_REGISTRY,
    "giveFeedback(uint256,int128,uint8,string,string,string,string,bytes32)",
    [str(agent_id), "95", "0", tag, "", "", "", feedback_hash], "itibar")

# Step 4: Doğrulama iste
print("\n── Adım 4: Doğrulama isteniyor ──")
request_hash = "0x" + w3.keccak(text=f"kyc_verification_request_agent_{agent_id}").hex()
send_tx(OWNER_ADDRESS, VALIDATION_REGISTRY,
    "validationRequest(address,uint256,string,bytes32)",
    [VALIDATOR_ADDRESS, str(agent_id), "ipfs://bafkreiexamplevalidationrequest", request_hash],
    "doğrulama isteği")

# Step 5: Doğrulama yanıtla
print("\n── Adım 5: Doğrulama yanıtlanıyor ──")
send_tx(VALIDATOR_ADDRESS, VALIDATION_REGISTRY,
    "validationResponse(bytes32,uint8,string,bytes32,string)",
    [request_hash, "100", "", "0x" + "0" * 64, "kyc_verified"],
    "doğrulama yanıtı")

print(f"\n✓ Tamamlandı! Explorer: https://testnet.arcscan.app/address/{OWNER_ADDRESS}")
