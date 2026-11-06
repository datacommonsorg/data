# Copyright 2025 Google LLC
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
"""Utility functions to generate deterministic DCIDs for MCF nodes.

Replicates Data Commons DCID generation from `datacommonsorg/import`
(`DcidGenerator.java`) for `StatVarObservation`, `StatisticalVariable`, and
`Place` nodes using 64-bit FarmHash fingerprints and base-32 encoding, while
supporting normalized general MCF node DCIDs (`dc/<id>`).
"""

import json
import os
import re
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(
    os.path.join(os.path.dirname(_SCRIPT_DIR), 'tools', 'statvar_importer'))

from file_dict_io import str_to_int_hash
import mcf_file_util

# Base32 encoding map and bit constants (matching DcidGenerator.java)
DCID_BASE32_MAP = '0123456789bcdfghjklmnpqrstvwxyze'
MAX_LONG_ID_LEN = 13
MAX_NUM_BITS = 5

# 64-bit FarmHash constants (matching Guava FarmHashFingerprint64)
_FARMHASH_K0 = 0xc3a5c85c97cb3127
_FARMHASH_K1 = 0xb492b66fbe98f273
_FARMHASH_K2 = 0x9ae16a3b2f90404f
_UINT64_MASK = 0xFFFFFFFFFFFFFFFF

# Default ignored properties when generating DCIDs for nodes
DCID_IGNORE_PROPS = frozenset({
    'Node',
    'dcid',
    'name',
    'description',
    'descriptionUrl',
    'alternateName',
    'nameWithLanguage',
    'DisplayName',
    'shortDisplayName',
    'label',
    'url',
    'definition',
    'utteranceTemplate',
    'source',
    'footnote',
    'constraintProperties',
    'member',
    'memberOf',
    'linkedMember',
    'linkedMemberOf',
    'ChildOf',
    'relevantVariable',
    'provenance',
    'isPublic',
    'isNormalizable',
    'denominatorForNormalization',
    'observationProperties',
    'keyString',
    'resMCFFile',
    'localCuratorLevelId',
    'censusACSTableId',
})

# Ordered key properties for StatVarObservation DCID generation
# (matching DcidGenerator.ORDERED_STAT_VAR_OBS_KEY_PROPS in datacommonsorg/import)
ORDERED_STAT_VAR_OBS_KEY_PROPS = (
    'observationAbout',
    'variableMeasured',
    'observationDate',
    'value',
    'observationPeriod',
    'unit',
    'measurementMethod',
    'scalingFactor',
)
REQUIRED_STAT_VAR_OBS_KEY_PROPS = frozenset({
    'observationAbout',
    'variableMeasured',
    'observationDate',
    'value',
})

# Fixed and non-constraint properties for StatisticalVariable DCID generation
FIXED_STAT_VAR_PROPS = frozenset({
    'typeOf',
    'populationType',
    'popType',
    'measuredProperty',
    'statType',
    'measurementQualifier',
    'measurementDenominator',
})

NON_CONSTRAINT_STAT_VAR_PROPERTIES = frozenset(
    DCID_IGNORE_PROPS | {
        'populationGroup',
        'location',
        'childhoodLocation',
        'measurementMethod',
        'scalingFactor',
        'unit',
    })

# Place types and ordered assignable ID properties
# (matching Vocabulary.PLACE_TYPES and PLACE_RESOLVABLE_AND_ASSIGNABLE_IDS)
PLACE_TYPES = frozenset({
    'Place',
    'Continent',
    'Country',
    'State',
    'Province',
    'County',
    'City',
    'StateComponent',
    'CensusCoreBasedStatisticalArea',
    'USMetropolitanDivision',
    'CensusCountyDivision',
    'CensusTract',
    'CensusBlockGroup',
    'CensusZipCodeTabulationArea',
    'CongressionalDistrict',
    'SchoolDistrict',
    'ElementarySchoolDistrict',
    'HighSchoolDistrict',
    'CommutingZone',
    'Borough',
    'Town',
    'Village',
    'Neighborhood',
    'EurostatNUTS1',
    'EurostatNUTS2',
    'EurostatNUTS3',
    'AdministrativeArea',
    'AdministrativeArea1',
    'AdministrativeArea2',
    'AdministrativeArea3',
    'AdministrativeArea4',
    'AdministrativeArea5',
    'CollegeOrUniversity',
})

