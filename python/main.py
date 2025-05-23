import os
import json
import hashlib
import time
import struct
import binascii
from bitcoinutils.transactions import Transaction
MAX_BLOCK_SIZE = 4000000  # 4MB


def calculate_witness_commitment(wtxids):
    """
    Calculates the 'witness commitment' based on a list of 'wtxids'.
    """
    # Concatenate the 'wtxids' into a single byte string
    commitment_data = b''.join(bytes.fromhex(wtxid)[::-1] for wtxid in wtxids)

    # Apply SHA-256 twice to the concatenated data
    commitment_hash = hashlib.sha256(
        hashlib.sha256(commitment_data).digest()).digest()

    # Return the commitment in hexadecimal format
    return commitment_hash.hex()


def calculate_transaction_weight(tx):
    """
    Returns the weight of a transaction directly from JSON.
    """
    return tx["weight"]


def calculate_block_weight(transactions, coinbase_tx):
    # Start with the weight of the coinbase transaction
    total_weight = coinbase_tx["weight"]
    for tx in transactions:
        total_weight += tx["weight"]
    return total_weight


def read_transactions(txid_folder="mempool"):
    # Ensure we get the correct file
    txid_file = os.path.join(txid_folder, "mempool.json")
    transactions = {}

    try:
        with open(txid_file, 'r') as f:
            txids = json.load(f)  # Load the list of txids

        for txid in txids:
            # Create a dictionary with txids
            wtxid = txid
            transactions[txid] = {"tx": txid, "wtxid": wtxid}

    except (json.JSONDecodeError, FileNotFoundError, IsADirectoryError) as e:
        print(f"Error reading {txid_file}: {e}")

    return transactions


def create_coinbase_transaction(witness_commitment=None):
    version = struct.pack('<L', 5)  # Version 1 (01000000)

    marker = b'\x00'
    flag = b'\x01'

    # Number of inputs (1)
    tx_in_count = b'\x01'

    # Input (Coinbase)
    prev_txid = b'\x00' * 32  # Previous transaction hash (zeroed out)
    prev_index = struct.pack('<L', 0xFFFFFFFF)  # Previous index (0xFFFFFFFF)

    # ScriptSig (Coinbase data)
    coinbase_data = b'\x4d696e657220526577617264'  # "Miner Reward" in ASCII
    script_sig_length = struct.pack('B', len(coinbase_data))

    sequence = struct.pack('<L', 0xFFFFFFFF)  # Sequence (0xFFFFFFFF)

    # Number of outputs (2)
    tx_out_count = b'\x02'

    # First output (miner reward)
    block_reward = struct.pack('<Q', 5000000000)  # 50 BTC in Satoshis
    script_pubkey = binascii.unhexlify(
        '76a914c9226865a8f36758f08a645c691b7bcc177f053388ac')
    script_length = struct.pack('B', len(script_pubkey))

    # Second output (commitment OP_RETURN)
    op_return = b'\x6a'  # OP_RETURN
    if witness_commitment:
        commitment_data = binascii.unhexlify(
            witness_commitment)  # The calculated witness commitment
    else:
        commitment_data = hashlib.sha256(
            b'Commitment').digest()  # Fallback to a default value

    # Correcting the prefix to 6a24aa21a9ed
    commitment_prefix = binascii.unhexlify("aa21a9ed")  # Correct prefix

    # Concatenating correctly
    full_commitment_data = commitment_prefix + commitment_data

    op_return_script = op_return + \
        struct.pack('B', len(full_commitment_data)) + full_commitment_data
    op_return_script_length = struct.pack('B', len(op_return_script))

    # Witness (SegWit)
    witness_count = b'\x01'
    witness_reserved_value = b'\x00' * 32  # 32 bytes of zero
    witness_length = struct.pack('B', len(witness_reserved_value))

    # Locktime (zero for coinbase)
    locktime = struct.pack('<L', 0)

    raw_tx = (
        version + marker + flag +
        tx_in_count + prev_txid + prev_index + script_sig_length + coinbase_data + sequence +
        tx_out_count + block_reward + script_length + script_pubkey +
        b'\x00' * 8 + op_return_script_length + op_return_script +
        witness_count + witness_length + witness_reserved_value +
        locktime
    )

    raw_tx_hex = binascii.hexlify(raw_tx).decode()

    # Calculate TXID and WTXID correctly
    txid = hashlib.sha256(hashlib.sha256(raw_tx).digest()).digest()[::-1].hex()
    wtxid = hashlib.sha256(hashlib.sha256(
        raw_tx).digest()).digest()[::-1].hex()

    return {
        "raw": raw_tx_hex,
        "txid": txid,
        "wtxid": wtxid
    }


