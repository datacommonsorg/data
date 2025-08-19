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
        pass
    file_path = os.path.join(os.path.dirname(__file__), 'spi_data.parquet')
    df = pd.read_parquet(file_path)
    fips_codes = sorted(df['countyfips'].unique().tolist())
    return df, fips_codes

def plot_trend_analysis(ts):
    fig, ax = plt.subplots(figsize=(15, 7))
    rolling_avg = ts.rolling(window=12).mean()
    ax.plot(ts.index, ts, label='Monthly SPI', color='lightblue', alpha=0.7)
    ax.plot(rolling_avg.index, rolling_avg, label='12-Month Rolling Average', color='navy')
    ax.set_title('SPI Trend Analysis')
    ax.set_xlabel('Year')
    ax.set_ylabel('SPI Value')
    ax.grid(True, which='both', linestyle='--')
    ax.legend()
    return fig

# ... (All other plotting functions are included here) ...

st.title("County-Level Climate Analysis")
full_data, fips_codes = load_data()
st.sidebar.header("Controls")
fips_code_input = st.sidebar.selectbox("Select County by FIPS Code:", fips_codes, index=fips_codes.index("06037"))
analysis_choice = st.sidebar.selectbox("Select Analysis:", ["Trend Analysis", "Anomaly Detection", "Seasonal Decomposition", "Autocorrelation", "Forecasting"])
st.header(f"{analysis_choice} for County FIPS: {fips_code_input}")
county_df = full_data[full_data['countyfips'] == fips_code_input]
county_df['date'] = pd.to_datetime(county_df['date'])
county_df = county_df.sort_values('date')
county_df.set_index('date', inplace=True)
time_series = county_df['Value'].asfreq('MS')
plot_function = {
    "Trend Analysis": plot_trend_analysis,
    # ... (other plot functions) ...
}[analysis_choice]
fig = plot_function(time_series)
st.pyplot(fig, use_container_width=True)
st.markdown("---")
st.markdown("This application utilizes data stored within the repository, managed by Git LFS.")