PLACE_RESOLVABLE_AND_ASSIGNABLE_IDS = (
    'unDataCode',
    'geoId',
    'isoCode',
    'nutsCode',
    'wikidataId',
    'geoNamesId',
    'istatId',
    'austrianMunicipalityKey',
    'indianCensusAreaCode2011',
    'indianCensusAreaCode2001',
    'lgdCode',
    'udiseCode',
    'fips52AlphaCode',
    'countryAlpha3Code',
    'countryNumericCode',
    'ipedsId',
    'ncesId',
)

_PLACE_ID_PREFIX_MAP = {
    'isoCode': 'iso',
    'nutsCode': 'nuts',
}

_ZERO_NUMERIC_RE = re.compile(r'^[+-]?(?:0+(?:\.0*)?|\.0+)$')


def _u64(val: int) -> int:
    return val & _UINT64_MASK


def _load64(data: bytes, pos: int) -> int:
    return int.from_bytes(data[pos:pos + 8], 'little')


def _load32(data: bytes, pos: int) -> int:
    return int.from_bytes(data[pos:pos + 4], 'little')


def _rotr64(val: int, shift: int) -> int:
    val &= _UINT64_MASK
    return ((val >> shift) | (val << (64 - shift))) & _UINT64_MASK


def _shift_mix(val: int) -> int:
    val &= _UINT64_MASK
    return (val ^ (val >> 47)) & _UINT64_MASK


def _hash_len_16(u: int, v: int, mul: int) -> int:
    a = _u64((u ^ v) * mul)
    a ^= (a >> 47)
    b = _u64((v ^ a) * mul)
    b ^= (b >> 47)
    return _u64(b * mul)


def _weak_hash_len_32_with_seeds(
    data: bytes,
    offset: int,
    seed_a: int,
    seed_b: int,
) -> tuple[int, int]:
    w = _load64(data, offset)
    x = _load64(data, offset + 8)
    y = _load64(data, offset + 16)
    z = _load64(data, offset + 24)
    a = _u64(seed_a + w)
    b_val = _rotr64(_u64(seed_b + a + z), 21)
    c = a
    a = _u64(a + x)
    a = _u64(a + y)
    b_val = _u64(b_val + _rotr64(a, 44))
    return (_u64(a + z), _u64(b_val + c))


