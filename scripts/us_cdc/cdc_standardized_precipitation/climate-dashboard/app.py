
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import requests
import zipfile
import io
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import warnings

# --- Configuration ---
# This URL points directly to the ZIP file attached to your GitHub Release.
DATA_URL = "https://github.com/vishalworkdatacommon/climate_dasboard/releases/download/v1.0.0/spi_data.zip"

# --- Page Configuration ---
st.set_page_config(
    page_title="County-Level SPI Analysis",
    page_icon="📊",
    layout="wide",
)

# Suppress warnings for a cleaner app
warnings.filterwarnings("ignore")

# --- Data Loading Function ---
@st.cache_data
def load_data_from_zip_url(url):
    """
    Downloads a ZIP file from a URL, extracts the Parquet file from it in memory,
    and loads it into a pandas DataFrame.
    """
    response = requests.get(url)
    response.raise_for_status()  # This will raise an error if the URL is not found (404)
    
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        parquet_file_name = [name for name in z.namelist() if name.endswith('.parquet')][0]
        with z.open(parquet_file_name) as f:
            df = pd.read_parquet(f)
            
    fips_codes = sorted(df['countyfips'].unique().tolist())
    return df, fips_codes

# --- Analysis Functions (These remain unchanged) ---
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

def plot_anomaly_detection(ts):
    fig, ax = plt.subplots(figsize=(15, 7))
    rolling_mean = ts.rolling(window=12).mean()
    rolling_std = ts.rolling(window=12).std()
    upper_bound = rolling_mean + (2 * rolling_std)
    lower_bound = rolling_mean - (2 * rolling_std)
    anomalies = ts[(ts > upper_bound) | (ts < lower_bound)]
    ax.plot(ts.index, ts, label='Monthly SPI', color='dodgerblue')
    ax.plot(rolling_mean.index, rolling_mean, label='12-Month Rolling Mean', color='orange')
    ax.scatter(anomalies.index, anomalies, color='red', label='Anomaly', s=50, zorder=5)
    ax.set_title('SPI Anomaly Detection')
    ax.set_xlabel('Year')
    ax.set_ylabel('SPI Value')
    ax.legend()
    ax.grid(True, which='both', linestyle='--')
    return fig

def plot_seasonal_decomposition(ts):
    decomposition = seasonal_decompose(ts.dropna(), model='additive', period=12)
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(15, 12), sharex=True)
    decomposition.observed.plot(ax=ax1, legend=False, color='dodgerblue')
    ax1.set_ylabel('Observed')
    decomposition.trend.plot(ax=ax2, legend=False, color='darkorange')
    ax2.set_ylabel('Trend')
    decomposition.seasonal.plot(ax=ax3, legend=False, color='forestgreen')
    ax3.set_ylabel('Seasonal')
    decomposition.resid.plot(ax=ax4, legend=False, color='crimson')
    ax4.set_ylabel('Residual')
    fig.suptitle('SPI Time Series Decomposition', fontsize=16)
    plt.xlabel('Year')
    return fig

def plot_autocorrelation(ts):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    plot_acf(ts.dropna(), ax=ax1, lags=40)
    ax1.set_title('Autocorrelation Function (ACF)')
    plot_pacf(ts.dropna(), ax=ax2, lags=40)
    ax2.set_title('Partial Autocorrelation Function (PACF)')
    return fig

def plot_forecasting(ts):
    fig, ax = plt.subplots(figsize=(15, 7))
    model = ARIMA(ts.dropna(), order=(5, 1, 0))
    model_fit = model.fit()
    forecast = model_fit.get_forecast(steps=24)
    forecast_index = pd.date_range(start=ts.index[-1], periods=24 + 1, freq='MS')[1:]
    ax.plot(ts.index, ts, label='Historical Monthly SPI')
    ax.plot(forecast_index, forecast.predicted_mean, label='Forecast', color='red')
    ax.fill_between(forecast_index, forecast.conf_int().iloc[:, 0], forecast.conf_int().iloc[:, 1], color='pink', alpha=0.7, label='95% Confidence Interval')
    ax.set_title('SPI Forecast (24-Month Horizon)')
    ax.set_xlabel('Year')
    ax.set_ylabel('SPI Value')
    ax.legend()
    ax.grid(True, which='both', linestyle='--')
    return fig

# --- Main Application UI ---
st.title("County-Level Climate Analysis")
st.markdown("This application provides time-series analysis for the Standardized Precipitation Index (SPI) for any selected US county.")

try:
    # Load the full dataset and the list of FIPS codes from the public URL
    full_data, fips_codes = load_data_from_zip_url(DATA_URL)

    # --- Sidebar Controls ---
    st.sidebar.header("Controls")
    fips_code_input = st.sidebar.selectbox(
        "Select County by FIPS Code:",
        fips_codes,
        index=fips_codes.index("06037") # Default to Los Angeles County
    )

    analysis_choice = st.sidebar.selectbox(
        "Select Analysis:",
        ["Trend Analysis", "Anomaly Detection", "Seasonal Decomposition", "Autocorrelation", "Forecasting"]
    )

    # --- Main Panel Logic ---
    st.header(f"{analysis_choice} for County FIPS: {fips_code_input}")
    county_df = full_data[full_data['countyfips'] == fips_code_input]
    
    # Prepare data for plotting
    county_df['date'] = pd.to_datetime(county_df['date'])
    county_df = county_df.sort_values('date')
    county_df.set_index('date', inplace=True)
    time_series = county_df['Value'].asfreq('MS')
    
    # --- Generate and Display the Selected Plot ---
    plot_function = {
        "Trend Analysis": plot_trend_analysis,
        "Anomaly Detection": plot_anomaly_detection,
        "Seasonal Decomposition": plot_seasonal_decomposition,
        "Autocorrelation": plot_autocorrelation,
        "Forecasting": plot_forecasting
    }[analysis_choice]
    
    fig = plot_function(time_series)
    st.pyplot(fig, use_container_width=True)

except Exception as e:
    st.error(f"An error occurred while loading data from the GitHub Release: {e}")
    st.info("Please ensure a release with the tag 'v1.0.0' exists and has the 'spi_data.zip' file attached.")

# --- Footer ---
st.markdown("---")
st.markdown("Data is sourced from a file hosted on the project's GitHub Releases page.")
