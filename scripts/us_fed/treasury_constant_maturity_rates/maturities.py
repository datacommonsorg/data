'''
Maturities for which interest rates are provided by BEA.
Treasury bills have maturities of a year or less, notes greater than 1 year up
to 10 years, and bonds greater than 10 years.
'''
MATURITIES = {
    "1-month": "Bill", "3-month": "Bill", "6-month": "Bill",
    "1-year": "Bill", "2-year": "Note", "3-year": "Note", "5-year": "Note",
    "7-year": "Note", "10-year": "Note", "20-year": "Bond", "30-year": "Bond"
}
