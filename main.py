import streamlit as st
import requests
import time

# Set a polling interval (in seconds)
POLLING_INTERVAL = 10  # 10 seconds


def get_conversion_factors():
    return {
        "length": {"meters": 1, "feet": 3.28084, "miles": 0.000621371, "kilometers": 0.001},
        "weight": {"kilograms": 1, "grams": 1000, "pounds": 2.20462, "ounces": 35.274},
        "temperature": {
            "Celsius": {"Fahrenheit": lambda c: (c * 9/5) + 32, "Kelvin": lambda c: c + 273.15},
            "Fahrenheit": {"Celsius": lambda f: (f - 32) * 5/9, "Kelvin": lambda f: (f - 32) * 5/9 + 273.15},
            "Kelvin": {"Celsius": lambda k: k - 273.15, "Fahrenheit": lambda k: (k - 273.15) * 9/5 + 32},
        },
        "speed": {"m/s": 1, "km/h": 3.6, "mph": 2.23694},
        "time": {"seconds": 1, "minutes": 1/60, "hours": 1/3600},
        "volume": {"liters": 1, "milliliters": 1000, "gallons": 0.264172},
        "area": {"square meters": 1, "square feet": 10.7639, "acres": 0.000247105},
        "data": {"bytes": 1, "KB": 1/1024, "MB": 1/1048576, "GB": 1/1073741824},
    }

@st.cache_data(ttl=3600)
def converter(value, from_unit, to_unit, category):
    conversion_dic = get_conversion_factors()
    if category == "temperature":
        if from_unit == to_unit:
            return value
        return conversion_dic["temperature"][from_unit][to_unit](value)
    
    return value * conversion_dic[category][to_unit] / conversion_dic[category][from_unit]

def currency_converter(amount, from_currency, to_currency):
    # Check if the exchange rates need to be updated
    current_time = time.time()

    # If exchange rates are cached and valid (based on polling interval), use them
    if hasattr(st.session_state, "last_exchange_check") and current_time - st.session_state.last_exchange_check < POLLING_INTERVAL:
        rates = st.session_state.cached_rates
    else:
        # Fetch new exchange rates if necessary
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            rates = data.get("rates", {})
            # Save the new rates and update the timestamp in session_state
            st.session_state.cached_rates = rates
            st.session_state.last_exchange_check = current_time
        else:
            st.error(f"Error: Unable to fetch exchange rates for {from_currency}. Status code: {response.status_code}")
            rates = None

    # If we have valid rates, convert the currency
    if rates and to_currency in rates:
        rate = rates[to_currency]
        if rate == 0:
            st.error(f"Invalid conversion rate from {from_currency} to {to_currency}. The rate is 0.")
        else:
            return amount * rate
    else:
        return None  # Return None if rates couldn't be fetched or to_currency not found


if "history" not in st.session_state:
    st.session_state.history = []


st.set_page_config(page_title="Unit Converter", page_icon="🔄", layout="wide")
st.markdown("""
<style>
body {
    background-color:#121212;
    color: white;
    overflow-x: hidden;
}

/* Widget styling */
.stTextInput, .stSelectbox, .stNumberInput {
    background-color: #1e1e1e !important;
    color: white !important;
}

/* Cursor + hover effects */
[data-testid="stSelectbox"] label,
[data-testid="stButton"] button,
.stButton>button {
    cursor: pointer !important;
}

.stButton>button:hover {
    background-color: #333 !important;
    border: 1px solid #555 !important;
    color: white !important;
}

/* Layout fix to prevent unnecessary scrolling */
html, body, [data-testid="stAppViewContainer"], [data-testid="stAppView"], .main {
    height: 100vh;
    min-height: 100vh;
    overflow: hidden;
}

main {
    overflow-y: auto;
}
</style>
""", unsafe_allow_html=True)

# Move the conversion selection to the sidebar
st.title("Unit Converter 🔄")

conversion_type = st.sidebar.radio("Choose conversion type:", ["Units", "Currency"])

if conversion_type == "Currency":
    from_currency = st.sidebar.selectbox("From Currency", ["USD", "EUR", "GBP", "INR", "JPY", "CAD", "PKR"])
    to_currency = st.sidebar.selectbox("To Currency", ["USD", "EUR", "GBP", "INR", "JPY", "CAD", "PKR"])
    amount = st.sidebar.number_input("Enter Amount", min_value=0.0, format="%.2f")
    
    if st.sidebar.button("Convert"):
        result = currency_converter(amount, from_currency, to_currency)
        if result:
            st.success(f"Converted Amount: {result:.2f} {to_currency}")
            st.session_state.history.append({
                "Type": "Currency","Category":"Currency", "From": from_currency, "To": to_currency, "Value": amount, "Result": result
            })
        else:
            st.error("Error fetching exchange rates. Try again later.")
elif conversion_type == "Units":
    conversion_fact = get_conversion_factors()
    category = st.sidebar.selectbox("Select Category", list(conversion_fact.keys()))
    units = list(conversion_fact[category].keys())
    from_unit = st.sidebar.selectbox("From", units)
    to_unit = st.sidebar.selectbox("To", units)
    value = st.sidebar.number_input("Enter value", min_value=0.0, format="%.2f")

    if st.sidebar.button("Convert"):
        result = converter(value, from_unit, to_unit, category)
        st.success(f"Converted Value {result:.4f} {to_unit}")
        
        st.session_state.history.append({
            "Type": "Unit Conversion", "Category": category, "From": from_unit, "To": to_unit, "Value": value, "Result": result
        })

st.subheader("Conversion history 📜")
if st.session_state.history:
    with st.expander("Show history", expanded=True):
        st.table(st.session_state.history)

    if st.button("Clear"):
        st.session_state.history = []
        st.rerun()
