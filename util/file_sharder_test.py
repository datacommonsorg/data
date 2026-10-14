import unittest
from unittest import mock
import os
import tempfile
import csv
from absl import logging
from file_sharder import FileSharder, shard_file
from file_dict_io import McfFileDictIO
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
                    {'id': f'k_{idx}_0', 'val': 'v0'},
                    {'id': f'k_{idx}_1', 'val': 'v1'},
                    {'id': 'shared_dup', 'val': 'same'},
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
                'shard_default_pvs': {'typeOf': 'dcs:StatVarObservation'},
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
                writer.writerows([f'geoId/{row}', str(row)] for row in range(30))
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
            {'dcid': 'geoId/06', 'typeOf': 'State', 'value': '1'},
            {'dcid': 'geoId/07', 'typeOf': 'State', 'value': '2'},
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
            {'Node': 'dcid:node11', 'name': '"a"'},
            {'Node': 'dcid:node22', 'name': '"b"'},
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
            {'Node': 'dcid:geoId/06', 'dcid': '', 'value': '1'},
            {'Node': '', 'dcid': '', 'value': '2'},
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
            ({'a': 'b', 'c': 'd'}, '[["a","b"],["c","d"]]', 'dc/l04l0vn731e83'),
            # Joining 'prop=value' strings gave this the same key as above.
            ({'a': 'bc=d'}, '[["a","bc=d"]]', 'dc/rpfyqsbsyh9f5'),
            ({
                'typeOf': 'dcs:StatVarObservation',
                'observationAbout': 'dcid:geoId/06',
                'variableMeasured': 'dcid:Count_Person',
                'observationDate': '2020',
                'value': '39538223',
            }, '[["observationAbout","geoId/06"],["observationDate","2020"],'
             '["typeOf","StatVarObservation"],["value","39538223"],'
             '["variableMeasured","Count_Person"]]', 'dc/o/p0qc9ky5qdfxg'),
            # A StatVarObservation without typeOf.
            ({
                'observationAbout': 'geoId/06',
                'variableMeasured': 'Count_Person',
                'observationDate': '2020',
                'value': '39538223',
            }, '[["observationAbout","geoId/06"],["observationDate","2020"],'
             '["value","39538223"],["variableMeasured","Count_Person"]]',
             'dc/o/tndkksp8x9778'),
            # Only '"', '\' and control characters are escaped in the key.
            ({
                'typeOf': 'dcs:Place',
                'note': 'x "y" \\ é/<&\t'
            }, r'[["note","x \"y\" \\ é/<&\t"],["typeOf","Place"]]',
             'dc/gv36cv9v6z367'),
        ]
        for record, key, dcid in vectors:
            self.assertEqual(dcid, file_sharder.generate_node_dcid(record),
                             record)
            self.assertEqual(
                dcid.rsplit('/', 1)[1], file_sharder._get_long_id(key), key)


if __name__ == '__main__':
    unittest.main()
