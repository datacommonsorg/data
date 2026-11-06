import unittest
from unittest import mock
import json
import os
import sys
import tempfile
import csv
import re
import dateutil.parser
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from file_sharder import FileSharder, shard_file
from file_dict_io import McfFileDictIO, open_dict_file, open_file_dict
import counters as counters_lib
import file_sharder


class TestFileSharder(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.input_file_path = os.path.join(self.test_dir.name, 'input.csv')
        self.mcf_input_file_path = os.path.join(self.test_dir.name, 'input.mcf')

    def tearDown(self):
        self.test_dir.cleanup()

    def _create_csv_file(self, data):
        with open(self.input_file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

    def _create_mcf_file(self, data):
        writer = McfFileDictIO(self.mcf_input_file_path, mode='w')
        for node in data:
            writer.write_record(node)
        writer.close()

    def _create_keyed_csv_file(self, num_keys, rows_per_key):
        """Writes `rows_per_key` rows for each of `num_keys` keys to the input CSV."""
        with open(self.input_file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'value'])
            for row in range(rows_per_key):
                for key in range(num_keys):
                    writer.writerow([f'geoId/{key}', str(row)])

    def _read_shards(self, prefix, shard_count):
        """Returns the rows in each output shard `<prefix>-NNNNN-of-MMMMM.csv`."""
        shards = []
        for index in range(shard_count):
            path = os.path.join(
                self.test_dir.name,
                f'{prefix}-{index:05d}-of-{shard_count:05d}.csv')
            with open(path, 'r') as f:
                shards.append(list(csv.DictReader(f)))
        return shards

    def test_shard_csv_file(self):
        data = [
            {
                'id': '11',
                'value': 'a'
            },
            {
                'id': '21',
                'value': 'b'
            },
            {
                'id': '11',
                'value': 'c'
            },
            {
                'id': '31',
                'value': 'd'
            },
        ]
        self._create_csv_file(data)

        output_path = os.path.join(self.test_dir.name, 'output@3.csv')
        config = {'shard_key': '{id}'}
        shard_file(self.input_file_path, output_path, config)

        # Verify output files
        shard_0_path = os.path.join(self.test_dir.name,
                                    'output-00000-of-00003.csv')
        shard_1_path = os.path.join(self.test_dir.name,
                                    'output-00001-of-00003.csv')
        shard_2_path = os.path.join(self.test_dir.name,
                                    'output-00002-of-00003.csv')

        self.assertTrue(os.path.exists(shard_0_path))
        self.assertTrue(os.path.exists(shard_1_path))
        self.assertTrue(os.path.exists(shard_2_path))

        with open(shard_1_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['id'], '11')
            self.assertEqual(rows[1]['id'], '11')

    def test_shard_mcf_file(self):
        data = [
            {
                'Node': 'dcid:node11',
                'prop': 'a'
            },
            {
                'Node': 'dcid:node22',
                'prop': 'b'
            },
            {
                'Node': 'dcid:node11',
                'prop': 'c'
            },
            {
                'Node': 'dcid:node33',
                'prop': 'd'
            },
        ]
        self._create_mcf_file(data)

        output_path = os.path.join(self.test_dir.name, 'output@3.mcf')
        config = {'shard_key': 'Node'}
        shard_file(self.mcf_input_file_path, output_path, config)

        # Verify output files
        shard_0_path = os.path.join(self.test_dir.name,
                                    'output-00000-of-00003.mcf')
        shard_1_path = os.path.join(self.test_dir.name,
                                    'output-00001-of-00003.mcf')
        shard_2_path = os.path.join(self.test_dir.name,
                                    'output-00002-of-00003.mcf')

        self.assertTrue(os.path.exists(shard_0_path))
        self.assertTrue(os.path.exists(shard_1_path))
        self.assertTrue(os.path.exists(shard_2_path))

        reader = McfFileDictIO(shard_0_path, 'r')
        nodes = []
        node = reader.next()
        while node:
            nodes.append(node)
            node = reader.next()
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0]['Node'], 'dcid:node11')
        self.assertEqual(nodes[1]['Node'], 'dcid:node11')

    def test_skip_duplicates(self):
        data = [
            {
                'id': '1',
                'value': 'a'
            },
            {
                'id': '2',
                'value': 'b'
            },
            {
                'id': '1',
                'value': 'a'
            },  # duplicate
            {
                'id': '3',
                'value': 'd'
            },
        ]
        self._create_csv_file(data)

        output_path = os.path.join(self.test_dir.name, 'output@2.csv')
        config = {'shard_key': 'id', 'shard_skip_duplicates': True}
        shard_file(self.input_file_path, output_path, config)

        shard_0_path = os.path.join(self.test_dir.name,
                                    'output-00000-of-00002.csv')
        shard_1_path = os.path.join(self.test_dir.name,
                                    'output-00001-of-00002.csv')

        with open(shard_0_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['id'], '2')

        with open(shard_1_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['id'], '1')
            self.assertEqual(rows[1]['id'], '3')

    def test_parallel_multiple_input_files(self):
        from counters import Counters
        from file_dict_io import open_dict_file

        input_files = []
        for idx in range(4):
            path = os.path.join(self.test_dir.name, f'part_{idx}.csv')
            input_files.append(path)
            with open_dict_file(path, 'w', headers=['id', 'val']) as writer:
                writer.write([
                    {
                        'id': f'k_{idx}_0',
                        'val': 'v0'
                    },
                    {
                        'id': f'k_{idx}_1',
                        'val': 'v1'
                    },
                    {
                        'id': 'shared_dup',
                        'val': 'same'
                    },
                ])

        output_path = os.path.join(self.test_dir.name, 'multi_out@3.csv')
        counters = Counters()
        shard_file(
            input_files,
            output_path,
            {
                'shard_key': 'id',
                'shard_skip_duplicates': True,
                'shard_threads': 4,
            },
            counters=counters,
        )

        self.assertEqual(12, counters.get_counter('processed'))
        self.assertEqual(3, counters.get_counter('shard-duplicate-dropped'))
        self.assertEqual(9, counters.get_counter('shard-output-records'))

        with open_dict_file(output_path, 'r') as reader:
            records = reader.readlines()
            self.assertEqual(9, len(records))

    def test_default_pvs_and_generate_dcid(self):
        from counters import Counters
        from file_dict_io import open_dict_file
        from file_sharder import generate_node_dcid

        obs_rows = [
            {
                'observationAbout': 'dcid:geoId/06',
                'variableMeasured': 'dcid:Count_Person',
                'observationDate': '2020',
                'value': '39538223',
                'tempNote': 'ignore_me_1',
            },
            {
                'observationAbout': 'dcid:geoId/36',
                'variableMeasured': 'dcid:Count_Person',
                'observationDate': '2020',
                'value': '20201249',
                'tempNote': 'ignore_me_2',
            },
        ]
        obs_csv = os.path.join(self.test_dir.name, 'obs_in.csv')
        with open_dict_file(
                obs_csv,
                'w',
                headers=[
                    'observationAbout',
                    'variableMeasured',
                    'observationDate',
                    'value',
                    'tempNote',
                ],
        ) as writer:
            writer.write(obs_rows)

        out_pattern = os.path.join(self.test_dir.name, 'obs_out@2.csv')
        counters = Counters()
        shard_file(
            obs_csv,
            out_pattern,
            {
                'shard_default_pvs': {
                    'typeOf': 'dcs:StatVarObservation'
                },
                'shard_generate_dcid': True,
                'shard_dcid_ignore_props': ['tempNote'],
                'shard_key': 'dcid',
            },
            counters=counters,
        )

        self.assertEqual(2, counters.get_counter('shard-dcid-generated'))
        with open_dict_file(out_pattern, 'r') as reader:
            sharded_rows = reader.readlines()
            self.assertEqual(2, len(sharded_rows))
            for row in sharded_rows:
                self.assertEqual('dcs:StatVarObservation', row['typeOf'])
                self.assertTrue(row['dcid'].startswith('dc/o/'))
                row_without_note = {
                    k: v for k, v in row.items() if k != 'tempNote'
                }
                expected_dcid = generate_node_dcid(row_without_note)
                self.assertEqual(expected_dcid, row['dcid'])

    def test_sample_rate_keeps_fraction_of_keys_uniformly_across_shards(self):
        num_keys = 10000
        self._create_keyed_csv_file(num_keys=num_keys, rows_per_key=2)
        output_path = os.path.join(self.test_dir.name, 'sampled@20.csv')
        shard_file(self.input_file_path, output_path, {
            'shard_key': 'id',
            'shard_sample_rate': 0.5,
        })

        shards = self._read_shards('sampled', 20)
        rows_per_key = {}
        for rows in shards:
            for row in rows:
                rows_per_key[row['id']] = rows_per_key.get(row['id'], 0) + 1
        # About half of the keys are kept, each with all of its rows.
        self.assertAlmostEqual(0.5, len(rows_per_key) / num_keys, delta=0.02)
        self.assertEqual({2}, set(rows_per_key.values()))
        # Kept records are spread uniformly across all shards.
        mean_rows = sum(len(rows) for rows in shards) / len(shards)
        for rows in shards:
            self.assertGreater(len(rows), 0.75 * mean_rows)
            self.assertLess(len(rows), 1.25 * mean_rows)

    def test_sample_rate_zero_keeps_no_records_and_one_keeps_all(self):
        self._create_keyed_csv_file(num_keys=100, rows_per_key=1)
        for rate, expected_rows in ((0.0, 0), (1.0, 100)):
            prefix = f'rate_{rate:g}'
            output_path = os.path.join(self.test_dir.name, f'{prefix}@4.csv')
            shard_file(self.input_file_path, output_path, {
                'shard_key': 'id',
                'shard_sample_rate': rate,
            })
            shards = self._read_shards(prefix, 4)
            self.assertEqual(expected_rows, sum(len(rows) for rows in shards))

    def test_invalid_sample_rate_raises(self):
        self._create_keyed_csv_file(num_keys=1, rows_per_key=1)
        output_path = os.path.join(self.test_dir.name, 'invalid@2.csv')
        for rate in (-0.1, 1.5):
            with self.assertRaises(ValueError):
                FileSharder(self.input_file_path, output_path,
                            {'shard_sample_rate': rate})

    def test_global_progress_updates_while_reading_a_file(self):
        self._create_keyed_csv_file(num_keys=50, rows_per_key=1)
        output_path = os.path.join(self.test_dir.name, 'progress@2.csv')
        counters = counters_lib.Counters()
        sharder = FileSharder(self.input_file_path, output_path,
                              {'shard_key': 'id'}, counters)
        processed_at_write = []
        write_record = sharder._writer.write_record

        def write_and_record_progress(record, key=None):
            processed_at_write.append(counters.get_counter('processed'))
            return write_record(record, key=key)

        sharder._writer.write_record = write_and_record_progress
        with mock.patch.object(file_sharder, '_PROGRESS_BATCH_SIZE', 10):
            sharder.process()

        # Global progress advances every 10 records, not once per input file.
        self.assertEqual([i // 10 * 10 for i in range(1, 51)],
                         processed_at_write)
        self.assertEqual(50, counters.get_counter('processed'))

    def test_merged_counters_do_not_sum_per_file_rates(self):
        input_files = []
        for idx in range(2):
            path = os.path.join(self.test_dir.name, f'rate_part_{idx}.csv')
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'value'])
                writer.writerows(
                    [f'geoId/{row}', str(row)] for row in range(30))
            input_files.append(path)
        output_path = os.path.join(self.test_dir.name, 'rate_out@2.csv')
        # Print counters on every update so per-file processing rates are set.
        print_always = counters_lib.CounterOptions(show_every_n_sec=1e-9)
        with mock.patch.object(counters_lib,
                               'get_default_counter_options',
                               return_value=print_always), mock.patch.object(
                                   file_sharder, '_PROGRESS_BATCH_SIZE', 10):
            sharder = FileSharder(input_files, output_path, {'shard_key': 'id'})
            sharder.process()

        reader_counters = sharder._reader_counters.get_counters()
        self.assertEqual(60, reader_counters['processed'])
        self.assertEqual(2, reader_counters['shard-input-files'])
        self.assertNotIn('processing_rate', reader_counters)

    def test_records_per_shard_is_based_on_sampled_records(self):
        self._create_keyed_csv_file(num_keys=2000, rows_per_key=1)
        output_path = os.path.join(self.test_dir.name, 'sized.csv')
        sharder = FileSharder(self.input_file_path, output_path, {
            'shard_key': 'id',
            'records_per_shard': 100,
            'shard_sample_rate': 0.25,
        })
        sharder.process()

        # About 500 sampled records need about 5 shards of 100 records, not
        # the 20 shards needed for all 2000 input records.
        num_shards = len(sharder._writer.files())
        self.assertGreaterEqual(num_shards, 5)
        self.assertLessEqual(num_shards, 7)
        shards = self._read_shards('sized', num_shards)
        self.assertTrue(all(shards))

    def _read_text(self, paths):
        """Returns the concatenated text of the files in `paths`."""
        text = ''
        for path in paths:
            with open(path, 'r') as f:
                text += f.read()
        return text

    def test_shard_csv_to_mcf_writes_node_and_no_column_headers(self):
        self._create_csv_file([
            {
                'dcid': 'geoId/06',
                'typeOf': 'State',
                'value': '1'
            },
            {
                'dcid': 'geoId/07',
                'typeOf': 'State',
                'value': '2'
            },
        ])
        output_path = os.path.join(self.test_dir.name, 'csv_to_mcf@2.mcf')
        shard_file(self.input_file_path, output_path, {'shard_key': 'dcid'})

        text = self._read_text([
            os.path.join(self.test_dir.name,
                         f'csv_to_mcf-{index:05d}-of-00002.mcf')
            for index in range(2)
        ])
        self.assertNotIn('#', text)
        self.assertIn('Node: dcid:geoId/06\n', text)
        self.assertIn('Node: dcid:geoId/07\n', text)

    def test_shard_mcf_without_shard_count_has_no_column_headers(self):
        self._create_mcf_file([
            {
                'Node': 'dcid:node11',
                'name': '"a"'
            },
            {
                'Node': 'dcid:node22',
                'name': '"b"'
            },
        ])
        output_path = os.path.join(self.test_dir.name, 'mcf_out.mcf')
        # Shards are opened after the headers are set from the first record.
        sharder = FileSharder(self.mcf_input_file_path, output_path,
                              {'records_per_shard': 1})
        sharder.process()

        text = self._read_text(sharder._writer.files())
        self.assertNotIn('#', text)
        self.assertEqual(2, text.count('Node: dcid:node'))

    def test_generate_dcid_keeps_node_when_dcid_is_blank(self):
        self._create_csv_file([
            {
                'Node': 'dcid:geoId/06',
                'dcid': '',
                'value': '1'
            },
            {
                'Node': '',
                'dcid': '',
                'value': '2'
            },
        ])
        output_path = os.path.join(self.test_dir.name, 'gen@1.csv')
        counters = counters_lib.Counters()
        shard_file(self.input_file_path,
                   output_path, {'shard_generate_dcid': True},
                   counters=counters)

        rows = self._read_shards('gen', 1)[0]
        self.assertEqual(2, len(rows))
        self.assertEqual('dcid:geoId/06', rows[0]['Node'])
        # Only the record without a dcid or Node gets a generated dcid.
        self.assertTrue(rows[1]['Node'].startswith('dcid:dc/'), rows[1])
        self.assertEqual(1, counters.get_counter('shard-dcid-generated'))

    def test_generate_node_dcid_test_vectors(self):
        # Fixed keys and dcids so other implementations of the steps in
        # generate_node_dcid can check against them.
        vectors = [
            ({
                'a': 'b',
                'c': 'd'
            }, '[["a","dcid:b"],["c","dcid:d"]]', 'dc/kkdk0b70h15g9'),
            # Joining 'prop=value' strings gave this the same key as above.
            ({
                'a': 'bc=d'
            }, '[["a","dcid:bc=d"]]', 'dc/kxdmbgjzp97w8'),
            ({
                'typeOf': 'dcs:StatVarObservation',
                'observationAbout': 'dcid:geoId/06',
                'variableMeasured': 'dcid:Count_Person',
                'observationDate': '2020',
                'value': '39538223',
            }, 'observationAbout=geoId/06variableMeasured=Count_Person'
             'observationDate=2020value=39538223', 'dc/o/xjmf6gpr46zzb'),
            # A StatVarObservation without typeOf.
            ({
                'observationAbout': 'geoId/06',
                'variableMeasured': 'Count_Person',
                'observationDate': '2020',
                'value': '39538223',
            }, 'observationAbout=geoId/06variableMeasured=Count_Person'
             'observationDate=2020value=39538223', 'dc/o/xjmf6gpr46zzb'),
            # A value with spaces is quoted. Only '"', '\' and control
            # characters are escaped in the key.
            ({
                'typeOf': 'dcs:Place',
                'note': 'x "y" \\ é/<&\tz'
            }, r'[["note","\"x \"y\" \\ é/<&\tz\""],["typeOf","dcid:Place"]]',
             'dc/97mr52dvxjgr5'),
            # Ranges, lists, numbers, namespaces and '__' parts are normalized.
            ({
                'typeOf': 'Place',
                'age': '[10 20 Years]',
                'mm': 'dcs:B, A,B',
                'v': '1.50',
                'e': 'a__c__b',
            }, '[["age","dcid:Years10To20"],["e","dcid:a__b__c"],'
             '["mm","dcid:A,dcid:B"],["typeOf","dcid:Place"],["v","1.5"]]',
             'dc/2ecet3e4wx0w2'),
            # The same node written differently has the same key and dcid.
            ({
                'typeOf': 'schema:Place',
                'age': 'Years10To20',
                'mm': 'A,dcid:B',
                'v': 1.5,
                'e': 'dcid:a__b__c',
            }, '[["age","dcid:Years10To20"],["e","dcid:a__b__c"],'
             '["mm","dcid:A,dcid:B"],["typeOf","dcid:Place"],["v","1.5"]]',
             'dc/2ecet3e4wx0w2'),
        ]
        for record, key, dcid in vectors:
            self.assertEqual(dcid, file_sharder.generate_node_dcid(record),
                             record)
            long_id_fn = (file_sharder.get_long_id if dcid.startswith('dc/o/')
                          else file_sharder._get_long_id)
            self.assertEqual(dcid.rsplit('/', 1)[1], long_id_fn(key), key)

    def test_merge_counters(self):
        source = counters_lib.Counters()
        source.add_counter('shard-output-records', 5)
        source.add_counter('processed', 7)
        source.add_counter('processing_rate', 100)
        target1 = counters_lib.Counters()
        target2 = counters_lib.Counters()
        target2.add_counter('shard-output-records', 1)
        file_sharder._merge_counters(source, target1, target2)
        for target, expected in ((target1, 5), (target2, 6)):
            self.assertEqual(expected,
                             target.get_counter('shard-output-records'))
            # 'processed' and rates are not summed.
            self.assertEqual(0, target.get_counter('processed'))
            self.assertEqual(0, target.get_counter('processing_rate'))

    def test_duplicates_use_record_fingerprint(self):
        sharder = FileSharder([], os.path.join(self.test_dir.name, 'd@1.csv'),
                              {'shard_skip_duplicates': True})
        self.assertFalse(sharder.is_duplicate_record({'a': '1', 'b': 'x, y'}))
        # Same record with properties and list values in a different order.
        self.assertTrue(sharder.is_duplicate_record({'b': 'y, x', 'a': '1'}))
        self.assertFalse(sharder.is_duplicate_record({'a': '2', 'b': 'x, y'}))
        self.assertEqual(
            file_sharder.record_to_canonical_str({
                'a': '1',
                'b': 'x, y'
            }), file_sharder.record_to_canonical_str({
                'b': 'y, x',
                'a': '1'
            }))

    def test_parse_default_pvs(self):
        self.assertEqual({}, file_sharder._parse_default_pvs(None))
        self.assertEqual({}, file_sharder._parse_default_pvs(''))
        # Items are separated by ';', so a value can be a comma separated
        # list. Each item is split at the first ':' or '=', so values can
        # contain the other.
        self.assertEqual(
            {
                'typeOf': 'dcs:StatVarObservation',
                'unit': 'dcs:USDollar',
                'measurementMethod': 'dcs:A,dcs:B',
                'note': 'a=b',
            },
            file_sharder._parse_default_pvs(
                'typeOf:dcs:StatVarObservation; unit=dcs:USDollar;'
                'measurementMethod=dcs:A,dcs:B;note:a=b;no_value;'))
        self.assertEqual({
            'typeOf': 'Place',
            'm': 'a,b'
        }, file_sharder._parse_default_pvs(['typeOf=Place', 'm:a,b']))
        self.assertEqual({'typeOf': 'Place'},
                         file_sharder._parse_default_pvs({'typeOf': 'Place'}))

    def test_parse_output_columns(self):
        self.assertEqual({}, file_sharder._parse_output_columns(None))
        self.assertEqual({}, file_sharder._parse_output_columns(''))
        # Columns are separated by ';', and everything after the first '='
        # is the expression, including ',', ':', '=' and quotes.
        self.assertEqual(
            {
                'id': '',
                'v2': 'int(v) * 2',
                'd': "format_date(date, '%Y, %m')",
                'hm': "datetime_strptime(t, '%H:%M').strftime('%H')",
                'same': 'a == b',
                'typeOf': "'dcs:StatVarObservation'",
            },
            file_sharder._parse_output_columns(
                " id ; v2=int(v) * 2; d=format_date(date, '%Y, %m');"
                "hm=datetime_strptime(t, '%H:%M').strftime('%H');same=a == b;"
                "typeOf='dcs:StatVarObservation';"))
        self.assertEqual({
            'id': '',
            'x': '1'
        }, file_sharder._parse_output_columns({
            'id': None,
            'x': 1
        }))
        self.assertEqual({
            'id': '',
            'x': 'f(a, b)'
        }, file_sharder._parse_output_columns(['id', 'x=f(a, b)']))

    def test_shard_output_columns(self):
        self._create_csv_file([
            {
                'id': 'geoId/06',
                'year': '2020',
                'v': '5',
                'name': 'ca state',
                'date': 'Jan 31, 2020',
                'type': ''
            },
            {
                'id': 'geoId/07',
                'year': '2021',
                'v': 'x',
                'name': 'nv',
                'date': 'Feb 1, 2021',
                'type': 'City'
            },
        ])
        output_path = os.path.join(self.test_dir.name, 'cols@1.csv')
        counters = counters_lib.Counters()
        shard_file(
            self.input_file_path,
            output_path, {
                'shard_output_columns':
                    "id;v2=int(v) * 2;label=f'{id}-{year}';"
                    'camel=str_to_camel_case(name);'
                    "month=format_date(date, '%Y, %m');"
                    "type=type or 'State';typeOf='dcs:Place';missing=nope"
            },
            counters=counters)

        path = os.path.join(self.test_dir.name, 'cols-00000-of-00001.csv')
        with open(path) as f:
            header = f.readline().strip()
        # Output columns are in the configured order; other columns are
        # dropped.
        self.assertEqual('id,v2,label,camel,month,type,typeOf,missing', header)
        rows = self._read_shards('cols', 1)[0]
        self.assertEqual(
            {
                'id': 'geoId/06',
                'v2': '10',
                'label': 'geoId/06-2020',
                'camel': 'CaState',
                'month': '2020, 01',
                'type': 'State',  # Default for an empty value.
                'typeOf': 'dcs:Place',
                'missing': '',
            },
            rows[0])
        self.assertEqual(
            {
                'id': 'geoId/07',
                'v2': '',  # int('x') fails.
                'label': 'geoId/07-2021',
                'camel': 'Nv',
                'month': '2021, 02',
                'type': 'City',  # Input value is kept.
                'typeOf': 'dcs:Place',
                'missing': '',
            },
            rows[1])
        # 'missing' fails for both rows and 'v2' for the second row.
        self.assertEqual(3, counters.get_counter('shard-output-column-errors'))

    def test_shard_output_columns_with_generated_dcid(self):
        self._create_csv_file([
            {
                'place': 'geoId/06',
                'year': '2020',
                'v': '5',
                'note': 'a'
            },
            {
                'place': 'geoId/06',
                'year': '2020',
                'v': '5',
                'note': 'b'
            },
        ])
        output_path = os.path.join(self.test_dir.name, 'gen@1.csv')
        shard_file(
            self.input_file_path, output_path, {
                'shard_output_columns': 'observationAbout=place;'
                                        'observationDate=year;value=int(v)',
                'shard_generate_dcid': True,
            })

        rows = self._read_shards('gen', 1)[0]
        self.assertEqual(
            ['dcid', 'observationAbout', 'observationDate', 'value'],
            list(rows[0].keys()))
        # The dcid is generated from the output columns only, so the two
        # records that differ in the dropped 'note' column get the same dcid.
        self.assertTrue(rows[0]['dcid'].startswith('dc/'), rows[0])
        self.assertEqual(rows[0]['dcid'], rows[1]['dcid'])
        self.assertEqual(
            file_sharder.generate_node_dcid({
                'observationAbout': 'geoId/06',
                'observationDate': '2020',
                'value': '5'
            }), rows[0]['dcid'])

    def test_shard_output_columns_multiple_inputs(self):
        # Inputs with different columns are not reported as mismatched,
        # since every output shard has only the output columns.
        input1 = os.path.join(self.test_dir.name, 'in1.csv')
        input2 = os.path.join(self.test_dir.name, 'in2.csv')
        with open(input1, 'w') as f:
            f.write('dcid,v,extra\ngeoId/1,1,x\ngeoId/2,2,y\n')
        with open(input2, 'w') as f:
            f.write('v,dcid\n3,geoId/3\n')
        output_path = os.path.join(self.test_dir.name, 'multi@2.csv')
        counters = counters_lib.Counters()
        shard_file([input1, input2],
                   output_path, {'shard_output_columns': 'dcid;v'},
                   counters=counters)

        rows = sum(self._read_shards('multi', 2), [])
        self.assertEqual([{
            'dcid': 'geoId/1',
            'v': '1'
        }, {
            'dcid': 'geoId/2',
            'v': '2'
        }, {
            'dcid': 'geoId/3',
            'v': '3'
        }], sorted(rows, key=lambda r: r['dcid']))
        self.assertEqual(0,
                         counters.get_counter('error-shard-mismatched-headers'))

    def test_output_columns_computed_from_input_columns(self):
        input_rows = [
            {
                'country': 'USA',
                'year': '2020',
                'month': '3',
                'count': '1500',
                'name': 'person count',
                'date': 'Mar 5, 2020',
                'zip': 'CA-94043',
                'measurementMethod': ''
            },
            {
                'country': 'IND',
                'year': '2021',
                'month': '11',
                'count': '250',
                'name': 'median-age',
                'date': '2021/11/30',
                'zip': '560 001',
                'measurementMethod': 'dcs:C'
            },
            {
                'country': 'FRA',
                'year': '2019',
                'month': '12',
                'count': '1000',
                'name': 'area_sq km',
                'date': '1 Dec 2019',
                'zip': '75001',
                'measurementMethod': ''
            },
        ]
        self._create_csv_file(input_rows)
        default_pvs = 'measurementMethod=dcs:A,dcs:B;unit:dcs:Count'
        output_columns = ';'.join([
            "observationAbout=f'country/{country}'",
            "observationDate='{}-{:02d}'.format(year, int(month))",
            "date=format_date(date, '%Y-%m-%d')",
            'value=round(float(count) / 1000, 2)',
            "size='large' if int(count) >= 1000 else 'small'",
            'variableMeasured=str_to_camel_case(name)',
            "code=re_sub('[^0-9]', '', zip)",
            'measurementMethod',
            "numMethods=len(measurementMethod.split(','))",
            'unit',
        ])

        def expected_output(row: dict) -> dict:
            """The output columns above, computed directly in Python."""
            method = row['measurementMethod'] or 'dcs:A,dcs:B'
            parsed_date = dateutil.parser.parse(row['date'])
            words = re.sub(r'[^A-Za-z_0-9]', ' ', row['name']).split()
            return {
                'observationAbout':
                    'country/' + row['country'],
                'observationDate':
                    f"{row['year']}-{int(row['month']):02d}",
                'date':
                    parsed_date.strftime('%Y-%m-%d'),
                'value':
                    str(round(float(row['count']) / 1000, 2)),
                'size':
                    'large' if int(row['count']) >= 1000 else 'small',
                'variableMeasured':
                    ''.join(w[0].upper() + w[1:] for w in words),
                'code':
                    re.sub('[^0-9]', '', row['zip']),
                'measurementMethod':
                    method,
                'numMethods':
                    str(len(method.split(','))),
                'unit':
                    'dcs:Count',
            }

        output_path = os.path.join(self.test_dir.name, 'computed@1.csv')
        counters = counters_lib.Counters()
        shard_file(self.input_file_path,
                   output_path, {
                       'shard_default_pvs': default_pvs,
                       'shard_output_columns': output_columns,
                   },
                   counters=counters)

        rows = self._read_shards('computed', 1)[0]
        self.assertEqual(len(input_rows), len(rows))
        for input_row, output_row in zip(input_rows, rows):
            self.assertEqual(expected_output(input_row), output_row)
        # Spot-check a few values so a shared mistake in the expected
        # function doesn't go unnoticed.
        self.assertEqual('country/USA', rows[0]['observationAbout'])
        self.assertEqual('2021-11', rows[1]['observationDate'])
        self.assertEqual('2019-12-01', rows[2]['date'])
        self.assertEqual('PersonCount', rows[0]['variableMeasured'])
        self.assertEqual('dcs:A,dcs:B', rows[0]['measurementMethod'])
        self.assertEqual('dcs:C', rows[1]['measurementMethod'])
        self.assertEqual(0, counters.get_counter('shard-output-column-errors'))

    def test_is_seekable_file(self):
        self.assertTrue(file_sharder.is_seekable_file('data.csv'))
        self.assertTrue(file_sharder.is_seekable_file('data.tsv'))
        self.assertTrue(file_sharder.is_seekable_file('data.jsonl'))
        self.assertTrue(file_sharder.is_seekable_file('data.ndjson'))
        self.assertTrue(file_sharder.is_seekable_file('data.mcf'))
        self.assertTrue(file_sharder.is_seekable_file('data.tmcf'))
        self.assertTrue(file_sharder.is_seekable_file('data.avro'))

        self.assertFalse(file_sharder.is_seekable_file('data.csv.gz'))
        self.assertFalse(file_sharder.is_seekable_file('data.tar.gz'))
        self.assertFalse(file_sharder.is_seekable_file('data.zip'))
        self.assertFalse(file_sharder.is_seekable_file('data.json'))
        self.assertFalse(file_sharder.is_seekable_file('gs://bucket/data.csv'))
        self.assertFalse(file_sharder.is_seekable_file(None))

        # Backward compatibility alias
        self.assertTrue(file_sharder.is_splittable_file('data.csv'))
        self.assertFalse(file_sharder.is_splittable_file('data.json'))

    def test_shard_single_large_file_multiple_workers(self):
        # Create CSV file with 500 rows.
        rows = [{
            'id': f'geoId/{i:04d}',
            'val': str(i * 10)
        } for i in range(500)]
        self._create_csv_file(rows)

        output_path = os.path.join(self.test_dir.name, 'parallel_out@2.csv')
        config = {
            'shard_threads': 4,
            'shard_min_chunk_size': 500,
            'shard_key': '{id}',
        }
        counters = counters_lib.Counters()
        shard_file(self.input_file_path, output_path, config, counters=counters)

        shards = self._read_shards('parallel_out', 2)
        combined = shards[0] + shards[1]
        self.assertEqual(500, len(combined))
        # Ensure all original IDs are present with no duplicates.
        output_ids = {r['id'] for r in combined}
        expected_ids = {r['id'] for r in rows}
        self.assertEqual(expected_ids, output_ids)

        # Verify worker and progress counters
        self.assertGreater(counters.get_counter('shard-workers'), 1)
        self.assertEqual(counters.get_counter('shard-workers'),
                         counters.get_counter('workers'))
        self.assertGreater(counters.get_counter('shard-tasks'), 1)
        self.assertEqual(counters.get_counter('shard-tasks'),
                         counters.get_counter('shard-tasks-completed'))
        self.assertEqual(500, counters.get_counter('processed'))
        self.assertGreaterEqual(counters.get_counter('total'), 500)
        self.assertEqual(500, counters.get_counter('shard-input-records'))
        self.assertEqual(500, counters.get_counter('shard-output-records'))

    def test_shard_multiple_files_with_splittable_and_non_splittable(self):
        csv_file = os.path.join(self.test_dir.name, 'file1.csv')
        jsonl_file = os.path.join(self.test_dir.name, 'file2.jsonl')
        json_file = os.path.join(self.test_dir.name, 'file3.json')

        rows_csv = [{'id': f'csv_{i:03d}', 'val': str(i)} for i in range(200)]
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'val'])
            writer.writeheader()
            writer.writerows(rows_csv)

        rows_jsonl = [{
            'id': f'jsonl_{i:03d}',
            'val': str(i)
        } for i in range(200)]
        with open(jsonl_file, 'w') as f:
            for r in rows_jsonl:
                f.write(json.dumps(r) + '\n')

        rows_json = [{'id': f'json_{i:03d}', 'val': str(i)} for i in range(50)]
        with open_file_dict(json_file, mode='w') as writer:
            for r in rows_json:
                writer.write(r)

        input_files = f'{csv_file},{jsonl_file},{json_file}'
        output_path = os.path.join(self.test_dir.name, 'multi_out@3.csv')
        config = {
            'shard_threads': 4,
            'shard_min_chunk_size': 500,
            'shard_key': '{id}',
        }
        counters = counters_lib.Counters()
        shard_file(input_files, output_path, config, counters=counters)

        shards = self._read_shards('multi_out', 3)
        combined = shards[0] + shards[1] + shards[2]
        self.assertEqual(450, len(combined))
        output_ids = {r['id'] for r in combined}
        all_expected_ids = {r['id'] for r in rows_csv + rows_jsonl + rows_json}
        self.assertEqual(all_expected_ids, output_ids)

        # Verify progress and seekable counters
        self.assertEqual(4, counters.get_counter('shard-workers'))
        self.assertEqual(4, counters.get_counter('workers'))
        self.assertEqual(2, counters.get_counter('shard-seekable-files'))
        self.assertEqual(1, counters.get_counter('shard-non-seekable-files'))
        self.assertEqual(counters.get_counter('shard-tasks'),
                         counters.get_counter('shard-tasks-completed'))
        self.assertEqual(450, counters.get_counter('processed'))
        self.assertGreaterEqual(counters.get_counter('total'), 450)
        self.assertEqual(450, counters.get_counter('shard-input-records'))
        self.assertEqual(450, counters.get_counter('shard-output-records'))

    def test_generate_input_tasks(self):
        csv_file = os.path.join(self.test_dir.name, 'task_split.csv')
        # Write 2000 bytes
        with open(csv_file, 'w') as f:
            f.write('id,val\n')
            for i in range(200):
                f.write(f'{i},{i*2}\n')

        json_file = os.path.join(self.test_dir.name, 'task_nosplit.json')
        with open_file_dict(json_file, 'w') as w:
            for i in range(100):
                w.write({'id': str(i)})

        sharder = FileSharder(
            f'{csv_file},{json_file}',
            os.path.join(self.test_dir.name, 'out@2.csv'),
            config={
                'shard_threads': 4,
                'shard_min_chunk_size': 400
            },
        )
        tasks = sharder._generate_input_tasks(max_threads=4)
        # csv_file is ~2KB, with min_chunk_size=400, can be split into min(4, 2000//400) = 4 chunks
        csv_tasks = [t for t in tasks if t[0] == csv_file]
        self.assertGreater(len(csv_tasks), 1)
        self.assertEqual(0, csv_tasks[0][1])
        self.assertIsNone(csv_tasks[-1][2])
        # Contiguous byte ranges
        for i in range(len(csv_tasks) - 1):
            self.assertEqual(csv_tasks[i][2], csv_tasks[i + 1][1])

        # json_file is not splittable, so it gets 1 task with full file
        json_tasks = [t for t in tasks if t[0] == json_file]
        self.assertEqual([(json_file, 0, None)], json_tasks)

        # When max_threads == 1, no splitting occurs
        tasks_single = sharder._generate_input_tasks(max_threads=1)
        self.assertEqual([(csv_file, 0, None), (json_file, 0, None)],
                         tasks_single)

    def test_dedup_preserves_zero_false_blank_dcid_and_ragged_csv(self):
        jsonl_path = os.path.join(self.test_dir.name, 'zero_bool.jsonl')
        with open_file_dict(jsonl_path, 'w') as writer:
            writer.write([
                {
                    'id': 'p1',
                    'value': 0
                },
                {
                    'id': 'p1',
                    'value': ''
                },
                {
                    'id': 'p1',
                    'value': False
                },
                {
                    'id': 'p1'
                },
                {
                    'id': 'p1',
                    'value': 0
                },
            ])
        out_jsonl = os.path.join(self.test_dir.name, 'zb_out@2.jsonl')
        shard_file(jsonl_path, out_jsonl, {
            'shard_key': 'id',
            'shard_skip_duplicates': True
        })
        with open_file_dict(out_jsonl, 'r') as reader:
            self.assertEqual(4, len(reader.readlines()))

        # Blank dcid column must not collide distinct Node rows.
        self._create_csv_file([
            {
                'Node': 'dcid:geoId/06',
                'dcid': '',
                'val': '1'
            },
            {
                'Node': 'dcid:geoId/36',
                'dcid': '',
                'val': '1'
            },
            {
                'Node': 'dcid:geoId/06',
                'dcid': '',
                'val': '1'
            },
        ])
        out_nodes = os.path.join(self.test_dir.name, 'nodes_dedup@2.csv')
        shard_file(self.input_file_path, out_nodes,
                   {'shard_skip_duplicates': True})
        self.assertEqual(2, len(sum(self._read_shards('nodes_dedup', 2), [])))

        # Ragged CSV rows with extra unheadered columns do not raise TypeError.
        ragged_csv = os.path.join(self.test_dir.name, 'ragged.csv')
        with open(ragged_csv, 'w') as f:
            f.write('id,val\n1\n2,b,extra_col\n3,c\n')
        out_ragged = os.path.join(self.test_dir.name, 'ragged_out@2.csv')
        shard_file(ragged_csv, out_ragged, {
            'shard_generate_dcid': True,
            'shard_skip_duplicates': True,
        })
        self.assertEqual(3, len(sum(self._read_shards('ragged_out', 2), [])))

    def test_generate_node_dcid_preserves_zero_values(self):
        base = {
            'observationAbout': 'geoId/06',
            'variableMeasured': 'Count_Crime',
            'observationDate': '2020',
        }
        missing_dcid = file_sharder.generate_node_dcid(dict(base))
        int_zero = file_sharder.generate_node_dcid({**base, 'value': 0})
        float_zero = file_sharder.generate_node_dcid({**base, 'value': 0.0})
        str_zero = file_sharder.generate_node_dcid({**base, 'value': '0'})
        str_zero_dec = file_sharder.generate_node_dcid({**base, 'value': '0.0'})
        self.assertNotEqual(missing_dcid, int_zero)
        self.assertEqual(int_zero, float_zero)
        self.assertEqual(int_zero, str_zero)
        self.assertEqual(int_zero, str_zero_dec)

    def test_shard_input_records_caps_dynamic_shard_count(self):
        self._create_keyed_csv_file(num_keys=2000, rows_per_key=1)
        output_path = os.path.join(self.test_dir.name, 'capped*.csv')
        sharder = FileSharder(
            self.input_file_path,
            output_path,
            {
                'shard_input_records': 20,
                'records_per_shard': 10,
            },
        )
        sharder.process()
        self.assertLessEqual(len(sharder._writer.files()), 4)
        with open_file_dict(output_path, 'r') as reader:
            self.assertEqual(20, len(reader.readlines()))

    def test_shard_key_preserved_when_omitted_from_output_columns(self):
        rows = [{
            'country': 'USA',
            'id': f'id_{i}',
            'val': str(i)
        } for i in range(20)]
        self._create_csv_file(rows)
        output_path = os.path.join(self.test_dir.name, 'country_routed@4.csv')
        shard_file(
            self.input_file_path,
            output_path,
            {
                'shard_key': 'country',
                'shard_output_columns': 'id;val',
            },
        )
        shards = self._read_shards('country_routed', 4)
        non_empty_shards = [s for s in shards if s]
        self.assertEqual(1, len(non_empty_shards))
        self.assertEqual(20, len(non_empty_shards[0]))
        self.assertEqual(['id', 'val'], list(non_empty_shards[0][0].keys()))

    def test_shard_ignore_columns_regex_and_csv_to_mcf(self):
        rows = [
            {
                '#input': 'row1_debug',
                'tmp_note': 'scratch1',
                'observationAbout': 'dcid:geoId/06001',
                'variableMeasured': 'dcid:Count_Person',
                'observationDate': '2017-01',
                'value': '1000',
            },
            {
                '#input': 'row2_debug',
                'tmp_note': 'scratch2',
                'observationAbout': 'dcid:geoId/06001',
                'variableMeasured': 'dcid:Count_Person',
                'observationDate': '2017-02',
                'value': '2000',
            },
        ]
        self._create_csv_file(rows)

        # 1. CSV output with regex ignore patterns ('#input' and 'tmp_.*').
        csv_out = os.path.join(self.test_dir.name, 'ignored_cols@1.csv')
        shard_file(
            self.input_file_path,
            csv_out,
            {
                'shard_ignore_columns': ['#input', 'tmp_.*'],
            },
        )
        csv_rows = self._read_shards('ignored_cols', 1)[0]
        self.assertEqual(2, len(csv_rows))
        self.assertEqual(
            [
                'observationAbout',
                'variableMeasured',
                'observationDate',
                'value',
            ],
            list(csv_rows[0].keys()),
        )

        # 2. MCF output drops '#.*' columns by default and supports regex ignore
        #    and shard_add_columns with auto-generated StatVarObservation DCID.
        mcf_out = os.path.join(self.test_dir.name, 'csv_obs@1.mcf')
        shard_file(
            self.input_file_path,
            mcf_out,
            {
                'shard_ignore_columns': 'tmp_.*',
                'shard_add_columns':
                    'Node;typeOf=dcid:StatVarObservation;observationPeriod=P1M;'
                    'unit=$;measurementMethod=CACensus;scalingFactor=100',
            },
        )
        mcf_shard = os.path.join(self.test_dir.name,
                                 'csv_obs-00000-of-00001.mcf')
        text = self._read_text([mcf_shard])
        self.assertNotIn('#input', text)
        self.assertNotIn('tmp_note', text)
        # First row matches the exact DcidGeneratorTest.java golden StatVarObs DCID.
        self.assertIn('Node: dcid:dc/o/3mptcb1vdfvr5\n', text)
        self.assertIn('typeOf: dcid:StatVarObservation\n', text)

    def test_shard_add_columns_fixed_format_eval_and_auto_dcid(self):
        rows = [
            {
                '#input': 'raw_line_1',
                'state_fips': '06',
                'county_fips': '001',
                'sv': 'Count_Person',
                'date': 'Jan 2017',
                'v': '10',
            },
        ]
        self._create_csv_file(rows)
        output_path = os.path.join(self.test_dir.name, 'added_cols@1.csv')
        counters = counters_lib.Counters()
        shard_file(
            self.input_file_path,
            output_path,
            {
                'shard_ignore_columns':
                    '^#.*|.*_fips|sv|date|v',
                'shard_add_columns':
                    ';'.join([
                        'dcid',
                        'typeOf=dcid:StatVarObservation',
                        'observationAbout=dcid:geoId/{state_fips}{county_fips}',
                        'variableMeasured=dcid:{sv}',
                        "observationDate=format_date(date, '%Y-%m')",
                        'value=int(v) * 100',
                        'observationPeriod=P1M',
                        "unit='$'",
                        'measurementMethod=CACensus',
                        'scalingFactor=100',
                    ]),
            },
            counters=counters,
        )
        out_rows = self._read_shards('added_cols', 1)[0]
        self.assertEqual(1, len(out_rows))
        self.assertEqual(
            {
                'dcid': 'dc/o/3mptcb1vdfvr5',
                'typeOf': 'dcid:StatVarObservation',
                'observationAbout': 'dcid:geoId/06001',
                'variableMeasured': 'dcid:Count_Person',
                'observationDate': '2017-01',
                'value': '1000',
                'observationPeriod': 'P1M',
                'unit': '$',
                'measurementMethod': 'CACensus',
                'scalingFactor': '100',
            },
            out_rows[0],
        )
        self.assertEqual(1, counters.get_counter('shard-dcid-generated'))
        self.assertEqual(0, counters.get_counter('shard-output-column-errors'))

    def test_auto_generate_dcid_on_empty_dcid_column_without_flag(self):
        rows = [
            {
                'dcid': '',
                'observationAbout': 'dcid:geoId/06',
                'variableMeasured': 'dcid:Count_Person',
                'observationDate': '2020',
                'value': '39538223',
            },
            {
                'dcid': 'custom/obs_id',
                'observationAbout': 'dcid:geoId/06',
                'variableMeasured': 'dcid:Count_Person',
                'observationDate': '2020',
                'value': '39538223',
            },
        ]
        self._create_csv_file(rows)
        output_path = os.path.join(self.test_dir.name, 'auto_dcid@1.csv')
        counters = counters_lib.Counters()
        shard_file(self.input_file_path, output_path, {}, counters=counters)

        out_rows = self._read_shards('auto_dcid', 1)[0]
        self.assertEqual(2, len(out_rows))
        self.assertEqual('dc/o/xjmf6gpr46zzb', out_rows[0]['dcid'])
        self.assertEqual('custom/obs_id', out_rows[1]['dcid'])
        self.assertEqual(1, counters.get_counter('shard-dcid-generated'))

    def test_shard_output_columns_wildcard_and_format_template(self):
        rows = [
            {
                '#input': 'ignore_me',
                'observationAbout': 'dcid:geoId/06',
                'variableMeasured': 'dcid:Count_Person',
                'observationDate': '2020',
                'value': '39538223',
            },
        ]
        self._create_csv_file(rows)
        output_path = os.path.join(self.test_dir.name, 'wildcard@1.csv')
        shard_file(
            self.input_file_path,
            output_path,
            {
                'shard_ignore_columns': '#.*',
                'shard_output_columns':
                    'dcid;*;typeOf=dcid:StatVarObservation;'
                    'label={observationAbout}_{observationDate}',
            },
        )
        out_rows = self._read_shards('wildcard', 1)[0]
        self.assertEqual(1, len(out_rows))
        self.assertEqual(
            [
                'dcid',
                'observationAbout',
                'variableMeasured',
                'observationDate',
                'value',
                'typeOf',
                'label',
            ],
            list(out_rows[0].keys()),
        )
        self.assertEqual('dc/o/xjmf6gpr46zzb', out_rows[0]['dcid'])
        self.assertEqual('dcid:StatVarObservation', out_rows[0]['typeOf'])
        self.assertEqual('dcid:geoId/06_2020', out_rows[0]['label'])

    def test_jsonl_to_csv_add_columns_and_nested_fstrings(self):
        jsonl_path = os.path.join(self.test_dir.name, 'obs.jsonl')
        with open(jsonl_path, 'w') as f:
            f.write(
                json.dumps({
                    'tmp_ignore': 'x',
                    'Node': 'l:LocalObs1',
                    'observationAbout': 'dcid:geoId/06',
                    'variableMeasured': 'dcid:Count_Person',
                    'year': '2020',
                    'month': 'January',
                    'value': '39538223',
                }) + '\n')
        out_path = os.path.join(self.test_dir.name, 'jsonl_csv@1.csv')
        sharder = FileSharder(
            jsonl_path,
            out_path,
            {
                'shard_ignore_columns': 'tmp_.*|year|month',
                'shard_add_columns':
                    "Node;typeOf=dcid:StatVarObservation;"
                    "observationDate=format_date(f'{year}-{month}', '%Y-%m')",
            },
        )
        sharder.process()
        rows = self._read_shards('jsonl_csv', 1)[0]
        self.assertEqual(1, len(rows))
        self.assertNotIn('dcid', rows[0])
        self.assertNotIn('tmp_ignore', rows[0])
        self.assertTrue(rows[0]['Node'].startswith('dcid:dc/o/'))
        self.assertEqual('2020-01', rows[0]['observationDate'])
        self.assertEqual('dcid:geoId/06', rows[0]['observationAbout'])
        self.assertNotEqual('tmp_ignore', sharder._writer._shard_key)

    def test_auto_dcid_sharding_for_mcf_and_schema_vs_general_csv(self):
        # 1. Observation CSV where all rows share the same first columns
        #    ('typeOf' and 'observationAbout') and have no dcid/Node column.
        obs_rows = [{
            'typeOf': 'dcs:StatVarObservation',
            'observationAbout': 'dcid:geoId/06',
            'variableMeasured': f'dcid:Count_Person_{i}',
            'observationDate': '2020',
            'value': str(i * 100),
        } for i in range(20)]
        self._create_csv_file(obs_rows)

        # Sharding to .mcf without --shard_generate_dcid automatically generates
        # Node: dcid:dc/o/... and distributes across shards by that DCID.
        mcf_out = os.path.join(self.test_dir.name, 'auto_obs@4.mcf')
        mcf_counters = counters_lib.Counters()
        shard_file(self.input_file_path, mcf_out, {}, counters=mcf_counters)
        self.assertEqual(20, mcf_counters.get_counter('shard-dcid-generated'))

        mcf_shards = []
        for idx in range(4):
            shard_path = os.path.join(self.test_dir.name,
                                      f'auto_obs-{idx:05d}-of-00004.mcf')
            with McfFileDictIO(shard_path, 'r') as reader:
                nodes = reader.readlines()
                for node in nodes:
                    self.assertTrue(node['Node'].startswith('dcid:dc/o/'))
                mcf_shards.append(nodes)
        self.assertGreater(sum(1 for s in mcf_shards if s), 1)

        # Sharding the same observation CSV to .csv without --shard_generate_dcid
        # routes each row to the exact same shard using its generated DCID
        # without adding an unrequested 'dcid' column to the CSV output.
        csv_out = os.path.join(self.test_dir.name, 'auto_obs@4.csv')
        csv_counters = counters_lib.Counters()
        shard_file(self.input_file_path, csv_out, {}, counters=csv_counters)
        self.assertEqual(0, csv_counters.get_counter('shard-dcid-generated'))
        csv_shards = self._read_shards('auto_obs', 4)
        for idx in range(4):
            self.assertEqual(len(mcf_shards[idx]), len(csv_shards[idx]))
            for row in csv_shards[idx]:
                self.assertNotIn('dcid', row)
                self.assertNotIn('Node', row)

        # 2. General non-schema CSV sharded to .csv without shard_key or dcid
        #    does not generate DCIDs and routes by its first column ('id').
        general_rows = [
            {
                'id': 'key_1',
                'val': 'a'
            },
            {
                'id': 'key_2',
                'val': 'b'
            },
            {
                'id': 'key_1',
                'val': 'c'
            },
        ]
        self._create_csv_file(general_rows)
        gen_out = os.path.join(self.test_dir.name, 'general@3.csv')
        gen_counters = counters_lib.Counters()
        shard_file(self.input_file_path, gen_out, {}, counters=gen_counters)
        self.assertEqual(0, gen_counters.get_counter('shard-dcid-generated'))
        gen_shards = self._read_shards('general', 3)
        key1_shards = [
            idx for idx, s in enumerate(gen_shards)
            if any(r['id'] == 'key_1' for r in s)
        ]
        self.assertEqual(1, len(key1_shards))
        for r in sum(gen_shards, []):
            self.assertEqual(['id', 'val'], list(r.keys()))

        # 3. Heterogeneous MCF/JSONL records sharded to CSV/Avro preserve optional
        #    properties that appear only after the first record.
        hetero_jsonl = os.path.join(self.test_dir.name, 'hetero.jsonl')
        with open_dict_file(hetero_jsonl, 'w') as writer:
            writer.write({'dcid': 'n1', 'value': '10'})
            writer.write({'dcid': 'n2', 'value': '20', 'unit': 'USD'})
        hetero_csv_out = os.path.join(self.test_dir.name, 'hetero@2.csv')
        shard_file(hetero_jsonl, hetero_csv_out, {})
        hetero_rows = sum(self._read_shards('hetero', 2), [])
        self.assertCountEqual(
            [
                {
                    'dcid': 'n1',
                    'value': '10',
                    'unit': ''
                },
                {
                    'dcid': 'n2',
                    'value': '20',
                    'unit': 'USD'
                },
            ],
            hetero_rows,
        )


if __name__ == '__main__':
    unittest.main()
