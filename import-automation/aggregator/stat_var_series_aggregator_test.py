# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for ET-layer StatVar series aggregation (aggregator/)."""

import csv
from datetime import datetime, timezone
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
for _p in [
        _SCRIPT_DIR,
        _ROOT_DIR,
        os.path.join(_ROOT_DIR, "util"),
        os.path.join(_ROOT_DIR, "tools", "import_differ"),
        os.path.join(_ROOT_DIR, "tools", "statvar_importer"),
]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import stat_var_aggregator
import stat_var_series_aggregator
from tools.import_differ import bigquery_differ


def _load_aggregator_main():
    """Loads import-automation/aggregator/main.py as 'aggregator_main' without polluting sys.modules['main']."""
    mod_name = "aggregator_main"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(
        mod_name, os.path.join(_SCRIPT_DIR, "main.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


aggregator_main = _load_aggregator_main()

_SUMMARY_CSV_HEADER = [
    "StatVar",
    "NumPlaces",
    "NumObservations",
    "MinValue",
    "MaxValue",
    "NumDates",
    "MinDate",
    "MaxDate",
    "MeasurementMethods",
    "Units",
    "ScalingFactors",
    "ObservationPeriods",
]


class StatVarSeriesAggregatorTest(unittest.TestCase):
    """Behavior-focused unit tests for stat_var_series_aggregator.py and main.py."""

    def test_load_config_all_six_ipcc_imports_and_fallbacks(self):
        """Loads all 6 NASA IPCC imports from YAML, verifies CMIP5 vs CMIP6 base years and rounds, and handles missing configs."""
        # 1-round CMIP5 imports: discrete dates ["1990", "2006"] only.
        for import_name in ("NASA_NEXDCP30", "NASA_NEXGDDP_Country"):
            rounds = (stat_var_series_aggregator.
                      load_stat_var_series_aggregation_config(import_name))
            self.assertEqual(1, len(rounds), msg=import_name)
            self.assertEqual(1, rounds[0]["round"])
            funcs = rounds[0]["aggr_funcs"]
            self.assertEqual(
                [
                    "max_diff_across_measurement_methods",
                    "diff_relative_to_base_date",
                ],
                [f["type"] for f in funcs],
            )
            self.assertEqual([{
                "dates": ["1990", "2006"]
            }], funcs[1]["date_specs"])

        # 1-round IpccPlaces50 (CMIP5): baseline range 2015..2020 + discrete ["1990", "2006"].
        ipcc50_rounds = (
            stat_var_series_aggregator.load_stat_var_series_aggregation_config(
                "NASA_NEXGDDP_IpccPlaces50"))
        self.assertEqual(1, len(ipcc50_rounds))
        self.assertEqual(
            [
                {
                    "start_date": "2015",
                    "end_date": "2020"
                },
                {
                    "dates": ["1990", "2006"]
                },
            ],
            ipcc50_rounds[0]["aggr_funcs"][1]["date_specs"],
        )

        # 3-round CMIP5 Subnational: 2006..2020 + ["1990", "2006"], Round 3 has MAX & MIN only.
        cmip5_sub = (
            stat_var_series_aggregator.load_stat_var_series_aggregation_config(
                "NASA_NEXGDDP_Subnational"))
        self.assertEqual([1, 2, 3], [r["round"] for r in cmip5_sub])
        self.assertEqual(
            [
                {
                    "start_date": "2006",
                    "end_date": "2020"
                },
                {
                    "dates": ["1990", "2006"]
                },
            ],
            cmip5_sub[0]["aggr_funcs"][1]["date_specs"],
        )
        self.assertEqual(["stats_across_models"],
                         [f["type"] for f in cmip5_sub[1]["aggr_funcs"]])
        cmip5_r3_aot = [
            f for f in cmip5_sub[2]["aggr_funcs"]
            if f["type"] == "aggr_over_time"
        ]
        cmip5_r3_cnt = [
            f for f in cmip5_sub[2]["aggr_funcs"]
            if f["type"] == "count_threshold_exception_over_time"
        ]
        self.assertEqual(
            [("P10Y", "2030"), ("P30Y", "2050"), ("P80Y", "2100")],
            [(f["time_range"]["output_obs_period"],
              f["time_range"]["output_obs_date"]) for f in cmip5_r3_aot],
        )
        for aot_func in cmip5_r3_aot:
            self.assertEqual(
                ["MAX", "MIN"],
                [svc["aggregation_op"] for svc in aot_func["sv_configs"]],
            )
        self.assertEqual(3, len(cmip5_r3_cnt))
        for cnt_func in cmip5_r3_cnt:
            self.assertEqual(
                [(5.0, "GE", "Celsius", "maxTemperature"),
                 (-5.0, "LE", "Celsius", "minTemperature")],
                [(t["threshold_value"], t["comparison"], t["unit"],
                  t["output_cprop"]) for t in cnt_func["thresholds"]],
            )

        # 3-round CMIP6 imports: 2015..2020 + ["1990", "2015"] (not "2006"), Round 3 has MAX, MIN, and MEAN.
        for cmip6_import in (
                "NASA_NEXGDDP_CMIP6_Subnational",
                "NASA_NEXGDDP_CMIP6_IpccPlaces50",
        ):
            cmip6_rounds = (
                stat_var_series_aggregator.
                load_stat_var_series_aggregation_config(cmip6_import))
            self.assertEqual([1, 2, 3], [r["round"] for r in cmip6_rounds],
                             msg=cmip6_import)
            self.assertEqual(
                [
                    {
                        "start_date": "2015",
                        "end_date": "2020"
                    },
                    {
                        "dates": ["1990", "2015"]
                    },
                ],
                cmip6_rounds[0]["aggr_funcs"][1]["date_specs"],
                msg=cmip6_import,
            )
            self.assertEqual(["stats_across_models"],
                             [f["type"] for f in cmip6_rounds[1]["aggr_funcs"]])
            cmip6_r3_aot = [
                f for f in cmip6_rounds[2]["aggr_funcs"]
                if f["type"] == "aggr_over_time"
            ]
            self.assertEqual(3, len(cmip6_r3_aot))
            for aot_func in cmip6_r3_aot:
                self.assertEqual(
                    ["MAX", "MIN", "MEAN"],
                    [svc["aggregation_op"] for svc in aot_func["sv_configs"]],
                    msg=cmip6_import,
                )

        # Unconfigured import, empty name, and nonexistent config file return [].
        self.assertEqual(
            [],
            stat_var_series_aggregator.load_stat_var_series_aggregation_config(
                "UnconfiguredImport"),
        )
        self.assertEqual(
            [],
            stat_var_series_aggregator.load_stat_var_series_aggregation_config(
                ""),
        )
        self.assertEqual(
            [],
            stat_var_series_aggregator.load_stat_var_series_aggregation_config(
                "NASA_NEXDCP30",
                config_path="/nonexistent/statvar_series_aggregation.yaml",
            ),
        )

    def test_load_config_import_spec_overrides_and_normalization(self):
        """Supports list and mapping import_spec overrides and normalizes operators and discrete dates."""
        raw_round = {
            "round":
                1,
            "aggr_funcs": [
                {
                    "type": "diff_relative_to_base_date",
                    "date_specs": [{
                        "dates": ["2015", "1990", "1990"]
                    }],
                },
                {
                    "type":
                        "aggr_over_time",
                    "time_range": {
                        "input_obs_period": "P1M",
                        "output_obs_period": "P10Y",
                        "output_obs_date": "2030",
                    },
                    "sv_configs": [{
                        "sv_regex": "^Temp_.*",
                        "aggregation_op": "operator_mean",
                    }],
                },
                {
                    "type":
                        "count_threshold_exception_over_time",
                    "time_range": {
                        "input_obs_period": "P1D",
                        "output_obs_period": "P10Y",
                        "output_obs_date": "2030",
                    },
                    "thresholds": [{
                        "sv_regex": "^Temp_.*",
                        "threshold_value": 35,
                        "unit": "Celsius",
                        "comparison": "OPERATOR_GE",
                    }],
                },
            ],
        }

        for spec_payload in (
            [raw_round],
            {
                "rounds": [raw_round]
            },
            {
                "stat_var_series_aggregation": [raw_round]
            },
        ):
            loaded = (stat_var_series_aggregator.
                      load_stat_var_series_aggregation_config(
                          "UnconfiguredImport",
                          import_spec={
                              "stat_var_series_aggregation": spec_payload
                          },
                      ))
            self.assertEqual(1, len(loaded))
            funcs = loaded[0]["aggr_funcs"]
            self.assertEqual(["1990", "2015"],
                             funcs[0]["date_specs"][0]["dates"])
            self.assertEqual("MEAN",
                             funcs[1]["sv_configs"][0]["aggregation_op"])
            self.assertFalse(funcs[1]["use_input_sv_for_output"])
            self.assertEqual("GE", funcs[2]["thresholds"][0]["comparison"])
            self.assertEqual(35.0, funcs[2]["thresholds"][0]["threshold_value"])

        # Explicit empty override disables YAML lookup even for a configured import.
        self.assertEqual(
            [],
            stat_var_series_aggregator.load_stat_var_series_aggregation_config(
                "NASA_NEXDCP30",
                import_spec={"stat_var_series_aggregation": []},
            ),
        )

    def test_invalid_configs_and_unsafe_table_names_raise_value_error(self):
        """Rejects malformed rounds, operators, ISO periods, dates, regexes, thresholds, and unsafe table IDs."""
        valid_round_1 = {
            "round": 1,
            "aggr_funcs": [{
                "type": "max_diff_across_measurement_methods"
            }],
        }

        invalid_round_configs = [
            # Non-sequential or non-integer round numbers
            [{
                "round": 2,
                "aggr_funcs": [{
                    "type": "stats_across_models"
                }]
            }],
            [
                valid_round_1,
                {
                    "round": 3,
                    "aggr_funcs": [{
                        "type": "stats_across_models"
                    }]
                },
            ],
            [{
                "round": 0,
                "aggr_funcs": [{
                    "type": "stats_across_models"
                }]
            }],
            [{
                "round": True,
                "aggr_funcs": [{
                    "type": "stats_across_models"
                }]
            }],
            # Empty aggr_funcs
            [{
                "round": 1,
                "aggr_funcs": []
            }],
            # Unknown aggregation function type
            [{
                "round": 1,
                "aggr_funcs": [{
                    "type": "unknown_series_func"
                }]
            }],
            # Invalid aggregation_op
            [{
                "round":
                    1,
                "aggr_funcs": [{
                    "type":
                        "aggr_over_time",
                    "time_range": {
                        "input_obs_period": "P1M",
                        "output_obs_period": "P10Y",
                        "output_obs_date": "2030",
                    },
                    "sv_configs": [{
                        "sv_regex": "^Temp.*",
                        "aggregation_op": "MEDIAN",
                    }],
                }],
            }],
            # Invalid comparison operator
            [{
                "round":
                    1,
                "aggr_funcs": [{
                    "type":
                        "count_threshold_exception_over_time",
                    "time_range": {
                        "input_obs_period": "P1M",
                        "output_obs_period": "P10Y",
                        "output_obs_date": "2030",
                    },
                    "thresholds": [{
                        "sv_regex": "^Temp.*",
                        "threshold_value": 5.0,
                        "unit": "Celsius",
                        "comparison": "GT",
                    }],
                }],
            }],
            # Unsupported ISO period P7D on aggr_over_time input and output
            [{
                "round":
                    1,
                "aggr_funcs": [{
                    "type":
                        "aggr_over_time",
                    "time_range": {
                        "input_obs_period": "P7D",
                        "output_obs_period": "P10Y",
                        "output_obs_date": "2030",
                    },
                    "sv_configs": [{
                        "sv_regex": "^Temp.*",
                        "aggregation_op": "MAX",
                    }],
                }],
            }],
            [{
                "round":
                    1,
                "aggr_funcs": [{
                    "type":
                        "aggr_over_time",
                    "time_range": {
                        "input_obs_period": "P1M",
                        "output_obs_period": "P7D",
                        "output_obs_date": "2030",
                    },
                    "sv_configs": [{
                        "sv_regex": "^Temp.*",
                        "aggregation_op": "MAX",
                    }],
                }],
            }],
            # Unsupported ISO period P1Y on count_threshold_exception_over_time input
            [{
                "round":
                    1,
                "aggr_funcs": [{
                    "type":
                        "count_threshold_exception_over_time",
                    "time_range": {
                        "input_obs_period": "P1Y",
                        "output_obs_period": "P10Y",
                        "output_obs_date": "2030",
                    },
                    "thresholds": [{
                        "sv_regex": "^Temp.*",
                        "threshold_value": 5.0,
                        "unit": "Celsius",
                        "comparison": "GE",
                    }],
                }],
            }],
            # Malformed dates and start_date > end_date
            [{
                "round":
                    1,
                "aggr_funcs": [{
                    "type": "diff_relative_to_base_date",
                    "date_specs": [{
                        "dates": ["2020-13"]
                    }],
                }],
            }],
            [{
                "round":
                    1,
                "aggr_funcs": [{
                    "type": "diff_relative_to_base_date",
                    "date_specs": [{
                        "dates": ["2020-01-15"]
                    }],
                }],
            }],
            [{
                "round":
                    1,
                "aggr_funcs": [{
                    "type": "diff_relative_to_base_date",
                    "date_specs": [{
                        "start_date": "2025",
                        "end_date": "2020",
                    }],
                }],
            }],
            [{
                "round":
                    1,
                "aggr_funcs": [{
                    "type": "diff_relative_to_base_date",
                    "date_specs": [{
                        "start_date": "2015"
                    }],
                }],
            }],
            # Non-finite threshold_value
            [{
                "round":
                    1,
                "aggr_funcs": [{
                    "type":
                        "count_threshold_exception_over_time",
                    "time_range": {
                        "input_obs_period": "P1M",
                        "output_obs_period": "P10Y",
                        "output_obs_date": "2030",
                    },
                    "thresholds": [{
                        "sv_regex": "^Temp.*",
                        "threshold_value": float("nan"),
                        "unit": "Celsius",
                        "comparison": "GE",
                    }],
                }],
            }],
            # Invalid regex, backreference regex, or quote in sv_regex / unit
            [{
                "round":
                    1,
                "aggr_funcs": [{
                    "type":
                        "aggr_over_time",
                    "time_range": {
                        "input_obs_period": "P1M",
                        "output_obs_period": "P10Y",
                        "output_obs_date": "2030",
                    },
                    "sv_configs": [{
                        "sv_regex": "[unclosed_group",
                        "aggregation_op": "MAX",
                    }],
                }],
            }],
            [{
                "round":
                    1,
                "aggr_funcs": [{
                    "type":
                        "aggr_over_time",
                    "time_range": {
                        "input_obs_period": "P1M",
                        "output_obs_period": "P10Y",
                        "output_obs_date": "2030",
                    },
                    "sv_configs": [{
                        "sv_regex": r"(Temp)\1",
                        "aggregation_op": "MAX",
                    }],
                }],
            }],
            [{
                "round":
                    1,
                "aggr_funcs": [{
                    "type":
                        "aggr_over_time",
                    "time_range": {
                        "input_obs_period": "P1M",
                        "output_obs_period": "P10Y",
                        "output_obs_date": "2030",
                    },
                    "sv_configs": [{
                        "sv_regex": "Temp'Quote",
                        "aggregation_op": "MAX",
                    }],
                }],
            }],
            [{
                "round":
                    1,
                "aggr_funcs": [{
                    "type":
                        "aggr_over_time",
                    "time_range": {
                        "input_obs_period": "P1M",
                        "output_obs_period": "P10Y",
                        "output_obs_date": "2030",
                    },
                    "sv_configs": [{
                        "sv_regex": "^Temp.*",
                        "aggregation_op": "MAX",
                        "unit": "Celsius--bad",
                    }],
                }],
            }],
        ]

        for idx, bad_rounds in enumerate(invalid_round_configs):
            with self.subTest(case_index=idx):
                with self.assertRaises(ValueError):
                    stat_var_series_aggregator.validate_stat_var_series_config(
                        bad_rounds)

        # Unsafe BigQuery table identifiers and empty rounds raise ValueError.
        for bad_raw, bad_agg in [
            ("", "proj.ds.agg_obs"),
            ("proj.ds.raw obs", "proj.ds.agg_obs"),
            ("proj.ds.raw_obs", "proj.ds.agg`obs"),
            ("proj.ds.raw_obs", "proj.ds.agg--obs"),
            ("proj.ds.raw;obs", "proj.ds.agg_obs"),
        ]:
            with self.subTest(raw_table=bad_raw, agg_table=bad_agg):
                with self.assertRaises(ValueError):
                    stat_var_series_aggregator.build_bigquery_series_agg_obs_sql(
                        raw_obs_table=bad_raw,
                        agg_obs_table=bad_agg,
                        rounds=[valid_round_1],
                    )

        with self.assertRaises(ValueError):
            stat_var_series_aggregator.build_bigquery_series_agg_obs_sql(
                raw_obs_table="proj.ds.raw_obs",
                agg_obs_table="proj.ds.agg_obs",
                rounds=[],
            )

    def test_format_numeric_value_preserves_scientific_values_and_rejects_non_finite(
            self):
        """Preserves 15-sig-fig scientific climate values, clean integers, and standard decimals."""
        self.assertEqual(
            "1.25e-06",
            stat_var_series_aggregator.format_numeric_value(1.25e-6))
        self.assertEqual("1e-08",
                         stat_var_series_aggregator.format_numeric_value(1e-8))
        self.assertEqual(
            "-3.5e-07",
            stat_var_series_aggregator.format_numeric_value(-3.5e-7),
        )
        self.assertEqual(
            "1.25e-06",
            stat_var_series_aggregator.format_numeric_value("1.25e-06"),
        )
        self.assertEqual("150",
                         stat_var_series_aggregator.format_numeric_value(150.0))
        self.assertEqual(
            "12.5", stat_var_series_aggregator.format_numeric_value(12.500))
        self.assertEqual("0",
                         stat_var_series_aggregator.format_numeric_value(0.0))
        self.assertEqual("0",
                         stat_var_series_aggregator.format_numeric_value(-0.0))
        self.assertEqual(
            "", stat_var_series_aggregator.format_numeric_value(float("nan")))
        self.assertEqual(
            "", stat_var_series_aggregator.format_numeric_value(float("inf")))
        self.assertEqual(
            "", stat_var_series_aggregator.format_numeric_value(float("-inf")))
        self.assertEqual("",
                         stat_var_series_aggregator.format_numeric_value(None))
        self.assertEqual("",
                         stat_var_series_aggregator.format_numeric_value(""))
        self.assertEqual("",
                         stat_var_series_aggregator.format_numeric_value(True))

    def test_mcf_roundtrip_and_summary_report_with_scientific_and_unitless_rows(
            self):
        """Writes and parses series MCF nodes (scientific + unitless threshold counts) and updates summary_report.csv idempotently."""
        dcid_a = stat_var_series_aggregator.compute_observation_dcid(
            variable_measured="DifferenceAcrossModels_PrecipitationRate",
            observation_about="country/USA",
            observation_date="2030-06",
            value_str="1.25e-06",
            observation_period="P1M",
            measurement_method="dcAggregate/MaxDiffAcrossMeasurementMethods",
            unit="KilogramPerSquareMeterPerSecond",
        )
        dcid_b = stat_var_series_aggregator.compute_observation_dcid(
            variable_measured="DifferenceAcrossModels_PrecipitationRate",
            observation_about="country/USA",
            observation_date="2030-06",
            value_str="1.26e-06",
            observation_period="P1M",
            measurement_method="dcAggregate/MaxDiffAcrossMeasurementMethods",
            unit="KilogramPerSquareMeterPerSecond",
        )
        self.assertTrue(dcid_a.startswith("dc/o/"))
        self.assertEqual(len("dc/o/") + 13, len(dcid_a))
        self.assertNotEqual(dcid_a, dcid_b)

        with tempfile.TemporaryDirectory() as tmp_dir:
            series_mcf = os.path.join(
                tmp_dir,
                stat_var_series_aggregator.STAT_VAR_SERIES_AGG_MCF_FILENAME,
            )
            summary_csv = os.path.join(tmp_dir, "summary_report.csv")
            with open(summary_csv, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(_SUMMARY_CSV_HEADER)
                writer.writerow([
                    "dcs:Max_Temperature",
                    "1",
                    "1",
                    "25.0",
                    "25.0",
                    "1",
                    "2020-01",
                    "2020-01",
                    "[dcs:NASA_CCSM4]",
                    "[dcs:Celsius]",
                    "[]",
                    "[P1M]",
                ])

            records = [
                {
                    "variableMeasured":
                        "DifferenceAcrossModels_PrecipitationRate",
                    "observationAbout":
                        "country/USA",
                    "observationDate":
                        "2030-06",
                    "value":
                        1.25e-6,
                    "observationPeriod":
                        "P1M",
                    "measurementMethod":
                        "dcAggregate/MaxDiffAcrossMeasurementMethods",
                    "unit":
                        "KilogramPerSquareMeterPerSecond",
                },
                {
                    "variableMeasured":
                        "NumberOfMonths_5CelsiusOrMore_MedianAcrossModels_DifferenceRelativeToBaseDate2015_Max_Temperature",
                    "observationAbout":
                        "geoId/06",
                    "observationDate":
                        "2030",
                    "value":
                        14.0,
                    "observationPeriod":
                        "P10Y",
                    "measurementMethod":
                        "dcAggregate/MedianAcrossModels",
                    "unit":
                        "",
                },
            ]
            stat_var_series_aggregator.write_mcf_observations(
                records, series_mcf)

            with open(series_mcf, "r", encoding="utf-8") as f:
                mcf_text = f.read()
            self.assertNotIn("typeOf: dcs:StatisticalVariable", mcf_text)
            self.assertIn("value: 1.25e-06", mcf_text)

            parsed = stat_var_series_aggregator.parse_mcf_observations(
                [series_mcf])
            self.assertEqual(2, len(parsed))
            self.assertAlmostEqual(1.25e-6, parsed[0]["value"], places=18)
            self.assertEqual("1.25e-06", parsed[0]["valueStr"])
            self.assertEqual(dcid_a, parsed[0]["dcid"])
            self.assertEqual(14.0, parsed[1]["value"])
            self.assertEqual("14", parsed[1]["valueStr"])
            self.assertEqual("", parsed[1]["unit"])

            stat_var_series_aggregator.update_summary_report_csv(
                summary_csv, parsed)
            with open(summary_csv, "r", encoding="utf-8") as f:
                rows_pass1 = {r["StatVar"]: r for r in csv.DictReader(f)}

            self.assertEqual(3, len(rows_pass1))
            precip_row = rows_pass1[
                "dcs:DifferenceAcrossModels_PrecipitationRate"]
            self.assertAlmostEqual(1.25e-6,
                                   float(precip_row["MinValue"]),
                                   places=18)
            self.assertAlmostEqual(1.25e-6,
                                   float(precip_row["MaxValue"]),
                                   places=18)
            self.assertEqual("[dcs:KilogramPerSquareMeterPerSecond]",
                             precip_row["Units"])

            cnt_sv_key = (
                "dcs:NumberOfMonths_5CelsiusOrMore_MedianAcrossModels_"
                "DifferenceRelativeToBaseDate2015_Max_Temperature")
            self.assertEqual("[]", rows_pass1[cnt_sv_key]["Units"])
            self.assertEqual("14.0", rows_pass1[cnt_sv_key]["MinValue"])

            # Re-running update_summary_report_csv overwrites existing series SVs in place without duplicates.
            stat_var_series_aggregator.update_summary_report_csv(
                summary_csv,
                [{
                    "variableMeasured":
                        "NumberOfMonths_5CelsiusOrMore_MedianAcrossModels_DifferenceRelativeToBaseDate2015_Max_Temperature",
                    "observationAbout":
                        "geoId/06",
                    "observationDate":
                        "2050",
                    "value":
                        42.0,
                    "observationPeriod":
                        "P30Y",
                    "measurementMethod":
                        "dcAggregate/MedianAcrossModels",
                    "unit":
                        "",
                }],
            )
            with open(summary_csv, "r", encoding="utf-8") as f:
                rerun_list = list(csv.DictReader(f))
            self.assertEqual(3, len(rerun_list))
            rerun_by_sv = {r["StatVar"]: r for r in rerun_list}
            self.assertEqual("42.0", rerun_by_sv[cnt_sv_key]["MinValue"])
            self.assertEqual("2050", rerun_by_sv[cnt_sv_key]["MinDate"])
            self.assertEqual("25.0",
                             rerun_by_sv["dcs:Max_Temperature"]["MinValue"])

    @mock.patch(
        "stat_var_series_aggregator.bigquery_differ.load_mcf_to_bq_tables")
    @mock.patch("stat_var_series_aggregator.bigquery_differ.ensure_bq_dataset")
    def test_run_bigquery_series_aggregation_streams_pages_and_sets_ttl(
            self, mock_ensure_ds, mock_load_mcf):
        """Streams paginated BigQuery series outputs to stat_var_series_agg_nodes.mcf and summary_report.csv."""
        mock_load_mcf.return_value = (24, 3)
        mock_bq_client = mock.MagicMock()

        create_job = mock.MagicMock()
        create_job.result.return_value = []

        page1 = [
            (
                "dcid:DifferenceAcrossModels_PrecipitationRate",
                "1.25e-06",
                "country/USA",
                "2030-06",
                "P1M",
                "dcAggregate/MaxDiffAcrossMeasurementMethods",
                "KilogramPerSquareMeterPerSecond",
                "",
            ),
            (
                "dcid:DifferenceRelativeToBaseDate2015_Max_Temperature",
                "-1.75",
                "country/USA",
                "2030-06",
                "P1M",
                "dcAggregate/NASA_MRI-ESM2-0",
                "Celsius",
                "",
            ),
        ]
        page2 = [
            (
                "dcid:NumberOfMonths_5CelsiusOrMore_MedianAcrossModels_DifferenceRelativeToBaseDate2015_Max_Temperature",
                "18",
                "country/USA",
                "2030",
                "P10Y",
                "dcAggregate/MedianAcrossModels",
                "",
                "",
            ),
        ]
        select_result = mock.MagicMock()
        select_result.pages = [page1, page2]
        select_job = mock.MagicMock()
        select_job.result.return_value = select_result

        mock_bq_client.query.side_effect = [create_job, select_job]

        rounds = (
            stat_var_series_aggregator.load_stat_var_series_aggregation_config(
                "NASA_NEXGDDP_CMIP6_Subnational"))

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_mcf = os.path.join(
                tmp_dir,
                stat_var_series_aggregator.STAT_VAR_SERIES_AGG_MCF_FILENAME,
            )
            summary_csv = os.path.join(tmp_dir, "summary_report.csv")
            with open(summary_csv, "w", encoding="utf-8", newline="") as f:
                csv.writer(f).writerow(_SUMMARY_CSV_HEADER)

            res = stat_var_series_aggregator.run_bigquery_series_aggregation(
                mcf_pattern="gs://bucket/ipcc/2026_10_28/input0/genmcf/*.mcf",
                rounds=rounds,
                output_mcf_path=out_mcf,
                project_id="test-proj",
                dataset_id="test_ds",
                import_name="NASA_NEXGDDP_CMIP6_Subnational",
                version="2026_10_28",
                input_prefix="input0",
                summary_report_path=summary_csv,
                expiration_hours=12,
                bq_client=mock_bq_client,
                page_size=5000,
            )

            self.assertEqual(24, res["raw_obs_count"])
            self.assertEqual(3, res["raw_schema_count"])
            self.assertEqual(3, res["agg_obs_count"])
            self.assertEqual(out_mcf, res["output_mcf_path"])

            expected_tables = bigquery_differ.get_import_bq_table_ids(
                "test-proj.test_ds",
                "NASA_NEXGDDP_CMIP6_Subnational",
                "2026_10_28",
                "input0",
            )
            self.assertEqual(expected_tables, res["table_ids"])

            mock_ensure_ds.assert_called_once_with(mock_bq_client,
                                                   "test-proj.test_ds",
                                                   expiration_hours=12)
            _, load_kwargs = mock_load_mcf.call_args
            self.assertEqual(
                {
                    "stat_var_agg_nodes.mcf",
                    "stat_var_series_agg_nodes.mcf",
                },
                load_kwargs["exclude_filenames"],
            )
            select_job.result.assert_called_once_with(page_size=5000)
            mock_bq_client.update_table.assert_called_once()
            updated_table_obj, updated_fields = (
                mock_bq_client.update_table.call_args[0])
            self.assertEqual(["expires"], updated_fields)
            self.assertGreater(updated_table_obj.expires,
                               datetime.now(timezone.utc))

            parsed = stat_var_series_aggregator.parse_mcf_observations(
                [out_mcf])
            self.assertEqual(3, len(parsed))
            by_sv = {r["variableMeasured"]: r for r in parsed}
            self.assertAlmostEqual(
                1.25e-6,
                by_sv["DifferenceAcrossModels_PrecipitationRate"]["value"],
                places=18,
            )
            self.assertEqual(
                -1.75,
                by_sv["DifferenceRelativeToBaseDate2015_Max_Temperature"]
                ["value"],
            )
            cnt_sv = ("NumberOfMonths_5CelsiusOrMore_MedianAcrossModels_"
                      "DifferenceRelativeToBaseDate2015_Max_Temperature")
            self.assertEqual(18.0, by_sv[cnt_sv]["value"])
            self.assertEqual("", by_sv[cnt_sv]["unit"])

            with open(summary_csv, "r", encoding="utf-8") as f:
                summary_rows = {r["StatVar"]: r for r in csv.DictReader(f)}
            self.assertEqual(3, len(summary_rows))
            self.assertEqual("[]", summary_rows[f"dcs:{cnt_sv}"]["Units"])

    @mock.patch(
        "stat_var_series_aggregator.bigquery_differ._get_existing_bq_table")
    @mock.patch(
        "stat_var_series_aggregator.bigquery_differ.load_mcf_to_bq_tables")
    @mock.patch("stat_var_series_aggregator.bigquery_differ.ensure_bq_dataset")
    def test_run_bigquery_series_aggregation_append_and_reuse_raw_obs_flow(
            self, mock_ensure_ds, mock_load_mcf, mock_get_existing_table):
        """Reuses existing raw_obs without reloading MCFs, appends series results, and deletes temp series table."""
        raw_obs_tbl = mock.MagicMock()
        raw_obs_tbl.num_rows = 30
        raw_schema_tbl = mock.MagicMock()
        raw_schema_tbl.num_rows = 4
        mock_get_existing_table.side_effect = [raw_obs_tbl, raw_schema_tbl]

        mock_bq_client = mock.MagicMock()
        create_series_job = mock.MagicMock()
        create_series_job.result.return_value = []
        append_job = mock.MagicMock()
        append_job.result.return_value = []
        select_result = mock.MagicMock()
        select_result.pages = [[(
            "dcid:AggregateMax_MedianAcrossModels_DifferenceRelativeToBaseDate2015_Max_Temperature",
            "4.25",
            "geoId/06",
            "2030",
            "P10Y",
            "dcAggregate/MedianAcrossModels",
            "Celsius",
            "",
        )]]
        select_series_job = mock.MagicMock()
        select_series_job.result.return_value = select_result
        mock_bq_client.query.side_effect = [
            create_series_job,
            append_job,
            select_series_job,
        ]

        rounds = (stat_var_series_aggregator.
                  load_stat_var_series_aggregation_config("NASA_NEXDCP30"))

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_mcf = os.path.join(
                tmp_dir,
                stat_var_series_aggregator.STAT_VAR_SERIES_AGG_MCF_FILENAME,
            )
            res = stat_var_series_aggregator.run_bigquery_series_aggregation(
                mcf_pattern=
                "gs://bucket/combined/2026_10_28/input0/genmcf/*.mcf",
                rounds=rounds,
                output_mcf_path=out_mcf,
                project_id="test-proj",
                dataset_id="test_ds",
                import_name="CombinedImport",
                version="2026_10_28",
                input_prefix="input0",
                bq_client=mock_bq_client,
                reuse_existing_raw_obs=True,
                append_to_agg_obs=True,
            )

            mock_load_mcf.assert_not_called()
            self.assertEqual(30, res["raw_obs_count"])
            self.assertEqual(4, res["raw_schema_count"])
            self.assertEqual(1, res["agg_obs_count"])
            self.assertEqual(out_mcf, res["output_mcf_path"])

            expected_tables = bigquery_differ.get_import_bq_table_ids(
                "test-proj.test_ds",
                "CombinedImport",
                "2026_10_28",
                "input0",
            )
            expected_temp_series_table = f"{expected_tables['agg_obs']}_series"
            mock_bq_client.update_table.assert_called_once()
            mock_bq_client.delete_table.assert_called_once_with(
                expected_temp_series_table, not_found_ok=True)

            parsed = stat_var_series_aggregator.parse_mcf_observations(
                [out_mcf])
            self.assertEqual(1, len(parsed))
            self.assertEqual(4.25, parsed[0]["value"])

            # Verify temp series table is still cleaned up if an error occurs mid-flight.
            mock_bq_client.delete_table.reset_mock()
            mock_get_existing_table.side_effect = [raw_obs_tbl, raw_schema_tbl]
            failing_append_job = mock.MagicMock()
            failing_append_job.result.side_effect = RuntimeError("BQ failure")
            mock_bq_client.query.side_effect = [
                create_series_job,
                failing_append_job,
            ]
            with self.assertRaisesRegex(RuntimeError, "BQ failure"):
                stat_var_series_aggregator.run_bigquery_series_aggregation(
                    mcf_pattern=
                    "gs://bucket/combined/2026_10_28/input0/genmcf/*.mcf",
                    rounds=rounds,
                    output_mcf_path=out_mcf,
                    project_id="test-proj",
                    dataset_id="test_ds",
                    import_name="CombinedImport",
                    version="2026_10_28",
                    input_prefix="input0",
                    bq_client=mock_bq_client,
                    reuse_existing_raw_obs=True,
                    append_to_agg_obs=True,
                )
            mock_bq_client.delete_table.assert_called_once_with(
                expected_temp_series_table, not_found_ok=True)

    @mock.patch(
        "stat_var_series_aggregator.bigquery_differ._get_existing_bq_table")
    @mock.patch(
        "stat_var_series_aggregator.bigquery_differ.load_mcf_to_bq_tables")
    @mock.patch("stat_var_series_aggregator.bigquery_differ.ensure_bq_dataset")
    def test_run_bigquery_series_aggregation_and_genmcf_wrapper_noops_and_local_run(
            self, mock_ensure_ds, mock_load_mcf, mock_get_existing_table):
        """Skips queries when rounds are empty or raw_obs_count is 0, and supports genmcf directory helper."""
        mock_bq_client = mock.MagicMock()
        rounds = (stat_var_series_aggregator.
                  load_stat_var_series_aggregation_config("NASA_NEXDCP30"))

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_mcf = os.path.join(
                tmp_dir,
                stat_var_series_aggregator.STAT_VAR_SERIES_AGG_MCF_FILENAME,
            )

            # 1) Empty rounds -> immediate no-op.
            empty_res = (
                stat_var_series_aggregator.run_bigquery_series_aggregation(
                    mcf_pattern="gs://bucket/in/*.mcf",
                    rounds=[],
                    output_mcf_path=out_mcf,
                    project_id="test-proj",
                    bq_client=mock_bq_client,
                ))
            self.assertEqual(0, empty_res["agg_obs_count"])
            self.assertIsNone(empty_res["output_mcf_path"])
            self.assertFalse(os.path.exists(out_mcf))
            mock_load_mcf.assert_not_called()
            mock_bq_client.query.assert_not_called()

            # 2) Zero raw observations loaded -> skips BigQuery aggregation queries.
            mock_load_mcf.return_value = (0, 2)
            zero_res = (
                stat_var_series_aggregator.run_bigquery_series_aggregation(
                    mcf_pattern="gs://bucket/in/*.mcf",
                    rounds=rounds,
                    output_mcf_path=out_mcf,
                    project_id="test-proj",
                    bq_client=mock_bq_client,
                ))
            self.assertEqual(0, zero_res["raw_obs_count"])
            self.assertEqual(2, zero_res["raw_schema_count"])
            self.assertEqual(0, zero_res["agg_obs_count"])
            self.assertIsNone(zero_res["output_mcf_path"])
            self.assertFalse(os.path.exists(out_mcf))
            mock_bq_client.query.assert_not_called()

            # 3) reuse_existing_raw_obs=True when raw_obs table is missing -> clean no-op.
            mock_get_existing_table.side_effect = [None, None]
            missing_raw_res = (
                stat_var_series_aggregator.run_bigquery_series_aggregation(
                    mcf_pattern="gs://bucket/in/*.mcf",
                    rounds=rounds,
                    output_mcf_path=out_mcf,
                    project_id="test-proj",
                    bq_client=mock_bq_client,
                    reuse_existing_raw_obs=True,
                ))
            self.assertEqual(0, missing_raw_res["agg_obs_count"])
            self.assertIsNone(missing_raw_res["output_mcf_path"])
            mock_bq_client.query.assert_not_called()

            # 4) run_stat_var_series_aggregation_for_genmcf: unconfigured, nonexistent dir, and valid local dir.
            self.assertIsNone(
                stat_var_series_aggregator.
                run_stat_var_series_aggregation_for_genmcf(
                    import_name="UnconfiguredImport",
                    genmcf_output_path=tmp_dir,
                    bigquery_project_id="test-proj",
                    bq_client=mock_bq_client,
                ))
            self.assertIsNone(
                stat_var_series_aggregator.
                run_stat_var_series_aggregation_for_genmcf(
                    import_name="NASA_NEXDCP30",
                    genmcf_output_path=os.path.join(tmp_dir, "missing_genmcf"),
                    bigquery_project_id="test-proj",
                    bq_client=mock_bq_client,
                ))

            mock_load_mcf.return_value = (10, 1)
            create_job = mock.MagicMock()
            create_job.result.return_value = []
            select_result = mock.MagicMock()
            select_result.pages = [[(
                "dcid:DifferenceRelativeToBaseDate1990_Max_Temperature",
                "1.5",
                "geoId/06",
                "2030-07",
                "P1M",
                "dcAggregate/NASA_CCSM4",
                "Celsius",
                "",
            )]]
            select_job = mock.MagicMock()
            select_job.result.return_value = select_result
            mock_bq_client.query.side_effect = [create_job, select_job]

            genmcf_out = (stat_var_series_aggregator.
                          run_stat_var_series_aggregation_for_genmcf(
                              import_name="NASA_NEXDCP30",
                              genmcf_output_path=tmp_dir,
                              bigquery_project_id="test-proj",
                              bq_client=mock_bq_client,
                          ))
            self.assertEqual(out_mcf, genmcf_out)
            self.assertTrue(os.path.exists(out_mcf))

    def test_main_cli_flags_and_entrypoint_forwarding(self):
        """Registers --statvar_config_path and --statvar_series_config_path flags and forwards them from main()."""
        aggregator_main._define_cli_flags()
        self.assertIn("statvar_config_path", aggregator_main.FLAGS)
        self.assertIn("statvar_series_config_path", aggregator_main.FLAGS)
        self.assertNotIn("config_path", aggregator_main.FLAGS)

        aggregator_main.FLAGS.mark_as_parsed()
        aggregator_main.FLAGS.import_name = ""
        with self.assertRaisesRegex(ValueError, "--import_name is required"):
            aggregator_main.main([])

        with mock.patch.object(aggregator_main,
                               "run_aggregation_job",
                               return_value=0) as mock_run_job:
            aggregator_main.FLAGS.import_name = (
                "scripts/ipcc:NASA_NEXGDDP_Country")
            aggregator_main.FLAGS.statvar_config_path = "/tmp/custom_sv.yaml"
            aggregator_main.FLAGS.statvar_series_config_path = (
                "/tmp/custom_series.yaml")
            try:
                with self.assertRaises(SystemExit) as cm:
                    aggregator_main.main([])
                self.assertEqual(0, cm.exception.code)
                _, kwargs = mock_run_job.call_args
                self.assertEqual("/tmp/custom_sv.yaml",
                                 kwargs["statvar_config_path"])
                self.assertEqual("/tmp/custom_series.yaml",
                                 kwargs["statvar_series_config_path"])
            finally:
                aggregator_main.FLAGS.import_name = ""
                aggregator_main.FLAGS.statvar_config_path = ""
                aggregator_main.FLAGS.statvar_series_config_path = ""

    @mock.patch(
        "aggregator_main.stat_var_series_aggregator.run_bigquery_series_aggregation"
    )
    @mock.patch("aggregator_main.stat_var_aggregator.run_bigquery_aggregation")
    @mock.patch("aggregator_main.storage.Client")
    def test_main_run_aggregation_job_series_only_import(
            self, mock_storage_cls, mock_run_sv_agg, mock_run_series_agg):
        """Runs series-only IPCC import, uploads stat_var_series_agg_nodes.mcf, and updates summary_report.csv & import_summary.json."""
        mock_gcs = mock_storage_cls.return_value
        mock_bucket = mock.MagicMock()
        mock_gcs.bucket.return_value = mock_bucket

        base_path = "scripts/ipcc/NASA_NEXGDDP_Country"
        blob_store = {
            f"{base_path}/staging_version.txt":
                "2026_10_28",
            f"{base_path}/2026_10_28/import_summary.json":
                json.dumps({
                    "import_name": "NASA_NEXGDDP_Country",
                    "status": "PENDING",
                }),
            f"{base_path}/2026_10_28/input0/genmcf/summary_report.csv":
                ",".join(_SUMMARY_CSV_HEADER),
            f"{base_path}/2026_10_28/input1/genmcf/summary_report.csv":
                ",".join(_SUMMARY_CSV_HEADER),
        }
        uploaded_strings = {}
        uploaded_files = {}

        def _get_blob(path):
            b = mock.MagicMock()
            b.name = path
            b.exists.return_value = path in blob_store
            b.download_as_text.return_value = blob_store.get(path, "")

            def _upload_str(content):
                uploaded_strings[path] = content

            def _upload_file(local_path):
                with open(local_path, "r", encoding="utf-8") as f:
                    uploaded_files[path] = f.read()

            b.upload_from_string.side_effect = _upload_str
            b.upload_from_filename.side_effect = _upload_file
            return b

        mock_bucket.blob.side_effect = _get_blob
        mock_iterator = mock.MagicMock()
        mock_iterator.prefixes = [
            f"{base_path}/2026_10_28/input0/",
            f"{base_path}/2026_10_28/input1/",
        ]
        mock_gcs.list_blobs.return_value = mock_iterator

        def _fake_series_agg(**kwargs):
            self.assertFalse(kwargs["reuse_existing_raw_obs"])
            self.assertFalse(kwargs["append_to_agg_obs"])
            if kwargs["input_prefix"] == "input1":
                return {"agg_obs_count": 0, "output_mcf_path": None}
            out_mcf = kwargs["output_mcf_path"]
            stat_var_series_aggregator.write_mcf_observations(
                [
                    {
                        "variableMeasured":
                            "DifferenceAcrossModels_Max_Temperature",
                        "observationAbout":
                            "country/USA",
                        "observationDate":
                            "2030-07",
                        "value":
                            2.25,
                        "unit":
                            "Celsius",
                        "observationPeriod":
                            "P1M",
                        "measurementMethod":
                            "dcAggregate/MaxDiffAcrossMeasurementMethods",
                    },
                    {
                        "variableMeasured":
                            "DifferenceRelativeToBaseDate1990_Max_Temperature",
                        "observationAbout":
                            "country/USA",
                        "observationDate":
                            "2030-07",
                        "value":
                            1.5,
                        "unit":
                            "Celsius",
                        "observationPeriod":
                            "P1M",
                        "measurementMethod":
                            "dcAggregate/NASA_CCSM4",
                    },
                ],
                out_mcf,
            )
            if kwargs.get("summary_report_path"):
                stat_var_series_aggregator.update_summary_report_csv(
                    kwargs["summary_report_path"],
                    stat_var_series_aggregator.parse_mcf_observations([out_mcf
                                                                      ]),
                )
            return {"agg_obs_count": 2, "output_mcf_path": out_mcf}

        mock_run_series_agg.side_effect = _fake_series_agg

        exit_code = aggregator_main.run_aggregation_job(
            absolute_import_name="scripts/ipcc:NASA_NEXGDDP_Country",
            import_config_str='{"gcp_project_id": "test-proj"}',
            bucket_name="test-bucket",
            bq_dataset="test_dataset",
        )
        self.assertEqual(0, exit_code)
        mock_run_sv_agg.assert_not_called()
        self.assertEqual(2, mock_run_series_agg.call_count)

        input0_series_blob = (
            f"{base_path}/2026_10_28/input0/genmcf/stat_var_series_agg_nodes.mcf"
        )
        input1_series_blob = (
            f"{base_path}/2026_10_28/input1/genmcf/stat_var_series_agg_nodes.mcf"
        )
        input0_sv_blob = (
            f"{base_path}/2026_10_28/input0/genmcf/stat_var_agg_nodes.mcf")
        input0_summary_blob = (
            f"{base_path}/2026_10_28/input0/genmcf/summary_report.csv")
        import_summary_blob = f"{base_path}/2026_10_28/import_summary.json"

        self.assertIn(input0_series_blob, uploaded_files)
        self.assertNotIn(input1_series_blob, uploaded_files)
        self.assertNotIn(input0_sv_blob, uploaded_files)
        self.assertIn(
            "variableMeasured: dcs:DifferenceAcrossModels_Max_Temperature",
            uploaded_files[input0_series_blob],
        )
        self.assertIn(input0_summary_blob, uploaded_files)
        self.assertIn(
            "dcs:DifferenceRelativeToBaseDate1990_Max_Temperature",
            uploaded_files[input0_summary_blob],
        )

        updated_summary = json.loads(uploaded_strings[import_summary_blob])
        self.assertEqual(
            2, updated_summary["import_stats"]["aggregated_obs_count"])
        self.assertIn("aggregation_execution_time",
                      updated_summary["import_stats"])

    @mock.patch(
        "aggregator_main.stat_var_series_aggregator.run_bigquery_series_aggregation"
    )
    @mock.patch("aggregator_main.stat_var_aggregator.run_bigquery_aggregation")
    @mock.patch("aggregator_main.storage.Client")
    def test_main_run_aggregation_job_combined_statvar_and_series_with_path_overrides(
            self, mock_storage_cls, mock_run_sv_agg, mock_run_series_agg):
        """Runs both StatVar and Series aggregators when both configs match, uploading both MCFs and summing counts."""
        with tempfile.TemporaryDirectory() as cfg_dir:
            sv_cfg_path = os.path.join(cfg_dir, "custom_statvar.yaml")
            series_cfg_path = os.path.join(cfg_dir, "custom_series.yaml")

            with open(sv_cfg_path, "w", encoding="utf-8") as f:
                f.write("imports:\n"
                        "  CombinedClimateImport:\n"
                        "    stat_var_aggregation:\n"
                        "      - ancestor_sv_id: SV_CombinedTotal\n"
                        "        source_sv_ids:\n"
                        "          - SV_Part1\n"
                        "          - SV_Part2\n")

            with open(series_cfg_path, "w", encoding="utf-8") as f:
                f.write(
                    "imports:\n"
                    "  CombinedClimateImport:\n"
                    "    stat_var_series_aggregation:\n"
                    "      - round: 1\n"
                    "        aggr_funcs:\n"
                    "          - type: max_diff_across_measurement_methods\n")

            # Unconfigured import against both custom config paths exits 0 with no GCS calls.
            noop_code = aggregator_main.run_aggregation_job(
                absolute_import_name="scripts/custom:OtherUnconfiguredImport",
                bucket_name="test-bucket",
                statvar_config_path=sv_cfg_path,
                statvar_series_config_path=series_cfg_path,
            )
            self.assertEqual(0, noop_code)
            mock_storage_cls.assert_not_called()

            mock_gcs = mock_storage_cls.return_value
            mock_bucket = mock.MagicMock()
            mock_gcs.bucket.return_value = mock_bucket

            base_path = "scripts/custom/CombinedClimateImport"
            blob_store = {
                f"{base_path}/staging_version.txt":
                    "2026_10_28",
                f"{base_path}/2026_10_28/import_summary.json":
                    json.dumps({
                        "import_name": "CombinedClimateImport",
                        "status": "PENDING",
                    }),
                f"{base_path}/2026_10_28/input0/genmcf/summary_report.csv":
                    ",".join(_SUMMARY_CSV_HEADER),
            }
            uploaded_strings = {}
            uploaded_files = {}
            upload_file_counts = {}

            def _get_blob(path):
                b = mock.MagicMock()
                b.name = path
                b.exists.return_value = path in blob_store
                b.download_as_text.return_value = blob_store.get(path, "")

                def _upload_str(content):
                    uploaded_strings[path] = content

                def _upload_file(local_path):
                    upload_file_counts[path] = upload_file_counts.get(path,
                                                                      0) + 1
                    with open(local_path, "r", encoding="utf-8") as f:
                        uploaded_files[path] = f.read()

                b.upload_from_string.side_effect = _upload_str
                b.upload_from_filename.side_effect = _upload_file
                return b

            mock_bucket.blob.side_effect = _get_blob
            mock_iterator = mock.MagicMock()
            mock_iterator.prefixes = [f"{base_path}/2026_10_28/input0/"]
            mock_gcs.list_blobs.return_value = mock_iterator

            def _fake_sv_agg(**kwargs):
                out_mcf = kwargs["output_mcf_path"]
                stat_var_aggregator.write_mcf_observations(
                    [{
                        "variableMeasured": "SV_CombinedTotal",
                        "observationAbout": "country/USA",
                        "observationDate": "2025",
                        "value": 100.0,
                        "unit": "Person",
                        "measurementMethod": "dcAggregate/MethodA",
                    }],
                    out_mcf,
                )
                if kwargs.get("summary_report_path"):
                    stat_var_aggregator.update_summary_report_csv(
                        kwargs["summary_report_path"],
                        stat_var_aggregator.parse_mcf_observations([out_mcf]),
                    )
                return {
                    "raw_obs_count": 15,
                    "agg_obs_count": 2,
                    "output_mcf_path": out_mcf,
                    "table_ids": {
                        "raw_obs": "proj.ds.raw",
                        "agg_obs": "proj.ds.agg",
                    },
                }

            def _fake_series_agg(**kwargs):
                self.assertTrue(kwargs["reuse_existing_raw_obs"])
                self.assertTrue(kwargs["append_to_agg_obs"])
                out_mcf = kwargs["output_mcf_path"]
                stat_var_series_aggregator.write_mcf_observations(
                    [{
                        "variableMeasured":
                            "DifferenceAcrossModels_PrecipitationRate",
                        "observationAbout":
                            "country/USA",
                        "observationDate":
                            "2030-06",
                        "value":
                            1.25e-6,
                        "unit":
                            "KilogramPerSquareMeterPerSecond",
                        "observationPeriod":
                            "P1M",
                        "measurementMethod":
                            "dcAggregate/MaxDiffAcrossMeasurementMethods",
                    }],
                    out_mcf,
                )
                if kwargs.get("summary_report_path"):
                    stat_var_series_aggregator.update_summary_report_csv(
                        kwargs["summary_report_path"],
                        stat_var_series_aggregator.parse_mcf_observations(
                            [out_mcf]),
                    )
                return {"agg_obs_count": 3, "output_mcf_path": out_mcf}

            mock_run_sv_agg.side_effect = _fake_sv_agg
            mock_run_series_agg.side_effect = _fake_series_agg

            exit_code = aggregator_main.run_aggregation_job(
                absolute_import_name="scripts/custom:CombinedClimateImport",
                import_config_str='{"gcp_project_id": "test-proj"}',
                bucket_name="test-bucket",
                bq_dataset="test_dataset",
                statvar_config_path=sv_cfg_path,
                statvar_series_config_path=series_cfg_path,
            )
            self.assertEqual(0, exit_code)
            mock_run_sv_agg.assert_called_once()
            mock_run_series_agg.assert_called_once()

            sv_mcf_blob = (
                f"{base_path}/2026_10_28/input0/genmcf/stat_var_agg_nodes.mcf")
            series_mcf_blob = (
                f"{base_path}/2026_10_28/input0/genmcf/stat_var_series_agg_nodes.mcf"
            )
            summary_blob = (
                f"{base_path}/2026_10_28/input0/genmcf/summary_report.csv")
            import_summary_blob = f"{base_path}/2026_10_28/import_summary.json"

            self.assertIn(sv_mcf_blob, uploaded_files)
            self.assertIn(series_mcf_blob, uploaded_files)
            self.assertIn("variableMeasured: dcs:SV_CombinedTotal",
                          uploaded_files[sv_mcf_blob])
            self.assertIn(
                "variableMeasured: dcs:DifferenceAcrossModels_PrecipitationRate",
                uploaded_files[series_mcf_blob],
            )
            # summary_report.csv uploaded once with both StatVar and Series entries.
            self.assertEqual(1, upload_file_counts[summary_blob])
            self.assertIn("dcs:SV_CombinedTotal", uploaded_files[summary_blob])
            self.assertIn("dcs:DifferenceAcrossModels_PrecipitationRate",
                          uploaded_files[summary_blob])

            updated_summary = json.loads(uploaded_strings[import_summary_blob])
            self.assertEqual(
                5, updated_summary["import_stats"]["aggregated_obs_count"])


if __name__ == "__main__":
    unittest.main()
