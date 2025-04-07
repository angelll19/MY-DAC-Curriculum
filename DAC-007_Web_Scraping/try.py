import streamlit as st
import requests
import re
from datetime import datetime
from statistics import mean

ETHERSCAN_API_KEY = "EVWY88Y9UDYU4JYTBFHRN7WNPVA253YRTA"

def is_ethereum_address(address):
    return bool(re.match(r"^0x[a-fA-F0-9]{40}$", address))

def is_bitcoin_address(address):
    return bool(re.match(r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$", address))

@st.cache_data(show_spinner=False)
def fetch_scam_bitcoin_addresses():
    url = "https://raw.githubusercontent.com/mitchellkrogza/Badd-Boyz-Bitcoin-Scammers/master/bitcoin-scammers.txt"
    try:
        response = requests.get(url)
        response.raise_for_status()
        btc_pattern = re.compile(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b')
        addresses = btc_pattern.findall(response.text)
        return set(addresses)
    except requests.RequestException:
        return set()

def check_bitcoin_scam_activity(address, scam_list):
    results = {}
    if address in scam_list:
        results["reported"] = True
    else:
        results["reported"] = False

    url = f"https://blockchain.info/rawaddr/{address}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        total_inputs = 0
        total_outputs = 0
        large_transactions = 0
        high_recipient_txs = 0
        tx_timestamps = []

        HIGH_RECIPIENT_THRESHOLD = 10
        LARGE_TX_THRESHOLD = 1_000_000

        for tx in data.get("txs", []):
            inputs = len(tx.get("inputs", []))
            outputs = len(tx.get("out", []))
            total_inputs += inputs
            total_outputs += outputs
            tx_timestamps.append(tx.get("time"))

            if outputs > HIGH_RECIPIENT_THRESHOLD:
                high_recipient_txs += 1

            for output in tx.get("out", []):
                if output.get("value", 0) > LARGE_TX_THRESHOLD:
                    large_transactions += 1

        results.update({
            "inward": total_inputs,
            "outward": total_outputs,
            "large_tx": large_transactions,
            "high_recipients": high_recipient_txs,
            "behavior_scam": large_transactions > 2 or high_recipient_txs > 2,
            "tx_count": len(tx_timestamps),
            "last_tx": datetime.utcfromtimestamp(tx_timestamps[-1]).strftime('%Y-%m-%d %H:%M:%S') if tx_timestamps else "N/A",
            "burst_activity": len(tx_timestamps) >= 3 and (max(tx_timestamps) - min(tx_timestamps)) < 3600  # 1 hour burst
        })

    except requests.RequestException as e:
        results["error"] = str(e)
    return results

def check_ethereum_scam_activity(address):
    results = {}
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={ETHERSCAN_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "1":
            results["invalid"] = True
            return results

        transactions = data.get("result", [])
        total_inward = 0
        total_outward = 0
        large_transactions = 0
        values = []
        timestamps = []

        LARGE_TX_THRESHOLD = 1 * 10**18

        for tx in transactions:
            from_address = tx.get("from", "").lower()
            to_address = tx.get("to", "").lower()
            value = int(tx.get("value", 0))
            timestamp = int(tx.get("timeStamp", 0))
            timestamps.append(timestamp)

            if to_address == address.lower():
                total_inward += 1
            if from_address == address.lower():
                total_outward += 1
                values.append(value)
                if value > LARGE_TX_THRESHOLD:
                    large_transactions += 1

        results.update({
            "inward": total_inward,
            "outward": total_outward,
            "large_tx": large_transactions,
            "avg_value_eth": round(mean(values) / 10**18, 4) if values else 0,
            "tx_count": len(transactions),
            "last_tx": datetime.utcfromtimestamp(timestamps[-1]).strftime('%Y-%m-%d %H:%M:%S') if timestamps else "N/A",
            "behavior_scam": large_transactions > 2,
            "burst_activity": len(timestamps) >= 3 and (max(timestamps) - min(timestamps)) < 3600
        })

    except requests.RequestException as e:
        results["error"] = str(e)
    return results

# === Streamlit App ===

st.set_page_config(page_title="Crypto Scam Address Detector", page_icon="🕵️‍♂️")
st.title("🕵️‍♂️ Crypto Scam Address Detector")
address_input = st.text_area("Enter Bitcoin or Ethereum address(es), separated by commas")

if st.button("Check Scam Status"):
    scam_bitcoin_addresses = fetch_scam_bitcoin_addresses()
    addresses = [addr.strip() for addr in address_input.split(",") if addr.strip()]

    st.info(f"📬 {len(addresses)} address(es) submitted for analysis.")

    for address in addresses:
        st.markdown("---")
        st.subheader(f"🔎 Address: `{address}`")
        st.caption(f"🕒 Checked on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

        if is_bitcoin_address(address):
            st.write("🔗 Type: Bitcoin")
            result = check_bitcoin_scam_activity(address, scam_bitcoin_addresses)

            if result.get("reported"):
                st.error("🚨 This address has been reported as a scam.")

            if "error" in result:
                st.error(f"❌ Error fetching data: {result['error']}")
            else:
                st.info("🧾 Summary of Address Activity:")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📥 Inward", result["inward"])
                    st.metric("💰 Large Tx", result["large_tx"])
                with col2:
                    st.metric("📤 Outward", result["outward"])
                    st.metric("🔀 High Recipients", result["high_recipients"])

                st.write(f"📥 Total Inward Transfers: `{result['inward']}`")
                st.write(f"📤 Total Outward Transfers: `{result['outward']}`")
                st.write(f"💰 Large Transactions (>1 BTC): `{result['large_tx']}`")
                st.write(f"🔀 High-Recipient Transactions (>10): `{result['high_recipients']}`")
                st.write(f"📊 Total Transactions: `{result['tx_count']}`")
                st.write(f"🕓 Last Transaction: `{result['last_tx']}`")

                if result.get("burst_activity"):
                    st.warning("⚡ Burst activity detected (many txs in short time)")

                if result.get("behavior_scam"):
                    st.warning("⚠️ Behavioral pattern suggests potential scam activity.")
                else:
                    st.success("✅ No suspicious behavior detected.")

        elif is_ethereum_address(address):
            st.write("🔗 Type: Ethereum")
            result = check_ethereum_scam_activity(address)

            if result.get("invalid"):
                st.warning("⚠️ No transactions found or invalid Ethereum address.")
            elif "error" in result:
                st.error(f"❌ Error fetching data: {result['error']}")
            else:
                st.info("🧾 Summary of Address Activity:")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📥 Inward", result["inward"])
                    st.metric("💰 Large Tx", result["large_tx"])
                with col2:
                    st.metric("📤 Outward", result["outward"])
                    st.metric("📈 Avg Tx Value (ETH)", result["avg_value_eth"])

                st.write(f"📥 Total Inward Transfers: `{result['inward']}`")
                st.write(f"📤 Total Outward Transfers: `{result['outward']}`")
                st.write(f"💰 Large Transactions (>1 ETH): `{result['large_tx']}`")
                st.write(f"📊 Total Transactions: `{result['tx_count']}`")
                st.write(f"🕓 Last Transaction: `{result['last_tx']}`")
                st.write(f"📈 Avg Tx Value (ETH): `{result['avg_value_eth']}`")

                if result.get("burst_activity"):
                    st.warning("⚡ Burst activity detected (many txs in short time)")

                if result.get("behavior_scam"):
                    st.warning("⚠️ Behavioral pattern suggests potential scam activity.")
                else:
                    st.success("✅ No suspicious behavior detected.")
        else:
            st.error("❌ Invalid address format.")

