# Copyright 2020 Google LLC
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
'''
Author: Samantha Piekos
Date: 10/20/20
Name: format_NCBI_Chromosome
Description:  Converts an NIH NCBI assembly reports file on a genome assembly
    into a mcf output file populating information on GenomeAssembly,
    GenomeAssemblyUnit, and Chromosome.

@file_input    path to the input NCBI file on a genome assembly
@file_output    path to the output mcf file to write the reformatted data
@genome     the shorthand name for the genome assembly represented in the
        file (e.g. hg38, mm10)
@species_abrv    the abbreviation used by Data Commons to represent species dcid
        (e.g. hs, mm)
'''

import re


def format_camel_case(value):
    '''
    Format string to camel case.

    @value     The string that needs to be formatted to camel case
    @return    The camel case formatted string
    '''
    value = value.replace(' ', '')
    value_split = re.split('_|-', value)
    value_formatted = ''
    # camel case enum type
    for i in range(len(value_split)):
        value_formatted = value_formatted + 
        value_split[i][0].upper() + value_split[i][1:]
    return (value_formatted)

def write_genome_coverage(value, key, w):
    '''
    Convert genome coverareturn (value_formatted)ge value to integer and write to output.
    
    @value    The string that needs to be converted to an int
    @key.     The property name to write the value to
    @w        Output file to write to
    '''
    v = ''
    for i in value:
        if i.isdigit():
            v += i
    w.write(key + ': ' + v + '\n')

def write_genome_assembly(file_output, dict_genome_assembly, genome,
                          species_abrv):
    '''
    Write the information on the genome assembly to a GenomeAssembly node in the
    mcf output file.

    @file_output        path to the output mcf file to write the reformatted
                data
    @dict_genome_assembly    dictionary of the data fields and values containing
                information on the genome assembly
    @genome         the shorthand name for the genome assembly
                represented in the file (e.g. hg38, mm10)
    @species_abrv        the abbreviation used by Data Commons to represent
                species dcid (e.g. hs, mm)
    '''
    dict_conversion = {
        'Assembly name':
            'genomeReferenceConsortiumAssemblyName',
        'Description':
            'description',
        'Taxid':
            'ncbiTaxonID',
        'BioProject':
            'ncbiBioProject',
        'BioSample':
            'ncbiBioSample',
        'Submitter':
            'submitter',
        'Date':
            'date',
        'Assemblytype':
            'genomeAssemblyType',
        'Releasetype':
            'genomeAssemblyReleaseType',
        'Assemblylevel':
            'genomeAssemblyLevel',
        'Genomerepresentation':
            'isGenomeRepresentationFull',
        'RefSeqcategory':
            'refSeqCategory',
        'GenBankassemblyaccession':
            'genBankAssemblyAccession',
        'RefSeqassemblyaccession':
            'refSeqAssemblyAccession',
        'RefSeqassemblyandGenBankassembliesidentical':
            'isRefSeqGenBankAssembliesIdentical',
        'Assemblyname':
            'ncbiAssemblyName',
        'Infraspecificname':
            'infraspecificName',
        'Synonyms':
            'alternativeName',
        'WGSproject':
            'wgsProject',
        'Assemblymethod':
            'assemblyMethod',
        'GenomeCoverage':
            'genomeCoverage',
        'Sequencingtechnology':
            'sequencingTechnology',
        'Sex':
            'gender',
        'Organismname':
            'ofSpecies'
    }  # convert NCBI fields to property names
    list_key_enums = [
        'Assemblytype', 'Releasetype', 'RefSeqcategory', 'Assemblylevel'
    ]
    w = open(file_output, mode='a')
    w.write('Node: dcid:bio/' + genome + '\n')
    w.write('name: "' + genome + '"\n')
    w.write('typeOf: dcs:GenomeAssembly\n')
    w.write('ofSpecies: dcid:bio/' + species_abrv + '\n')
    for key, value in dict_genome_assembly.items():
        if key == 'Organism name':
            w.write(dict_conversion[key] + ': dcid:bio/' + species_abrv + '\n')
        elif key == 'RefSeqassemblyandGenBankassembliesidentical':
            if value.lower() == 'no':
                w.write(dict_conversion[key] + ': False\n')
            elif value.lower() == 'yes':
                w.write(dict_conversion[key] + ': True\n')
        elif key in list_key_enums:
            w.write(dict_conversion[key] + ': dcid:' +
                    format_camel_case(dict_conversion[key]) +
                    format_camel_case(value) + '\n')
        elif key == 'Genomerepresentation':
            if value.lower() == 'full':
                w.write(dict_conversion[key] + ': True\n')
            else:
                w.write(dict_conversion[key] + ': False\n')
        elif key == 'Infraspecificname':
            value = value.strip('strain=')
            w.write(dict_conversion[key] + ': "' + value + '"\n')
        elif key == 'Genomecoverage':
            write_genome_coverage(value, dict_conversion[key], w)
        elif key == 'Sex':
            value = 'dcs:' + value.lower().capitalize()
        elif key not in dict_conversion.keys():
            print('Warning: ' + key + ' is not represented as a property for' +
                  'GenomeAssembly')
        elif key != 'Organismname':
            w.write(dict_conversion[key] + ': "' + value + '"\n')


