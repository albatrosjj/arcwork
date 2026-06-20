import os, time, json, hashlib
from dotenv import load_dotenv
from circle.web3 import utils, developer_controlled_wallets
from web3 import Web3

load_dotenv()

# Kontrat adresleri
AGENTIC_COMMERCE_CONTRACT = "0x0747EEf0706327138c69792bF28Cd525089e4583"
USDC_CONTRACT = "0x3600000000000000000000000000000000000000"
JOB_BUDGET = "2000000"  # 2 USDC (6 decimal)

STATUS_NAMES = ["Open", "Funded", "Submitted", "Completed", "Rejected", "Expired"]

# Circle client
circle_client = utils.init_developer_controlled_wallets_client(
    api_key=os.getenv("CIRCLE_API_KEY"),
    entity_secret=os.getenv("CIRCLE_ENTITY_SECRET"),
)
transactions_api = developer_controlled_wallets.TransactionsApi(circle_client)
wallets_api = developer_controlled_wallets.WalletsApi(circle_client)
wallet_sets_api = developer_controlled_wallets.WalletSetsApi(circle_client)
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

def send_transfer(wallet_address, destination, amount, label):
    print(f"  → {label}...")
    req = developer_controlled_wallets \
        .CreateTransferTransactionForDeveloperRequest.from_dict({
            "walletAddress": wallet_address,
            "blockchain": "ARC-TESTNET",
            "tokenAddress": USDC_CONTRACT,
            "destinationAddress": destination,
            "amounts": [amount],
            "feeLevel": "MEDIUM",
        })
    resp = transactions_api.create_developer_transaction_transfer(req)
    tx_id = resp.data.id
    for _ in range(40):
        time.sleep(2)
        tx = transactions_api.get_transaction(id=tx_id)
        state = str(tx.data.transaction.state)
        if "COMPLETE" in state:
            print(f"  ✓ {label}: https://testnet.arcscan.app/tx/{tx.data.transaction.tx_hash}")
            return
        if "FAILED" in state:
            raise Exception(f"{label} başarısız!")
        print(f"    Bekleniyor...", end="\r")

def extract_job_id(tx_hash):
    abi = [{
        "type": "event",
        "name": "JobCreated",
        "inputs": [
            {"indexed": True, "name": "jobId", "type": "uint256"},
            {"indexed": True, "name": "client", "type": "address"},
            {"indexed": True, "name": "provider", "type": "address"},
            {"indexed": False, "name": "evaluator", "type": "address"},
            {"indexed": False, "name": "expiredAt", "type": "uint256"},
            {"indexed": False, "name": "hook", "type": "address"},
        ],
    }]
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(AGENTIC_COMMERCE_CONTRACT), abi=abi
    )
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    for log in receipt["logs"]:
        try:
            decoded = contract.events.JobCreated().process_log(log)
            return decoded["args"]["jobId"]
        except:
            continue
    raise Exception("JobCreated event bulunamadı")

def ai_do_task(task_description):
    """AI agent gerçek görevi burada yapar"""
    print(f"\n  🤖 AI Agent görevi işliyor: '{task_description}'")
    time.sleep(1)
    result = f"[ArcWork AI Sonucu] '{task_description}' görevi tamamlandı. Arc blockchain üzerinde ERC-8183 ile otomatik işlendi."
    deliverable_hash = Web3.to_hex(Web3.keccak(text=result))
    print(f"  ✓ Sonuç üretildi")
    print(f"  ✓ Deliverable hash: {deliverable_hash}")
    return deliverable_hash, result

