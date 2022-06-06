"""
File to provide the URLs of input files to download.py
"""
website = 'https://ec.europa.eu/eurostat/'
link = 'estat-navtree-portlet-prod/BulkDownloadListing?file=data/'
input_files = [
    "hlth_ehis_pe9e.tsv.gz", "hlth_ehis_pe9i.tsv.gz", "hlth_ehis_pe9u.tsv.gz",
    "hlth_ehis_pe1e.tsv.gz", "hlth_ehis_pe1i.tsv.gz", "hlth_ehis_pe1u.tsv.gz",
    "hlth_ehis_pe3e.tsv.gz", "hlth_ehis_pe3i.tsv.gz", "hlth_ehis_pe3u.tsv.gz",
    "hlth_ehis_pe2e.tsv.gz", "hlth_ehis_pe2i.tsv.gz", "hlth_ehis_pe2u.tsv.gz",
    "hlth_ehis_pe9b.tsv.gz", "hlth_ehis_pe9c.tsv.gz", "hlth_ehis_pe9d.tsv.gz",
    "hlth_ehis_pe2m.tsv.gz", "hlth_ehis_de9.tsv.gz"
]
input_urls = [f'{website}{link}{x}' for x in input_files]
