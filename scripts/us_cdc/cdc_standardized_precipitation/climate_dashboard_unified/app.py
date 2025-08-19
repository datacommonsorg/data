# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
import warnings
import urllib.request
from datetime import datetime

# --- Plotting and Analysis ---
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import acf, pacf
import pmdarima as pm

# --- Page Configuration ---
st.set_page_config(
    page_title="U.S. County-Level Drought Analysis",
    page_icon="💧",
    layout="wide",
)

# Suppress warnings for a cleaner app
warnings.filterwarnings("ignore")

# --- Live Data Pipeline ---
@st.cache_data(ttl="1d")
def get_live_data():
    """
    Downloads, parses, and combines live climate data from data.cdc.gov.
    The result is cached for 24 hours. Returns the data and the update time.
    """
    with st.spinner("Fetching and processing live data from data.cdc.gov. This may take several minutes..."):
        urls = {
            "SPEI": "https://data.cdc.gov/resource/6nbv-ifib.csv",
            "SPI": "https://data.cdc.gov/resource/xbk2-5i4e.csv",
            "PDSI": "https://data.cdc.gov/resource/en5r-5ds4.csv"
        }
        all_data = []
        for index_type, url in urls.items():
            try:
                full_url = f"{url}?$limit=10000000"
                df = pd.read_csv(full_url)

                # --- Standardize the dataframe ---
                df["month"] = df["month"].map("{:02}".format)
                df["date"] = df["year"].astype(str) + "-" + df["month"].astype(str)
                if "fips" in df.columns:
                    df.rename(columns={'fips': 'countyfips'}, inplace=True)
                df['countyfips'] = df['countyfips'].astype(str).str.zfill(5)
                if index_type == 'SPEI':
                    df.rename(columns={'spei': 'Value'}, inplace=True)
                elif index_type == 'SPI':
                    df.rename(columns={'spi': 'Value'}, inplace=True)
                elif index_type == 'PDSI':
                    df.rename(columns={'pdsi': 'Value'}, inplace=True)

                df['index_type'] = index_type
                
                # Keep only the necessary columns
                cols_to_keep = ['date', 'countyfips', 'Value', 'index_type']
                if all(col in df.columns for col in cols_to_keep):
                    all_data.append(df[cols_to_keep])
                else:
                    st.warning(f"Could not process {index_type} due to missing columns.")

            except Exception as e:
                st.error(f"Failed to load or process data for {index_type}. Error: {e}")
                continue

        if not all_data:
            st.error("Could not load any climate data. The application cannot proceed.")
            return pd.DataFrame(), pd.Series(), None

        # --- Combine and Merge Data ---
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df['date'] = pd.to_datetime(combined_df['date'])

        # --- Load FIPS Data ---
        fips_file_path = os.path.join(os.path.dirname(__file__), 'fips_to_county.csv')
        if not os.path.exists(fips_file_path):
            st.error(f"Fatal Error: The FIPS data file was not found.")
            return pd.DataFrame(), pd.Series(), None
        
        fips_df = pd.read_csv(fips_file_path)
        fips_df['state_fips'] = fips_df['state_fips'].astype(str).str.zfill(2)
        fips_df['county_fips'] = fips_df['county_fips'].astype(str).str.zfill(3)
        fips_df['countyfips'] = fips_df['state_fips'] + fips_df['county_fips']
        fips_df.rename(columns={'county': 'county_name'}, inplace=True)

        # Merge
        df = pd.merge(combined_df, fips_df[['countyfips', 'county_name', 'state']], on='countyfips', how='left')
        df.dropna(subset=['county_name', 'state'], inplace=True)
        df['display_name'] = df['county_name'] + ", " + df['state']
        
        fips_options = df[['countyfips', 'display_name']].drop_duplicates().sort_values('display_name').set_index('countyfips')
        
        return df, fips_options, datetime.now()

