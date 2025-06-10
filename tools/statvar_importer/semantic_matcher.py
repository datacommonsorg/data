# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utility for semantic text search using embeddings."""

import csv
import os
import pickle
import sys
import time

from absl import app
from absl import flags
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
_DATA_DIR = _SCRIPT_DIR.split('/data', 1)[0]
sys.path.append(os.path.join(_DATA_DIR, 'data', 'util'))

_FLAGS = flags.FLAGS

flags.DEFINE_string('semantic_matcher_corpus', '',
                    'Corpus file with key, value')
flags.DEFINE_string('semantic_matcher_cache',
                    'sample_schema_embeddings-all-MiniLM-L6-v2.pkl',
                    'Cache pickle file with corpus text and embeddings')
flags.DEFINE_string('semantic_matcher_input', '',
                    'Input file with lookup queries.')
flags.DEFINE_string('semantic_matcher_output', '',
                    'Output file with results per query.')
flags.DEFINE_string('semantic_matcher_model', 'all-MiniLM-L6-v2',
                    'Output file with results per query.')
flags.DEFINE_bool('semantic_matcher_debug', False, 'Enable debug logs.')

import file_util
import process_http_server

from config_map import ConfigMap
from counters import Counters


# Class to perform semantic search for text strings using embeddings.
# Uses embeddings to get semantic matches for a text query
# from a predefined list of keys.
#
# Example:
# matcher = SemanticMatcher()
# # Add key values for lookup.
# matcher.add_key_value('child', 'age: [- 17 Years]')
# matcher.add_key_value('adult', 'age: [18 - Years]')
#
# # Lookup key:value for query strings.
# results = matcher.lookup('boy')
# # Should return list of keys, values matching the lookup string
# # [ ('child', 'age: [- 17 Years]'), ]
class SemanticMatcher:

    def __init__(self, config: ConfigMap = None, counters: Counters = None):
        self._config = ConfigMap(get_semantic_matcher_default_config())
        if config:
            self._config.update_config(config.get_configs())
        self._counters = counters
        if self._counters is None:
            self._counters = Counters()

        # dict of {key: value} tuples.
        self._key_values = dict()
        self._corpus = list()
        self._corpus_embeddings = None

        # Embeddings matcher
        self._embedder = None
        cache_file = self._config.get('semantic_matcher_cache')
        if cache_file:
            self.load_corpus_cache(cache_file)

        # Cache of query embeddings.
        self._query_embeddings = dict()

    def load_corpus_cache(self, cache_file: str):
        """Load corpus text and embeddings from cache pickle file."""
        cache_files = file_util.file_get_matching(cache_file)
        if not cache_files:
            return
        cache_file = cache_files[0]
        logging.info(f'Loading sematic matcher cache {cache_file}')
        with file_util.FileIO(cache_file, 'rb') as file:
            cache = pickle.load(file)
        self._key_values = cache.get('key_values')
        self._corpus = cache.get('corpus')
        self._corpus_embeddings = cache.get('embeddings')
        logging.info(
            f'Loaded {len(self._corpus)} sentences from cache {cache_file}')
        self.init_transformer()

    def save_corpus_to_cache(self, cache_file: str):
        """Write corpus sentences and embeddings into cache."""
        if not cache_file:
            return

        cache = {}
        cache['key_values'] = self._key_values
        cache['corpus'] = self._corpus
        cache['embeddings'] = self._corpus_embeddings

        with file_util.FileIO(cache_file, 'wb') as file:
            pickle.dump(cache, file)
        logging.info(
            f'Wrote {len(self._corpus)} corpus sentences to cache {cache_file}')

    def add_key_value(self, key: str, value: str = ''):
        """Add a key:value for lookup corpus.
      Should be called before any lookups.
      """
        if self.is_initialized():
            logging.error(
                f'Cannot add key:value {key}:{value} for SemanticMatcher after init.'
            )
            return False
        values = self._key_values.get(key)
        if values:
            # Add value for an existing key
            if not isinstance(values, list):
                values = [values]
            if value in values:
                # Value already loaded.
                return True
            values.append(value)
            self._key_values[key] = values
        else:
            # Add value for a new key
            self._key_values[key] = value
            self._corpus.append(key)
        self._counters.add_counter('semantic_match_keys', 1)
        return True

    def init_transformer(self):
        """Initialize the transformer model and load embeddings for the keys.
        Initialized on first lookup if not called directly."""
        if self.is_initialized():
            return

        # Import modules needed when running SemanticMatcher
        # This is not imported in import-executor automation
        # that calls stvtar processor, but doesn't need semantic matching.
        from sentence_transformers import SentenceTransformer, util

        model = self._config.get('embeddings_model', 'all-MiniLM-L6-v2')
        logging.info(f'Creating SentenceTransformer with {model}')
        self._embedder = SentenceTransformer(model)
        self._semantic_search_util = util.semantic_search

        if self._corpus_embeddings is None:
            logging.info(
                f'Generating embeddings for corpus {len(self._corpus)}')
            self._corpus_embeddings = self.get_embeddings(self._corpus)
            self._counters.add_counter('semantic_matcher_corpus_embeddings',
                                       len(self._corpus))
            logging.info(
                f'Created corpus embeddings for {len(self._corpus)} keys')
            self.save_corpus_to_cache(
                self._config.get('semantic_matcher_cache'))

    def lookup(self, key: str, num_results: int = 10) -> list:
        """Returns a list of tuples [(key, value)...] matching the key.

      Args:
        key: string to lookup
        num_results: max results to return
      Returns
        list of tuples of (key, value) ordered by score.
      """
        self.init_transformer()
        if not key:
            return []

        # Get the query embeddings.
        query_embedding = self.get_query_embedding(key)
        if query_embedding is None:
            logging.error(f'Unable to get embeddings for query: {key}')
            return []

        # Lookup query embeddings in corpus
        start_time = time.perf_counter()
        matches = self._semantic_search_util(query_embedding,
                                             self._corpus_embeddings,
                                             top_k=num_results)
        end_time = time.perf_counter()
        logging.level_debug() and logging.debug(
            f'Got semantic search result for {key}: {matches}')
        if matches is None:
            self._counters.add_counter(f'semantic_search_lookup_failures', 1)
            return []

        # Get values for corpus matches
        results = []
        for match in matches[0]:
            corpus_id = match.get('corpus_id', '')
            key = self._corpus[corpus_id]
            value = self._key_values.get(key, None)
            if key and value is not None:
                results.append((key, value))

        # Update counters
        self._counters.add_counter(f'semantic_search_lookups', 1)
        self._counters.add_counter(
            f'semantic_search_lookup_results_{len(results)}', 1)
        query_time = end_time - start_time
        tot_query_time = self._counters.get_counter(
            'semantic_search_lookup_time')
        tot_query_time += query_time
        tot_lookups = self._counters.get_counter('semantic_search_lookups')
        avg_time = tot_query_time / tot_lookups
        self._counters.set_counter(f'semantic_search_avg_lookup_time', avg_time)
        return results

    def get_query_embedding(self, key: str) -> str:
        """Returns the embedding for the query, building it if not set in cache."""
        query_embedding = self._query_embeddings.get(key)
        if query_embedding is not None:
            self._counters.add_counter('semantic_matcher_query_cache_hits', 1)
            return query_embedding

        # Create embeddings for the query.
        query_embedding = self.get_embeddings(key)
        self._query_embeddings[key] = query_embedding
        self._counters.add_counter('semantic_matcher_query_embeddings', 1)
        return query_embedding

    def get_embeddings(self, text) -> str:
        """Returns the embeddings for the text."""
        start_time = time.perf_counter()
        embeddings = self._embedder.encode(text, convert_to_tensor=True)
        end_time = time.perf_counter()
        self._counters.add_counter(f'semantic_matcher_encode_time',
                                   end_time - start_time)
        self._counters.add_counter(f'semantic_matcher_encode_calls', 1)
        return embeddings

    # Returns True if sentence transformer is initialized.
    # More key values cannot be added once initialized.
    def is_initialized(self):
        return self._embedder is not None


