from solcx import compile_standard, install_solc
import json

install_solc("0.8.19")

with open("blockchain/contract.sol", "r") as file:
    source_code = file.read()

compiled = compile_standard(
    {
        "language": "Solidity",
        "sources": {
            "contract.sol": {
                "content": source_code
            }
        },
        "settings": {
            "outputSelection": {
                "*": {
                    "*": ["abi", "evm.bytecode"]
                }
            }
        }
    },
    solc_version="0.8.19"
)

contract_data = compiled["contracts"]["contract.sol"]["EvidenceRegistry"]

with open("blockchain/compiled_contract.json", "w") as file:
    json.dump(contract_data, file, indent=2)

print("Contract compiled successfully!")
print("ABI and bytecode saved.")