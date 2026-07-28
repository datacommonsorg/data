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
the output into Excel spreadsheets.
"""

import os
import time
import requests
import urllib3
import pandas as pd
from absl import app, logging, flags
from pathlib import Path

# Suppress SSL InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(SCRIPT_DIR, "input_files")

PANEL_FOLDER_MAP = {
    1: "Employment_And_Unemployment_Labor_Force",
    2: "Population_Economic_sector",
    3: "Average_Real_Income",
    4: "Mass_Income"
}

LOCATIONS = {
    "Brasil": "N1[1]",
    "Norte": "N2[1]",
    "Nordeste": "N2[2]",
    "Sudeste": "N2[3]",
    "Sul": "N2[4]",
    "Centro-Oeste": "N2[5]",
    "Rondônia": "N3[11]",
    "Acre": "N3[12]",
    "Amazonas": "N3[13]",
    "Roraima": "N3[14]",
    "Pará": "N3[15]",
    "Amapá": "N3[16]",
    "Tocantins": "N3[17]",
    "Maranhão": "N3[21]",
    "Piauí": "N3[22]",
    "Ceará": "N3[23]",
    "Rio Grande do Norte": "N3[24]",
    "Paraíba": "N3[25]",
    "Pernambuco": "N3[26]",
    "Alagoas": "N3[27]",
    "Sergipe": "N3[28]",
    "Bahia": "N3[29]",
    "Minas Gerais": "N3[31]",
    "Espírito Santo": "N3[32]",
    "Rio de Janeiro": "N3[33]",
    "São Paulo": "N3[35]",
    "Paraná": "N3[41]",
    "Santa Catarina": "N3[42]",
    "Rio Grande do Sul": "N3[43]",
    "Mato Grosso do Sul": "N3[50]",
    "Mato Grosso": "N3[51]",
    "Goiás": "N3[52]",
    "Distrito Federal": "N3[53]"
}

PERIOD_START = "202201"

def get_available_periods():
    """
    Fetches available period metadata starting from Q1 2022 to the latest available period.
    """
    url = "https://servicodados.ibge.gov.br/api/v3/agregados/6461/periodos"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, verify=False, timeout=30)
    res.raise_for_status()
    periods_data = res.json()
    return [p for p in periods_data if p["id"] >= PERIOD_START]

def format_quarter_label(period_item):
    """
    Formats period literals to match UI quarter headers (e.g. '1º trimestre 2022').
    """
    for lit in period_item.get("literals", []):
        if "trimestre" in lit.lower():
            return lit.lower().replace("  ", " ").strip()
    p_id = period_item["id"]
    year = p_id[:4]
    q = int(p_id[4:])
    return f"{q}º trimestre {year}"

def fetch_aggregate_series(agg_id, var_id, geo_code, period_query, classif=None):
    """
    Helper function to query IBGE aggregate API endpoint.
    """
    url = f"https://servicodados.ibge.gov.br/api/v3/agregados/{agg_id}/periodos/{period_query}/variaveis/{var_id}?localidades={geo_code}"
    if classif:
        url += f"&classificacao={classif}"
    
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=30)
        if r.status_code != 200:
            return {}
        data = r.json()
        if not data or "resultados" not in data[0]:
            return {}
        
        result_map = {}
        for res in data[0]["resultados"]:
            cat_key = "Total"
            if res.get("classificacoes"):
                cats = res["classificacoes"][0].get("categoria", {})
                if cats:
                    cat_key = list(cats.keys())[0]
            for s in res.get("series", []):
                serie = s.get("serie", {})
                result_map[cat_key] = serie
        return result_map
    except Exception as e:
        logging.warning(f"Error fetching agg {agg_id} var {var_id}: {e}")
        return {}

def fetch_panel_data(place_name, geo_code, panel_index, periods):
    """
    Fetches SIDRA data for 2022Q1 to the latest available period and reshapes the output
    to match the original homepage UI export configuration.
    """
    period_ids = [p["id"] for p in periods]
    period_labels = [format_quarter_label(p) for p in periods]
    period_query = "|".join(period_ids)

    folder_name = PANEL_FOLDER_MAP[panel_index]
    dest_dir = os.path.join(DOWNLOAD_DIR, folder_name)
    Path(dest_dir).mkdir(parents=True, exist_ok=True)
    
    filename = f"{place_name.replace(' ', '_')}_Panel_{panel_index}_Pesquisa Nacional por Amostra de Domicílios Contínua - Divulgação Trimestral.xlsx"
    filepath = os.path.join(dest_dir, filename)

    title_row = "Pesquisa Nacional por Amostra de Domicílios Contínua - Divulgação Trimestral"
    num_cols = len(period_labels) + 1
    rows = []

    if panel_index == 1:
        subtitle_row = f"Taxas e Níveis - Indicadores selecionados - Últimos {len(periods)} trimestres"
    elif panel_index == 2:
        subtitle_row = f"População - Indicadores selecionados - Últimos {len(periods)} trimestres"
    elif panel_index == 3:
        subtitle_row = f"Rendimento - Indicadores selecionados - Últimos {len(periods)} trimestres"
    else:
        subtitle_row = f"Massa de rendimento - Indicadores selecionados - Últimos {len(periods)} trimestres"

    rows.append([title_row] + [''] * (num_cols - 1))
    rows.append([subtitle_row] + [''] * (num_cols - 1))
    rows.append([place_name] + [''] * (num_cols - 1))
    rows.append(['Indicador', 'Trimestre de coleta'] + [''] * (num_cols - 2))
    rows.append([''] + period_labels)

    if panel_index == 1:
        s1 = fetch_aggregate_series(6461, 4096, geo_code, period_query).get("Total", {})
        s2 = fetch_aggregate_series(6466, 4097, geo_code, period_query).get("Total", {})
        s3 = fetch_aggregate_series(6467, 4098, geo_code, period_query).get("Total", {})
        s4 = fetch_aggregate_series(6468, 4099, geo_code, period_query).get("Total", {})

        ind_specs = [
            ("Taxa de participação na força de trabalho das pessoas de 14 anos ou mais de idade, na semana de referência (%)", s1),
            ("Nível da ocupação das pessoas de 14 anos ou mais de idade, na semana de referência (%)", s2),
            ("Nível da desocupação das pessoas de 14 anos ou mais de idade, na semana de referência (%)", s3),
            ("Taxa de desocupação das pessoas de 14 anos ou mais de idade, na semana de referência (%)", s4),
        ]
        for name, serie in ind_specs:
            vals = [serie.get(pid, '') for pid in period_ids]
            rows.append([name] + vals)
            
        rows.append(["Fonte: IBGE, Diretoria de Pesquisas, Coordenação de Trabalho e Rendimento, Pesquisa Nacional por Amostra de Domicílios Contínua"] + [''] * (num_cols - 1))

    elif panel_index == 2:
        s_pop = fetch_aggregate_series(6462, 606, geo_code, period_query).get("Total", {})
        m_6463 = fetch_aggregate_series(6463, 1641, geo_code, period_query, classif="629[all]")
        m_6464 = fetch_aggregate_series(6464, 4090, geo_code, period_query, classif="11913[all]")
        m_6465 = fetch_aggregate_series(6465, 4090, geo_code, period_query, classif="888[all]")

        ind_specs = [
            ("População total (milhares)", s_pop),
            ("Pessoas de 14 anos ou mais de idade (milhares)", m_6463.get("32385", {})),
            ("Pessoas de 14 anos ou mais de idade, na força de trabalho, na semana de referência (milhares)", m_6463.get("32386", {})),
            ("Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência (milhares)", m_6463.get("32387", {})),
            ("Pessoas de 14 anos ou mais de idade, desocupadas na semana de referência (milhares)", m_6463.get("32446", {})),
            ("Pessoas de 14 anos ou mais de idade, fora da força de trabalho, na semana de referência (milhares)", m_6463.get("32447", {})),
            ("Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência como Empregado no setor privado com carteira de trabalho assinada (milhares)", m_6464.get("31722", {})),
            ("Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência como Empregado no setor privado sem carteira de trabalho assinada (milhares)", m_6464.get("31723", {})),
            ("Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência como Trabalhador doméstico (milhares)", m_6464.get("31724", {})),
            ("Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência como Empregado no setor público (inclusive servidor estatutário e militar) (milhares)", m_6464.get("31727", {})),
            ("Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência como Empregador (milhares)", m_6464.get("96170", {})),
            ("Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência como Conta-própria (milhares)", m_6464.get("96171", {})),
            ("Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência como Trabalhador familiar auxiliar (milhares)", m_6464.get("31731", {})),
            ("Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Agricultura, pecuária, produção florestal, pesca e aquicultura (milhares)", m_6465.get("47947", {})),
            ("Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Indústria geral (milhares)", m_6465.get("47948", {})),
            ("Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Indústria de transformação (milhares)", {}),
            ("Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Construção (milhares)", m_6465.get("47949", {})),
            ("Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Comércio, reparação de veículos automotores e motocicletas (milhares)", m_6465.get("47950", {})),
            ("Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Transporte, armazenagem e correio (milhares)", m_6465.get("56622", {})),
            ("Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Alojamento e alimentação (milhares)", m_6465.get("56623", {})),
            ("Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Informação, comunicação e atividades financeiras, imobiliárias, profissionais e administrativas (milhares)", m_6465.get("56624", {})),
            ("Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Administração pública, defesa, seguridade social, educação, saúde humana e serviços sociais (milhares)", m_6465.get("60032", {})),
            ("Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Outros serviços (milhares)", m_6465.get("56627", {})),
            ("Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Serviços Domésticos (milhares)", m_6465.get("56628", {})),
            ("Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Atividades mal definidas (milhares)", {}),
        ]
        for name, serie in ind_specs:
            vals = [serie.get(pid, '') for pid in period_ids]
            rows.append([name] + vals)

    elif panel_index == 3:
        s_all_usual = fetch_aggregate_series(6472, 5933, geo_code, period_query).get("Total", {})
        s_all_eff = fetch_aggregate_series(6469, 5935, geo_code, period_query).get("Total", {})
        m_6471 = fetch_aggregate_series(6471, 5932, geo_code, period_query, classif="11913[all]")
        s_main_eff = fetch_aggregate_series(6470, 5934, geo_code, period_query).get("Total", {})
        m_6473 = fetch_aggregate_series(6473, 5932, geo_code, period_query, classif="888[all]")

        ind_specs = [
            ("Rendimento médio real de todos os trabalhos, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho (R$)", s_all_usual),
            ("Rendimento médio real de todos os trabalhos, efetivamente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho (R$)", s_all_eff),
            ("Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho (R$)", m_6471.get("96165", {})),
            ("Rendimento médio real do trabalho principal, efetivamente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho (R$)", s_main_eff),
            ("Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, como Empregado no setor privado com carteira de trabalho assinada (R$)", m_6471.get("31722", {})),
            ("Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, como Empregado no setor privado sem carteira de trabalho assinada (R$)", m_6471.get("31723", {})),
            ("Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, como Trabalhador doméstico (R$)", m_6471.get("31724", {})),
            ("Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, como Empregado no setor público (inclusive servidor estatutário e militar) (R$)", m_6471.get("31727", {})),
            ("Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, como Empregador (R$)", m_6471.get("96170", {})),
            ("Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, como Conta-própria (R$)", m_6471.get("96171", {})),
            ("Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, no grupamento de atividade Agricultura, pecuária, produção florestal, pesca e aquicultura (R$)", m_6473.get("47947", {})),
            ("Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, no grupamento de atividade Indústria geral (R$)", m_6473.get("47948", {})),
            ("Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, no grupamento de atividade Indústria de transformação (R$)", {}),
            ("Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, no grupamento de atividade Construção (R$)", m_6473.get("47949", {})),
            ("Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, no grupamento de atividade Comércio, reparação de veículos automotores e motocicletas (R$)", m_6473.get("47950", {})),
            ("Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, no grupamento de atividade Transporte, armazenagem e correio (R$)", m_6473.get("56622", {})),
            ("Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho,no grupamento de atividade Alojamento e alimentação (R$)", m_6473.get("56623", {})),
            ("Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, no grupamento de atividade Informação, comunicação e atividades financeiras, imobiliárias, profissionais e administrativas (R$)", m_6473.get("56624", {})),
            ("Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, no grupamento de atividade Administração pública, defesa, seguridade social, educação, saúde humana e serviços sociais (R$)", m_6473.get("60032", {})),
            ("Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, no grupamento de atividade Outros serviços (R$)", m_6473.get("56627", {})),
            ("Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, no grupamento de atividade Serviços Domésticos (R$)", m_6473.get("56628", {})),
            ("Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, no grupamento de atividade Atividades mal definidas (R$)", {}),
        ]
        for name, serie in ind_specs:
            vals = [serie.get(pid, '') for pid in period_ids]
            rows.append([name] + vals)

    elif panel_index == 4:
        s_mass_usual = fetch_aggregate_series(6474, 6293, geo_code, period_query).get("Total", {})
        s_mass_eff = fetch_aggregate_series(6475, 6295, geo_code, period_query).get("Total", {})

        ind_specs = [
            ("Massa de rendimento real de todos os trabalhos, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho (milhões de R$)", s_mass_usual),
            ("Massa de rendimento real de todos os trabalhos, efetivamente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho (milhões de R$)", s_mass_eff),
        ]
        for name, serie in ind_specs:
            vals = [serie.get(pid, '') for pid in period_ids]
            rows.append([name] + vals)
            
        rows.append(["Fonte: IBGE, Diretoria de Pesquisas, Coordenação de Trabalho e Rendimento, Pesquisa Nacional por Amostra de Domicílios Contínua"] + [''] * (num_cols - 1))
        rows.append(["Nota: 1 - O rendimento está deflacionado para o mês do meio do último trimestre de coleta divulgado."] + [''] * (num_cols - 1))
        rows.append(["2 - O rendimento efetivo se refere ao valor recebido no mês anterior ao da coleta."] + [''] * (num_cols - 1))

    df_out = pd.DataFrame(rows)
    os.makedirs(dest_dir, exist_ok=True)
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        df_out.to_excel(writer, sheet_name='Sheet 1', index=False, header=False)

    logging.info(f"Saved: '{filepath}'")

def main(argv):
    del argv
    logging.info("Script started.")

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    for folder_name in PANEL_FOLDER_MAP.values():
        os.makedirs(os.path.join(DOWNLOAD_DIR, folder_name), exist_ok=True)

    periods = get_available_periods()
    logging.info(f"Fetched {len(periods)} available periods starting from {PERIOD_START}: {[p['id'] for p in periods]}")

    for place_name, geo_code in LOCATIONS.items():
        logging.info(f"Processing: {place_name}")
        for panel_index in range(1, 5):
            fetch_panel_data(place_name, geo_code, panel_index, periods)
            time.sleep(0.1)

    logging.info("Script finished successfully.")

if __name__ == "__main__":
    flags.FLAGS.log_dir = SCRIPT_DIR
    app.run(main)