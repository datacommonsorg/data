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

"""Configuration variables and location mappings for IBGE SIDRA data extraction."""

from typing import Any, Dict, List, Tuple

# Mapping of Brazilian location display names to IBGE geo-location codes
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
    "Distrito Federal": "N3[53]",
}

# ---------------------------------------------------------
# Panel 1: Employment and Unemployment / Labor Force
# ---------------------------------------------------------

def get_panel_1_specs(
    s1: Dict[str, Any], s2: Dict[str, Any], s3: Dict[str, Any], s4: Dict[str, Any]
) -> List[Tuple[str, Dict[str, Any]]]:
    """Returns indicator specification mappings for Panel 1."""
    return [
        (
            "Taxa de participação na força de trabalho das pessoas de 14 anos ou mais de idade, na semana de referência (%)",
            s1,
        ),
        (
            "Nível da ocupação das pessoas de 14 anos ou mais de idade, na semana de referência (%)",
            s2,
        ),
        (
            "Nível da desocupação das pessoas de 14 anos ou mais de idade, na semana de referência (%)",
            s3,
        ),
        (
            "Taxa de desocupação das pessoas de 14 anos ou mais de idade, na semana de referência (%)",
            s4,
        ),
    ]

# ---------------------------------------------------------
# Panel 2: Population & Economic Sectors
# ---------------------------------------------------------

def get_panel_2_specs(
    s_pop: Dict[str, Any],
    m_6463: Dict[str, Dict[str, Any]],
    m_6464: Dict[str, Dict[str, Any]],
    m_6465: Dict[str, Dict[str, Any]],
) -> List[Tuple[str, Dict[str, Any]]]:
    """Returns indicator specification mappings for Panel 2."""
    return [
        ("População total (milhares)", s_pop),
        ("Pessoas de 14 anos ou mais de idade (milhares)", m_6463.get("32385", {})),
        (
            "Pessoas de 14 anos ou mais de idade, na força de trabalho, na semana de referência (milhares)",
            m_6463.get("32386", {}),
        ),
        (
            "Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência (milhares)",
            m_6463.get("32387", {}),
        ),
        (
            "Pessoas de 14 anos ou mais de idade, desocupadas na semana de referência (milhares)",
            m_6463.get("32446", {}),
        ),
        (
            "Pessoas de 14 anos ou mais de idade, fora da força de trabalho, na semana de referência (milhares)",
            m_6463.get("32447", {}),
        ),
        (
            "Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência como Empregado no setor privado com carteira de trabalho assinada (milhares)",
            m_6464.get("31722", {}),
        ),
        (
            "Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência como Empregado no setor privado sem carteira de trabalho assinada (milhares)",
            m_6464.get("31723", {}),
        ),
        (
            "Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência como Trabalhador doméstico (milhares)",
            m_6464.get("31724", {}),
        ),
        (
            "Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência como Empregado no setor público (inclusive servidor estatutário e militar) (milhares)",
            m_6464.get("31727", {}),
        ),
        (
            "Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência como Empregador (milhares)",
            m_6464.get("96170", {}),
        ),
        (
            "Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência como Conta-própria (milhares)",
            m_6464.get("96171", {}),
        ),
        (
            "Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência como Trabalhador familiar auxiliar (milhares)",
            m_6464.get("31731", {}),
        ),
        (
            "Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Agricultura, pecuária, produção florestal, pesca e aquicultura (milhares)",
            m_6465.get("47947", {}),
        ),
        (
            "Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Indústria geral (milhares)",
            m_6465.get("47948", {}),
        ),
        (
            "Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Indústria de transformação (milhares)",
            {},
        ),
        (
            "Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Construção (milhares)",
            m_6465.get("47949", {}),
        ),
        (
            "Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Comércio, reparação de veículos automotores e motocicletas (milhares)",
            m_6465.get("47950", {}),
        ),
        (
            "Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Transporte, armazenagem e correio (milhares)",
            m_6465.get("56622", {}),
        ),
        (
            "Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Alojamento e alimentação (milhares)",
            m_6465.get("56623", {}),
        ),
        (
            "Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Informação, comunicação e atividades financeiras, imobiliárias, profissionais e administrativas (milhares)",
            m_6465.get("56624", {}),
        ),
        (
            "Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Administração pública, defesa, seguridade social, educação, saúde humana e serviços sociais (milhares)",
            m_6465.get("60032", {}),
        ),
        (
            "Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Outros serviços (milhares)",
            m_6465.get("56627", {}),
        ),
        (
            "Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Serviços Domésticos (milhares)",
            m_6465.get("56628", {}),
        ),
        (
            "Pessoas de 14 anos ou mais de idade, ocupadas na semana de referência no grupamento de atividade Atividades mal definidas (milhares)",
            {},
        ),
    ]

