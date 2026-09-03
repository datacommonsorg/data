# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Downloads PNAD Continuous (PNADc) quarterly data directly via IBGE REST API.
Fetches data starting from Q1 2022 to the latest available period and reshapes
the output into CSV files.
"""

import os
import time
from typing import Any, Dict, List, Optional

from absl import app, flags, logging
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from panel_specs import (
    LOCATIONS,
    get_panel_1_specs,
    get_panel_2_specs,
    get_panel_3_specs,
    get_panel_4_specs,
)

# --- Robust Session Setup ---
def get_robust_session() -> requests.Session:
    """Configures a global requests Session with automated retries and connection pooling.
    
    Retries up to 10 times with exponential backoff on common server error codes (429, 500, 502, 503, 504).
    """
    session = requests.Session()
    retries = Retry(
        total=10,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

# Global session instance
SESSION = get_robust_session()

# --- Configuration Constants ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(SCRIPT_DIR, "input_files")

# Maps panel indices (1 to 4) to their target folder names
PANEL_FOLDER_MAP = {
    1: "Employment_And_Unemployment_Labor_Force",
    2: "Population_Economic_sector",
    3: "Average_Real_Income",
    4: "Mass_Income"
}

# The starting quarter code (YYYYQQ) for filtering period metadata
PERIOD_START = "202201"


def get_available_periods() -> List[Dict[str, Any]]:
    """Fetches available period metadata starting from Q1 2022 to the latest available period.

    Returns:
        List[Dict[str, Any]]: List of dictionary objects containing period metadata.

    Raises:
        RuntimeError: If the network request fails, returns an invalid response,
            or no periods are found starting from PERIOD_START.
    """
    url = "https://servicodados.ibge.gov.br/api/v3/agregados/6461/periodos"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        logging.info(f"Fetching IBGE period metadata: GET {url}")
        res = SESSION.get(url, headers=headers, timeout=30)
        res.raise_for_status()
        periods_data = res.json()
        
        # Verify JSON structure before filtering
        if not isinstance(periods_data, list) or not periods_data:
            err_msg = (
                f"Invalid or empty period metadata response from IBGE API. "
                f"URL: {url}, Response preview: {str(periods_data)[:200]}"
            )
            raise RuntimeError(err_msg)
            
        periods = [p for p in periods_data if isinstance(p, dict) and p.get("id", "") >= PERIOD_START]
        if not periods:
            err_msg = (
                f"No available periods found starting from {PERIOD_START}. "
                f"URL: {url}, Raw count: {len(periods_data)}"
            )
            raise RuntimeError(err_msg)

        logging.info(f"Successfully retrieved {len(periods)} periods from {url}")
        return periods

    except requests.exceptions.RequestException as req_err:
        logging.error(f"Network error fetching period metadata from IBGE API. URL: {url}, Error: {req_err}")
        raise
    except ValueError as json_err:
        logging.error(f"Failed to parse JSON period metadata response. URL: {url}, Error: {json_err}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error when retrieving available periods. URL: {url}, Error: {e}")
        raise


def format_quarter_label(period_item: Dict[str, Any]) -> str:
    """Formats period literals to match UI quarter headers (e.g., '1º trimestre 2022').

    Args:
        period_item: A dictionary containing period properties ('id', 'literals').

    Returns:
        str: Formatted string header for the quarter.
    """
    try:
        # Check literals list for an explicit quarter description string
        for lit in period_item.get("literals", []):
            if "trimestre" in lit.lower():
                return lit.lower().replace("  ", " ").strip()
        
        # Fallback parsing based on period ID structure (YYYYQQ)
        p_id = period_item["id"]
        year = p_id[:4]
        q = int(p_id[4:])
        return f"{q}º trimestre {year}"
    except Exception as e:
        logging.warning(f"Failed to format quarter label for {period_item}: {e}. Falling back to period id.")
        p_id = period_item.get("id")
        if p_id:
            return str(p_id)
        err_msg = f"Malformed period item missing 'id': {period_item}"
        logging.error(err_msg)
        raise ValueError(err_msg)


def fetch_aggregate_series(agg_id: int, var_id: int, geo_code: str, period_query: str, classif: Optional[str] = None) -> Dict[str, Dict[str, str]]:
    """Helper function to query IBGE aggregate API endpoint with robust error handling.

    Args:
        agg_id: The aggregate code.
        var_id: The variable code.
        geo_code: IBGE geographical region string (e.g., 'N1[1]').
        period_query: Pipeline-separated period string (e.g., '202201|202202').
        classif: Optional classification parameters string.

    Returns:
        Dict[str, Dict[str, str]]: Dictionary mapping category keys to time series data.

    Raises:
        RuntimeError: If the network request fails, returns HTTP error, or response
            contains invalid/unexpected payload structure.
    """
    url = f"https://servicodados.ibge.gov.br/api/v3/agregados/{agg_id}/periodos/{period_query}/variaveis/{var_id}?localidades={geo_code}"
    if classif:
        url += f"&classificacao={classif}"

    context = f"URL: {url} (agg_id={agg_id}, var_id={var_id}, geo_code={geo_code}, period_query={period_query}, classif={classif})"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        logging.info(f"Fetching IBGE aggregate series: GET {url}")
        r = SESSION.get(url, headers=headers, timeout=30)
        r.raise_for_status()
            
        data = r.json()

        # Guard check to ensure valid list structure returned from API
        if not isinstance(data, list) or not data or "resultados" not in data[0]:
            err_msg = f"Invalid or empty response structure from IBGE API. Context: {context}. Response preview: {str(data)[:300]}"
            raise RuntimeError(err_msg)

        result_map = {}
        for res in data[0]["resultados"]:
            cat_key = "Total"
            # Extract category classification keys if present
            if res.get("classificacoes"):
                cats = res["classificacoes"][0].get("categoria", {})
                if cats:
                    cat_key = list(cats.keys())[0]
            
            # Map time-series dictionary to category key
            for s in res.get("series", []):
                serie = s.get("serie", {})
                result_map[cat_key] = serie

        logging.info(f"Successfully retrieved {len(result_map)} series from {url}")
        return result_map

    except requests.exceptions.RequestException as req_err:
        logging.error(f"Network exception downloading aggregate series from IBGE API. Context: {context}. Error: {req_err}")
        raise
    except ValueError as json_err:
        logging.error(f"JSON decoding error for aggregate series from IBGE API. Context: {context}. Error: {json_err}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error fetching aggregate series from IBGE API. Context: {context}. Error: {e}")
        raise


def fetch_panel_data(place_name: str, geo_code: str, panel_index: int, periods: List[Dict[str, Any]]) -> None:
    """Fetches SIDRA data for 2022Q1 to latest period, reshapes output, and writes to CSV.

    Args:
        place_name: Display name of state/region.
        geo_code: IBGE spatial lookup code.
        panel_index: Index number (1 to 4) representing the panel configuration.
        periods: List of available periods metadata dictionaries.

    Raises:
        RuntimeError: If fetching data, directory creation, or writing CSV file fails.
    """
    period_ids = [p["id"] for p in periods]
    period_labels = [format_quarter_label(p) for p in periods]
    period_query = "|".join(period_ids)

    if panel_index not in PANEL_FOLDER_MAP:
        err_msg = f"Invalid panel_index: {panel_index} for place: {place_name}"
        logging.error(err_msg)
        raise ValueError(err_msg)

    folder_name = PANEL_FOLDER_MAP[panel_index]
    dest_dir = os.path.join(DOWNLOAD_DIR, folder_name)

    # Safely create target output directory
    try:
        os.makedirs(dest_dir, exist_ok=True)
    except Exception as e:
        err_msg = f"Could not create destination directory '{dest_dir}' for place '{place_name}', panel {panel_index}: {e}"
        logging.error(err_msg)
        raise

    filename = f"{place_name.replace(' ', '_')}_Panel_{panel_index}_Pesquisa Nacional por Amostra de Domicílios Contínua - Divulgação Trimestral.csv"
    filepath = os.path.join(dest_dir, filename)

    title_row = "Pesquisa Nacional por Amostra de Domicílios Contínua - Divulgação Trimestral"
    num_cols = len(period_labels) + 1
    rows = []

    # Define subheaders by panel type
    if panel_index == 1:
        subtitle_row = f"Taxas e Níveis - Indicadores selecionados - Últimos {len(periods)} trimestres"
    elif panel_index == 2:
        subtitle_row = f"População - Indicadores selecionados - Últimos {len(periods)} trimestres"
    elif panel_index == 3:
        subtitle_row = f"Rendimento - Indicadores selecionados - Últimos {len(periods)} trimestres"
    elif panel_index == 4:
        subtitle_row = f"Massa de rendimento - Indicadores selecionados - Últimos {len(periods)} trimestres"
    else:
        err_msg = f"Invalid panel_index: {panel_index} for place: {place_name}"
        logging.error(err_msg)
        raise ValueError(err_msg)

    # Build table metadata header block
    rows.append([title_row] + [''] * (num_cols - 1))
    rows.append([subtitle_row] + [''] * (num_cols - 1))
    rows.append([place_name] + [''] * (num_cols - 1))
    rows.append(['Indicador', 'Trimestre de coleta'] + [''] * (num_cols - 2))
    rows.append([''] + period_labels)

    # ---------------------------------------------------------
    # Panel 1: Employment and Unemployment / Labor Force
    # ---------------------------------------------------------
    if panel_index == 1:
        s1 = fetch_aggregate_series(6461, 4096, geo_code, period_query).get("Total", {})
        s2 = fetch_aggregate_series(6466, 4097, geo_code, period_query).get("Total", {})
        s3 = fetch_aggregate_series(6467, 4098, geo_code, period_query).get("Total", {})
        s4 = fetch_aggregate_series(6468, 4099, geo_code, period_query).get("Total", {})

        ind_specs = get_panel_1_specs(s1, s2, s3, s4)
        for name, serie in ind_specs:
            vals = [serie.get(pid, '') for pid in period_ids]
            rows.append([name] + vals)

        rows.append(["Fonte: IBGE, Diretoria de Pesquisas, Coordenação de Trabalho e Rendimento, Pesquisa Nacional por Amostra de Domicílios Contínua"] + [''] * (num_cols - 1))

    # ---------------------------------------------------------
    # Panel 2: Population & Economic Sectors
    # ---------------------------------------------------------
    elif panel_index == 2:
        s_pop = fetch_aggregate_series(6462, 606, geo_code, period_query).get("Total", {})
        m_6463 = fetch_aggregate_series(6463, 1641, geo_code, period_query, classif="629[all]")
        m_6464 = fetch_aggregate_series(6464, 4090, geo_code, period_query, classif="11913[all]")
        m_6465 = fetch_aggregate_series(6465, 4090, geo_code, period_query, classif="888[all]")

        ind_specs = get_panel_2_specs(s_pop, m_6463, m_6464, m_6465)
        for name, serie in ind_specs:
            vals = [serie.get(pid, '') for pid in period_ids]
            rows.append([name] + vals)

    # ---------------------------------------------------------
    # Panel 3: Average Real Income
    # ---------------------------------------------------------
    elif panel_index == 3:
        s_all_usual = fetch_aggregate_series(6472, 5933, geo_code, period_query).get("Total", {})
        s_all_eff = fetch_aggregate_series(6469, 5935, geo_code, period_query).get("Total", {})
        m_6471 = fetch_aggregate_series(6471, 5932, geo_code, period_query, classif="11913[all]")
        s_main_eff = fetch_aggregate_series(6470, 5934, geo_code, period_query).get("Total", {})
        m_6473 = fetch_aggregate_series(6473, 5932, geo_code, period_query, classif="888[all]")

        ind_specs = get_panel_3_specs(s_all_usual, s_all_eff, m_6471, s_main_eff, m_6473)
        for name, serie in ind_specs:
            vals = [serie.get(pid, '') for pid in period_ids]
            rows.append([name] + vals)

    # ---------------------------------------------------------
    # Panel 4: Mass Income
    # ---------------------------------------------------------
    elif panel_index == 4:
        s_mass_usual = fetch_aggregate_series(6474, 6293, geo_code, period_query).get("Total", {})
        s_mass_eff = fetch_aggregate_series(6475, 6295, geo_code, period_query).get("Total", {})

        ind_specs = get_panel_4_specs(s_mass_usual, s_mass_eff)
        for name, serie in ind_specs:
            vals = [serie.get(pid, '') for pid in period_ids]
            rows.append([name] + vals)

        rows.append(["Fonte: IBGE, Diretoria de Pesquisas, Coordenação de Trabalho e Rendimento, Pesquisa Nacional por Amostra de Domicílios Contínua"] + [''] * (num_cols - 1))
        rows.append(["Nota: 1 - O rendimento está deflacionado para o mês do meio do último trimestre de coleta divulgado."] + [''] * (num_cols - 1))
        rows.append(["2 - O rendimento efetivo se refere ao valor recebido no mês anterior ao da coleta."] + [''] * (num_cols - 1))

    # Convert constructed matrix to DataFrame
    df_out = pd.DataFrame(rows)

    # Safely write CSV out to file
    try:
        df_out.to_csv(filepath, index=False, header=False, encoding='utf-8')
        logging.info(f"Saved: '{filepath}'")
    except Exception as write_err:
        err_msg = f"Failed writing CSV file to '{filepath}' for place '{place_name}', panel {panel_index}: {write_err}"
        logging.error(err_msg)
        raise


def main(argv):
    """Main execution function to orchestrate downloading and processing data."""
    del argv
    logging.info("Script started.")

    # Safely create input base directory structure
    try:
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        for folder_name in PANEL_FOLDER_MAP.values():
            os.makedirs(os.path.join(DOWNLOAD_DIR, folder_name), exist_ok=True)
    except Exception as dir_err:
        logging.fatal(f"Could not setup target download folders in '{DOWNLOAD_DIR}': {dir_err}")
        return

    # Retrieve period metadata
    try:
        periods = get_available_periods()
    except Exception as fetch_err:
        logging.fatal(f"Unrecoverable error fetching period metadata: {fetch_err}")
        return

    logging.info(f"Fetched {len(periods)} available periods starting from {PERIOD_START}: {[p['id'] for p in periods]}")

    # Process each location and panel step-by-step
    for place_name, geo_code in LOCATIONS.items():
        logging.info(f"Processing: {place_name}")
        for panel_index in range(1, 5):
            try:
                fetch_panel_data(place_name, geo_code, panel_index, periods)
            except Exception as panel_err:
                logging.fatal(f"Unrecoverable error processing {place_name} (Panel {panel_index}): {panel_err}")
                return
            # Short pause to reduce load on the IBGE REST API
            time.sleep(0.1)

    logging.info("Script finished successfully.")


if __name__ == "__main__":
    flags.FLAGS.log_dir = SCRIPT_DIR
    app.run(main)