import streamlit as st  # Streamlit for building the web interface
import requests         # To send HTTP requests to blockchain APIs
import re               # For regular expression-based address pattern matching

#https://chainwatch.streamlit.app/

ETHERSCAN_API_KEY = "EVWY88Y9UDYU4JYTBFHRN7WNPVA253YRTA"    # Etherscan API key

# === Functions ===
# Function to check if an address is a valid Ethereum address
# It must start with '0x' and be followed by exactly 40 hexadecimal characters
def is_ethereum_address(address):
    return bool(re.match(r"^0x[a-fA-F0-9]{40}$", address))

# Function to check if an address is a valid Bitcoin address
# It must start with '1' or '3' and be 26 to 35 characters long
def is_bitcoin_address(address):
    return bool(re.match(r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$", address))

# Cached function to fetch known scam Bitcoin addresses from a public GitHub list
@st.cache_data(show_spinner=False)
def fetch_scam_bitcoin_addresses():
    url = "https://raw.githubusercontent.com/mitchellkrogza/Badd-Boyz-Bitcoin-Scammers/master/bitcoin-scammers.txt"# Blockchain.info API endpoint
    try:
        response = requests.get(url)
        response.raise_for_status()
        btc_pattern = re.compile(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b')
        addresses = btc_pattern.findall(response.text)
        return set(addresses)
    except requests.RequestException:
        return set()

# Function to analyze Bitcoin address behavior and check against known scams
def check_bitcoin_scam_activity(address, scam_list):
    results = {}
    if address in scam_list:
        results["reported"] = True  # Flag if the address is in the known scam list
    else:
        results["reported"] = False

    url = f"https://blockchain.info/rawaddr/{address}" # Blockchain.info API endpoint
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        total_inputs = 0
        total_outputs = 0
        large_transactions = 0
        high_recipient_txs = 0

        HIGH_RECIPIENT_THRESHOLD = 10   # Flag if a transaction has more than 10 recipients
        LARGE_TX_THRESHOLD = 1_000_000  

        for tx in data.get("txs", []):  # Iterate over transactions
            inputs = len(tx.get("inputs", []))  # Count number of inputs
            outputs = len(tx.get("out", []))    # Count number of outputs
            total_inputs += inputs
            total_outputs += outputs

            if outputs > HIGH_RECIPIENT_THRESHOLD:
                high_recipient_txs += 1 # Flag for high recipient txns

            for output in tx.get("out", []):
                if output.get("value", 0) > LARGE_TX_THRESHOLD:
                    large_transactions += 1 # Flag for large value txns

        results.update({
            "inward": total_inputs,
            "outward": total_outputs,
            "large_tx": large_transactions,
            "high_recipients": high_recipient_txs,
            "behavior_scam": large_transactions > 2 or high_recipient_txs > 2
        })

    except requests.RequestException as e:
        results["error"] = str(e)   # Capture any HTTP error
    return results

# Function to analyze Ethereum address behavior using Etherscan API
def check_ethereum_scam_activity(address):
    results = {}
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={ETHERSCAN_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "1":
            results["invalid"] = True   # Address is invalid or has no transactions
            return results

        transactions = data.get("result", [])
        total_inward = 0
        total_outward = 0
        large_transactions = 0

        LARGE_TX_THRESHOLD = 1 * 10**18 # 1 ETH in Wei

        for tx in transactions:
            from_address = tx.get("from", "").lower()
            to_address = tx.get("to", "").lower()
            value = int(tx.get("value", 0))

            if to_address == address.lower():
                total_inward += 1   # Count incoming transfers
            if from_address == address.lower():
                total_outward += 1  # Count outgoing transfers
                if value > LARGE_TX_THRESHOLD:
                    large_transactions += 1   # Count large ETH transfers

        results.update({
            "inward": total_inward,
            "outward": total_outward,
            "large_tx": large_transactions,
            "behavior_scam": large_transactions > 2   
        })

    except requests.RequestException as e:
        results["error"] = str(e)   # Capture any API error
    return results

# === Streamlit App ===

st.set_page_config(page_title="Crypto Scam Address Detector", page_icon="🕵️‍♂️")# Set title and icon in browser tab
st.title("🕵️‍♂️ Crypto Scam Address Detector") # Main title displayed

# Input box for addresses (comma-separated)
address_input = st.text_area("Enter Bitcoin or Ethereum address(es), separated by commas")

# When user clicks the button
if st.button("Check Scam Status"):
    scam_bitcoin_addresses = fetch_scam_bitcoin_addresses()     # Load scam BTC address list
    addresses = [addr.strip() for addr in address_input.split(",") if addr.strip()] # Clean input addresses


    for address in addresses:# If it's a BTC address
        st.markdown("---")  # Section separator
        st.subheader(f"🔎 Address: `{address}`")    # Show the address being analyzed


        if is_bitcoin_address(address):
            result = check_bitcoin_scam_activity(address, scam_bitcoin_addresses)

            if result.get("reported"):
                st.error("🚨 This address has been reported as a scam.")

            if "error" in result:
                st.error(f"❌ Error fetching data: {result['error']}")
            else:
                st.write(f"📥 Total Inward Transfers: `{result['inward']}`")
                st.write(f"📤 Total Outward Transfers: `{result['outward']}`")
                st.write(f"💰 Large Transactions (>1 BTC): `{result['large_tx']}`")
                st.write(f"🔀 High-Recipient Transactions (>10): `{result['high_recipients']}`")

                if result.get("behavior_scam"):
                    st.warning("⚠️ Behavioral pattern suggests potential scam activity.")
                else:
                    st.success("✅ No suspicious behavior detected.")
        elif is_ethereum_address(address):  # If it's an ETH address
            result = check_ethereum_scam_activity(address)

            if result.get("invalid"):
                st.warning("⚠️ No transactions found or invalid Ethereum address.")
            elif "error" in result:
                st.error(f"❌ Error fetching data: {result['error']}")
            else:
                st.write(f"📥 Total Inward Transfers: `{result['inward']}`")
                st.write(f"📤 Total Outward Transfers: `{result['outward']}`")
                st.write(f"💰 Large Transactions (>1 ETH): `{result['large_tx']}`")

                if result.get("behavior_scam"):
                    st.warning("⚠️ Behavioral pattern suggests potential scam activity.")
                else:
                    st.success("✅ No suspicious behavior detected.")
        else:
            st.error("❌ Invalid address format.")# If the input doesn't match BTC or ETH format