def hash256(data):
    """Applies SHA-256 twice and returns the hash in hexadecimal"""
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def compute_merkle_root(txids):
    if len(txids) == 0:
        return "0" * 64  # Empty hash if no transactions

    # Convert TXIDs to little-endian before calculation
    level = [binascii.unhexlify(txid)[::-1] for txid in txids]

    while len(level) > 1:
        if len(level) % 2 == 1:
            # Duplicate the last TXID if the count is odd
            level.append(level[-1])

        new_level = []
        for i in range(0, len(level), 2):
            # Concatenate the pairs of hashes
            combined = level[i] + level[i + 1]
            new_hash = hash256(combined)  # Apply double SHA-256
            new_level.append(new_hash)

        level = new_level

    # Return the final hash in big-endian
    return binascii.hexlify(level[0]).decode()


def mine_block(prev_block_hash, merkle_root, difficulty_target):
    version = struct.pack('<L', 4).hex()  # CORRECTED: correct version (>=4)
    timestamp = struct.pack('<L', int(time.time())).hex()
    # CORRECTED: correct bits expected by the test
    bits = struct.pack('<L', 0x1f00ffff).hex()
    nonce = 0
    prev_block_hash = bytes.fromhex(prev_block_hash)[::-1].hex()

    while True:
        nonce_hex = struct.pack('<L', nonce).hex()
        header = version + prev_block_hash + merkle_root + timestamp + bits + nonce_hex
        block_hash = hashlib.sha256(hashlib.sha256(
            binascii.unhexlify(header)).digest()).digest()[::-1].hex()

        if int(block_hash, 16) < int(difficulty_target, 16):
            return header, block_hash
        nonce += 1


def write_output(filename, header, coinbase_tx, txids):
    with open(filename, 'w') as f:
        f.write(header + '\n')
        f.write(coinbase_tx["raw"] + '\n')
        for txid in txids:
            f.write(txid + '\n')


def main():
    mempool_folder = "mempool"
    difficulty_target = "0000ffff00000000000000000000000000000000000000000000000000000000"
    prev_block_hash = "0000000000000000000000000000000000000000000000000000000000000000"

    mempool = read_transactions(mempool_folder)
    # selected_txids = select_transactions(mempool)

    txids = [data["tx"] for data in mempool.values()]
    selected_txids = []
    wtxids = ["0000000000000000000000000000000000000000000000000000000000000000"]
    totalWeight = 0
    for i in range(1, len(txids)):
        # Reading the corresponding JSON file for the txid
        with open(f'./mempool/{txids[i]}.json', 'r') as f:
            tx = json.load(f)

        # Adding the transaction weight to totalWeight
        totalWeight += int(tx['weight'])

        # Adding txid to the list
        selected_txids.append(txids[i])
        parsedTx = Transaction.from_raw(tx["hex"])
        wtxid = parsedTx.get_wtxid()
        wtxids.append(wtxid)
        # Checking if the total weight reached the limit
        if totalWeight >= 400000:
            break

    witness_reserved_value = b'\x00' * 32  # 32 bytes of zeros
    witness_commitment = hash256(
        binascii.unhexlify(compute_merkle_root(wtxids)) +
        witness_reserved_value
    ).hex()
    coinbase_tx = create_coinbase_transaction(
        witness_commitment=witness_commitment)
    txids = [coinbase_tx["txid"]] + [data for data in selected_txids]

    witness_merkle_root = compute_merkle_root(txids)

    header, block_hash = mine_block(
        prev_block_hash, witness_merkle_root, difficulty_target
    )

    write_output("out.txt", header, coinbase_tx, txids)


if __name__ == "__main__":
    main()