def write_assembly_unit(line, file_output, genome):
    '''
    Wrie a line on a genome assembly unit to a GenomeAssemblyUnit node in the
    mcf output file.

    @line        line containing information on a GenomeAssemblyUnit
    @file_output    path to the output mcf file to write the reformatted data
    @genome     the shorthand name for the genome assembly represented in
            the file (e.g. hg38, mm10)
    '''
    w = open(file_output, mode='a')
    line[0] = line[0].strip('## ')
    line[2] = line[2].replace(' ', '_')
    w.write('Node: dcid:bio/' + genome + '_' + line[2] + '\n')
    w.write('name:' + line[2] + '\n')
    w.write('typeOf: dcs:GenomeAssemblyUnit\n')
    w.write('inGenomeAssembly: dcid:bio/' + genome + '\n')
    w.write('genBankAccession: "' + line[0] + '"\n')
    w.write('refSeqAccession: "' + line[1] + '"\n\n')


def write_chromosome(line, file_output, genome):
    '''
    Wrie a line on a chromosome or unlocalized scaffold/fragment/sequence to a
    GenomeAssemblyUnit node in the mcf output file.

    @line        line containing information on a Chromosome
    @file_output    path to the output mcf file to write the reformatted data
    @genome     the shorthand name for the genome assembly represented in
            the file (e.g. hg38, mm10)
    '''
    list_chromosome = [
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13',
        '14', '15', '16', '17', '18', '19', '20', '21', '22', 'X', 'Y', 'MT'
    ]  # list of known defined chromosomes
    w = open(file_output, mode='a')
    w.write('Node: dcid:bio/' + genome + '_' + line[9] + '\n')
    w.write('name: "' + line[9] + '"\n')
    w.write('typeOf: dcs:Chromosome\n')
    w.write('ncbiDNASequenceName: "' + line[0] + '"\n')
    w.write('dnaSequenceRole: dcid:DNASequenceRole' +
            format_camel_case(line[1]) + '\n')
    w.write('inGenomeAssembly: dcid:bio/' + genome + '\n')
    if line[2] not in list_chromosome and line[3] != 'na':
        w.write('inChromosome: ' + genome + '_chr' + line[3] + '\n')
    w.write('genBankAccession:  "' + line[4] + '"\n')
    if line[6] != 'na':
        w.write('refSeqAccession: "' + line[6] + '"\n')
    w.write('inGenomeAssemblyUnit: dcid:bio/' + genome + '_' +
            line[7].replace(' ', '_') + '\n')
    w.write('chromosomeSize: [' + line[8] + ' BasePairs]\n\n')


def main():
    import sys
    file_input = sys.argv[1]  # import defined properties from command line
    file_output = sys.argv[2]
    genome = sys.argv[3]
    species_abrv = sys.argv[4]

    dict_genome_assembly = {}
    f = open(file_input, mode='r')
    is_genome_assembly = True
    for line in f:
        line = line.strip('\r\n').split('\t')
        if is_genome_assembly:
            line[0] = line[0].strip('#')
            if len(line[0]) == 0:
                is_genome_assembly = False
                continue
            key, value = line[0].split(':')
            dict_genome_assembly[key.replace(' ', '')] = ' '.join(value.split())
        elif (line[0].startswith('##') and len(line) == 3 and
              'Accession' not in line[1]):
            # write GenomeAssemblyUnit node
            write_assembly_unit(line, file_output, genome)
        elif line[0].startswith('#'):
            continue
        else:
            write_chromosome(line, file_output, genome)  # write Chromosome node
    # write GenomeAssembly node
    write_genome_assembly(file_output, dict_genome_assembly, genome,
                          species_abrv)


if __name__ == '__main__':
    main()
