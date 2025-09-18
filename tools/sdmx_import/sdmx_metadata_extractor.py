# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
SDMX Metadata Extractor

This module provides functionality to extract comprehensive structural metadata
for SDMX dataflows and convert them to a simplified JSON format. It includes
dataclasses for representing the JSON structure and functions to extract metadata
from SDMX objects.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Literal, Any

from absl import app
from absl import flags

import sdmx
from sdmx.model.internationalstring import InternationalString, DEFAULT_LOCALE
from sdmx.model.common import FacetType, FacetValueType


def _get_localized_string(obj: Optional[InternationalString]) -> str:
    """
    Safely get localized string from an InternationalString object.
    In the SDMX model, names and descriptions are multilingual.
    This function assumes a default locale like 'en' and returns the string
    for that locale, or an empty string if not available.
    """
    if isinstance(obj, InternationalString) and obj:
        try:
            return obj.localized_default(DEFAULT_LOCALE)
        except Exception as e:
            # Fallback if localized_default fails
            logging.warning("Failed to get localized string from %r: %s", obj, e)
            return str(obj) if obj else ""
    return ""


@dataclass
class Code:
    """Represents a single Code within a Codelist."""
    id: str
    name: str = ""
    description: str = ""


@dataclass
class CodelistDetails:
    """Represents the details of a Codelist, including its Codes."""
    id: str
    name: str = ""
    description: str = ""
    codes: List[Code] = field(default_factory=list)


@dataclass
class FacetDetails:
    """Represents a single Facet for non-enumerated representations."""
    type: str  # Corresponds to sdmx.model.common.FacetType, e.g., 'string', 'integer'
    value: Optional[str] = None
    value_type: Optional[
        str] = None  # Corresponds to sdmx.model.common.FacetValueType


@dataclass
class RepresentationDetails:
    """
    Describes the permissible values for a Dimension, Attribute, or Measure.
    It can be either enumerated (using a Codelist) or non-enumerated (using Facets).
    """
    type: Literal["enumerated", "non-enumerated"]
    codelist: Optional[
        CodelistDetails] = None  # Present if type is "enumerated"
    facets: List[FacetDetails] = field(
        default_factory=list)  # Present if type is "non-enumerated"


@dataclass
class ConceptDetails:
    """Represents the Concept associated with a Component (Dimension, Attribute, Measure)."""
    id: str
    name: str = ""
    description: str = ""
    concept_scheme_id: Optional[
        str] = None  # The ID of the ConceptScheme it belongs to


@dataclass
class ComponentDetails:
    """
    A base structure for Dimensions, Attributes, and Measures, as they share common properties.
    Each is a Component of a data structure.
    """
    id: str
    name: str = ""
    description: str = ""
    concept: Optional[ConceptDetails] = None
    representation: Optional[RepresentationDetails] = None


@dataclass
class DataStructureDefinitionDetails:
    """
    Represents the Data Structure Definition (DSD) associated with a Dataflow.
    It describes the dimensions, attributes, and measures of the data.
    """
    id: str
    name: str = ""
    description: str = ""
    dimensions: List[ComponentDetails] = field(
        default_factory=list)  # Each is a DimensionComponent
    attributes: List[ComponentDetails] = field(
        default_factory=list)  # Each is a DataAttribute
    measures: List[ComponentDetails] = field(
        default_factory=list
    )  # Each is a PrimaryMeasure (v2.1) or Measure (v3.0)


@dataclass
class ReferencedConceptSchemeDetails:
    """Represents a ConceptScheme and its Concepts referenced within the Dataflow."""
    id: str
    name: str = ""
    description: str = ""
    concepts: List[ConceptDetails] = field(default_factory=list)


@dataclass
class DataflowSomeAttributes:
    """
    A collection of additional attributes for the Dataflow, corresponding to
    properties of a MaintainableArtefact and VersionableArtefact.
    """
    version: Optional[str] = None  # A version string
    valid_from: Optional[str] = None  # Date from which the dataflow is valid
    valid_to: Optional[str] = None  # Date from which the dataflow is superseded
    is_final: Optional[
        bool] = None  # True if the object is final; otherwise it is in a draft state
    is_external_reference: Optional[
        bool] = None  # True if the content of the object is held externally
    service_url: Optional[str] = None  # URL of an SDMX-compliant web service
    structure_url: Optional[str] = None  # URL of an SDMX-ML document


@dataclass
class DataflowStructure:
    """
    Represents a single Dataflow object, corresponding to
    sdmx.model.common.BaseDataflow (e.g., v21.DataflowDefinition or v30.Dataflow).
    """
    id: str
    name: str = ""
    description: str = ""
    some_attributes: Optional[DataflowSomeAttributes] = None
    data_structure_definition: Optional[DataStructureDefinitionDetails] = None
    referenced_concept_schemes: List[ReferencedConceptSchemeDetails] = field(
        default_factory=list)