# ---------------------------------------------------------
# Panel 3: Average Real Income
# ---------------------------------------------------------

def get_panel_3_specs(
    s_all_usual: Dict[str, Any],
    s_all_eff: Dict[str, Any],
    m_6471: Dict[str, Dict[str, Any]],
    s_main_eff: Dict[str, Any],
    m_6473: Dict[str, Dict[str, Any]],
) -> List[Tuple[str, Dict[str, Any]]]:
    """Returns indicator specification mappings for Panel 3."""
    return [
        (
            "Rendimento médio real de todos os trabalhos, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho (R$)",
            s_all_usual,
        ),
        (
            "Rendimento médio real de todos os trabalhos, efetivamente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho (R$)",
            s_all_eff,
        ),
        (
            "Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho (R$)",
            m_6471.get("96165", {}),
        ),
        (
            "Rendimento médio real do trabalho principal, efetivamente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho (R$)",
            s_main_eff,
        ),
        (
            "Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, como Empregado no setor privado com carteira de trabalho assinada (R$)",
            m_6471.get("31722", {}),
        ),
        (
            "Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, como Empregado no setor privado sem carteira de trabalho assinada (R$)",
            m_6471.get("31723", {}),
        ),
        (
            "Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, como Trabalhador doméstico (R$)",
            m_6471.get("31724", {}),
        ),
        (
            "Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, como Empregado no setor público (inclusive servidor estatutário e militar) (R$)",
            m_6471.get("31727", {}),
        ),
        (
            "Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, como Empregador (R$)",
            m_6471.get("96170", {}),
        ),
        (
            "Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, como Conta-própria (R$)",
            m_6471.get("96171", {}),
        ),
        (
            "Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, no grupamento de atividade Agricultura, pecuária, produção florestal, pesca e aquicultura (R$)",
            m_6473.get("47947", {}),
        ),
        (
            "Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, no grupamento de atividade Indústria geral (R$)",
            m_6473.get("47948", {}),
        ),
        (
            "Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, no grupamento de atividade Indústria de transformação (R$)",
            {},
        ),
        (
            "Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, no grupamento de atividade Construção (R$)",
            m_6473.get("47949", {}),
        ),
        (
            "Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, no grupamento de atividade Comércio, reparação de veículos automotores e motocicletas (R$)",
            m_6473.get("47950", {}),
        ),
        (
            "Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, no grupamento de atividade Transporte, armazenagem e correio (R$)",
            m_6473.get("56622", {}),
        ),
        (
            "Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho,no grupamento de atividade Alojamento e alimentação (R$)",
            m_6473.get("56623", {}),
        ),
        (
            "Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, no grupamento de atividade Informação, comunicação e atividades financeiras, imobiliárias, profissionais e administrativas (R$)",
            m_6473.get("56624", {}),
        ),
        (
            "Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, no grupamento de atividade Administração pública, defesa, seguridade social, educação, saúde humana e serviços sociais (R$)",
            m_6473.get("60032", {}),
        ),
        (
            "Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, no grupamento de atividade Outros serviços (R$)",
            m_6473.get("56627", {}),
        ),
        (
            "Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, no grupamento de atividade Serviços Domésticos (R$)",
            m_6473.get("56628", {}),
        ),
        (
            "Rendimento médio real do trabalho principal, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho, no grupamento de atividade Atividades mal definidas (R$)",
            {},
        ),
    ]

# ---------------------------------------------------------
# Panel 4: Mass Income
# ---------------------------------------------------------

def get_panel_4_specs(
    s_mass_usual: Dict[str, Any], s_mass_eff: Dict[str, Any]
) -> List[Tuple[str, Dict[str, Any]]]:
    """Returns indicator specification mappings for Panel 4."""
    return [
        (
            "Massa de rendimento real de todos os trabalhos, habitualmente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho (milhões de R$)",
            s_mass_usual,
        ),
        (
            "Massa de rendimento real de todos os trabalhos, efetivamente recebido por mês, pelas pessoas de 14 anos ou mais de idade, ocupadas na semana de referência, com rendimento de trabalho (milhões de R$)",
            s_mass_eff,
        ),
    ]
