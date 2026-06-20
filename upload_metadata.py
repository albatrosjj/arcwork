import os, json, requests
from dotenv import load_dotenv

load_dotenv()

metadata = {
    "name": "ArcWork AI Agent v1.0",
    "description": "Autonomous AI agent on Arc blockchain. Accepts translation, summarization and analysis tasks. Pays and gets paid in USDC via ERC-8183 job contracts.",
    "image": "ipfs://bafkreibdi6623n3xpf7ymk62ckb4bo75o3qemwkpfvp5i25j66itxvsoei",
    "agent_type": "freelance_worker",
    "capabilities": [
        "text_translation",
        "text_summarization", 
        "data_analysis",
        "content_generation"
    ],
    "standards": ["ERC-8004", "ERC-8183"],
    "network": "Arc Testnet",
    "version": "1.0.0",
    "author": "ArcWork Project",
    "repository": "https://github.com/arcwork"
}

response = requests.post(
    "https://api.pinata.cloud/pinning/pinJSONToIPFS",
    headers={
        "pinata_api_key": os.getenv("PINATA_API_KEY"),
        "pinata_secret_api_key": os.getenv("PINATA_SECRET"),
        "Content-Type": "application/json"
    },
    json={
        "pinataContent": metadata,
        "pinataMetadata": {"name": "arcwork-agent-metadata.json"}
    }
)

result = response.json()
print("✓ Metadata IPFS'e yüklendi!")
print(f"IPFS Hash: {result['IpfsHash']}")
print(f"URI: ipfs://{result['IpfsHash']}")
print(f"Gateway: https://gateway.pinata.cloud/ipfs/{result['IpfsHash']}")