@dataclass
class MultiDataflowOutput:
    """The root object for multiple dataflows, containing the 'dataflows' key."""
    dataflows: List[DataflowStructure] = field(default_factory=list)


def write_dataclass_to_json(dataclass_obj, output_path: str) -> None:
    """
    Write any dataclass to JSON file.

    Args:
        dataclass_obj: Any dataclass instance to be written to JSON
        output_path: Path to the output JSON file
    """
    with open(output_path, 'w') as f:
        # Filter out None, empty strings, and empty lists
        # but preserve False and 0 which may be meaningful
        clean_dict = asdict(dataclass_obj,
                            dict_factory=lambda x: {
                                k: v for k, v in x if v not in (None, '', [])
                            })
        json.dump(clean_dict, f, indent=2)


def _get_concept_details(concept: Any) -> Optional[ConceptDetails]:
    """Extract details for a Concept object."""
    if not concept:
        return None

    concept_scheme_id = None
    try:
        if hasattr(concept, 'get_scheme') and concept.get_scheme():
            concept_scheme_id = concept.get_scheme().id
        elif hasattr(concept, 'scheme') and concept.scheme:
            concept_scheme_id = concept.scheme.id
    except Exception as e:
        logging.warning(
            f"Could not get concept scheme for concept {concept.id}: {e}")

    return ConceptDetails(
        id=concept.id,
        name=_get_localized_string(concept.name),
        description=_get_localized_string(concept.description),
        concept_scheme_id=concept_scheme_id,
    )


def _get_representation_details(
        representation: Any) -> Optional[RepresentationDetails]:
    """Extract details for a Representation object (enumerated or non-enumerated)."""
    if not representation:
        return None

    if representation.enumerated:
        codelist = representation.enumerated  # This is a Codelist object
        codes = []
        try:
            for _, code in codelist.items.items(
            ):  # Codelist.items is a DictLike collection of Code objects
                codes.append(
                    Code(
                        id=code.id,
                        name=_get_localized_string(code.name),
                        description=_get_localized_string(code.description),
                    ))
        except Exception as e:
            logging.warning(
                f"Error processing codes for codelist {codelist.id}: {e}")

        return RepresentationDetails(
            type="enumerated",
            codelist=CodelistDetails(
                id=codelist.id,
                name=_get_localized_string(codelist.name),
                description=_get_localized_string(codelist.description),
                codes=codes,
            ),
        )
    elif representation.non_enumerated:
        facets = []
        try:
            for facet in representation.non_enumerated:  # Representation.non_enumerated is a list of Facet objects
                facets.append(
                    FacetDetails(
                        type=str(facet.type.name) if isinstance(
                            facet.type, FacetType) else str(facet.type),
                        value=str(facet.value)
                        if facet.value is not None else None,
                        value_type=str(facet.value_type.name) if isinstance(
                            facet.value_type, FacetValueType) else str(
                                facet.value_type),
                    ))
        except Exception as e:
            logging.warning(f"Error processing facets: {e}")

        return RepresentationDetails(
            type="non-enumerated",
            facets=facets,
        )

    return None


