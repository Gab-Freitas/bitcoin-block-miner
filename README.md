# Bitcoin Block Mining Simulation

## Overview

As part of my personal exploration of the Bitcoin protocol, I developed a simulation of the mining process for a Bitcoin block. This includes selecting, validating, and including transactions from a mempool, constructing a valid block header, creating a coinbase transaction, and performing proof-of-work to meet the difficulty requirement.

All transaction data is provided as individual JSON files inside a folder named `mempool`. Each JSON file represents a transaction with all necessary metadata.

## Objective

The goal of this project was to implement a script that:

- Parses and validates transactions from the mempool.
- Constructs a coinbase transaction.
- Builds a complete block header with all required fields.
- Mines the block by finding a nonce such that the block hash meets the given difficulty target.
- Outputs the result to a file named `out.txt`.

### Output Format (`out.txt`)

```

<block header>
<serialized coinbase transaction>
<txid_1>
<txid_2>
...
```

* First line: the full block header (hexadecimal).
* Second line: the serialized coinbase transaction.
* Following lines: transaction IDs (txids) of the included transactions, starting with the coinbase txid.

## Technical Specifications

* **Difficulty Target**: `0000ffff00000000000000000000000000000000000000000000000000000000`
* **Previous Block Hash**: Can be any valid 64-character hex string, as long as the final block hash meets the difficulty target.
* **Transaction Selection**: Transactions are selected from the `mempool` folder and can be filtered based on validity, fees, or custom rules.

## Implementation

This entire project was implemented using **Python** due to its readability, flexibility, and rich ecosystem of libraries for JSON handling, cryptography, and data processing. All logic—from transaction parsing to block mining—was coded from scratch to gain a deeper understanding of how the Bitcoin protocol operates at a low level.

## Running the Project

To run the script locally:

1. Make sure you have Python 3 installed.
2. Run the main Python script (e.g., `python mine_block.py`).
3. The script will process the mempool, mine a block, and generate `out.txt`.

If successful, the script will generate a valid mined block that satisfies the difficulty constraints.

## Goals and Learning Outcomes

This project was an opportunity to:

* Deepen my understanding of Bitcoin’s mining mechanism and block structure.
* Work with real-like transaction data and simulate a realistic mempool.
* Implement proof-of-work from scratch.
* Gain hands-on experience with transaction serialization and block hashing.
