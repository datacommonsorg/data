
HEADERS = {'content-type' : 'application/json'}

COLUMNS_SELECTOR_URL = "https://nces.ed.gov/ccd/elsi/export.aspx/ExportToCSV"

COLUMNS_SELECTOR = {"sSection": "tableGenerator",
                    "sZipCode": "",
                    "sZipMiles": "",
                    "sState": "",
                    "sCountyValue": "",
                    "sDistrictValue": "",
                    "sTableTitle": "",
                    "sTableID": "",
                    "sState": "",
                    "sLevel": None,
                    "sYear": "",
                    "lYearsSelected":None,
                    "lColumnsSelected":None,
                    "lFilterNames": [["State","Static"]],
                    "lFilterData": [["all"]],
                    "lFilterYears": [[]],
                    "lFilterMasterData": [[]],
                    "lFilterTitles": ["State"],
                    "sGroupByColumn": "0",
                    "sNYCMerged": "false"
}

COMPRESS_FILE_URL = "https://nces.ed.gov/ccd/elsi/export.aspx/CompressFile"

COMPRESS_FILE = {
    "sFileName": None
}

DOWNLOAD_URL = 'https://nces.ed.gov/{compressed_src_file}'

COLUMNS_TO_DOWNLOAD_WITH_SINGLE_API_CALL = 60