def process_all_dataflows_in_structure_message(sm: Any) -> MultiDataflowOutput:
    """
    Process an SDMX StructureMessage and extract metadata for all dataflows.

    Args:
        sm: The SDMX StructureMessage object containing dataflows and related structures

    Returns:
        MultiDataflowOutput dataclass containing all dataflows structure

    Raises:
        Exception: For errors during extraction
    """
    try:
        dataflows = []

        for dataflow_id, dataflow_obj in sm.dataflow.items():
            dsd_obj = dataflow_obj.structure

            # Populate DataflowSomeAttributes
            some_attrs = DataflowSomeAttributes(
                version=str(dataflow_obj.version)
                if dataflow_obj.version else None,
                valid_from=str(dataflow_obj.valid_from)
                if dataflow_obj.valid_from else None,
                valid_to=str(dataflow_obj.valid_to)
                if dataflow_obj.valid_to else None,
                is_final=getattr(dataflow_obj, 'is_final', None),
                is_external_reference=getattr(dataflow_obj,
                                              'is_external_reference', None),
                service_url=getattr(dataflow_obj, 'service_url', None),
                structure_url=getattr(dataflow_obj, 'structure_url', None),
            )

            # Populate DataStructureDefinitionDetails
            dsd_details = DataStructureDefinitionDetails(
                id=dsd_obj.id,
                name=_get_localized_string(dsd_obj.name),
                description=_get_localized_string(dsd_obj.description),
            )

            # Populate dimensions
            if hasattr(dsd_obj, 'dimensions') and dsd_obj.dimensions:
                for dim_component in dsd_obj.dimensions.components:
                    dsd_details.dimensions.append(
                        ComponentDetails(
                            id=dim_component.id,
                            name=_get_localized_string(
                                dim_component.concept_identity.name)
                            if dim_component.concept_identity else "",
                            description=_get_localized_string(
                                dim_component.concept_identity.description)
                            if dim_component.concept_identity else "",
                            concept=_get_concept_details(
                                dim_component.concept_identity),
                            representation=_get_representation_details(
                                dim_component.local_representation),
                        ))

            # Populate attributes
            if hasattr(dsd_obj, 'attributes') and dsd_obj.attributes:
                for attr_component in dsd_obj.attributes.components:
                    dsd_details.attributes.append(
                        ComponentDetails(
                            id=attr_component.id,
                            name=_get_localized_string(
                                attr_component.concept_identity.name)
                            if attr_component.concept_identity else "",
                            description=_get_localized_string(
                                attr_component.concept_identity.description)
                            if attr_component.concept_identity else "",
                            concept=_get_concept_details(
                                attr_component.concept_identity),
                            representation=_get_representation_details(
                                attr_component.local_representation),
                        ))

            # Populate measures
            if hasattr(dsd_obj, 'measures') and dsd_obj.measures:
                for measure_component in dsd_obj.measures.components:
                    dsd_details.measures.append(
                        ComponentDetails(
                            id=measure_component.id,
                            name=_get_localized_string(
                                measure_component.concept_identity.name)
                            if measure_component.concept_identity else "",
                            description=_get_localized_string(
                                measure_component.concept_identity.description)
                            if measure_component.concept_identity else "",
                            concept=_get_concept_details(
                                measure_component.concept_identity),
                            representation=_get_representation_details(
                                measure_component.local_representation),
                        ))

            # Populate referenced concept schemes (shared across all dataflows)
            referenced_concept_schemes = []
            if hasattr(sm, 'concept_scheme') and sm.concept_scheme:
                for cs_id, concept_scheme in sm.concept_scheme.items():
                    concepts_in_scheme = []
                    try:
                        for _, concept_item in concept_scheme.items.items():
                            concepts_in_scheme.append(
                                ConceptDetails(
                                    id=concept_item.id,
                                    name=_get_localized_string(
                                        concept_item.name),
                                    description=_get_localized_string(
                                        concept_item.description),
                                    concept_scheme_id=concept_scheme.id))
                    except Exception as e:
                        logging.warning(
                            f"Error processing concepts in scheme {cs_id}: {e}")

                    referenced_concept_schemes.append(
                        ReferencedConceptSchemeDetails(
                            id=concept_scheme.id,
                            name=_get_localized_string(concept_scheme.name),
                            description=_get_localized_string(
                                concept_scheme.description),
                            concepts=concepts_in_scheme,
                        ))

            # Assemble the DataflowStructure
            dataflow_structure = DataflowStructure(
                id=dataflow_obj.id,
                name=_get_localized_string(dataflow_obj.name),
                description=_get_localized_string(dataflow_obj.description),
                some_attributes=some_attrs,
                data_structure_definition=dsd_details,
                referenced_concept_schemes=referenced_concept_schemes,
            )

            dataflows.append(dataflow_structure)

        return MultiDataflowOutput(dataflows=dataflows)

    except Exception as e:
        e.add_note("Error processing structure message for all dataflows")
        raise


def extract_dataflow_metadata(input_metadata: str, output_path: str) -> None:
    """
    Extracts comprehensive metadata for all SDMX dataflows from a local file
    and writes it to a JSON output file.

    This function is useful for testing and offline processing of SDMX metadata.

    Args:
        input_metadata: Path to the SDMX file containing the dataflow metadata
        output_path: Path to the output JSON file

    Raises:
        FileNotFoundError: If the input file does not exist
        Exception: For other errors during extraction or parsing
    """
    try:
        logging.info(f"Loading SDMX metadata from file: {input_metadata}")

        # Read the SDMX file using the sdmx library
        sm = sdmx.read_sdmx(input_metadata)

        result = process_all_dataflows_in_structure_message(sm)
        write_dataclass_to_json(result, output_path)

    except FileNotFoundError as e:
        e.add_note(f"SDMX file not found: {input_metadata}")
        raise
    except Exception as e:
        e.add_note(f"Failed to extract metadata from {input_metadata}")
        raise


if __name__ == '__main__':
    # Flag definitions are placed here to avoid conflicts when this module
    # is imported. When used as a library, callers use extract_dataflow_metadata()
    # directly without needing CLI flags.
    FLAGS = flags.FLAGS
    flags.DEFINE_string('input_metadata', None, 'Path to input SDMX XML file')
    flags.DEFINE_string('output_path', None, 'Path to output JSON file')
    flags.mark_flag_as_required('input_metadata')
    flags.mark_flag_as_required('output_path')

    def main(unused_argv) -> None:
        """Main entry point for the SDMX metadata extractor CLI tool."""
        extract_dataflow_metadata(FLAGS.input_metadata, FLAGS.output_path)

    app.run(main)
