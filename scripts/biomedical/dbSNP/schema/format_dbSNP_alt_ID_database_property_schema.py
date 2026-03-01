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
Author:  Samantha Piekos
Date:  09/30/20
Name:  format_dbSNP_alt_ID_database_property_schema.py
Description: Write all unique databases that have alternative IDs for genetic 
variant for a .vcf or .txt input file as properties of GeneticVariant.

@file_input	input .vcf or .txt file of genetic variants
@file_output	mcf output file recording all databases with alternative IDs for
		genetic variants as properties of GeneticVariant
'''

import sys
import re


def make_camel_case(item):
    """
	Converts string with words seperated by '_' to camel case.

	@item	string whose words are separated by '_'
	@return	string that is in camel case
	"""
    camel_item = ""
    l = item.split('_')
    if len(l) > 2:
        for i in l:
            if len(i) > 2:
                i = i.lower()
                camel_item = camel_item + i.capitalize()
    else:
        return ()
    # make sure first character of the name is lowercase
    camel_item = camel_item[0].lower() + camel_item[1:]
    return camel_item


def clean_alt_db_IDs(item):
    '''
	Replace unusual characters and fix typos in the names of databases with 
	alternative IDs for genetic variants.
	@item	string of database with alternative IDs for genetic variants than 
		rsIDs
	@return	cleaned up string of database with alternative IDs for genetic 
		variants than rsIDs
	'''
    # remove end of line characters and other undesirable characters
    item = item.strip('\r\n')
    item = item.strip("'")
    item = item.replace("'", "")
    item = item.replace("\\x2c_", "_")  # replace unusual characters
    item = item.replace("\\x2c", "_")
    item = item.replace('_@_', '_')
    item = item.replace("\\x59_", "_")
    item = item.replace('_-_', '_')
    item = item.replace('&', 'and')
    item = item.replace('/', '_')
    item = item.replace('.', '_')
    item = item.replace('-', '_')
    if item.startswith('eiden'):
        item = 'L' + item
    if item.startswith('llumina'):
        item = 'I' + item
    item = re.sub(r'\([^)]*\)', '', item)  # remove text in parantheses
    item = make_camel_case(item)  # convert property name to camel case
    return item


def collect_alt_db_IDs(db_IDs, set_alt_db_IDs):
    '''
	For each genetic variant instance add all databases with an alternative ID
	for it to a set.
	@db_IDs		string of all databases with alternative IDs for a given 
			genetic variant instance
	@set_alt_db_IDs	set of all databases with alternative IDs for the genetic 
			variant
	@return		set of all databases with alternative IDs for genetic 
			variants
	'''
    list_existing_ID_prop = ['dbvar', 'clinvar', 'pharmgkb']
    pops = db_IDs.split(',')
    for item in pops:
        # remove those with existing schema
        if item.lower() in list_existing_ID_prop or len(item) == 0:
            return (set_alt_db_IDs)
        item = clean_alt_db_IDs(item.split(':')[0])
        if item and re.match("^[a-zA-Z]+.*", item):
            set_alt_db_IDs.add(item)
    return set_alt_db_IDs


def compile_freq_pop_list(file_input):
    '''
	Compile list of all populations for genetic variant frequencies.
	@file_input	input .vcf or .txt file of genetic variants
	@return		unique list of all populations recording genetic variant 
			frequencies
	'''
    set_alt_db_IDs = set()
    f = open(file_input, mode='r')
    for line in f:
        line = line.strip('\r\n').split('\t')
        values = line[7].split(';')
        for item in values:
            if item.startswith("CLNVI="):
                set_alt_db_IDs = collect_alt_db_IDs(item.strip('CLNVI='),
                                                    set_alt_db_IDs)
    return list(set_alt_db_IDs)


def check_database_ID_length(list_alt_db_IDs):
    '''
	Double check that all the dcids generated using the database names will be 
	less than 256 characters. Print out database names that fail this check and 
	truncate it.

	@list_alt_db_IDs		unique list of all populations recording genetic 
					variant frequencies
	@list_alt_db_IDs_truncated	unique list of all populations recording genetic 
					variant frequencies with names limited to first 
					137 characters
	'''
    list_alt_db_IDs_truncated = []
    for item in list_alt_db_IDs:
        if len(item) > 254:
            print('This database name exceeds the length allowed for dcids: ' +
                  item)
            print('Truncated database name to the first 137 characters.')
            item = item[0:254]
        list_alt_db_IDs_truncated.append(item)
    return list_alt_db_IDs_truncated


def write_mcf(file_output, list_alt_db_IDs):
    '''
	Write all populations recording genetic variant frequencies as enums of 
	class GenVarSourceEnum to an output mcf file.
	@file_output	mcf output file recording all databases with alternative IDs
			for genetic variants as properties of GeneticVariant
	@return		unique list of all populations recording genetic variant 
			frequencies
	'''
    w = open(file_output, mode='w')
    w.write(
        '# Generated by script format_dbSNP_alt_ID_database_property_schema')
    w.write('.py\n\n')
    for item in list_alt_db_IDs:
        w.write('Node: dcid:' + item + 'ID\n')
        w.write('name: "' + item + 'ID"\n')
        w.write('typeOf: schema:Property\n')
        w.write('rangeIncludes: schema:Text\n')
        w.write('domainIncludes: dcs:GeneticVariant\n')
        w.write('description: "The ID used by database ' +
                re.sub(r"\B([A-Z])", r" \1", item.capitalize()) +
                ' for a genetic variant."\n')
        w.write("\n")


def main():
    file_input = sys.argv[1]
    file_output = sys.argv[2]
    list_alt_db_IDs = compile_freq_pop_list(file_input)
    list_alt_db_IDs_truncated = check_database_ID_length(list_alt_db_IDs)
    write_mcf(file_output, list_alt_db_IDs_truncated)


if __name__ == "__main__":
    main()
