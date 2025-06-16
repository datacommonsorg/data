# Copyright 2025 Google LLC
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
"""This script converts financial incentive data from textproto format to CSV format."""
import csv

from absl import app
from absl import flags
from google.protobuf import text_format

import sustainable_financial_incentives_pb2

FLAGS = flags.FLAGS

flags.DEFINE_string('textproto_path', 'testdata/sample_incentives.textproto',
                    'Local path to the textproto file.')
flags.DEFINE_string('csv_path', 'output.csv',
                    'Local path to write the CSV file.')


def convert_textproto_to_csv(textproto_path: str, csv_path: str) -> None:
    """Converts a textproto file to a CSV file with a flattened, dot-notation header.

    Args:
        textproto_path: The local path to the input textproto file.
        csv_path: The local path to write the output CSV file to.
    """
    with open(textproto_path, 'r', encoding='utf-8') as f:
        incentive_summaries = text_format.Parse(
            f.read(),
            sustainable_financial_incentives_pb2.IncentiveSummaries()  # pylint: disable=no-member
        )

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write header
        header = [
            'extraction_config.url', 'extraction_config.locale.language',
            'extraction_config.locale.country_iso',
            'extraction_config.locale.admin_area_1',
            'extraction_config.incentive_category', 'incentive.purchase_type',
            'incentive.redemption_type',
            'incentive.maximum_amount.currency_code',
            'incentive.maximum_amount.units', 'incentive.maximum_amount.nanos',
            'incentive.name', 'incentive.provider_name',
            'incentive.percentage_of_costs_covered',
            'incentive.per_unit_amount.amount.currency_code',
            'incentive.per_unit_amount.amount.units',
            'incentive.per_unit_amount.amount.nanos',
            'incentive.per_unit_amount.unit', 'incentive.tax_waiver_type'
        ]
        writer.writerow(header)

        # Write data
        for summary in incentive_summaries.incentive_summaries:
            row = [
                summary.extraction_config.url,
                summary.extraction_config.locale.language,
                summary.extraction_config.locale.country_iso,
                summary.extraction_config.locale.admin_area_1,
                sustainable_financial_incentives_pb2.IncentiveCategory.Name(
                    summary.extraction_config.incentive_category),
                sustainable_financial_incentives_pb2.PurchaseType.Name(
                    summary.incentive.purchase_type),
                sustainable_financial_incentives_pb2.RedemptionType.Name(
                    summary.incentive.redemption_type),
                summary.incentive.maximum_amount.currency_code,
                summary.incentive.maximum_amount.units,
                summary.incentive.maximum_amount.nanos, summary.incentive.name,
                summary.incentive.provider_name,
                f"{summary.incentive.percentage_of_costs_covered:.1f}",
                summary.incentive.per_unit_amount.amount.currency_code,
                summary.incentive.per_unit_amount.amount.units,
                summary.incentive.per_unit_amount.amount.nanos,
                sustainable_financial_incentives_pb2.CreditUnits.Name(
                    summary.incentive.per_unit_amount.unit),
                sustainable_financial_incentives_pb2.TaxWaiverType.Name(
                    summary.incentive.tax_waiver_type)
            ]
            writer.writerow(row)


def main(argv):
    """Converts a textproto file to a CSV file."""
    del argv  # Unused
    print(f'Converting {FLAGS.textproto_path} to {FLAGS.csv_path}...')
    convert_textproto_to_csv(FLAGS.textproto_path, FLAGS.csv_path)
    print('Conversion complete.')


if __name__ == '__main__':
    app.run(main)