# --- Analysis Functions ---
def plot_trend_analysis(ts, index_type):
    rolling_avg = ts.rolling(window=12).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ts.index, y=ts, mode='lines', name=f'Monthly {index_type}', line=dict(color='lightblue')))
    fig.add_trace(go.Scatter(x=rolling_avg.index, y=rolling_avg, mode='lines', name='12-Month Rolling Average', line=dict(color='navy', width=2.5)))
    fig.update_layout(title=f'{index_type} Trend Analysis', xaxis_title='Year', yaxis_title=f'{index_type} Value', legend=dict(x=0.01, y=0.99, bordercolor="Black", borderwidth=1), template='plotly_white', font=dict(size=14), height=600)
    return fig

def plot_anomaly_detection(ts, index_type):
    rolling_mean = ts.rolling(window=12).mean()
    rolling_std = ts.rolling(window=12).std()
    upper_bound = rolling_mean + (2 * rolling_std)
    lower_bound = rolling_mean - (2 * rolling_std)
    anomalies = ts[(ts > upper_bound) | (ts < lower_bound)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ts.index, y=ts, mode='lines', name=f'Monthly {index_type}', line=dict(color='dodgerblue')))
    fig.add_trace(go.Scatter(x=rolling_mean.index, y=rolling_mean, mode='lines', name='12-Month Rolling Mean', line=dict(color='orange', width=2.5)))
    fig.add_trace(go.Scatter(x=anomalies.index, y=anomalies, mode='markers', name='Anomaly', marker=dict(color='red', size=8, symbol='x')))
    fig.update_layout(title=f'{index_type} Anomaly Detection', xaxis_title='Year', yaxis_title=f'{index_type} Value', legend=dict(x=0.01, y=0.99, bordercolor="Black", borderwidth=1), template='plotly_white', font=dict(size=14), height=600)
    return fig

def plot_seasonal_decomposition(ts, index_type):
    decomposition = seasonal_decompose(ts.dropna(), model='additive', period=12)
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, subplot_titles=("Observed", "Trend", "Seasonal", "Residual"))
    fig.add_trace(go.Scatter(x=decomposition.observed.index, y=decomposition.observed, mode='lines', name='Observed', line=dict(color='dodgerblue')), row=1, col=1)
    fig.add_trace(go.Scatter(x=decomposition.trend.index, y=decomposition.trend, mode='lines', name='Trend', line=dict(color='orange')), row=2, col=1)
    fig.add_trace(go.Scatter(x=decomposition.seasonal.index, y=decomposition.seasonal, mode='lines', name='Seasonal', line=dict(color='green')), row=3, col=1)
    fig.add_trace(go.Scatter(x=decomposition.resid.index, y=decomposition.resid, mode='markers', name='Residual', marker=dict(color='red', size=4)), row=4, col=1)
    fig.update_layout(title_text=f'{index_type} Time Series Decomposition', height=700, showlegend=False, template='plotly_white', font=dict(size=14))
    return fig

def plot_autocorrelation(ts, index_type):
    nlags = 40
    ts_dropna = ts.dropna()
    acf_values, confint_acf = acf(ts_dropna, nlags=nlags, alpha=0.05)
    pacf_values, confint_pacf = pacf(ts_dropna, nlags=nlags, alpha=0.05)
    ci_acf = confint_acf - acf_values[:, None]
    ci_pacf = confint_pacf - pacf_values[:, None]
    fig = make_subplots(rows=2, cols=1, subplot_titles=("Autocorrelation (ACF)", "Partial Autocorrelation (PACF)"))
    fig.add_trace(go.Bar(x=list(range(1, nlags + 1)), y=acf_values[1:], name='ACF'), row=1, col=1)
    fig.add_trace(go.Scatter(x=list(range(1, nlags + 1)), y=ci_acf[1:, 0], mode='lines', line=dict(color='blue', dash='dash'), showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=list(range(1, nlags + 1)), y=ci_acf[1:, 1], mode='lines', line=dict(color='blue', dash='dash'), fill='tonexty', fillcolor='rgba(0,0,255,0.1)', showlegend=False), row=1, col=1)
    fig.add_trace(go.Bar(x=list(range(1, nlags + 1)), y=pacf_values[1:], name='PACF'), row=2, col=1)
    fig.add_trace(go.Scatter(x=list(range(1, nlags + 1)), y=ci_pacf[1:, 0], mode='lines', line=dict(color='blue', dash='dash'), showlegend=False), row=2, col=1)
    fig.add_trace(go.Scatter(x=list(range(1, nlags + 1)), y=ci_pacf[1:, 1], mode='lines', line=dict(color='blue', dash='dash'), fill='tonexty', fillcolor='rgba(0,0,255,0.1)', showlegend=False), row=2, col=1)
    fig.update_layout(title_text=f'Autocorrelation for {index_type}', height=600, template='plotly_white', font=dict(size=14))
    return fig

