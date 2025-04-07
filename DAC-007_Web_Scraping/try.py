

import streamlit as st
import requests
import pandas as pd
import time
import networkx as nx
import matplotlib.pyplot as plt

# Constants
LARGE_TX_THRESHOLD_BTC = 0.01  # 0.01 BTC
LARGE_TX_THRESHOLD_ETH = 1 * 10**18  # 1 ETH in wei

def get_btc_transactions(address):
    url = f"https://blockchain.info/rawaddr/{address}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get('txs', [])
    except Exception as e:
        st.error(f"BTC API Error: {e}")
    return []

def get_eth_transactions(address, api_key):
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get('result', [])
    except Exception as e:
        st.error(f"ETH API Error: {e}")
    return []

def analyze_btc_transactions(transactions):
    results = []
    for tx in transactions:
        total_received = sum(out.get('value', 0) for out in tx.get('out', [])) / 1e8
        if total_received >= LARGE_TX_THRESHOLD_BTC:
            results.append({
                'hash': tx['hash'],
                'time': tx['time'],
                'amount_btc': total_received
            })
    return pd.DataFrame(results)

def analyze_eth_transactions(transactions):
    results = []
    for tx in transactions:
        value = int(tx['value'])
        if value >= LARGE_TX_THRESHOLD_ETH:
            results.append({
                'hash': tx['hash'],
                'timeStamp': tx['timeStamp'],
                'amount_eth': value / 1e18
            })
    return pd.DataFrame(results)

def build_btc_graph(transactions, target_address):
    G = nx.DiGraph()
    for tx in transactions:
        inputs = tx.get('inputs', [])
        outputs = tx.get('out', [])

        for inp in inputs:
            from_addr = inp.get('prev_out', {}).get('addr')
            if from_addr:
                G.add_edge(from_addr, target_address)

        for out in outputs:
            to_addr = out.get('addr')
            if to_addr:
                G.add_edge(target_address, to_addr)

    return G

def build_eth_graph(transactions, target_address):
    G = nx.DiGraph()
    for tx in transactions:
        from_addr = tx['from']
        to_addr = tx['to']
        G.add_edge(from_addr, to_addr)
    return G

def draw_graph(G, title='Wallet Network'):
    fig, ax = plt.subplots(figsize=(10, 10))
    pos = nx.spring_layout(G, k=0.5)
    nx.draw(G, pos, with_labels=False, node_size=50, arrows=True, ax=ax)
    st.pyplot(fig)

def main():
    st.title("ChainWatch - Wallet Scam Detector")

    address = st.text_input("Enter BTC or ETH address")
    eth_api_key = st.text_input("Enter your Etherscan API Key", type="password")

    if address:
        if st.button("Analyze Transactions"):
            if address.startswith("0x"):
                st.subheader("Ethereum Wallet")
                eth_txs = get_eth_transactions(address, eth_api_key)
                if eth_txs:
                    df = analyze_eth_transactions(eth_txs)
                    st.write(df)
                    st.success(f"Found {len(df)} large ETH transactions")
                else:
                    st.warning("No ETH transactions found or API issue")
            else:
                st.subheader("Bitcoin Wallet")
                btc_txs = get_btc_transactions(address)
                if btc_txs:
                    df = analyze_btc_transactions(btc_txs)
                    st.write(df)
                    st.success(f"Found {len(df)} large BTC transactions")
                else:
                    st.warning("No BTC transactions found or API issue")

        if st.button("Analyze Wallet Network"):
            if address.startswith("0x"):
                eth_txs = get_eth_transactions(address, eth_api_key)
                if eth_txs:
                    G = build_eth_graph(eth_txs, address)
                    st.write(f"ETH Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
                    draw_graph(G)
            else:
                btc_txs = get_btc_transactions(address)
                if btc_txs:
                    G = build_btc_graph(btc_txs, address)
                    st.write(f"BTC Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
                    draw_graph(G)

if __name__ == "__main__":
    main()

