import sys

def determine_tag(seq_role):
	if seq_role == 'fix-patch':
		return 'fix'
	if seq_role == 'novel-patch':
		return 'alt'
	print('Error: Sequence Role not recognized: ' + seq_role)
	return seq_role


def format_ucsc_name(line):
	seq_role, chrom, name = line[1], line[2], line[4]
	seq_role = determine_tag(seq_role)
	name = name.replace('.', 'v')
	ucsc_name = 'chr' + chrom + '_' + name + '_' + seq_role
	return ucsc_name


def generate_dcid_to_file(file_genome, genome_assembly):
	l = []
	f = open(file_genome, 'r')
	for line in f:
		line = line.strip('\r\n').split('\t')
		refseq, ucsc_name = line[6], line[9]
		if refseq == 'na':
			continue
		elif ucsc_name == 'na':
			ucsc_name = format_ucsc_name(line)
		dcid = 'dcid:bio/' + genome_assembly + '_' + ucsc_name
		l.append((refseq, dcid))
	f.close()
	return l


def write_to_file(file_output, hg19_dcids, hg19_patch13_dcids, hg38_dcids, hg38_patch14_dcids):
	output = open(file_output, 'w')
	output.write('RefSeqID\tchromosome_dcid\n')
	for l in [hg19_dcids, hg19_patch13_dcids, hg38_dcids, hg38_patch14_dcids]:
		for item in l:
			output.write(('\t').join(item) + '\n')
	output.close()


def convert_refseq_ID_to_dcid(file_hg19, file_hg38, file_hg19_patch13, file_hg38_patch14, file_output):
	hg19_dcids = generate_dcid_to_file(file_hg19, 'hg19')
	hg19_patch13_dcids = generate_dcid_to_file(file_hg19_patch13, 'hg19')
	hg38_dcids = generate_dcid_to_file(file_hg38, 'hg38')
	hg38_patch14_dcids = generate_dcid_to_file(file_hg38_patch14, 'hg38')
	write_to_file(file_output, hg19_dcids, hg19_patch13_dcids, hg38_dcids, hg38_patch14_dcids)


def main():
	file_hg19 = sys.argv[1]
	file_hg19_patch13 = sys.argv[2]
	file_hg38 = sys.argv[3]
	file_hg38_patch14 = sys.argv[4]
	file_output = sys.argv[5]
	convert_refseq_ID_to_dcid(file_hg19, file_hg19_patch13, file_hg38, file_hg38_patch14, file_output)


if __name__ == '__main__':
    main()