def get_semantic_matcher_default_config() -> dict:
    """Get default config for semantic_matcher."""
    # Use default values of flags for tests
    if not _FLAGS.is_parsed():
        _FLAGS.mark_as_parsed()
    return {
        'embeddings_model': _FLAGS.semantic_matcher_model,
        'semantic_matcher_cache': _FLAGS.semantic_matcher_cache,
    }


def semantic_matcher_lookup(corpus_file: str,
                            input_file: str,
                            output_file: str,
                            config: ConfigMap = None,
                            counters: Counters = None):
    """Lookup queries in the corpus."""
    if counters is None:
        counters = Counters()
    semantic_matcher = SemanticMatcher(config, counters)

    # Load corpus of key,values into semantic_matcher
    if not semantic_matcher.is_initialized():
        corpus_dict = file_util.file_load_py_dict(corpus_file)
        logging.info(
            f'Adding {len(corpus_dict)} keys from {corpus_file} into semantic matcher.'
        )
        for key, values in corpus_dict.items():
            value = values
            if isinstance(values, dict):
                # Convert value to comma seperated list of key:values.
                value = ','.join([f'{k}:{v}' for k, v in values])
            else:
                value = str(values)
            semantic_matcher.add_key_value(key, value)
    else:
        logging.info(f'Using corpus from semantic_matcher_cache')

    # Lookup queries in semantic_matcher
    queries = file_util.file_load_py_dict(input_file)
    logging.info(f'Looking up {len(queries)} queries from {input_file}')
    results = {}
    counters.add_counter('total', len(queries))
    for query in queries.keys():
        matches = semantic_matcher.lookup(query)
        result = {}
        for kv in matches:
            k, v = kv
            result_index = len(result) / 2
            result[f'key_{result_index}'] = k
            result[f'value_{result_index}'] = v
        results[query] = result
        counters.add_counter('processed', 1)

    if output_file:
        file_util.file_write_py_dict(results, output_file)
    else:
        # Print the results.
        for key, result in results.items():
            print(f'{key}: {result}')


def main(_):
    # Launch a web server if --http_port is set.
    if process_http_server.run_http_server(script=__file__, module=__name__):
        return

    if _FLAGS.semantic_matcher_debug:
        logging.set_verbosity(2)

    semantic_matcher_lookup(
        _FLAGS.semantic_matcher_corpus,
        _FLAGS.semantic_matcher_input,
        _FLAGS.semantic_matcher_output,
    )


if __name__ == '__main__':
    app.run(main)
