# Copyright 2023 Google LLC
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
"""Class to match sub-strings using ngrams.

Example:
  # Load the matcher with search-key: values
  matcher = NgramMatcher({'ngram-size': 4})
  matcher.add_key_value('California', 'dcid:geoId/06')
  matcher.add_key_value('San Jose California', 'dcid:geoId/0668000')
  matcher.add_key_value('San Jose Costa Rica', 'dcid:wikidataId/Q647808')

  # Look for matching keys
  results = matcher.lookup('SanJose')
  # returns a ranked list of (key, value) tuples:
  # [('San Jose California', 'dcid:geoId/0668000'), ('San Jose Costa Rica',
  'dcid:wikidataId/Q647808')]

  # To get top 10 results with match details:
  results = matcher.lookup('SanJose', 10, True)
  # Returns a list of tuples with (key, <details>):
  # [(<key>, { 'value': <value>, 'info': {'score': 1.2, 'ngram_matches': 3} }),
  # ...]
"""

import unicodedata

from absl import logging

# Default configuration settings for NgramMatcher
_DEFAULT_CONFIG = {
    'ngram_size': 4,
    'ignore_non_alphanum': True,
    'min_match_fraction': 0.8,
}


class NgramMatcher:

    def __init__(self, config: dict = {}):
        self._config = dict(_DEFAULT_CONFIG)
        if config:
            self._config.update(config)
        self._ngram_size = self._config.get('ngram_size', 4)
        # List of (key, value) tuples.
        self._key_values = list()
        # Dictionary of ngram to set of string ids that contain the ngram.
        # { '<ngram>': { (id1, pos1), (id2, pos2), ...}, ...}
        self._ngram_dict = {}

    def get_tuples_count(self):
        return len(self._key_values)

    def get_key_values(self):
        return dict(self._key_values)

    def add_keys_values(self, kvs: dict[str, any]) -> None:
        for key, value in kvs.items():
            self.add_key_value(key, value)

    def add_key_value(self, key: str, value):
        """Add a key and value.

    When the key matches a lookup string, the key and corresponding value is
    returned.

    Args:
      key: string to be looked up
      value: value to be returned on key match.
    """
        self._key_values.append((key, value))
        key_index = len(self._key_values) - 1
        self._add_key_index(key, key_index)

    def get_ngrams_count(self) -> int:
        """Returns the number of ngrams in the index."""
        return len(self._ngram_dict)

    def lookup(
        self,
        key: str,
        num_results: int = None,
        return_score: bool = False,
        config: dict = None,
    ) -> list:
        """Lookup a key string.

    Returns an ordered list of (key, value) tuples matching the key.
    """
        normalized_key = self._normalize_string(key)
        ngrams = self._get_ngrams(normalized_key)
        logging.level_debug() and logging.log(
            2, f'looking up ngrams {ngrams} for {key}')
        lookup_config = self._config
        if config:
            # Use the match config passed in.
            lookup_config = dict(self._config)
            lookup_config.update(config)
        # Get the matching key indices for all ngrams.
        matches = dict()
        for ngram in ngrams:
            ngram_matches = self._ngram_dict.get(ngram, {})
            if ngram_matches:
                # Use IDF score for each ngram
                ngram_score = 1 / len(ngram_matches)
                for key_index, ngram_pos in ngram_matches:
                    # Collect matches and update score for each ngram
                    if key_index not in matches:
                        matches[key_index] = {
                            'score': ngram_score,
                            'ngram_matches': 1,
                            'ngram_pos': ngram_pos,
                        }
                    else:
                        key_match = matches[key_index]
                        key_match['score'] = key_match['score'] + ngram_score
                        key_match[
                            'ngram_matches'] = key_match['ngram_matches'] + 1
                        key_match['ngram_pos'] = min(key_match['ngram_pos'],
                                                     ngram_pos)

        logging.level_debug() and logging.log(2,
                                              f'Matches for {key}: {matches}')
        # Collect all key indices that matches with counts.
        match_indices = list()
        min_matches = max(
            1,
            len(ngrams) * lookup_config.get('min_match_fraction', 0.8))
        for key_index, result in matches.items():
            if result['ngram_matches'] >= min_matches:
                match_indices.append((key_index, result))

        # Order key_index by decreasing number of matches.
        key_len = len(normalized_key)
        match_indices.sort(
            key=lambda x: self._get_ngram_match_score(x[1], key_len),
            reverse=True)
        logging.level_debug() and logging.log(
            2, f'Sorted matches for {key}: {match_indices}')

        # Collect results in sorted order
        results = list()
        for match in match_indices:
            result_key, result_value = self._key_values[match[0]]
            if return_score:
                results.append((result_key, {
                    'value': result_value,
                    'info': match[1]
                }))
            else:
                results.append((result_key, result_value))
            if num_results and len(results) >= num_results:
                # There are enough results. Return these.
                break
        return results

    def _get_ngrams(self, key: str) -> list:
        """Returns a list of ngrams for the key."""
        normalized_key = self._normalize_string(key)
        ngrams = normalized_key.split(' ')
        max_index = max(len(normalized_key) - self._ngram_size, 0) + 1
        for pos in range(max_index):
            ngram = normalized_key[pos:pos + self._ngram_size]
            if ngram not in ngrams:
                ngrams.append(ngram)
        return ngrams

    def _add_key_index(self, key: str, key_index: int):
        """Adds the key into the ngrams index."""
        # Remove extra characters and convert to lower case.
        normalized_key = self._normalize_string(key)
        # index by all unique ngrams in the key
        ngrams = self._get_ngrams(normalized_key)
        for ngram in ngrams:
            if ngram not in self._ngram_dict:
                self._ngram_dict[ngram] = set()
            ngram_pos = normalized_key.find(ngram)
            self._ngram_dict[ngram].add((key_index, ngram_pos))
            logging.level_debug() and logging.log(
                3, f'Added ngram "{ngram}" for {key}:{key_index}')

    def _normalize_string(self, key: str) -> str:
        """Returns a normalized string removing special characters"""
        return normalized_string(key,
                                 self._config.get('ignore_non_alphanum', True))

    def _get_ngram_match_score(self, match: dict, key_len: int) -> float:
        """Returns a score for the ngram match components."""
        # IDF score
        score = match['score']
        # Boost for match at the beginning of the key.
        score += (key_len - match['ngram_pos']) * 10000
        # DF score
        score += match['ngram_matches'] * 100
        return score


def normalized_string(key: str, ignore_non_alnum: bool = True) -> str:
    """Returns a normalized string for match.

    Args:
      key: string to be normalized.
      ignore_non_alnum: if True, non alpha numeric characters are removed.

    Returns:
      normalized string
    """
    normalized_key = unicodedata.normalize('NFKD', key)
    normalized_key = normalized_key.lower()
    # Remove extra spaces
    normalized_key = ' '.join([w for w in normalized_key.split(' ') if w])
    # Remove extra punctuation.
    if ignore_non_alnum:
        normalized_key = ''.join(
            [c for c in normalized_key if c.isalnum() or c == ' '])
    return normalized_key
