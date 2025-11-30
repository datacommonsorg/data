#!/bin/bash


echo "File split GCF_000001405.24 started"
split -l 15000000 input/GCF25/GCF_000001405.25.vcf input/GCF25/gcf25_shard_ --additional-suffix=.vcf
echo "File split GCF_000001405.40 started"
split -l 15000000 input/GCF40/GCF_000001405.40.vcf input/GCF40/gcf40_shard_ --additional-suffix=.vcf
echo "File split freq started"
split -l 30000000 input/freq/freq.vcf input/freq/freq_shard_ --additional-suffix=.vcf
