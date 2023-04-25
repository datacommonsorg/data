# load environment
import pandas as pd
import sys


# declare universal variables
DICT_CHANGE_ENUM = {
'abolished': 'VirusLastTaxonomicChangeAbolished',\
'demoted' : 'VirusLastTaxonomicChangeDemoted',\
'merged': 'VirusLastTaxonomicChangeMerged',\
'moved': 'VirusLastTaxonomicChangeMoved',\
'new': 'VirusLastTaxonomicChangeNew',\
'promoted': 'VirusLastTaxonomicChangePromoted',\
'removed as type species': 'VirusLastTaxonomicChangeRemoved',\
'renamed': 'VirusLastTaxonomicChangeRenamed',\
'split': 'VirusLastTaxonomicChangeSplit'
}


DICT_GC = {
'dsDNA': 'VirusGenomeCompositionDoubleStrandedDNA',\
'ssDNA': 'VirusGenomeCompositionSingleStrandedDNA',\
'ssDNA(-)': 'VirusGenomeCompositionSingleStrandedDNANegative',\
'ssDNA(+)': 'VirusGenomeCompositionSingleStrandedDNAPositive',\
'ssDNA(+/-)': 'VirusGenomeCompositionSingleStrandedDNA',\
'dsDNA-RT': 'VirusGenomeCompositionDoubleStrandedDNAReverseTranscription',\
'ssRNA-RT': 'VirusGenomeCompositionSingleStrandedDNAReverseTranscription',\
'dsRNA': 'VirusGenomeCompositionDoubleStrandedRNA',\
'ssRNA': 'VirusGenomeCompositionSingleStrandedRNA',\
'ssRNA(-)': 'VirusGenomeCompositionSingleStrandedRNANegative',\
'ssRNA(+)': 'VirusGenomeCompositionSingleStrandedRNAPositive',\
'ssRNA(+/-)': 'VirusGenomeCompositionSingleStrandedRNA'
}


HEADER = [
'sort',\
'realm',\
'subrealm',\
'kingdom',\
'subkingdom',\
'phylum',\
'subphylum',\
'class',\
'subclass',\
'order',\
'suborder',\
'family',\
'subfamily',\
'genus',\
'subgenus',\
'species',\
'genomeComposition',\
'lastChange',\
'lastChangeVersion',\
'proposalForLastChange',\
'taxonHistoryURL',\
'dcid'
]


LIST_TAXONOMIC_LEVELS = [
'realm',\
'subrealm',\
'kingdom',\
'subkingdom',\
'phylum',\
'subphylum',\
'class',\
'subclass',\
'order',\
'suborder',\
'family',\
'subfamily',\
'genus',\
'subgenus'
]


# declare functions
def pascalcase(s):
	list_words = s.split()
	converted = "".join(word[0].upper() + word[1:].lower() for word in list_words)
	return converted


def check_for_illegal_charc(s):
	list_illegal = ["'", "–", "*" ">", "<", "@", "]", "[", "|", ":", ";" " "]
	if any([x in s for x in list_illegal]):
		print('Error! dcid contains illegal characters!', s)


def format_taxonomic_rank_properties(df, index, row):
	for rank in LIST_TAXONOMIC_LEVELS:
		if row[rank] == row[rank]:
			enum = 'Virus' + rank.upper() + pascalcase(row[rank])
			df.loc[index, rank] = enum
	return df


def convert_gc_to_enum(gc):
	list_enum = []
	list_gc = gc.split(';')
	for item in list_gc:
		item = item.strip()
		enum = DICT_GC[item]
		list_enum.append(enum)
	return (',').join(list_enum)


def convert_change_to_enum(change):
	list_enum = []
	change = change.lower()
	list_changes = change.split(',')[:-1]
	for item in list_changes:
		enum = DICT_CHANGE_ENUM[item]
		list_enum.append(enum)
	return (',').join(list_enum)


def clean_df(df):
	for index, row in df.iterrows():
		dcid = 'bio/' + pascalcase(row['species'])
		check_for_illegal_charc(dcid)
		df = format_taxonomic_rank_properties(df, index, row)
		df.loc[index, 'dcid'] = dcid
		df.loc[index,'genomeComposition'] = convert_gc_to_enum(row['genomeComposition'])
		df.loc[index, 'lastChange'] = convert_change_to_enum(row['lastChange'])
		df.loc[index, 'taxonHistoryURL'] = row['taxonHistoryURL'].strip('ICTVonline=')
	return df 


def clean_file(f, w):
	df = pd.read_excel(f, names=HEADER, header=None, sheet_name=2)
	df = df.drop('sort', axis=1).drop(0, axis=0)
	df = clean_df(df)
	df.to_csv(w, index=False)


def main():
	file_input = sys.argv[1]
	file_output = sys.argv[2]

	clean_file(file_input, file_output)


if __name__ == '__main__':
    main()
