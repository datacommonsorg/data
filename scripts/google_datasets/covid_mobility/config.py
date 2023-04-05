# Every row name in the CSV file is mapped to a Schema.org place.
# key = CSV's row name
# value = Schema.org place

PLACE_CATEGORIES: dict = {
    "retail_and_recreation_percent_change_from_baseline":
        "LocalBusiness",
    "grocery_and_pharmacy_percent_change_from_baseline":
        "GroceryStore&Pharmacy",
    "parks_percent_change_from_baseline":
        "Park",
    "transit_stations_percent_change_from_baseline":
        "TransportHub",
    "workplaces_percent_change_from_baseline":
        "Workplace",
    "residential_percent_change_from_baseline":
        "Residence"
}
