# Importing  Data

## Table of Contents

1. [About the Dataset](#about-the-dataset)
    1. [Download URL](#download-url)
    2. [Database Overview](#database-overview)
    3. [Schema Overview](#schema-overview)
    4. [Notes and Caveats](#notes-and-caveats)
    5. [License](#license)
    6. [Dataset Documentation and Relevant Links](#dataset-documentation-and-relevant-links)
2. [About the Import](#about-the-import)
    1. [Artifacts](#artifacts)
    2. [Import Procedure](#import-procedure)


## About the Dataset

### Download URL

Files were [downloaded](https://www.encodeproject.org/help/getting-started/) from the ENCODE Consortium using their batch download feature.

### Database Overview

"The Encyclopedia of DNA Elements (ENCODE) Consortium is an ongoing international collaboration of research groups funded by the National Human Genome Research Institute (NHGRI). The goal of ENCODE is to build a comprehensive parts list of functional elements in the human genome, including elements that act at the protein and RNA levels, and regulatory elements that control cells and circumstances in which a gene is active.

ENCODE investigators employ a variety of assays and methods to identify functional elements. The discovery and annotation of gene elements is accomplished primarily by sequencing a diverse range of RNA sources, comparative genomics, integrative bioinformatic methods, and human curation. Regulatory elements are typically investigated through DNA hypersensitivity assays, assays of DNA methylation, and immunoprecipitation (IP) of proteins that interact with DNA and RNA, i.e., modified histones, transcription factors, chromatin regulators, and RNA-binding proteins, followed by sequencing." - [The ENCODE Consortium](https://www.encodeproject.org/help/project-overview/).

We have downloaded all bed (epigenomics data peak calls) and rpkm (transcritomics data) files available as of June 2019. This includes files across all species, biosamples, and assays. We also contain all of the meta data on the ENCODE Experiment, Award, Biosample, Biosample Type, Library, and Lab. Each line of a file was made into it's own node, which allows for querying of the data by genomic coordinates.

### Schema Overview

The schema representing data from NCBI assembly reports is represented in [encode.mcf](https://github.com/datacommonsorg/schema/tree/main/biomedical_schema/encode.mcf).

The ENCODE datasets contain instances of entities "BedLine", "EncodeAward", "EncodeBedFile", "EncodeBiosample", "EncodeBiosampleType", "EncodeExperiment", "EncodeLibrary", and "Lab". "BedLine" is a subclass of "EncodeBedFile" and is connected by property "fromBedFile". "EncodeAward", "EncodeBedFile", "EncodeBiosample", "EncodeBiosampleType", "EncodeExperiment", and "EncodeLibrary" are all subclasses of "EncodeObject". "EncodeBedFile" is connected to "EncodeExperiment" by property "fromExperiment". "EncodeBiosample" is connected to "EncodeAward", "EncodeBiosample", and "EncodeBiosampleType" by properties "award", "partOf", and "biosampleOntology" respectively. "EncodeExperiment" is also connected to "EncodeBiosampleType" by the property "biosampleOntology".

Although, not directly linked, "EncodeExperiment" award property "award" contains the url to the Encode award as it's value. Likewise, "Lab" contains url links to Encode Awards by property "awards". Although, not linked directly "EncodeBedFile", "EncodeBiosample", "EncodeExperiment", and "EncodeLibrary" all contain information on the "Lab" that generated the data. Finally, "EncodeLibrary" contains information on "EncodeBiosample" through property "biosample" although it's not linked directly.

Additional properties and information on the ENCODE schema can be found in the file [encode.mcf](https://github.com/datacommonsorg/schema/tree/main/biomedical_schema/encode.mcf).

### Notes and Caveats

We have not processed or normalized these files in anyway beyond the initial processing done by the ENCODE Consortium in accordance with their [pipelines](https://www.encodeproject.org/pipelines/). These files are presented the same as what is available for download from the ENCODE Consortium. Also, Google internal libraries were used for extracting the data from ENCODE and those scripts will not be able to run without substituting for publicly available libraries. Also, some links between different entities can be made by the user, but are not represented in the graph as noted in the schema subsection. This is because the data provided by querying ENCODE Consortium presented those connections as urls representing the information and not the id of the data of interest itself.

Note that the schema.py script automatically generates the schema. It does not generate the domainIncludes or rangeIncludes information for the classes or properties. This needs to be manually curated after the script is run to ensure proper linkage of the schema in the graph.

### License

This data is from the ENCODE Consortium and whose [data use agreement](https://www.encodeproject.org/help/citing-encode/) allows free data use with no restrictions. The ENCODE Consortium requests that researchers that use ENCODE data in publications or presentations [cite](https://www.encodeproject.org/help/citing-encode/) ENCODE in the following ways:
1. Cite the Consortium's most recent publications
2. Acknowledge the ENCODE Consortium and the ENCODE production laboratory(s) generating the particular dataset(s)
3. Reference the ENCODE accession numbers of the datasets (ENCSR...) and files (ENCFF...) used

### Dataset Documentation and Relevant Links

An overview of the ENCODE Consortium Project can be found [here](https://www.encodeproject.org/help/project-overview/). 

## About the import

### Artifacts

#### Scripts
`scraper.py` - Scrapes data from ENCDOE Consortium
`parser.py` - parses data into json or MCF file
`schema.py` - generates schema for ENCODE data

#### Files
`BUILD`
`enc_list.txt`
`parser.borg`
`terms.json`

### Import Procedure

#### Processing Steps 

To batch download the data from ENCODE Consortium run `scraper.py`.

```bash
python3 scraper.py
```
Then run `parser.py` to convert downloaded data into MCF format.

```bash
python3 parser.py
```

Finally, run `schema.py` to auto generate the schema for the downloaded ENCODE data.

```bash
python3 schema.py
```

#### Post-Processing Steps

We recommend manually adding the domainIncludes and rangeIncludes information for the classes and properties generated by schema.py. This ensures that the schema is properly linked in the graph.
