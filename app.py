import os, time
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
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
    task_type: str  # "translate" or "summarize"

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ArcWork — AI Freelance Marketplace</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, sans-serif; background: #0a0a0f; color: #e0e0e0; min-height: 100vh; }
        .header { background: #111118; border-bottom: 1px solid #222; padding: 20px 40px; display: flex; align-items: center; gap: 12px; }
        .logo { font-size: 24px; font-weight: 700; color: #fff; }
        .badge { background: #1a3a2a; color: #4ade80; padding: 4px 10px; border-radius: 20px; font-size: 12px; }
        .container { max-width: 800px; margin: 60px auto; padding: 0 20px; }
        h1 { font-size: 42px; font-weight: 800; margin-bottom: 12px; }
        h1 span { color: #4ade80; }
        .subtitle { color: #888; margin-bottom: 40px; font-size: 16px; line-height: 1.6; }
        .card { background: #111118; border: 1px solid #222; border-radius: 16px; padding: 32px; margin-bottom: 24px; }
        .card h2 { font-size: 18px; margin-bottom: 20px; color: #fff; }
        .task-select { display: flex; gap: 12px; margin-bottom: 20px; }
        .task-btn { flex: 1; padding: 12px; border: 2px solid #333; border-radius: 10px; background: transparent; color: #888; cursor: pointer; font-size: 14px; transition: all 0.2s; }
        .task-btn.active { border-color: #4ade80; color: #4ade80; background: #0d2a1a; }
        textarea { width: 100%; background: #0a0a0f; border: 1px solid #333; border-radius: 10px; padding: 16px; color: #e0e0e0; font-size: 15px; resize: vertical; min-height: 120px; font-family: inherit; }
        textarea:focus { outline: none; border-color: #4ade80; }
        .submit-btn { width: 100%; padding: 16px; background: #4ade80; color: #000; border: none; border-radius: 10px; font-size: 16px; font-weight: 700; cursor: pointer; margin-top: 16px; transition: all 0.2s; }
        .submit-btn:hover { background: #22c55e; }
        .submit-btn:disabled { background: #333; color: #666; cursor: not-allowed; }
        .result { display: none; }
        .result.show { display: block; }
        .step { display: flex; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px solid #1a1a1a; }
        .step:last-child { border-bottom: none; }
        .step-icon { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; flex-shrink: 0; }
        .step-icon.pending { background: #1a1a1a; color: #666; }
        .step-icon.loading { background: #1a3a2a; color: #4ade80; animation: pulse 1s infinite; }
        .step-icon.done { background: #1a3a2a; color: #4ade80; }
        .step-icon.error { background: #2a1a1a; color: #f87171; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
        .step-text { flex: 1; font-size: 14px; }
        .step-link { font-size: 12px; color: #4ade80; text-decoration: none; }
        .answer-box { background: #0a0a0f; border: 1px solid #4ade80; border-radius: 10px; padding: 20px; margin-top: 8px; font-size: 15px; line-height: 1.7; color: #e0e0e0; }
        .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 24px; }
        .stat { background: #0a0a0f; border: 1px solid #222; border-radius: 10px; padding: 16px; text-align: center; }
        .stat-value { font-size: 22px; font-weight: 700; color: #4ade80; }
        .stat-label { font-size: 12px; color: #666; margin-top: 4px; }
        .error-msg { color: #f87171; font-size: 14px; margin-top: 12px; display: none; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">⚡ ArcWork</div>
        <div class="badge">Arc Testnet</div>
    </div>
    <div class="container">
        <h1>AI Tasks, Paid in <span>USDC</span></h1>
        <p class="subtitle">Submit a task, AI completes it, payment happens automatically on Arc blockchain via ERC-8183 escrow.</p>

        <div class="card">
            <h2>Create a Job</h2>
            <div class="task-select">
                <button class="task-btn active" onclick="selectTask('translate', this)">🌐 Translate to Turkish</button>
                <button class="task-btn" onclick="selectTask('summarize', this)">📝 Summarize Text</button>
            </div>
            <textarea id="inputText" placeholder="Enter your text here..."></textarea>
            <button class="submit-btn" onclick="submitJob()" id="submitBtn">Submit Job & Pay 1 USDC</button>
            <div class="error-msg" id="errorMsg"></div>
        </div>

        <div class="card result" id="resultCard">
            <h2>Job Progress</h2>
            <div id="steps"></div>
            <div id="answerSection" style="display:none; margin-top:20px;">
                <div style="font-size:13px; color:#666; margin-bottom:8px;">AI Result:</div>
                <div class="answer-box" id="answerBox"></div>
            </div>
        </div>

        <div class="stats">
            <div class="stat">
                <div class="stat-value">ERC-8004</div>
                <div class="stat-label">Agent Identity Standard</div>
            </div>
            <div class="stat">
                <div class="stat-value">ERC-8183</div>
                <div class="stat-label">Job & Escrow Standard</div>
            </div>
            <div class="stat">
                <div class="stat-value">USDC</div>
                <div class="stat-label">Native Payment Token</div>
            </div>
        </div>
    </div>

    <script>
        let selectedTask = 'translate';

        function selectTask(task, btn) {
            selectedTask = task;
            document.querySelectorAll('.task-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        }

        function setStep(steps, index, status, text, link) {
            const icons = { pending: '○', loading: '◌', done: '✓', error: '✗' };
            steps[index].querySelector('.step-icon').className = `step-icon ${status}`;
            steps[index].querySelector('.step-icon').textContent = icons[status];
            steps[index].querySelector('.step-text').textContent = text;
            if (link) {
                let a = steps[index].querySelector('.step-link');
                if (!a) { a = document.createElement('a'); a.className = 'step-link'; a.target = '_blank'; steps[index].appendChild(a); }
                a.href = link;
                a.textContent = 'View TX →';
            }
        }

        async function submitJob() {
            const text = document.getElementById('inputText').value.trim();
            if (!text) { alert('Please enter some text!'); return; }

            document.getElementById('submitBtn').disabled = true;
            document.getElementById('errorMsg').style.display = 'none';
            document.getElementById('resultCard').className = 'card result show';
            document.getElementById('answerSection').style.display = 'none';

            const stepDefs = [
                'Creating job on Arc blockchain...',
                'Locking 1 USDC in escrow...',
                'AI agent processing task...',
                'Submitting deliverable on-chain...',
                'Releasing USDC to agent...',
            ];
            const stepsEl = document.getElementById('steps');
            stepsEl.innerHTML = stepDefs.map(s => `
                <div class="step">
                    <div class="step-icon pending">○</div>
                    <div class="step-text">${s}</div>
                </div>
            `).join('');
            const steps = stepsEl.querySelectorAll('.step');

            try {
                const res = await fetch('/job', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text, task_type: selectedTask })
                });

                const reader = res.body.getReader();
                const decoder = new TextDecoder();

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    const lines = decoder.decode(value).split('\\n').filter(l => l.startsWith('data: '));
                    for (const line of lines) {
                        const data = JSON.parse(line.slice(6));
                        if (data.step !== undefined) {
                            
                            setStep(steps, data.step, data.status || 'loading', data.text || stepDefs[data.step], data.tx);
                        }
                        if (data.result) {
                            steps.forEach((s, i) => setStep(steps, i, 'done', stepDefs[i]));
                            document.getElementById('answerBox').textContent = data.result;
                            document.getElementById('answerSection').style.display = 'block';
                        }
                        if (data.error) {
                            document.getElementById('errorMsg').textContent = '❌ ' + data.error;
                            document.getElementById('errorMsg').style.display = 'block';
                        }
                    }
                }
            } catch(e) {
                document.getElementById('errorMsg').textContent = '❌ ' + e.message;
                document.getElementById('errorMsg').style.display = 'block';
            }

            document.getElementById('submitBtn').disabled = false;
        }
    </script>
</body>
</html>
"""

from fastapi.responses import StreamingResponse
import json, asyncio

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
                prompt = f"Translate the following text to Turkish. Return only the translation:\n\n{req.text}"
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
