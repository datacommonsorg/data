# OECD Bulk Import

This folder contains scripts for the bulk OECD import.

Note: This was a very quick first pass attempt to get some data in, so only contains a few hundred of the OECD datasets that follow a specific format.

TODO(nhdiaz): Add tests / get remaining data.

To download data: 
```
OPENSSL_CONF=openssl.cnf python3 download.py
```

To process data and generate artifacts:
```
python3 process.py
```