def farmhash_fingerprint64(data: bytes | str) -> int:
    """Computes the 64-bit unsigned FarmHash fingerprint of `data`.

    Matches `com.google.common.hash.Hashing.farmHashFingerprint64()` in Guava
    and `util::Fingerprint64` in C++ FarmHash (`farmhashna`).

    Args:
      data: UTF-8 string or bytes to hash.

    Returns:
      64-bit unsigned integer fingerprint.
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    length = len(data)
    if length <= 16:
        if length >= 8:
            mul = _u64(_FARMHASH_K2 + length * 2)
            a = _u64(_load64(data, 0) + _FARMHASH_K2)
            b = _load64(data, length - 8)
            c = _u64(_rotr64(b, 37) * mul + a)
            d = _u64((_rotr64(a, 25) + b) * mul)
            return _hash_len_16(c, d, mul)
        if length >= 4:
            mul = _u64(_FARMHASH_K2 + length * 2)
            a = _load32(data, 0)
            return _hash_len_16(
                _u64(length + (a << 3)),
                _load32(data, length - 4),
                mul,
            )
        if length > 0:
            a = data[0]
            b = data[length >> 1]
            c = data[length - 1]
            y = a + (b << 8)
            z = length + (c << 2)
            return _u64(
                _shift_mix(_u64(y * _FARMHASH_K2) ^ _u64(z * _FARMHASH_K0)) *
                _FARMHASH_K2)
        return _FARMHASH_K2

    if length <= 32:
        mul = _u64(_FARMHASH_K2 + length * 2)
        a = _u64(_load64(data, 0) * _FARMHASH_K1)
        b = _load64(data, 8)
        c = _u64(_load64(data, length - 8) * mul)
        d = _u64(_load64(data, length - 16) * _FARMHASH_K2)
        return _hash_len_16(
            _u64(_rotr64(_u64(a + b), 43) + _rotr64(c, 30) + d),
            _u64(a + _rotr64(_u64(b + _FARMHASH_K2), 18) + c),
            mul,
        )

    if length <= 64:
        mul = _u64(_FARMHASH_K2 + length * 2)
        a = _u64(_load64(data, 0) * _FARMHASH_K2)
        b = _load64(data, 8)
        c = _u64(_load64(data, length - 8) * mul)
        d = _u64(_load64(data, length - 16) * _FARMHASH_K2)
        y = _u64(_rotr64(_u64(a + b), 43) + _rotr64(c, 30) + d)
        z = _hash_len_16(
            y,
            _u64(a + _rotr64(_u64(b + _FARMHASH_K2), 18) + c),
            mul,
        )
        e = _u64(_load64(data, 16) * mul)
        f = _load64(data, 24)
        g = _u64((y + _load64(data, length - 32)) * mul)
        h = _u64((z + _load64(data, length - 24)) * mul)
        return _hash_len_16(
            _u64(_rotr64(_u64(e + f), 43) + _rotr64(g, 30) + h),
            _u64(e + _rotr64(_u64(f + a), 18) + g),
            mul,
        )

    seed = 81
    x = seed
    y = _u64(seed * _FARMHASH_K1 + 113)
    z = _u64(_shift_mix(_u64(y * _FARMHASH_K2 + 113)) * _FARMHASH_K2)
    v0, v1 = 0, 0
    w0, w1 = 0, 0
    x = _u64(x * _FARMHASH_K2 + _load64(data, 0))
    end = ((length - 1) // 64) * 64
    last64 = end + ((length - 1) & 63) - 63
    offset = 0
    while True:
        x = _u64(
            _rotr64(_u64(x + y + v0 + _load64(data, offset + 8)), 37) *
            _FARMHASH_K1)
        y = _u64(
            _rotr64(_u64(y + v1 + _load64(data, offset + 48)), 42) *
            _FARMHASH_K1)
        x ^= w1
        y = _u64(y + v0 + _load64(data, offset + 40))
        z = _u64(_rotr64(_u64(z + w0), 33) * _FARMHASH_K1)
        v0, v1 = _weak_hash_len_32_with_seeds(
            data,
            offset,
            _u64(v1 * _FARMHASH_K1),
            _u64(x + w0),
        )
        w0, w1 = _weak_hash_len_32_with_seeds(
            data,
            offset + 32,
            _u64(z + w1),
            _u64(y + _load64(data, offset + 16)),
        )
        x, z = z, x
        offset += 64
        if offset == end:
            break

    mul = _u64(_FARMHASH_K1 + ((z & 0xff) << 1))
    offset = last64
    w0 = _u64(w0 + ((length - 1) & 63))
    v0 = _u64(v0 + w0)
    w0 = _u64(w0 + v0)
    x = _u64(_rotr64(_u64(x + y + v0 + _load64(data, offset + 8)), 37) * mul)
    y = _u64(_rotr64(_u64(y + v1 + _load64(data, offset + 48)), 42) * mul)
    x ^= _u64(w1 * 9)
    y = _u64(y + _u64(v0 * 9) + _load64(data, offset + 40))
    z = _u64(_rotr64(_u64(z + w0), 33) * mul)
    v0, v1 = _weak_hash_len_32_with_seeds(
        data,
        offset,
        _u64(v1 * mul),
        _u64(x + w0),
    )
    w0, w1 = _weak_hash_len_32_with_seeds(
        data,
        offset + 32,
        _u64(z + w1),
        _u64(y + _load64(data, offset + 16)),
    )
    return _hash_len_16(
        _u64(
            _hash_len_16(v0, w0, mul) + _u64(_shift_mix(y) * _FARMHASH_K0) + x),
        _u64(_hash_len_16(v1, w1, mul) + z),
        mul,
    )


def base32_encode_uint64(value: int) -> str:
    """Encodes a 64-bit unsigned integer into up to 13 DC base32 characters."""
    val = value & _UINT64_MASK
    chars = []
    for _ in range(MAX_LONG_ID_LEN):
        chars.append(DCID_BASE32_MAP[val & 0x1F])
        val >>= MAX_NUM_BITS
        if val == 0:
            break
    return ''.join(chars)


def get_long_id(key_string: str) -> str:
    """Computes the FarmHash64 base32 ID for `key_string` (matching DcidGenerator.getLongId)."""
    return base32_encode_uint64(farmhash_fingerprint64(key_string))


def get_sha256_long_id(key_string: str) -> str:
    """Computes a cross-language portable SHA-256 64-bit base32 ID for `key_string`."""
    return base32_encode_uint64(str_to_int_hash(key_string))


_MCF_NAMESPACE_PREFIXES = ('dcid:', 'dcs:', 'schema:')


def _strip_mcf_namespace(val_str: str) -> str:
    """Strips only known MCF namespaces (`dcid:`, `dcs:`, `schema:`) from unquoted strings."""
    if not val_str:
        return ''
    s = val_str.strip()
    if s.startswith('"') and s.endswith('"') and len(s) >= 2:
        return s[1:-1].strip()
    for prefix in _MCF_NAMESPACE_PREFIXES:
        if s.startswith(prefix):
            return s[len(prefix):].strip()
    return s


def _clean_scalar_value(raw_val) -> str:
    """Normalizes a raw scalar value to string, preserving numeric zero."""
    if raw_val is None:
        return ''
    if isinstance(raw_val, bool):
        return str(raw_val)
    if isinstance(raw_val, (int, float)) and raw_val == 0:
        return '0'
    if isinstance(raw_val, list):
        return '' if not raw_val else _clean_scalar_value(raw_val[0])
    val_str = str(raw_val).strip(' "')
    if not val_str:
        return ''
    if _ZERO_NUMERIC_RE.match(val_str):
        return '0'
    return val_str


def _has_local_ref(raw_val) -> bool:
    """Returns True if `raw_val` contains an unresolved `l:` local reference."""
    if raw_val is None or isinstance(raw_val, (bool, int, float)):
        return False
    for item in mcf_file_util.get_value_list(raw_val):
        raw_item = str(item).strip()
        if raw_item.startswith('"') and raw_item.endswith('"'):
            continue
        v_str = raw_item.strip(' "')
        if v_str.startswith('l:'):
            return True
        if _strip_mcf_namespace(v_str).strip(' "').startswith('l:'):
            return True
    return False


def generate_place_dcid(
    record: dict,
    ignore_props: set[str] | frozenset[str] = None,
) -> str:
    """Generates a DCID for a Place node using `PLACE_RESOLVABLE_AND_ASSIGNABLE_IDS`.

    Replicates `DcidGenerator.forPlace` from `datacommonsorg/import`:
    inspects `PLACE_RESOLVABLE_AND_ASSIGNABLE_IDS` in priority order and
    returns `<prefix>/<value>` (using `'iso'` for `'isoCode'`, `'nuts'` for
    `'nutsCode'`, and `<prop>` otherwise). Returns `''` if no assignable place
    ID property is present or if its value is an unresolved local reference.

    Args:
      record: Dictionary of property-value pairs for the node.
      ignore_props: Optional set of property names to skip.

    Returns:
      Generated place DCID (e.g. `'geoId/06001'`, `'nuts/DE1'`,
      `'wikidataId/Q62'`), or `''` if no assignable ID property is present.
    """
    if not record:
        return ''
    ignored = ignore_props or frozenset()
    for prop in PLACE_RESOLVABLE_AND_ASSIGNABLE_IDS:
        if prop in ignored or prop not in record:
            continue
        raw_val = record.get(prop)
        val_str = _clean_scalar_value(raw_val)
        if not val_str:
            continue
        if _has_local_ref(raw_val):
            return ''
        clean_val = _strip_mcf_namespace(str(raw_val).strip()).strip(' "')
        if not clean_val or clean_val.startswith('l:'):
            continue
        prefix = _PLACE_ID_PREFIX_MAP.get(prop, prop)
        if clean_val.startswith(f'{prefix}/'):
            return clean_val
        return f'{prefix}/{clean_val}'
    return ''


def generate_statvar_obs_dcid(
    record: dict,
    ignore_props: set[str] | frozenset[str] = None,
) -> str:
    """Generates a deterministic DCID for a `StatVarObservation` node.

    Replicates `DcidGenerator.forStatVarObs` from `datacommonsorg/import`:
      1. Inspects `ORDERED_STAT_VAR_OBS_KEY_PROPS` in fixed order:
         `observationAbout`, `variableMeasured`, `observationDate`, `value`,
         `observationPeriod`, `unit`, `measurementMethod`, `scalingFactor`.
      2. Requires `observationAbout`, `variableMeasured`, `observationDate`,
         and `value` (unless explicitly listed in `ignore_props`).
      3. Rejects multi-valued properties or unresolved local references (`l:`).
      4. Strips quotes and MCF namespaces (`dcid:`, `dcs:`, `schema:`), joins
         `f'{prop}={val}'` with `''`, and hashes with 64-bit FarmHash + base32
         under the `'dc/o/'` prefix.

    Args:
      record: Dictionary of property-value pairs for the observation node.
      ignore_props: Optional set of property names to exclude from the key.

    Returns:
      Generated DCID string (`'dc/o/<id>'`), or `''` if required properties
      are missing, multi-valued, or contain unresolved local references (`l:`).
    """
    if not record:
        return ''
    ignored = ignore_props or frozenset()
    key_parts = []
    for prop in ORDERED_STAT_VAR_OBS_KEY_PROPS:
        if prop in ignored:
            continue
        raw_val = record.get(prop)
        if isinstance(raw_val, list):
            if len(raw_val) > 1:
                return ''
            raw_val = raw_val[0] if raw_val else None
        val_str = _clean_scalar_value(raw_val)
        if not val_str:
            if prop in REQUIRED_STAT_VAR_OBS_KEY_PROPS:
                return ''
            continue
        raw_str = str(raw_val).strip()
        if ',' in raw_str and len(mcf_file_util.get_value_list(raw_str)) != 1:
            return ''
        if _has_local_ref(raw_val):
            return ''
        clean_val = _strip_mcf_namespace(raw_str).strip(' "')
        if _ZERO_NUMERIC_RE.match(clean_val):
            clean_val = '0'
        if not clean_val:
            if prop in REQUIRED_STAT_VAR_OBS_KEY_PROPS:
                return ''
            continue
        if clean_val.startswith('l:'):
            return ''
        key_parts.append(f'{prop}={clean_val}')

    if not key_parts:
        return ''
    key_string = ''.join(key_parts)
    return f'dc/o/{get_long_id(key_string)}'


def generate_statvar_hash_dcid(
    record: dict,
    ignore_props: set[str] | frozenset[str] = None,
) -> str:
    """Generates a deterministic hashed DCID (`dc/<id>`) for a `StatisticalVariable` node.

    Replicates `DcidGenerator.forStatVar` from `datacommonsorg/import`:
    retains `FIXED_STAT_VAR_PROPS` and constraint properties (converting
    quantity ranges like `[Years 16 -]` to `Years16Onwards`), sorts
    `f'{prop}={val}'` alphabetically by property name, joins with `''`, and
    hashes with 64-bit FarmHash + base32.

    Args:
      record: Dictionary of property-value pairs for the StatisticalVariable.
      ignore_props: Optional set of additional property names to ignore.

    Returns:
      Generated DCID (`'dc/<id>'`), or `''` if required properties are missing
      or an unresolved local reference (`l:`) is present.
    """
    if not record:
        return ''
    ignored = (ignore_props or frozenset()) | (
        NON_CONSTRAINT_STAT_VAR_PROPERTIES - FIXED_STAT_VAR_PROPS)

    sv_record = dict(record)
    if 'typeOf' not in sv_record and 'typeOf' not in ignored:
        sv_record['typeOf'] = 'StatisticalVariable'

    sorted_props = []
    for prop in sorted(sv_record.keys()):
        if not prop or str(prop).startswith('#') or prop in ignored:
            continue
        raw_val = sv_record.get(prop)
        val_str = _clean_scalar_value(raw_val)
        if not val_str:
            continue
        if _has_local_ref(raw_val):
            return ''
        values = mcf_file_util.get_value_list(raw_val)
        clean_vals = []
        for v in values:
            raw_v = str(v).strip()
            v_str = raw_v.strip(' "')
            if not v_str:
                continue
            if v_str.startswith('[') and v_str.endswith(']'):
                v_str = mcf_file_util.normalize_range(
                    v_str, quantity_range_to_dcid=True)
                v_clean = _strip_mcf_namespace(v_str).strip(' "')
            else:
                v_clean = _strip_mcf_namespace(raw_v).strip(' "')
            if v_clean.startswith('l:'):
                return ''
            clean_vals.append(v_clean)
        if not clean_vals:
            continue
        clean_vals.sort()
        sorted_props.append((prop, clean_vals))

    if not sorted_props:
        return ''
    present_props = {prop for prop, _ in sorted_props}
    if ('measuredProperty' not in ignored and
            'measuredProperty' not in present_props):
        return ''
    if ('populationType' not in ignored and 'popType' not in ignored and
            'populationType' not in present_props and
            'popType' not in present_props):
        return ''
    key_parts = []
    for prop, vals in sorted_props:
        for val in vals:
            key_parts.append(f'{prop}={val}')
    key_string = ''.join(key_parts)
    return f'dc/{get_long_id(key_string)}'


def generate_node_dcid(
    record: dict,
    ignore_props: set[str] | frozenset[str] = DCID_IGNORE_PROPS,
) -> str:
    r"""Generates a deterministic DCID for `record`.

    Dispatches by node type while preserving full normalization for general MCF
    nodes:
      - `StatVarObservation` (when `typeOf` is `StatVarObservation`, or when
        `observationAbout` and `variableMeasured` are present with no `typeOf`):
        uses `generate_statvar_obs_dcid(record, ignore_props)` (`dc/o/<id>`
        computed with 64-bit FarmHash over `ORDERED_STAT_VAR_OBS_KEY_PROPS`).
        If the record is a partial observation missing required SVObs properties
        (and has no unresolved `l:` reference), falls back to the normalized
        JSON-key hash under `dc/o/`.
      - `Place` types (or nodes with an assignable place ID property when
        `typeOf` is a Place type): uses `generate_place_dcid(record, ignore_props)`
        (e.g. `geoId/...`, `nuts/...`, `iso/...`, `wikidataId/...`), falling
        back to the general node hash if no assignable place ID property is set.
      - `StatisticalVariable`: uses `generate_statvar_hash_dcid(record, ignore_props)`
        (`dc/<id>`).
      - Other nodes: normalizes all non-ignored properties with
        `mcf_file_util.normalize_mcf_node(props, quantity_range_to_dcid=True)`,
        serializes sorted `[property, value]` pairs as compact JSON, and
        encodes the 64-bit SHA-256 prefix in base-32 under `dc/<id>`.

    Args:
      record: Dictionary of property-value pairs for the node.
      ignore_props: Set of property names to exclude when building the DCID key.

    Returns:
      Generated DCID string (e.g. `'dc/o/...'`, `'geoId/...'`, or `'dc/...'`),
      or `''` if no non-ignored properties are present or an unresolved local
      reference (`l:...`) is found.
    """
    if not record:
        return ''

    ignored = DCID_IGNORE_PROPS if ignore_props is None else ignore_props
    type_of = _strip_mcf_namespace(str(record.get('typeOf', '')).strip(' "'))
    if not type_of and 'observationAbout' in record and 'variableMeasured' in record:
        type_of = 'StatVarObservation'

    props = {}
    for prop, raw_val in record.items():
        if not prop or str(prop).startswith('#') or prop in ignored:
            continue
        val_str = '' if raw_val is None else str(raw_val).strip(' "')
        if not val_str:
            continue
        if _has_local_ref(raw_val):
            return ''
        if isinstance(raw_val, bool):
            props[prop] = str(raw_val)
        elif isinstance(raw_val, (int, float)) and raw_val == 0:
            props[prop] = '0'
        elif isinstance(raw_val, str) and _ZERO_NUMERIC_RE.match(val_str):
            props[prop] = '0'
        elif prop in ('Node', 'dcid'):
            props[prop] = str(raw_val)
        else:
            props[prop] = raw_val

    if not props:
        return ''

    if type_of == 'StatVarObservation':
        svobs_dcid = generate_statvar_obs_dcid(props, ignored)
        if svobs_dcid or all(req in props or req in ignored
                             for req in REQUIRED_STAT_VAR_OBS_KEY_PROPS):
            return svobs_dcid

    if type_of in PLACE_TYPES:
        place_dcid = generate_place_dcid(props, ignored)
        if place_dcid:
            return place_dcid

    if type_of == 'StatisticalVariable':
        return generate_statvar_hash_dcid(props, ignored)

    normalized = mcf_file_util.normalize_mcf_node(props,
                                                  quantity_range_to_dcid=True)
    pairs = [[prop, str(val)] for prop, val in sorted(normalized.items())]
    key_string = json.dumps(pairs, ensure_ascii=False, separators=(',', ':'))
    prefix = 'dc/o/' if type_of == 'StatVarObservation' else 'dc/'
    return f'{prefix}{get_sha256_long_id(key_string)}'
