import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import subprocess
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import warnings

st.set_page_config(page_title="County-Level SPI Analysis", page_icon="📊", layout="wide")
warnings.filterwarnings("ignore")

@st.cache_data
def load_data():
    try:
        subprocess.run(["git", "lfs", "pull"], check=True)
    except Exception:
        pass # Fails silently if git lfs is not available
    file_path = os.path.join(os.path.dirname(__file__), 'spi_data.parquet')
    df = pd.read_parquet(file_path)
    fips_codes = sorted(df['countyfips'].unique().tolist())
    return df, fips_codes

# ... (plotting functions) ...

st.title("County-Level Climate Analysis")
full_data, fips_codes = load_data()
st.sidebar.header("Controls")
fips_code_input = st.sidebar.selectbox("Select County by FIPS Code:", fips_codes, index=fips_codes.index("06037"))
analysis_choice = st.sidebar.selectbox("Select Analysis:", ["Trend Analysis", "Anomaly Detection", "Seasonal Decomposition", "Autocorrelation", "Forecasting"])
st.header(f"{analysis_choice} for County FIPS: {fips_code_input}")
# ... (rest of app logic) ...
