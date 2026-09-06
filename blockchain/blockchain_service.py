from web3 import Web3
import json
from evidence import hash_evidence


RPC_URL = "http://127.0.0.1:7545"


def connect_blockchain():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))

    if not w3.is_connected():
        raise Exception("Could not connect to Ganache")

    return w3


def load_contract(w3):
    with open("blockchain/deployment.json", "r") as file:
        deployment = json.load(file)

    contract = w3.eth.contract(
        address=deployment["contract_address"],
        abi=deployment["abi"]
    )

    return contract, deployment["contract_address"]


def store_evidence(evidence):
    """
    Hash evidence and store the hash on the blockchain.
    """

    w3 = connect_blockchain()
    contract, contract_address = load_contract(w3)

    evidence_hash = hash_evidence(evidence)

    account = w3.eth.accounts[0]

    tx_hash = contract.functions.storeEvidence(
        evidence_hash
    ).transact({
        "from": account
    })

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return {
        "evidence_hash": evidence_hash.hex(),
        "transaction_hash": receipt.transactionHash.hex(),
        "block_number": receipt.blockNumber,
        "contract_address": contract_address
    }


def verify_evidence(evidence):
    """
    Re-hash evidence and check whether that hash exists on-chain.
    """

    w3 = connect_blockchain()
    contract, contract_address = load_contract(w3)

    evidence_hash = hash_evidence(evidence)

    verified = contract.functions.verifyEvidence(
        evidence_hash
    ).call()

    return {
        "evidence_hash": evidence_hash.hex(),
        "verified": verified,
        "contract_address": contract_address
    }