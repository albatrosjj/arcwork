import os, time
from dotenv import load_dotenv
from circle.web3 import utils, developer_controlled_wallets
from web3 import Web3

load_dotenv()

AGENTIC_COMMERCE_CONTRACT = "0x0747EEf0706327138c69792bF28Cd525089e4583"
USDC_CONTRACT = "0x3600000000000000000000000000000000000000"
JOB_BUDGET = "2000000"

# Mevcut bilgiler
JOB_ID = 128598
CLIENT_ADDRESS  = "0xca67d7f23a30198901457559270b5d9a4f27a18a"
PROVIDER_ADDRESS = "0xfa2a266bed7b2c17dda319a0e2516b4a74831998"
TASK = "Bu metni Türkçeye çevir: 'Arc is the fastest stablecoin blockchain in the world'"

circle_client = utils.init_developer_controlled_wallets_client(
    api_key=os.getenv("CIRCLE_API_KEY"),
    entity_secret=os.getenv("CIRCLE_ENTITY_SECRET"),
)
transactions_api = developer_controlled_wallets.TransactionsApi(circle_client)
w3 = Web3(Web3.HTTPProvider("https://rpc.testnet.arc.network/"))

def send_tx(wallet_address, contract, sig, params, label):
    print(f"  → {label}...")
    req = developer_controlled_wallets \
        .CreateContractExecutionTransactionForDeveloperRequest.from_dict({
            "walletAddress": wallet_address,
            "blockchain": "ARC-TESTNET",
            "contractAddress": contract,
            "abiFunctionSignature": sig,
            "abiParameters": params,
            "feeLevel": "MEDIUM",
        })
    resp = transactions_api.create_developer_transaction_contract_execution(req)
    tx_id = resp.data.id
    for _ in range(40):
        time.sleep(2)
        tx = transactions_api.get_transaction(id=tx_id)
        state = str(tx.data.transaction.state)
        if "COMPLETE" in state:
            print(f"  ✓ {label}: https://testnet.arcscan.app/tx/{tx.data.transaction.tx_hash}")
            return tx.data.transaction.tx_hash
        if "FAILED" in state:
            raise Exception(f"{label} başarısız!")
        print(f"    Bekleniyor...", end="\r")
    raise Exception(f"{label} zaman aşımı")

print(f"\n  Job ID: {JOB_ID} — kaldığımız yerden devam ediyoruz\n")

# Adım 5: Bütçe belirle
print("── Adım 5: Bütçe belirleniyor (2 USDC) ──")
send_tx(PROVIDER_ADDRESS, AGENTIC_COMMERCE_CONTRACT,
    "setBudget(uint256,uint256,bytes)",
    [str(JOB_ID), JOB_BUDGET, "0x"], "setBudget")

# Adım 6: USDC onayla
print("\n── Adım 6: USDC escrow onayı ──")
send_tx(CLIENT_ADDRESS, USDC_CONTRACT,
    "approve(address,uint256)",
    [AGENTIC_COMMERCE_CONTRACT, JOB_BUDGET], "approve USDC")

# Adım 7: Escrow'a USDC kilitle
print("\n── Adım 7: USDC escrow'a kilitleniyor ──")
send_tx(CLIENT_ADDRESS, AGENTIC_COMMERCE_CONTRACT,
    "fund(uint256,bytes)", [str(JOB_ID), "0x"], "fund escrow")

# Adım 8: AI görevi yap
print("\n── Adım 8: AI Agent görevi yapıyor ──")
print(f"  🤖 Görev: {TASK}")
result = "Arc, dünyanın en hızlı stablecoin blockchain'idir."
deliverable_hash = Web3.to_hex(Web3.keccak(text=result))
print(f"  ✓ Sonuç: {result}")
print(f"  ✓ Hash:  {deliverable_hash}")

# Adım 9: Teslim et
print("\n── Adım 9: Teslim ediliyor ──")
send_tx(PROVIDER_ADDRESS, AGENTIC_COMMERCE_CONTRACT,
    "submit(uint256,bytes32,bytes)",
    [str(JOB_ID), deliverable_hash, "0x"], "submit deliverable")

# Adım 10: Tamamla
print("\n── Adım 10: İş tamamlanıyor, USDC ödeniyor ──")
reason_hash = Web3.to_hex(Web3.keccak(text="deliverable-approved"))
send_tx(CLIENT_ADDRESS, AGENTIC_COMMERCE_CONTRACT,
    "complete(uint256,bytes32,bytes)",
    [str(JOB_ID), reason_hash, "0x"], "complete job")

print(f"\n{'='*50}")
print(f"  ✅ ArcWork İş Akışı Tamamlandı!")
print(f"  Job ID:   {JOB_ID}")
print(f"  Görev:    {TASK}")
print(f"  Sonuç:    {result}")
print(f"  Ödeme:    2 USDC → {PROVIDER_ADDRESS}")
print(f"  Explorer: https://testnet.arcscan.app/address/{CLIENT_ADDRESS}")
print(f"{'='*50}\n")