def plot_forecasting(ts, index_type):
    with st.spinner("Finding best forecast model... This may take a moment."):
        model = pm.auto_arima(ts.dropna(), start_p=1, start_q=1, test='adf', max_p=3, max_q=3, m=12, d=None, seasonal=True, start_P=0, D=1, trace=False, error_action='ignore', suppress_warnings=True, stepwise=True)
    n_periods = 24
    forecast, conf_int = model.predict(n_periods=n_periods, return_conf_int=True)
    forecast_index = pd.date_range(start=ts.index[-1], periods=n_periods + 1, freq='MS')[1:]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ts.index, y=ts, mode='lines', name=f'Historical Monthly {index_type}'))
    fig.add_trace(go.Scatter(x=forecast_index, y=forecast, mode='lines', name='Forecast', line=dict(color='red', width=2.5)))
    fig.add_trace(go.Scatter(x=forecast_index, y=[c[0] for c in conf_int], mode='lines', line=dict(width=0), showlegend=False))
    fig.add_trace(go.Scatter(x=forecast_index, y=[c[1] for c in conf_int], mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(255, 0, 0, 0.2)', name='95% Confidence Interval'))
    fig.update_layout(title=f'{index_type} Forecast (24-Month Horizon)', xaxis_title='Year', yaxis_title=f'{index_type} Value', legend=dict(x=0.01, y=0.99, bordercolor="Black", borderwidth=1), template='plotly_white', font=dict(size=14), height=600)
    return fig

if __name__ == "__main__":
    st.title("💧 U.S. County-Level Drought Analysis")
    st.markdown("Explore and compare key drought indices for any county in the United States. This dashboard uses live data, automatically refreshed daily.")

    full_data, fips_options, last_updated = get_live_data()

    with st.sidebar:
        st.header("Dashboard Controls")
        if last_updated:
            st.info(f"Data last updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S')} UTC")

        if not full_data.empty and not fips_options.empty:
            index_choice = st.selectbox("1. Select Climate Index:", options=sorted(full_data['index_type'].unique()), key="index_selectbox")
            
            default_selection = [fips_options.index.tolist()[0]] if not fips_options.empty else []
            fips_code_inputs = st.multiselect("2. Select County/Counties:", options=fips_options.index.tolist(), format_func=lambda x: fips_options.loc[x]['display_name'], default=default_selection, key="fips_multiselect")

            if len(fips_code_inputs) > 1:
                analysis_options = ["Trend Analysis", "Anomaly Detection"]
            else:
                analysis_options = ["Trend Analysis", "Anomaly Detection", "Seasonal Decomposition", "Autocorrelation", "Forecasting"]
            analysis_choice = st.selectbox("3. Select Analysis:", analysis_options, key="analysis_selectbox")

            if fips_code_inputs:
                csv_data = full_data[full_data['countyfips'].isin(fips_code_inputs)]
                st.download_button(label="Download Selected Data (CSV)", data=csv_data.to_csv(index=False).encode('utf-8'), file_name=f"{index_choice}_data_{'_'.join(fips_code_inputs)}.csv", mime="text/csv", key="download_button")
        else:
            st.error("Data could not be loaded. The dashboard cannot be displayed.")
            st.stop()

    if not fips_code_inputs:
        st.warning("Please select at least one county from the sidebar to begin.")
        st.stop()

    selected_county_names = [fips_options.loc[fips]['display_name'] for fips in fips_code_inputs]
    st.header(f"{analysis_choice}: {index_choice}")
    st.markdown(f"**Displaying data for:** `{', '.join(selected_county_names)}`")

    with st.expander("About This Analysis"):
        analysis_explanations = {
            "Trend Analysis": "This chart shows the monthly index values over time, along with a 12-month rolling average. It helps you see the long-term trends and patterns in the data, smoothing out short-term fluctuations.",
            "Anomaly Detection": "This analysis highlights periods that were unusually wet or dry. The red dots mark months where the index value was significantly different (more than two standard deviations) from the 12-month rolling average, indicating extreme conditions.",
            "Seasonal Decomposition": "This technique breaks down the time series into three components: the long-term **Trend**, the repeating annual **Seasonal** cycle, and the irregular **Residual** noise. This helps to understand the underlying patterns driving the index values.",
            "Autocorrelation": "These plots show how correlated the index is with itself at different points in time. The ACF (Autocorrelation Function) and PACF (Partial Autocorrelation Function) are used in statistical modeling to identify how much past values influence future values.",
            "Forecasting": "This chart displays a 24-month forecast of the climate index. It uses a sophisticated **auto-ARIMA model** to automatically find the best statistical fit for the historical data, providing a more robust and data-driven prediction. The pink area represents the 95% confidence interval."
        }
        st.info(analysis_explanations[analysis_choice])

    plot_function_mapping = {
        "Trend Analysis": plot_trend_analysis, "Anomaly Detection": plot_anomaly_detection,
        "Seasonal Decomposition": plot_seasonal_decomposition, "Autocorrelation": plot_autocorrelation,
        "Forecasting": plot_forecasting
    }

    fig = go.Figure()
    for fips_code in fips_code_inputs:
        filtered_df = full_data[(full_data['countyfips'] == fips_code) & (full_data['index_type'] == index_choice)]
        if not filtered_df.empty:
            time_series = filtered_df.set_index('date')['Value'].asfreq('MS')
            county_name = fips_options.loc[fips_code]['display_name']
            
            if len(fips_code_inputs) == 1:
                fig = plot_function_mapping[analysis_choice](time_series, index_choice)
                break
            
            if analysis_choice == "Trend Analysis":
                rolling_avg = time_series.rolling(window=12).mean()
                fig.add_trace(go.Scatter(x=time_series.index, y=time_series, mode='lines', name=f'{county_name}'))
                fig.add_trace(go.Scatter(x=rolling_avg.index, y=rolling_avg, mode='lines', name=f'{county_name} (Rolling Avg)', line=dict(dash='dash')))
            elif analysis_choice == "Anomaly Detection":
                rolling_mean = time_series.rolling(window=12).mean()
                rolling_std = time_series.rolling(window=12).std()
                anomalies = time_series[(time_series > rolling_mean + (2 * rolling_std)) | (time_series < rolling_mean - (2 * rolling_std))]
                fig.add_trace(go.Scatter(x=time_series.index, y=time_series, mode='lines', name=f'{county_name}'))
                fig.add_trace(go.Scatter(x=anomalies.index, y=anomalies, mode='markers', name=f'{county_name} Anomaly', marker=dict(symbol='x')))

    if len(fips_code_inputs) > 1:
        fig.update_layout(title=f'{index_choice} {analysis_choice}', xaxis_title='Year', yaxis_title=f'{index_choice} Value', legend_title="Counties", template='plotly_white', font=dict(size=14), height=600)

    if fig.data:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for the selected combination of counties and index. Please make another selection.")

    st.markdown("---")
    st.markdown("Data Source: [NOAA National Centers for Environmental Information (NCEI)](https://www.ncei.noa.gov/access/monitoring/nadm/indices)")
    st.markdown("This application provides a comparative tool for various climate indices, allowing for a deeper understanding of regional climate patterns.")