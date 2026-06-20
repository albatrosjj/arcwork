import os, time, json
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from circle.web3 import utils, developer_controlled_wallets
from web3 import Web3
import anthropic

load_dotenv()

app = FastAPI()

AGENTIC_COMMERCE_CONTRACT = "0x0747EEf0706327138c69792bF28Cd525089e4583"
USDC_CONTRACT = "0x3600000000000000000000000000000000000000"
JOB_BUDGET = "1000000"  # 1 USDC

circle_client = utils.init_developer_controlled_wallets_client(
    api_key=os.getenv("CIRCLE_API_KEY"),
    entity_secret=os.getenv("CIRCLE_ENTITY_SECRET"),
)
transactions_api = developer_controlled_wallets.TransactionsApi(circle_client)
wallets_api = developer_controlled_wallets.WalletsApi(circle_client)
wallet_sets_api = developer_controlled_wallets.WalletSetsApi(circle_client)
ai_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
w3 = Web3(Web3.HTTPProvider("https://rpc.testnet.arc.network/"))

CLIENT_ADDRESS   = "0xca67d7f23a30198901457559270b5d9a4f27a18a"
PROVIDER_ADDRESS = "0xfa2a266bed7b2c17dda319a0e2516b4a74831998"

def send_tx(wallet_address, contract, sig, params):
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
            return tx.data.transaction.tx_hash
        if "FAILED" in state:
            raise Exception("Transaction başarısız")
    raise Exception("Zaman aşımı")

class JobRequest(BaseModel):
    text: str
    task_type: str
    source_lang: str = "English"
    target_lang: str = "Turkish"

@app.get("/", response_class=HTMLResponse)
async def home():
    html = open("templates/index.html").read()
    return html

@app.post("/job")
async def create_job(req: JobRequest):
    async def stream():
        try:
            # Step 0: Job oluştur
            yield f"data: {json.dumps({'step': 0, 'status': 'loading'})}\n\n"
            expired_at = w3.eth.get_block("latest")["timestamp"] + 3600
            task_desc = f"{'Translate to Turkish' if req.task_type == 'translate' else 'Summarize'}: {req.text}"
            tx0 = send_tx(CLIENT_ADDRESS, AGENTIC_COMMERCE_CONTRACT,
                "createJob(address,address,uint256,string,address)",
                [PROVIDER_ADDRESS, CLIENT_ADDRESS, str(expired_at), task_desc,
                 "0x0000000000000000000000000000000000000000"])
            
            # Job ID'yi bul
            receipt = w3.eth.get_transaction_receipt(tx0)
            job_id = int(receipt["logs"][1]["topics"][1].hex(), 16)

            yield f"data: {json.dumps({'step': 0, 'status': 'done', 'tx': f'https://testnet.arcscan.app/tx/{tx0}', 'prev': -1})}\n\n"

            # Step 1: Escrow
            yield f"data: {json.dumps({'step': 1, 'status': 'loading', 'prev': 0})}\n\n"
            send_tx(PROVIDER_ADDRESS, AGENTIC_COMMERCE_CONTRACT,
                "setBudget(uint256,uint256,bytes)", [str(job_id), JOB_BUDGET, "0x"])
            send_tx(CLIENT_ADDRESS, USDC_CONTRACT,
                "approve(address,uint256)", [AGENTIC_COMMERCE_CONTRACT, JOB_BUDGET])
            tx1 = send_tx(CLIENT_ADDRESS, AGENTIC_COMMERCE_CONTRACT,
                "fund(uint256,bytes)", [str(job_id), "0x"])
            yield f"data: {json.dumps({'step': 1, 'status': 'done', 'tx': f'https://testnet.arcscan.app/tx/{tx1}', 'prev': 0})}\n\n"

            # Step 2: AI
            yield f"data: {json.dumps({'step': 2, 'status': 'loading', 'prev': 1})}\n\n"
            if req.task_type == "translate":
                source = getattr(req, "source_lang", "English")
                target = getattr(req, "target_lang", "Turkish")
                prompt = f"Translate the following text from {source} to {target}. Return only the translation:\n\n{req.text}"
            else:
                prompt = f"Summarize the following text in 2-3 sentences. Return only the summary:\n\n{req.text}"
            
            message = ai_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            result = message.content[0].text
            deliverable_hash = Web3.to_hex(Web3.keccak(text=result))
            yield f"data: {json.dumps({'step': 2, 'status': 'done', 'prev': 1})}\n\n"

            # Step 3: Submit
            yield f"data: {json.dumps({'step': 3, 'status': 'loading', 'prev': 2})}\n\n"
            tx3 = send_tx(PROVIDER_ADDRESS, AGENTIC_COMMERCE_CONTRACT,
                "submit(uint256,bytes32,bytes)", [str(job_id), deliverable_hash, "0x"])
            yield f"data: {json.dumps({'step': 3, 'status': 'done', 'tx': f'https://testnet.arcscan.app/tx/{tx3}', 'prev': 2})}\n\n"

            # Step 4: Complete
            yield f"data: {json.dumps({'step': 4, 'status': 'loading', 'prev': 3})}\n\n"
            reason_hash = Web3.to_hex(Web3.keccak(text="approved"))
            tx4 = send_tx(CLIENT_ADDRESS, AGENTIC_COMMERCE_CONTRACT,
                "complete(uint256,bytes32,bytes)", [str(job_id), reason_hash, "0x"])
            yield f"data: {json.dumps({'step': 4, 'status': 'done', 'tx': f'https://testnet.arcscan.app/tx/{tx4}', 'prev': 3})}\n\n"

            yield f"data: {json.dumps({'result': result})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
