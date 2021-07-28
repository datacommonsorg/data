# India Post - Pincodes

## About the Dataset
[Local Government Directory](https://lgdirectory.gov.in/) is a complete directory of land regions/revenue, rural and urban local governments.

### Overview
[All India Pincode Directory](https://data.gov.in/node/6818285) is share by Ministry of CommunicationsDepartment of Posts on data.go.in.  All India Pincode Directory contains the pincode list across India with relevant information like Circle Name, Region Name, Division Name, Office Name, Pincode, Office Type, Delivery, District, State Name. Postal Index Number (PIN or PIN Code) is a 6 digit code of Post Office numbering used by India Post. 

- CircleName
- RegionName
- DivisionName
- OfficeName
- Pincode
- OfficeType
- Delivery
- District
- StateName
- Latitude
- Longitude


#### Cleaned Data
In this set we will have unique pincodes along with the districts they belong.

- Pincode
- PincodeDCID
- District
- StateName
- DistrictLGDCode

#### Template MCFs
- [IndiaPost_Pincodes.tmcf](IndiaPost_Pincodes.tmcf).

#### Scripts
- [preprocess.py](preprocess.py): Clean up and import script.

### Running Tests

```bash
python3 -m unittest discover -v -s scripts/ -p *_test.py
```

### Import Procedure

To import data, run the following command:

```bash
python -m india_post.pincodes.preprocess
```
