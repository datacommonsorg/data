import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import warnings

# --- Page Configuration ---
st.set_page_config(
    page_title="National SPI Analysis",
    page_icon="📊",
    layout="wide",
)

# Suppress warnings for a cleaner app
warnings.filterwarnings("ignore")

# --- Data Loading Function ---
@st.cache_data
def load_data():
    """
    Loads the pre-aggregated national data file from the local repository.
    """
    file_path = os.path.join(os.path.dirname(__file__), 'spi_national_monthly.csv')
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df['MeanValue']

# --- Analysis Functions (These remain unchanged) ---
def plot_trend_analysis(ts):
    fig, ax = plt.subplots(figsize=(15, 7))
    rolling_avg = ts.rolling(window=12).mean()
    ax.plot(ts.index, ts, label='Monthly Average SPI', color='lightblue', alpha=0.7)
    ax.plot(rolling_avg.index, rolling_avg, label='12-Month Rolling Average', color='navy')
    ax.set_title('National SPI Trend Analysis')
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
    ax.set_title('National SPI Anomaly Detection')
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
    fig.suptitle('National SPI Time Series Decomposition', fontsize=16)
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
    ax.set_title('National SPI Forecast (24-Month Horizon)')
    ax.set_xlabel('Year')
    ax.set_ylabel('SPI Value')
    ax.legend()
    ax.grid(True, which='both', linestyle='--')
    return fig

# --- Main Application UI ---
st.title("National Climate Analysis")
st.markdown("This application provides time-series analysis for the national average Standardized Precipitation Index (SPI).")

# Load the pre-aggregated dataset
time_series = load_data()

# --- Sidebar Controls ---
st.sidebar.header("Controls")
analysis_choice = st.sidebar.selectbox(
    "Select Analysis:",
    ["Trend Analysis", "Anomaly Detection", "Seasonal Decomposition", "Autocorrelation", "Forecasting"]
)

# --- Main Panel Logic ---
st.header(f"National SPI: {analysis_choice}")

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

# --- Footer ---
st.markdown("---")
st.markdown("This application uses pre-aggregated national data stored within the repository.")