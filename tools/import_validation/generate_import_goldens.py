#!/usr/bin/env python3
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
"""Generates per-import golden StatVar and Place CSVs and wires validation configs.

All configuration parameters are supplied via command-line flags or GCS URIs,
with zero session-specific or machine-specific path dependencies.

Examples:
  # Generate and apply goldens for a single import from GCS auto-refresh output:
  python3 generate_import_goldens.py \
    --manifest statvar_imports/commerce_eda \
    --force-refresh --apply

  # Generate and apply goldens for a new import using local CSV outputs:
  python3 generate_import_goldens.py \
    --manifest statvar_imports/my_new_import \
    --summary-report /path/to/summary_report.csv \
    --cleaned-csv /path/to/output.csv \
    --apply

  # Discover all imports in the repo missing GOLDENS_CHECK and process shard 1 of 4:
  python3 generate_import_goldens.py \
    --discover-missing --shard 1 --num-shards 4 --apply
"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import fnmatch
import glob
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_GOLDEN_STATVARS_URI = (
    "gs://unresolved_mcf/import_validation/golden_statvars.csv"
)
DEFAULT_GOLDEN_PLACES_URI = (
    "gs://unresolved_mcf/import_validation/golden_places.csv"
)
DEFAULT_GCS_BUCKET = "datcom-prod-imports"
DEFAULT_READONLY_SA = (
    "sa-dev-datacommons-readonly@datcom-dev-keys.iam.gserviceaccount.com"
)
DEFAULT_CACHE_DIR = os.path.join(tempfile.gettempdir(), "dc_goldens_cache")

STABLE_SUMMARY_COLS = [
    "StatVar",
    "MeasurementMethods",
    "Units",
    "ScalingFactors",
    "observationPeriods",
]
VOLATILE_SUMMARY_COLS = {
    "NumPlaces",
    "NumObservations",
    "MinValue",
    "MaxValue",
    "NumObservationsDates",
    "MinDate",
    "MaxDate",
}


def resolve_default_repo_root() -> str:
  env_root = os.environ.get("DC_REPO_ROOT", "").strip()
  if env_root:
    return os.path.abspath(env_root)
  try:
    res = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode == 0 and res.stdout.strip():
      return os.path.abspath(res.stdout.strip())
  except OSError:
    pass
  return os.getcwd()


def resolve_gcloud_bin(explicit_bin: str | None = None) -> str | None:
  if explicit_bin and os.path.exists(explicit_bin):
    return explicit_bin
  which_bin = shutil.which("gcloud")
  if which_bin:
    return which_bin
  fallback = "/google/data/ro/teams/cloud-sdk/gcloud"
  if os.path.exists(fallback):
    return fallback
  return None


def strip_ns(val: str) -> str:
  if not isinstance(val, str):
    return ""
  val = val.strip().strip('"').strip("'")
  for prefix in ("dcid:", "dcs:", "schema:"):
    if val.startswith(prefix):
      return val[len(prefix) :].strip()
  return val


def parse_gcs_uri(uri: str) -> tuple[str, str] | None:
  if not uri.startswith("gs://"):
    return None
  without_scheme = uri[len("gs://") :]
  parts = without_scheme.split("/", 1)
  if len(parts) != 2 or not parts[0] or not parts[1]:
    raise ValueError(f"Invalid GCS URI: {uri}")
  return parts[0], parts[1]


def mint_access_token(
    gcloud_bin: str | None = None,
    impersonate_sa: str | None = DEFAULT_READONLY_SA,
) -> str | None:
  env_tok = os.environ.get("DATCOM_GCS_TOKEN", "").strip()
  if env_tok:
    return env_tok

  resolved_gcloud = resolve_gcloud_bin(gcloud_bin)
  if resolved_gcloud:
    if impersonate_sa:
      cmd = [
          resolved_gcloud,
          "auth",
          "application-default",
          "print-access-token",
          f"--impersonate-service-account={impersonate_sa}",
      ]
      res = subprocess.run(cmd, capture_output=True, text=True, check=False)
      if res.returncode == 0 and res.stdout.strip():
        return res.stdout.strip()

    for subcmd in (
        ["auth", "application-default", "print-access-token"],
        ["auth", "print-access-token"],
    ):
      res = subprocess.run(
          [resolved_gcloud] + subcmd,
          capture_output=True,
          text=True,
          check=False,
      )
      if res.returncode == 0 and res.stdout.strip():
        return res.stdout.strip()

  adc_path = os.path.expanduser(
      "~/.config/gcloud/application_default_credentials.json"
  )
  if os.path.exists(adc_path):
    try:
      with open(adc_path, "r", encoding="utf-8") as f:
        adc = json.load(f)
      if all(k in adc for k in ("client_id", "client_secret", "refresh_token")):
        req = urllib.request.Request(
            "https://oauth2.googleapis.com/token",
            data=urllib.parse.urlencode({
                "client_id": adc["client_id"],
                "client_secret": adc["client_secret"],
                "refresh_token": adc["refresh_token"],
                "grant_type": "refresh_token",
            }).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
          return json.loads(resp.read().decode("utf-8")).get("access_token")
    except Exception:
      pass
  return None


class GCSClient:

  def __init__(self, token: str | None, bucket: str = DEFAULT_GCS_BUCKET):
    self.token = token
    self.bucket = bucket

  def read_text(
      self,
      object_name: str,
      max_bytes: int | None = None,
      bucket: str | None = None,
  ) -> str | None:
    if not self.token:
      return None
    target_bucket = bucket or self.bucket
    quoted = urllib.parse.quote(object_name, safe="")
    url = (
        f"https://storage.googleapis.com/storage/v1/b/{target_bucket}/o/"
        f"{quoted}?alt=media"
    )
    headers = {"Authorization": f"Bearer {self.token}"}
    if max_bytes is not None:
      headers["Range"] = f"bytes=0-{max_bytes - 1}"
    req = urllib.request.Request(url, headers=headers)
    try:
      with urllib.request.urlopen(req, timeout=30) as resp:
        status = getattr(resp, "status", 200)
        raw = resp.read()
        text = raw.decode("utf-8", errors="replace")
        if max_bytes is not None and (status == 206 or len(raw) >= max_bytes):
          last_nl = text.rfind("\n")
          if last_nl > 0:
            text = text[: last_nl + 1]
        return text
    except urllib.error.HTTPError as e:
      if e.code == 404:
        return None
      if e.code == 416:
        return ""
      raise

  def list_objects(
      self,
      prefix: str,
      delimiter: str | None = None,
      max_results: int = 500,
      bucket: str | None = None,
  ) -> tuple[list[dict], list[str]]:
    if not self.token:
      return [], []
    target_bucket = bucket or self.bucket
    params = {"prefix": prefix, "maxResults": str(max_results)}
    if delimiter:
      params["delimiter"] = delimiter
    qs = urllib.parse.urlencode(params)
    url = f"https://storage.googleapis.com/storage/v1/b/{target_bucket}/o?{qs}"
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {self.token}"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
      data = json.loads(resp.read().decode("utf-8", errors="replace"))
    return data.get("items", []), data.get("prefixes", [])


def read_local_or_gcs_text(
    path_or_uri: str,
    gcs: GCSClient,
    max_bytes: int | None = None,
) -> str | None:
  parsed = parse_gcs_uri(path_or_uri)
  if parsed:
    bucket, obj_name = parsed
    return gcs.read_text(obj_name, max_bytes=max_bytes, bucket=bucket)
  if os.path.exists(path_or_uri):
    with open(path_or_uri, "r", encoding="utf-8", errors="replace") as f:
      if max_bytes is not None:
        text = f.read(max_bytes)
        last_nl = text.rfind("\n")
        if last_nl > 0 and len(text) >= max_bytes:
          text = text[: last_nl + 1]
        return text
      return f.read()
  return None


def load_dcid_set(path_or_uri: str, gcs: GCSClient) -> set[str]:
  text = read_local_or_gcs_text(path_or_uri, gcs) or ""
  dcids = set()
  for row in csv.DictReader(io.StringIO(text)):
    d = strip_ns(row.get("dcid", ""))
    if d:
      dcids.add(d)
  return dcids


def resolve_latest_version(
    gcs: GCSClient, manifest_rel_dir: str, import_name: str
) -> tuple[str | None, str]:
  prefix = f"{manifest_rel_dir}/{import_name}"
  for ptr_file in ("latest_version.txt", "staging_version.txt"):
    txt = gcs.read_text(f"{prefix}/{ptr_file}")
    if txt and txt.strip():
      ver = txt.strip().splitlines()[0].strip().rstrip("/")
      if "/" in ver:
        ver = ver.split("/")[-1]
      if ver:
        return ver, ptr_file

  _, prefixes = gcs.list_objects(f"{prefix}/", delimiter="/", max_results=100)
  candidates = []
  for p in prefixes:
    rel = p[len(prefix) :].strip("/")
    if rel and rel not in ("historic", "source_files"):
      candidates.append(rel)
  for ver in sorted(candidates, reverse=True):
    test_summary = gcs.read_text(
        f"{prefix}/{ver}/input0/genmcf/summary_report.csv", max_bytes=1024
    )
    if test_summary:
      return ver, "listed_prefix"
  return None, "missing"


def parse_tmcf_place_columns(tmcf_text: str) -> tuple[list[str], bool]:
  if not tmcf_text:
    return [], False

  blocks = re.split(r"(?m)^(?=\s*Node\s*:)", tmcf_text)
  entity_blocks = {}
  obs_about_vals = []

  for b in blocks:
    m_node = re.search(r"(?m)^\s*Node\s*:\s*([^\r\n#]+)", b)
    if m_node:
      node_id = m_node.group(1).strip()
      entity_blocks[node_id] = b
    for m_obs in re.finditer(r"(?m)^\s*observationAbout\s*:\s*([^\r\n#]+)", b):
      obs_about_vals.append(m_obs.group(1).strip())

  if entity_blocks and not obs_about_vals:
    return [], True

  cols = []
  has_constant = False
  for val in obs_about_vals:
    m_col = re.search(r"C:[^-]+->(.+)", val)
    if m_col:
      col = m_col.group(1).strip().strip('"').strip("'")
      if col and col not in cols:
        cols.append(col)
      continue

    m_ent = re.search(r"(E:[^-]+->[^\s,#]+)", val)
    if m_ent:
      ent_id = m_ent.group(1).strip()
      eb = entity_blocks.get(ent_id, "")
      for prop in ("dcid", "isoCode", "wikidataId", "fips52AlphaCode", r"\w+"):
        for m_c in re.finditer(
            rf"(?m)^\s*{prop}\s*:\s*C:[^-]+->([^\r\n#]+)", eb
        ):
          col = m_c.group(1).strip().strip('"').strip("'")
          if col and col not in cols:
            cols.append(col)
      continue

    if val.startswith(("dcid:", "dcs:", "schema:")) or re.match(
        r"^[A-Za-z0-9_/.-]+$", val
    ):
      has_constant = True

  return cols, (has_constant and not cols)


def generate_summary_goldens_from_csv(
    summary_csv_text: str,
    golden_statvars: set[str],
    sample_rows: int = 20,
) -> tuple[list[str], list[dict], str]:
  if not summary_csv_text or not summary_csv_text.strip():
    return [], [], "empty"

  reader = csv.DictReader(io.StringIO(summary_csv_text))
  if not reader.fieldnames or "StatVar" not in reader.fieldnames:
    return [], [], "no_statvar_col"

  rows = [r for r in reader if r.get("StatVar", "").strip()]
  if not rows:
    return [], [], "no_rows"

  matched_rows = [
      r for r in rows if strip_ns(r.get("StatVar", "")) in golden_statvars
  ]
  if matched_rows:
    selected_rows = matched_rows
    mode = f"matched_global({len(matched_rows)})"
  else:

    def sort_key(r):
      try:
        n_obs = int(float(r.get("NumObservations") or 0))
      except ValueError:
        n_obs = 0
      try:
        n_plc = int(float(r.get("NumPlaces") or 0))
      except ValueError:
        n_plc = 0
      return (-n_obs, -n_plc, r.get("StatVar", ""))

    selected_rows = sorted(rows, key=sort_key)[:sample_rows]
    mode = f"fallback_top{sample_rows}({len(selected_rows)})"

  na_like = {"", "na", "nan", "null", "none"}
  stable_cols = []
  for c in STABLE_SUMMARY_COLS:
    if c not in reader.fieldnames:
      continue
    if c == "StatVar":
      stable_cols.append(c)
    else:
      vals = [str(r.get(c) or "").strip() for r in selected_rows]
      if all(v.lower() not in na_like for v in vals):
        stable_cols.append(c)

  seen = set()
  deduped = []
  for r in selected_rows:
    proj = {c: r.get(c, "").strip() for c in stable_cols}
    key = tuple(proj[c] for c in stable_cols)
    if key not in seen:
      seen.add(key)
      deduped.append(proj)

  return stable_cols, deduped, mode


def extract_golden_places_from_csv(
    csv_text: str,
    candidate_cols: list[str],
    golden_places: set[str],
    sample_rows: int = 20,
) -> tuple[str | None, list[str], str, str]:
  if not csv_text or not csv_text.strip():
    return None, [], "", "empty_csv"

  lines = [
      line
      for line in csv_text.splitlines()
      if not line.lstrip().startswith("#")
  ]
  if not lines:
    return None, [], "", "no_uncommented_lines"

  clean_text = "\n".join(lines) + "\n"
  reader = csv.DictReader(io.StringIO(clean_text))
  if not reader.fieldnames:
    return None, [], "", "no_header"

  fieldnames = [f for f in reader.fieldnames if f is not None]
  place_col = None
  for c in candidate_cols:
    if c in fieldnames:
      place_col = c
      break
    for f in fieldnames:
      if f.lower() == c.lower():
        place_col = f
        break
    if place_col:
      break

  if not place_col:
    for fallback_c in (
        "observationAbout",
        "place",
        "GeoId",
        "geo",
        "location",
        "country",
        "state",
        "region",
        "territory",
    ):
      for f in fieldnames:
        if f.lower() == fallback_c.lower():
          place_col = f
          break
      if place_col:
        break

  if not place_col:
    return (
        None,
        [],
        "",
        f"col_not_found(candidates={candidate_cols},header={fieldnames[:10]})",
    )

  counts = Counter()
  matched_raw_ordered = []
  matched_seen = set()
  all_rows = []

  for row in reader:
    if None in row:
      del row[None]
    raw_val = (row.get(place_col) or "").strip()
    if not raw_val or raw_val.startswith("#"):
      continue
    all_rows.append(row)
    counts[raw_val] += 1
    stripped = strip_ns(raw_val)
    if stripped in golden_places and raw_val not in matched_seen:
      matched_seen.add(raw_val)
      matched_raw_ordered.append(raw_val)

  if not counts:
    return place_col, [], "", "no_place_values"

  if matched_raw_ordered:
    selected_places = matched_raw_ordered
    mode = f"matched_global({len(selected_places)})"
  else:
    selected_places = [val for val, _ in counts.most_common(sample_rows)]
    mode = f"fallback_top{sample_rows}({len(selected_places)})"

  selected_set = set(selected_places)
  sampled_rows = []
  covered = set()
  for row in all_rows:
    val = (row.get(place_col) or "").strip()
    if val in selected_set and val not in covered:
      sampled_rows.append(row)
      covered.add(val)
      if len(covered) == len(selected_set):
        break
  for row in all_rows[:50]:
    if len(sampled_rows) >= max(50, len(selected_set) + 20):
      break
    sampled_rows.append(row)

  sample_buf = io.StringIO()
  writer = csv.DictWriter(
      sample_buf,
      fieldnames=fieldnames,
      lineterminator="\n",
      extrasaction="ignore",
  )
  writer.writeheader()
  for r in sampled_rows:
    writer.writerow(r)

  return place_col, selected_places, sample_buf.getvalue(), mode


def write_csv_file(path: str, fieldnames: list[str], rows: list[dict]):
  os.makedirs(os.path.dirname(path), exist_ok=True)
  with open(path, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames,
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )
    writer.writeheader()
    for r in rows:
      writer.writerow(r)


def apply_cached_spec(
    repo_root: str,
    manifest_rel_dir: str,
    spec: dict,
    total_specs_in_manifest: int,
    cache_spec_dir: str,
    meta: dict,
    apply_changes: bool,
    shared_vcfs: set[str] | None = None,
) -> dict:
  """Applies generated golden files and validation rules to the repository."""
  import_name = spec["import_name"]
  manifest_abs_dir = os.path.join(repo_root, manifest_rel_dir)
  if not apply_changes or meta.get("status") != "GENERATED":
    return meta

  existing_spec_vcf = spec.get("validation_config_file")
  if existing_spec_vcf and (
      not shared_vcfs or existing_spec_vcf not in shared_vcfs
  ):
    vcf_name = existing_spec_vcf
  elif existing_spec_vcf and shared_vcfs and existing_spec_vcf in shared_vcfs:
    vcf_name = f"validation_config_{import_name}.json"
  else:
    vcf_name = meta.get("validation_config_file") or (
        "validation_config.json"
        if total_specs_in_manifest == 1
        else f"validation_config_{import_name}.json"
    )
  meta["validation_config_file"] = vcf_name
  vcf_abs = os.path.join(manifest_abs_dir, vcf_name)
  vc_data = {"schema_version": "1.0", "rules": []}
  if os.path.exists(vcf_abs):
    try:
      with open(vcf_abs, "r", encoding="utf-8") as f:
        vc_data = json.load(f)
    except Exception:
      vc_data = {"schema_version": "1.0", "rules": []}
  elif existing_spec_vcf:
    seed_abs = os.path.join(manifest_abs_dir, existing_spec_vcf)
    if os.path.exists(seed_abs):
      try:
        with open(seed_abs, "r", encoding="utf-8") as f:
          vc_data = json.load(f)
      except Exception:
        vc_data = {"schema_version": "1.0", "rules": []}
  if "schema_version" not in vc_data:
    vc_data["schema_version"] = "1.0"
  if "rules" not in vc_data or not isinstance(vc_data["rules"], list):
    vc_data["rules"] = []

  has_upstream_obs_golden = any(
      r.get("validator") == "GOLDENS_CHECK"
      and r.get("rule_id")
      not in ("check_goldens_summary_report", "check_goldens_output_csv")
      and "observations" in str(r.get("params", {}).get("golden_files", ""))
      for r in vc_data["rules"]
  )

  if meta.get("summary_golden_file"):
    summary_fname = os.path.basename(meta["summary_golden_file"])
    cached_g_sum = os.path.join(cache_spec_dir, summary_fname)
    if os.path.exists(cached_g_sum):
      dest_sum = os.path.join(manifest_abs_dir, meta["summary_golden_file"])
      os.makedirs(os.path.dirname(dest_sum), exist_ok=True)
      shutil.copyfile(cached_g_sum, dest_sum)

  if meta.get("obs_golden_file") and not has_upstream_obs_golden:
    obs_fname = os.path.basename(meta["obs_golden_file"])
    cached_g_obs = os.path.join(cache_spec_dir, obs_fname)
    if os.path.exists(cached_g_obs):
      dest_obs = os.path.join(manifest_abs_dir, meta["obs_golden_file"])
      with open(cached_g_obs, "r", encoding="utf-8") as f:
        lines = [l.rstrip("\r\n") for l in f if l.strip()]
      if lines:
        header = lines[0]
        seen_s = set()
        obs_rows = []
        for v in lines[1:]:
          sv = strip_ns(v)
          if sv and sv not in seen_s:
            seen_s.add(sv)
            obs_rows.append({header: sv})
        write_csv_file(cached_g_obs, [header], obs_rows)
        write_csv_file(dest_obs, [header], obs_rows)

  new_rules = [
      r
      for r in vc_data["rules"]
      if r.get("rule_id")
      not in ("check_goldens_summary_report", "check_goldens_output_csv")
  ]
  import_inputs = spec.get("import_inputs", [])
  if meta.get("summary_golden_file"):
    summary_params = {
        "golden_files": f"../../../../{meta['summary_golden_file']}"
    }
    if len(import_inputs) > 1:
      idx = meta.get("summary_input_idx", 0)
      summary_params["input_files"] = f"../../input{idx}/genmcf/summary_report.csv"
    new_rules.append({
        "rule_id": "check_goldens_summary_report",
        "description": (
            "Verifies that expected StatVars and metadata in"
            " golden_summary_report.csv are present in the summary report"
        ),
        "validator": "GOLDENS_CHECK",
        "params": summary_params,
    })

  if (
      meta.get("obs_golden_file")
      and meta.get("cleaned_csv_rel")
      and not has_upstream_obs_golden
  ):
    new_rules.append({
        "rule_id": "check_goldens_output_csv",
        "description": (
            "Verifies the generated output CSV data matches established"
            " critical golden records"
        ),
        "validator": "GOLDENS_CHECK",
        "params": {
            "golden_files": f"../../../../{meta['obs_golden_file']}",
            "input_files": f"../../../../{meta['cleaned_csv_rel']}",
        },
    })

  vc_data["rules"] = new_rules
  os.makedirs(os.path.dirname(vcf_abs), exist_ok=True)
  with open(vcf_abs, "w", encoding="utf-8") as f:
    json.dump(vc_data, f, indent=4)
    f.write("\n")

  return meta


def process_import_spec(
    repo_root: str,
    cache_dir: str,
    gcs: GCSClient,
    manifest_rel_dir: str,
    spec: dict,
    total_specs_in_manifest: int,
    golden_statvars: set[str],
    golden_places: set[str],
    apply_changes: bool,
    force_refresh: bool = False,
    shared_vcfs: set[str] | None = None,
    explicit_summary_report: str | None = None,
    explicit_cleaned_csv: str | None = None,
    sample_rows: int = 20,
) -> dict:
  import_name = spec["import_name"]
  manifest_abs_dir = os.path.join(repo_root, manifest_rel_dir)
  cache_spec_dir = os.path.join(cache_dir, manifest_rel_dir, import_name)
  meta_path = os.path.join(cache_spec_dir, "meta.json")

  if (
      not force_refresh
      and not explicit_summary_report
      and not explicit_cleaned_csv
      and os.path.exists(meta_path)
  ):
    cached_meta = None
    try:
      with open(meta_path, "r", encoding="utf-8") as f:
        cached_meta = json.load(f)
    except Exception:
      cached_meta = None
    if cached_meta and cached_meta.get("status") in (
        "GENERATED",
        "SKIPPED_NO_GCS_VERSION",
        "SKIPPED_NO_GOLDENS_GENERATED",
    ):
      return apply_cached_spec(
          repo_root=repo_root,
          manifest_rel_dir=manifest_rel_dir,
          spec=spec,
          total_specs_in_manifest=total_specs_in_manifest,
          cache_spec_dir=cache_spec_dir,
          meta=cached_meta,
          apply_changes=apply_changes,
          shared_vcfs=shared_vcfs,
      )

  os.makedirs(cache_spec_dir, exist_ok=True)
  result = {
      "manifest_dir": manifest_rel_dir,
      "import_name": import_name,
      "status": "PENDING",
      "version": None,
      "version_source": None,
      "summary_golden_file": None,
      "summary_rows": 0,
      "summary_mode": None,
      "obs_golden_file": None,
      "obs_rows": 0,
      "obs_place_col": None,
      "obs_mode": None,
      "cleaned_csv_rel": None,
      "validation_config_file": None,
      "error": None,
  }

  try:
    if explicit_summary_report or explicit_cleaned_csv:
      version = "local"
      ver_src = "explicit_cli"
    else:
      version, ver_src = resolve_latest_version(
          gcs, manifest_rel_dir, import_name
      )
    result["version"] = version
    result["version_source"] = ver_src
    if not version:
      result["status"] = "SKIPPED_NO_GCS_VERSION"
      with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
      return result

    prefix_ver = f"{manifest_rel_dir}/{import_name}/{version}"
    import_inputs = spec.get("import_inputs", [])
    num_inputs = max(1, len(import_inputs))

    best_input_idx = 0
    best_summary_text = None
    best_cols = []
    best_rows = []
    best_mode = None
    ver_objects_cache = None

    if explicit_summary_report:
      s_text = read_local_or_gcs_text(explicit_summary_report, gcs)
      if s_text:
        cols, rows, mode = generate_summary_goldens_from_csv(
            s_text, golden_statvars, sample_rows=sample_rows
        )
        if rows:
          best_summary_text = s_text
          best_cols = cols
          best_rows = rows
          best_mode = mode
    else:
      for idx in range(num_inputs):
        s_text = gcs.read_text(
            f"{prefix_ver}/input{idx}/genmcf/summary_report.csv"
        )
        if not s_text:
          continue
        cols, rows, mode = generate_summary_goldens_from_csv(
            s_text, golden_statvars, sample_rows=sample_rows
        )
        if rows:
          if best_summary_text is None or (
              mode.startswith("matched_global")
              and not (best_mode or "").startswith("matched_global")
          ):
            best_input_idx = idx
            best_summary_text = s_text
            best_cols = cols
            best_rows = rows
            best_mode = mode
          if mode.startswith("matched_global"):
            break

      if not best_rows:
        if ver_objects_cache is None:
          items, _ = gcs.list_objects(f"{prefix_ver}/", max_results=500)
          ver_objects_cache = [it["name"] for it in items]
        for obj_name in ver_objects_cache:
          if obj_name.endswith("/summary_report.csv"):
            s_text = gcs.read_text(obj_name)
            if not s_text:
              continue
            cols, rows, mode = generate_summary_goldens_from_csv(
                s_text, golden_statvars, sample_rows=sample_rows
            )
            if rows:
              if best_summary_text is None or (
                  mode.startswith("matched_global")
                  and not (best_mode or "").startswith("matched_global")
              ):
                best_input_idx = 0
                best_summary_text = s_text
                best_cols = cols
                best_rows = rows
                best_mode = mode
              if mode.startswith("matched_global"):
                break

      if not best_rows:
        stg_txt = gcs.read_text(
            f"{manifest_rel_dir}/{import_name}/staging_version.txt"
        )
        if stg_txt and stg_txt.strip():
          stg_ver = (
              stg_txt.strip()
              .splitlines()[0]
              .strip()
              .rstrip("/")
              .split("/")[-1]
          )
          if stg_ver and stg_ver != version:
            stg_prefix = f"{manifest_rel_dir}/{import_name}/{stg_ver}"
            for idx in range(num_inputs):
              s_text = gcs.read_text(
                  f"{stg_prefix}/input{idx}/genmcf/summary_report.csv"
              )
              if not s_text:
                continue
              cols, rows, mode = generate_summary_goldens_from_csv(
                  s_text, golden_statvars, sample_rows=sample_rows
              )
              if rows:
                if best_summary_text is None or (
                    mode.startswith("matched_global")
                    and not (best_mode or "").startswith("matched_global")
                ):
                  best_input_idx = idx
                  best_summary_text = s_text
                  best_cols = cols
                  best_rows = rows
                  best_mode = mode
                if mode.startswith("matched_global"):
                  break

    if best_rows:
      summary_fname = (
          "golden_summary_report.csv"
          if total_specs_in_manifest == 1
          else f"golden_summary_report_{import_name}.csv"
      )
      summary_rel = f"golden_data/{summary_fname}"
      result["summary_golden_file"] = summary_rel
      result["summary_rows"] = len(best_rows)
      result["summary_mode"] = best_mode
      result["summary_input_idx"] = best_input_idx

      with open(
          os.path.join(cache_spec_dir, "summary_report.csv"),
          "w",
          encoding="utf-8",
      ) as f:
        f.write(best_summary_text)
      write_csv_file(
          os.path.join(cache_spec_dir, summary_fname), best_cols, best_rows
      )

    for inp in import_inputs:
      csv_rel = inp.get("cleaned_csv")
      tmcf_rel = inp.get("template_mcf")
      if isinstance(csv_rel, list):
        csv_rel = csv_rel[0] if csv_rel else None
      if isinstance(tmcf_rel, list):
        tmcf_rel = tmcf_rel[0] if tmcf_rel else None
      if not csv_rel and not explicit_cleaned_csv:
        continue

      tmcf_text = None
      if tmcf_rel:
        local_tmcf = os.path.join(manifest_abs_dir, tmcf_rel)
        if os.path.exists(local_tmcf):
          with open(local_tmcf, "r", encoding="utf-8", errors="replace") as f:
            tmcf_text = f.read()
        if not tmcf_text and version != "local":
          tmcf_text = gcs.read_text(f"{prefix_ver}/{tmcf_rel}")
        if not tmcf_text and version != "local":
          tmcf_text = gcs.read_text(
              f"{prefix_ver}/{os.path.basename(tmcf_rel)}"
          )
      if not tmcf_text:
        local_tmcfs = sorted(
            glob.glob(
                os.path.join(manifest_abs_dir, "**", "*.tmcf"), recursive=True
            )
        )
        if local_tmcfs:
          with open(
              local_tmcfs[0], "r", encoding="utf-8", errors="replace"
          ) as f:
            tmcf_text = f.read()
      if not tmcf_text and version != "local":
        if ver_objects_cache is None:
          items, _ = gcs.list_objects(f"{prefix_ver}/", max_results=500)
          ver_objects_cache = [it["name"] for it in items]
        for obj_name in ver_objects_cache:
          if obj_name.endswith(".tmcf"):
            tmcf_text = gcs.read_text(obj_name)
            if tmcf_text:
              break

      cand_cols, is_const_only = parse_tmcf_place_columns(tmcf_text or "")
      if is_const_only:
        result["obs_mode"] = "skipped_constant_observationAbout"
        continue

      max_csv_bytes = 8 * 1024 * 1024
      csv_text = None
      if explicit_cleaned_csv:
        csv_text = read_local_or_gcs_text(
            explicit_cleaned_csv, gcs, max_bytes=max_csv_bytes
        )
      elif csv_rel:
        local_csv_path = os.path.join(manifest_abs_dir, csv_rel)
        if (
            "*" not in csv_rel
            and "?" not in csv_rel
            and os.path.exists(local_csv_path)
        ):
          csv_text = read_local_or_gcs_text(
              local_csv_path, gcs, max_bytes=max_csv_bytes
          )
        if not csv_text and version != "local":
          if "*" not in csv_rel and "?" not in csv_rel:
            csv_text = gcs.read_text(
                f"{prefix_ver}/{csv_rel}", max_bytes=max_csv_bytes
            )
            if not csv_text:
              csv_text = gcs.read_text(
                  f"{prefix_ver}/{os.path.basename(csv_rel)}",
                  max_bytes=max_csv_bytes,
              )
          if not csv_text:
            if ver_objects_cache is None:
              items, _ = gcs.list_objects(f"{prefix_ver}/", max_results=500)
              ver_objects_cache = [it["name"] for it in items]
            base_pat = os.path.basename(csv_rel)
            stem_pat = os.path.splitext(base_pat)[0].lower()
            for obj_name in ver_objects_cache:
              rel_obj = obj_name[len(prefix_ver) + 1 :]
              if (
                  "/genmcf/" in rel_obj
                  or "/validation/" in rel_obj
                  or rel_obj.startswith("source_files/")
              ):
                continue
              base_obj = os.path.basename(rel_obj)
              if (
                  fnmatch.fnmatch(rel_obj, csv_rel)
                  or fnmatch.fnmatch(base_obj, base_pat)
                  or (
                      base_obj.lower().endswith(".csv")
                      and stem_pat
                      and base_obj.lower().startswith(stem_pat)
                  )
              ):
                csv_text = gcs.read_text(obj_name, max_bytes=max_csv_bytes)
                if csv_text and csv_text.strip():
                  break

      if not csv_text:
        continue

      place_col, place_vals, sample_csv_text, obs_mode = (
          extract_golden_places_from_csv(
              csv_text, cand_cols, golden_places, sample_rows=sample_rows
          )
      )
      if place_col and place_vals:
        obs_fname = (
            "golden_observations.csv"
            if total_specs_in_manifest == 1
            else f"golden_observations_{import_name}.csv"
        )
        obs_rel = f"golden_data/{obs_fname}"
        seen_stripped = set()
        obs_rows = []
        for v in place_vals:
          sv = strip_ns(v)
          if sv and sv not in seen_stripped:
            seen_stripped.add(sv)
            obs_rows.append({place_col: sv})
        result["obs_golden_file"] = obs_rel
        result["obs_rows"] = len(obs_rows)
        result["obs_place_col"] = place_col
        result["obs_mode"] = obs_mode
        result["cleaned_csv_rel"] = csv_rel or os.path.basename(
            explicit_cleaned_csv or "output.csv"
        )

        with open(
            os.path.join(cache_spec_dir, "sampled_output.csv"),
            "w",
            encoding="utf-8",
        ) as f:
          f.write(sample_csv_text)
        write_csv_file(
            os.path.join(cache_spec_dir, obs_fname), [place_col], obs_rows
        )
        break
      else:
        result["obs_mode"] = obs_mode

    if not result["summary_golden_file"] and not result["obs_golden_file"]:
      result["status"] = "SKIPPED_NO_GOLDENS_GENERATED"
      with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
      return result

    vcf_name = spec.get("validation_config_file")
    if not vcf_name:
      vcf_name = (
          "validation_config.json"
          if total_specs_in_manifest == 1
          else f"validation_config_{import_name}.json"
      )
    result["validation_config_file"] = vcf_name
    result["status"] = "GENERATED"

    with open(meta_path, "w", encoding="utf-8") as f:
      json.dump(result, f, indent=2)

    if apply_changes:
      apply_cached_spec(
          repo_root=repo_root,
          manifest_rel_dir=manifest_rel_dir,
          spec=spec,
          total_specs_in_manifest=total_specs_in_manifest,
          cache_spec_dir=cache_spec_dir,
          meta=result,
          apply_changes=apply_changes,
          shared_vcfs=shared_vcfs,
      )
  except Exception as e:
    result["status"] = "ERROR"
    result["error"] = str(e)
    with open(meta_path, "w", encoding="utf-8") as f:
      json.dump(result, f, indent=2)

  return result


def process_manifest_dir(
    repo_root: str,
    cache_dir: str,
    gcs: GCSClient,
    manifest_rel_dir: str,
    target_import_names: list[str] | None,
    golden_statvars: set[str],
    golden_places: set[str],
    apply_changes: bool,
    force_refresh: bool = False,
    explicit_summary_report: str | None = None,
    explicit_cleaned_csv: str | None = None,
    sample_rows: int = 20,
) -> list[dict]:
  manifest_abs_path = os.path.join(repo_root, manifest_rel_dir, "manifest.json")
  with open(manifest_abs_path, "r", encoding="utf-8") as f:
    manifest_data = json.load(f)

  specs = manifest_data.get("import_specifications", [])
  total_specs = len(specs)
  vcf_counts = Counter(
      s.get("validation_config_file")
      for s in specs
      if s.get("validation_config_file")
  )
  shared_vcfs = {k for k, v in vcf_counts.items() if v > 1}
  results = []
  manifest_modified = False

  for spec in specs:
    iname = spec.get("import_name", "")
    if target_import_names is not None and iname not in target_import_names:
      continue
    old_vcf = spec.get("validation_config_file")
    res = process_import_spec(
        repo_root=repo_root,
        cache_dir=cache_dir,
        gcs=gcs,
        manifest_rel_dir=manifest_rel_dir,
        spec=spec,
        total_specs_in_manifest=total_specs,
        golden_statvars=golden_statvars,
        golden_places=golden_places,
        apply_changes=apply_changes,
        force_refresh=force_refresh,
        shared_vcfs=shared_vcfs,
        explicit_summary_report=explicit_summary_report,
        explicit_cleaned_csv=explicit_cleaned_csv,
        sample_rows=sample_rows,
    )
    results.append(res)
    if apply_changes and res["status"] == "GENERATED":
      if spec.get("validation_config_file") != res["validation_config_file"]:
        spec["validation_config_file"] = res["validation_config_file"]
        manifest_modified = True
      legacy_src_file = spec.pop("source_file", None)
      src_files = spec.get("source_files")
      if src_files is None or not isinstance(src_files, list):
        src_files = []
        spec["source_files"] = src_files
        manifest_modified = True
      if isinstance(legacy_src_file, list):
        for item in legacy_src_file:
          if item not in src_files:
            src_files.append(item)
        manifest_modified = True
      elif isinstance(legacy_src_file, str) and legacy_src_file:
        if legacy_src_file not in src_files:
          src_files.append(legacy_src_file)
        manifest_modified = True
      if (
          old_vcf
          and old_vcf in src_files
          and old_vcf != res["validation_config_file"]
      ):
        idx_v = src_files.index(old_vcf)
        src_files[idx_v] = res["validation_config_file"]
        manifest_modified = True
      if "golden_data/*.csv" not in src_files:
        src_files.append("golden_data/*.csv")
        manifest_modified = True
    elif apply_changes and res["status"] == "SKIPPED_NO_GOLDENS_GENERATED":
      manifest_abs_dir = os.path.join(repo_root, manifest_rel_dir)
      g_dir = os.path.join(manifest_abs_dir, "golden_data")
      if os.path.exists(g_dir) and total_specs == 1:
        shutil.rmtree(g_dir, ignore_errors=True)
      src_files = spec.get("source_files")
      if isinstance(src_files, list) and "golden_data/*.csv" in src_files:
        src_files.remove("golden_data/*.csv")
        manifest_modified = True
      vcf = spec.get("validation_config_file")
      if vcf and total_specs == 1:
        vcf_abs = os.path.join(manifest_abs_dir, vcf)
        if os.path.exists(vcf_abs):
          try:
            with open(vcf_abs, "r", encoding="utf-8") as vf:
              vcd = json.load(vf)
            non_g = [
                r
                for r in vcd.get("rules", [])
                if r.get("validator") != "GOLDENS_CHECK"
            ]
            if not non_g:
              os.remove(vcf_abs)
              del spec["validation_config_file"]
              manifest_modified = True
          except Exception:
            pass

  if apply_changes and manifest_modified:
    with open(manifest_abs_path, "w", encoding="utf-8") as f:
      json.dump(manifest_data, f, indent=4)
      f.write("\n")

  return results


def discover_manifests_missing_goldens(repo_root: str) -> list[dict]:
  """Scans scripts/** and statvar_imports/** for manifests missing GOLDENS_CHECK."""
  discovered = []
  for root_sub in ("scripts", "statvar_imports"):
    base_dir = os.path.join(repo_root, root_sub)
    if not os.path.isdir(base_dir):
      continue
    for m_path in sorted(
        glob.glob(os.path.join(base_dir, "**", "manifest.json"), recursive=True)
    ):
      rel_dir = os.path.relpath(os.path.dirname(m_path), repo_root)
      try:
        with open(m_path, "r", encoding="utf-8") as f:
          m_data = json.load(f)
      except Exception:
        continue
      specs = m_data.get("import_specifications", [])
      missing_names = []
      for spec in specs:
        iname = spec.get("import_name")
        if not iname:
          continue
        vcf = spec.get("validation_config_file")
        has_goldens = False
        if vcf:
          vcf_abs = os.path.join(os.path.dirname(m_path), vcf)
          if os.path.exists(vcf_abs):
            try:
              with open(vcf_abs, "r", encoding="utf-8") as vf:
                vc_data = json.load(vf)
              has_goldens = any(
                  r.get("validator") == "GOLDENS_CHECK"
                  and r.get("enabled", True) is not False
                  for r in vc_data.get("rules", [])
              )
            except Exception:
              has_goldens = False
        if not has_goldens:
          missing_names.append(iname)
      if missing_names:
        discovered.append({
            "manifest_dir": rel_dir,
            "target_import_names": missing_names,
        })
  return discovered


def main():
  parser = argparse.ArgumentParser(
      description=(
          "Generate per-import golden StatVar and Place CSVs and wire"
          " validation_config.json and manifest.json."
      )
  )
  parser.add_argument(
      "--manifest",
      type=str,
      help=(
          "Comma-separated relative paths to manifest directories or"
          " manifest.json files (e.g. statvar_imports/commerce_eda)"
      ),
  )
  parser.add_argument(
      "--discover-missing",
      action="store_true",
      help=(
          "Automatically discover manifests under scripts/ and"
          " statvar_imports/ lacking GOLDENS_CHECK rules"
      ),
  )
  parser.add_argument(
      "--shards-file",
      type=str,
      default=None,
      help="Optional path or gs:// URI to a JSON shard assignment file",
  )
  parser.add_argument(
      "--shard",
      type=str,
      default=None,
      help=(
          "Shard ID (e.g. 1..N or shard-1..shard-N, or comma-separated list)"
          " when using --shards-file or --discover-missing"
      ),
  )
  parser.add_argument(
      "--num-shards",
      type=int,
      default=4,
      help="Total number of shards when partitioning --discover-missing",
  )
  parser.add_argument(
      "--repo-root",
      type=str,
      default=None,
      help=(
          "Path to the datacommonsorg/data repository root (defaults to"
          " DC_REPO_ROOT, git top-level, or current working directory)"
      ),
  )
  parser.add_argument(
      "--golden-statvars",
      type=str,
      default=DEFAULT_GOLDEN_STATVARS_URI,
      help=(
          "Local path or gs:// URI to the global golden StatVars CSV"
          f" (default: {DEFAULT_GOLDEN_STATVARS_URI})"
      ),
  )
  parser.add_argument(
      "--golden-places",
      type=str,
      default=DEFAULT_GOLDEN_PLACES_URI,
      help=(
          "Local path or gs:// URI to the global golden Places CSV"
          f" (default: {DEFAULT_GOLDEN_PLACES_URI})"
      ),
  )
  parser.add_argument(
      "--gcs-bucket",
      type=str,
      default=DEFAULT_GCS_BUCKET,
      help=(
          "GCS bucket containing auto-refresh import outputs"
          f" (default: {DEFAULT_GCS_BUCKET})"
      ),
  )
  parser.add_argument(
      "--cache-dir",
      type=str,
      default=DEFAULT_CACHE_DIR,
      help=(
          "Local cache directory for downloaded GCS artifacts"
          f" (default: {DEFAULT_CACHE_DIR})"
      ),
  )
  parser.add_argument(
      "--summary-report",
      type=str,
      default=None,
      help=(
          "Optional local path or gs:// URI to a summary_report.csv file"
          " (overrides GCS auto-refresh discovery for --manifest)"
      ),
  )
  parser.add_argument(
      "--cleaned-csv",
      type=str,
      default=None,
      help=(
          "Optional local path or gs:// URI to a cleaned observation CSV file"
          " (overrides GCS auto-refresh discovery for --manifest)"
      ),
  )
  parser.add_argument(
      "--impersonate-service-account",
      type=str,
      default=DEFAULT_READONLY_SA,
      help=(
          "GCP service account to impersonate for GCS reads (pass empty string"
          " '' to use default credentials without impersonation)"
      ),
  )
  parser.add_argument(
      "--gcloud-bin",
      type=str,
      default=None,
      help="Optional path to the gcloud CLI binary",
  )
  parser.add_argument(
      "--sample-rows",
      type=int,
      default=20,
      help=(
          "Number of fallback rows to sample when an import has 0 overlap with"
          " global golden lists (default: 20)"
      ),
  )
  parser.add_argument(
      "--apply",
      action="store_true",
      help="Write golden_data/*.csv, validation_config*.json, and manifest.json",
  )
  parser.add_argument(
      "--force-refresh",
      action="store_true",
      help="Re-fetch from GCS even if --cache-dir already has meta.json",
  )
  parser.add_argument(
      "--workers",
      type=int,
      default=6,
      help="Number of parallel worker threads (default: 6)",
  )
  parser.add_argument(
      "--report-file",
      type=str,
      default=None,
      help="Optional path to save the JSON execution report",
  )
  args = parser.parse_args()

  if not args.manifest and not args.discover_missing and not args.shards_file:
    parser.error(
        "Must specify at least one of --manifest, --discover-missing, or"
        " --shards-file"
    )

  repo_root = (
      os.path.abspath(args.repo_root)
      if args.repo_root
      else resolve_default_repo_root()
  )
  cache_dir = os.path.abspath(args.cache_dir)
  token = mint_access_token(
      gcloud_bin=args.gcloud_bin,
      impersonate_sa=args.impersonate_service_account or None,
  )
  gcs = GCSClient(token=token, bucket=args.gcs_bucket)

  golden_statvars = load_dcid_set(args.golden_statvars, gcs)
  golden_places = load_dcid_set(args.golden_places, gcs)

  tasks = []
  if args.manifest:
    for m_item in args.manifest.split(","):
      m_rel = m_item.strip().rstrip("/")
      if not m_rel:
        continue
      if m_rel.endswith("/manifest.json"):
        m_rel = m_rel[: -len("/manifest.json")]
      if os.path.isabs(m_rel):
        m_rel = os.path.relpath(m_rel, repo_root)
      tasks.append((m_rel, None))
  elif args.shards_file:
    shards_text = read_local_or_gcs_text(args.shards_file, gcs)
    if not shards_text:
      raise FileNotFoundError(f"Could not read shards file: {args.shards_file}")
    shards = json.loads(shards_text)
    shard_keys = (
        [
            s.strip() if s.strip().startswith("shard-") else f"shard-{s.strip()}"
            for s in args.shard.split(",")
        ]
        if args.shard
        else sorted(shards.keys())
    )
    for shard_key in shard_keys:
      if shard_key not in shards:
        raise ValueError(f"Unknown shard {shard_key} in {args.shards_file}")
      for entry in shards[shard_key]:
        tasks.append((entry["manifest_dir"], entry.get("target_import_names")))
  elif args.discover_missing:
    discovered = discover_manifests_missing_goldens(repo_root)
    if args.shard:
      num_shards = max(1, args.num_shards)
      shards = {f"shard-{i + 1}": [] for i in range(num_shards)}
      for idx, entry in enumerate(discovered):
        shards[f"shard-{(idx % num_shards) + 1}"].append(entry)
      for s_part in args.shard.split(","):
        s_part = s_part.strip()
        shard_key = s_part if s_part.startswith("shard-") else f"shard-{s_part}"
        if shard_key not in shards:
          raise ValueError(f"Unknown shard {shard_key}")
        for entry in shards[shard_key]:
          tasks.append(
              (entry["manifest_dir"], entry.get("target_import_names"))
          )
    else:
      for entry in discovered:
        tasks.append((entry["manifest_dir"], entry.get("target_import_names")))

  all_results = []
  if len(tasks) == 1 or args.workers <= 1:
    for m_dir, t_names in tasks:
      res_list = process_manifest_dir(
          repo_root=repo_root,
          cache_dir=cache_dir,
          gcs=gcs,
          manifest_rel_dir=m_dir,
          target_import_names=t_names,
          golden_statvars=golden_statvars,
          golden_places=golden_places,
          apply_changes=args.apply,
          force_refresh=args.force_refresh,
          explicit_summary_report=args.summary_report,
          explicit_cleaned_csv=args.cleaned_csv,
          sample_rows=args.sample_rows,
      )
      for r in res_list:
        print(
            f"[{r['status']}] {r['manifest_dir']} ({r['import_name']}):"
            f" ver={r['version']}"
            f" summary={r['summary_rows']}({r['summary_mode']})"
            f" obs={r['obs_rows']}({r['obs_mode']})"
            + (f" err={r.get('error')}" if r.get("error") else ""),
            flush=True,
        )
      all_results.extend(res_list)
  else:
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
      fut_map = {
          ex.submit(
              process_manifest_dir,
              repo_root,
              cache_dir,
              gcs,
              m_dir,
              t_names,
              golden_statvars,
              golden_places,
              args.apply,
              args.force_refresh,
              args.summary_report,
              args.cleaned_csv,
              args.sample_rows,
          ): m_dir
          for m_dir, t_names in tasks
      }
      for fut in as_completed(fut_map):
        res_list = fut.result()
        for r in res_list:
          print(
              f"[{r['status']}] {r['manifest_dir']} ({r['import_name']}):"
              f" ver={r['version']}"
              f" summary={r['summary_rows']}({r['summary_mode']})"
              f" obs={r['obs_rows']}({r['obs_mode']})"
              + (f" err={r.get('error')}" if r.get("error") else ""),
              flush=True,
          )
        all_results.extend(res_list)

  by_status = Counter(r["status"] for r in all_results)
  print("\n=== Summary ===", flush=True)
  print(f"Total specs processed: {len(all_results)}", flush=True)
  for k, v in sorted(by_status.items()):
    print(f"  {k}: {v}", flush=True)

  if args.report_file:
    os.makedirs(
        os.path.dirname(os.path.abspath(args.report_file)), exist_ok=True
    )
    with open(args.report_file, "w", encoding="utf-8") as f:
      json.dump(all_results, f, indent=2)
    print(f"Saved report to {args.report_file}", flush=True)


if __name__ == "__main__":
  main()
