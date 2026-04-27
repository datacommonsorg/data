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
"""Script to convert DataCommons manifest files (.textproto) to MCF format.

This script scans a directory for .textproto files containing DataCommons
manifests (DataCommonsManifest proto) and converts them into corresponding
.mcf files. It processes both 'import' and 'dataset_source' fields from
the manifest.

Usage:
    python3 manifest_to_mcf.py <directory_path>
"""
import os
from urllib.parse import urlparse
from google.protobuf import text_format
from absl import app
from absl import flags
import dc_manifest_pb2

FLAGS = flags.FLAGS
flags.DEFINE_string("directory", os.getcwd(),
                    "Directory to scan for .textproto files.")


def convert_to_mcf(import_proto, test_time=15700000):
    import_name = import_proto.import_name
    dcid = f"dc/base/{import_name}"

    mcf_lines = []
    mcf_lines.append(f"Node: dcid:{dcid}")

    # curator
    curator_email = import_proto.curator_email
    if not curator_email or curator_email == "imports@datacommons.org":
        mcf_lines.append("curator: dcid:dc/cjj7vp")
    else:
        # Simple hash as in Java code fallback
        mcf_lines.append(
            f"curator: dcid:dc/curator_{hash(curator_email) & 0xffffffff}")

    mcf_lines.append(f'dcid: "{dcid}"')

    if import_proto.provenance_description:
        mcf_lines.append(
            f'description: "{import_proto.provenance_description}"')

    # entityResolutionType
    res_type = "dcid:NoEntityResolution"
    if import_proto.HasField("resolution_info"):
        res_info = import_proto.resolution_info
        if res_info.uses_id_resolver:
            if res_info.kg_for_resolution == dc_manifest_pb2.ResolutionInfo.KG_MCF:
                res_type = "dcid:IdBasedKgResolution"
            else:
                res_type = "dcid:IdResolutionWithoutKg"
    mcf_lines.append(f"entityResolutionType: {res_type}")

    # importTime
    mcf_lines.append(f"importTime: {test_time}")

    # isPartOf
    dataset_name = import_proto.dataset_name
    if dataset_name:
        clean_dataset_name = dataset_name.replace(" ", "")
        mcf_lines.append(f"isPartOf: dcid:dc/d/TestSource_{clean_dataset_name}")

    mcf_lines.append(f'name: "{import_name}"')
    mcf_lines.append(f"provenance: dcid:{dcid}")

    # provenanceCategory
    cat_map = {
        dc_manifest_pb2.DataCommonsManifest.SCHEMA:
            "SchemaProvenance",
        dc_manifest_pb2.DataCommonsManifest.PLACE:
            "PlaceProvenance",
        dc_manifest_pb2.DataCommonsManifest.CURATED_STATVAR:
            "StatVarProvenance",
        dc_manifest_pb2.DataCommonsManifest.GENERATED_STATVAR:
            "StatVarProvenance",
        dc_manifest_pb2.DataCommonsManifest.STATS:
            "StatsProvenance",
        dc_manifest_pb2.DataCommonsManifest.AGGREGATED_STATS:
            "StatsProvenance",
        dc_manifest_pb2.DataCommonsManifest.IMPUTED_STATS:
            "StatsProvenance",
        dc_manifest_pb2.DataCommonsManifest.INTERMEDIATE_STATS:
            "StatsProvenance",
    }
    category = import_proto.category
    cat_dcid = cat_map.get(category, "UnknownProvenance")
    mcf_lines.append(f"provenanceCategory: dcid:{cat_dcid}")

    if import_proto.mcf_url:
        mcf_lines.append(f'resolvedTextMcfUrl: "{import_proto.mcf_url[0]}"')

    mcf_lines.append("source: dcid:dc/s/TestSource")
    mcf_lines.append("typeOf: dcid:Provenance")

    if import_proto.provenance_url:
        mcf_lines.append(f'url: "{import_proto.provenance_url}"')

    return "\n".join(mcf_lines)


def convert_dataset_sources_to_mcf(dataset_sources):
    out_nodes = []

    for ds in dataset_sources:
        source_id = ds.name.replace(" ", "")
        s_node_id = f"dcid:dc/s/{source_id}"

        s_props = {}
        s_props['dcid'] = [f'"{s_node_id.split(":", 1)[1]}"']
        s_props['name'] = [f'"{ds.name}"']

        if ds.url:
            s_props['url'] = [f'"{ds.url}"']
            domain = urlparse(ds.url).netloc
            if domain:
                s_props['domain'] = [f'"{domain}"']

        s_props['provenance'] = ['dcid:dc/base/GeneratedGraphs']
        s_props['typeOf'] = ['dcid:Source']

        d_nodes_out = []
        for d in ds.datasets:
            dataset_id = d.name.replace(" ", "")
            d_node_id = f"dcid:dc/d/{source_id}_{dataset_id}"

            d_props = {}
            d_props['dcid'] = [f'"{d_node_id.split(":", 1)[1]}"']
            d_props['isPartOf'] = [f"dcid:dc/s/{source_id}"]
            d_props['name'] = [f'"{d.name}"']

            if d.url:
                d_props['url'] = [f'"{d.url}"']

            d_props['provenance'] = ['dcid:dc/base/GeneratedGraphs']
            d_props['typeOf'] = ['dcid:Dataset']

            lines = [f"Node: {d_node_id}"]
            for prop in sorted(d_props.keys()):
                for val in d_props[prop]:
                    lines.append(f"{prop}: {val}")
            d_nodes_out.append("\n".join(lines))

        lines = [f"Node: {s_node_id}"]
        for prop in sorted(s_props.keys()):
            for val in s_props[prop]:
                lines.append(f"{prop}: {val}")

        out_nodes.extend(d_nodes_out)
        out_nodes.append("\n".join(lines))

    return "\n\n".join(out_nodes)


def process_text(input_text):
    input_text = input_text.strip()

    # Try parsing as DataCommonsManifest
    manifest = dc_manifest_pb2.DataCommonsManifest()
    try:
        text_format.Merge(input_text, manifest)
        # Use getattr because 'import' is a Python keyword and cannot be accessed via dot notation.
        imports = getattr(manifest, 'import', [])
        dataset_sources = getattr(manifest, 'dataset_source', [])

        if imports or dataset_sources:
            out_mcf = []
            if dataset_sources:
                out_mcf.append(convert_dataset_sources_to_mcf(dataset_sources))
            if imports:
                for imp in imports:
                    out_mcf.append(convert_to_mcf(imp))

            return "\n\n".join(out_mcf)
        else:
            raise ValueError(
                "No imports or dataset_sources found in the parsed manifest.")
    except Exception as e:
        raise ValueError(f"Failed to parse input as DataCommonsManifest: {e}")


def process_directory(path):
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".textproto"):
                textproto_path = os.path.join(root, file)
                mcf_path = textproto_path.replace(".textproto", ".mcf")

                with open(textproto_path, 'r') as f:
                    input_text = f.read()

                try:
                    out_mcf = process_text(input_text)
                    with open(mcf_path, 'w') as f:
                        f.write(out_mcf + "\n")
                    print(f"Processed {textproto_path} -> {mcf_path}")
                except Exception as e:
                    print(f"Error processing {textproto_path}: {e}")


def main(_):
    process_directory(FLAGS.directory)


if __name__ == "__main__":
    app.run(main)
