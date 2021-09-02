# India Post - Pincodes

## About the Dataset
[All India Pincode Directory](https://data.gov.in/node/6818285) is shared by Ministry of CommunicationsDepartment of Posts on data.go.in.

### Overview
All India Pincode Directory contains the Pincode list across India with relevant information like Circle Name, Region Name, Division Name, Office Name, Pincode, Office Type, Delivery, District, State Name. Postal Index Number (PIN or PIN Code) is a 6 digit code of Post Office numbering used by India Post. 

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
In this set, we will have unique pincodes along with the districts they belong.

- Pincode
- PincodeDCID
- District
- StateName
- DistrictLGDCode0
- DistrictLGDCode1
- DistrictLGDCode<N> - Can have N columns 

#### Template MCFs
- [IndiaPost_Pincodes.tmcf](IndiaPost_Pincodes.tmcf).

#### Scripts
- [preprocess.py](preprocess.py): Clean up and import script. The script also generates the TMCF file.

### Running Tests

```bash
# To run test cases specific to this process
python -m india_post.pincodes.preprocess_test

# TO run all test cases
python -m unittest discover -v -s scripts/ -p *_test.py
```
### Reconciliation
1. The districts are resolved using lgdCode, which is expected to be added to the KG first. All districts are expected to resolve.

### Import Procedure

To import data, run the following command:

```bash
python -m india_post.pincodes.preprocess
```