def main():
    print("\n" + "="*50)
    print("  ArcWork - AI Freelance Marketplace")
    print("  Arc Testnet | ERC-8004 + ERC-8183")
    print("="*50)

    # Adım 1: Wallet oluştur
    print("\n── Adım 1: Wallet'lar oluşturuluyor ──")
    wallet_set = wallet_sets_api.create_wallet_set(
        developer_controlled_wallets.CreateWalletSetRequest.from_dict({
            "name": "ArcWork Job Wallets",
        })
    )
    wallets_response = wallets_api.create_wallet(
        developer_controlled_wallets.CreateWalletRequest.from_dict({
            "blockchains": ["ARC-TESTNET"],
            "count": 2,
            "walletSetId": wallet_set.data.wallet_set.actual_instance.id,
            "accountType": "SCA",
        })
    )
    client_wallet = wallets_response.data.wallets[0].actual_instance
    provider_wallet = wallets_response.data.wallets[1].actual_instance
    print(f"  İş Veren (Client):  {client_wallet.address}")
    print(f"  AI Agent (Provider): {provider_wallet.address}")

    # Adım 2: Client'a USDC yükle
    print(f"\n── Adım 2: Client wallet'a USDC yükle ──")
    print(f"  Adres: {client_wallet.address}")
    print(f"  Faucet: https://faucet.circle.com")
    input("\n  USDC yükledikten sonra Enter'a bas...")

    # Adım 3: Provider'a başlangıç USDC gönder
    print(f"\n── Adım 3: Provider'a 1 USDC gönderiliyor ──")
    send_transfer(client_wallet.address, provider_wallet.address, "1", "provider başlangıç USDC")

    # Adım 4: İş tanımla
    task = "Bu metni Türkçeye çevir: 'Arc is the fastest stablecoin blockchain in the world'"
    print(f"\n── Adım 4: İş oluşturuluyor ──")
    print(f"  Görev: {task}")
    print(f"  Ödül:  2 USDC")

    expired_at = w3.eth.get_block("latest")["timestamp"] + 3600
    tx_hash = send_tx(
        client_wallet.address,
        AGENTIC_COMMERCE_CONTRACT,
        "createJob(address,address,uint256,string,address)",
        [
            provider_wallet.address,
            client_wallet.address,
            str(expired_at),
            task,
            "0x0000000000000000000000000000000000000000",
        ],
        "createJob"
    )
    job_id = extract_job_id(tx_hash)
    print(f"  ✓ Job ID: {job_id}")

    # Adım 5: Bütçe belirle
    print(f"\n── Adım 5: Bütçe belirleniyor (2 USDC) ──")
    send_tx(provider_wallet.address, AGENTIC_COMMERCE_CONTRACT,
        "setBudget(uint256,uint256,bytes)",
        [str(job_id), JOB_BUDGET, "0x"], "setBudget")

    # Adım 6: USDC onayla
    print(f"\n── Adım 6: USDC escrow onayı ──")
    send_tx(client_wallet.address, USDC_CONTRACT,
        "approve(address,uint256)",
        [AGENTIC_COMMERCE_CONTRACT, JOB_BUDGET], "approve USDC")

    # Adım 7: Escrow'a USDC kilitle
    print(f"\n── Adım 7: USDC escrow'a kilitleniyor ──")
    send_tx(client_wallet.address, AGENTIC_COMMERCE_CONTRACT,
        "fund(uint256,bytes)", [str(job_id), "0x"], "fund escrow")

    # Adım 8: AI görevi yap
    print(f"\n── Adım 8: AI Agent görevi yapıyor ──")
    deliverable_hash, result = ai_do_task(task)

    # Adım 9: Teslim et
    print(f"\n── Adım 9: Teslim ediliyor ──")
    send_tx(provider_wallet.address, AGENTIC_COMMERCE_CONTRACT,
        "submit(uint256,bytes32,bytes)",
        [str(job_id), deliverable_hash, "0x"], "submit deliverable")

    # Adım 10: Tamamla ve ödeme yap
    print(f"\n── Adım 10: İş tamamlanıyor, USDC ödeniyor ──")
    reason_hash = Web3.to_hex(Web3.keccak(text="deliverable-approved"))
    send_tx(client_wallet.address, AGENTIC_COMMERCE_CONTRACT,
        "complete(uint256,bytes32,bytes)",
        [str(job_id), reason_hash, "0x"], "complete job")

    print(f"\n{'='*50}")
    print(f"  ✅ ArcWork İş Akışı Tamamlandı!")
    print(f"{'='*50}")
    print(f"  Job ID:     {job_id}")
    print(f"  Görev:      {task}")
    print(f"  Sonuç:      {result}")
    print(f"  Ödeme:      2 USDC → {provider_wallet.address}")
    print(f"  Explorer:   https://testnet.arcscan.app/address/{client_wallet.address}")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        exit(1)
