#!/bin/bash
set -e

# PATH=$PATH:$(dirname $0)
# # Sleep as long as N jobs of given name are running in background
# function num_jobs {
#   local name="$1"; shift;
#   if [[ "$name" == "" ]]; then
#     echo  $(jobs -r | wc -l)
#   else
#     echo $(ps -ef | egrep "$name" | wc -l)
#   fi
# }
# function sleep_while_active {
#   max_jobs=$1; shift
#   job_name="$1"; shift
#   j=$(num_jobs $job_name);
#   while (( $j > ${max_jobs:-0} )); do
#     sleep 10;
#     j=$(num_jobs $job_name);
#   done;
# }

config=spi_9m_polygon


# Run download script
python3 download.py

# Run NOAA_GPCC_StandardardizedPrecipitationIndex script
python3 preprocess_gpcc_spi.py

# Run NOAA_GPCC_StandardardizedPrecipitationIndex_AggPlace script
python3 gpcc_spi_aggregation.py

# shard data by year
echo "Creating a directory for the sharded files"
rm -rf output_files/shard "output_files/events_${config}"
mkdir -p output_files/shard

echo "Sharding pcc_spi_pearson_09.csv based on year and writing them to the shard folder."
bash ../../../tools/pd_csv.sh -i output_files/gpcc_spi_pearson_09.csv -o output_files/shard/gpcc_spi_pearson_09 "df=df.sort_values(by=['time', 'place'], kind='stable');df['year']=df['time'].str.slice(0,4)" -shard year


# Convert into events
set -x
years=$(ls output_files/shard/gpcc_spi_pearson_09*.csv | sed -e 's/.*-year-//;s/-.*//' | egrep -o "[0-9]{4}" | sort | uniq)
for yr in $years; do
  time python3 ../../earthengine/process_events.py \
  --config=events_drought_gpcc_${config}.py \
  --input_csv=output_files/shard/gpcc_spi_pearson_09-year-${yr}-*.csv \
  --output_path=output_files/events_${config}/drought_${config}_${yr}_ \
  --pprof_port=$((8180 + $yr )) \
  --place_cache_file=grid_1_contains.csv
#   2>&1 | tee tmp/events-$config-$yr.log &
  # sleep_while_active 10
done
wait

# bash scripts to merge multiple csv files into one file
input_folders=("output_files/events_spi_9m_polygon/events" "output_files/events_spi_9m_polygon/event_svobs" "output_files/events_spi_9m_polygon/place_svobs")
output_file_name=("drought_spi_9m_polygon_events" "drought_spi_9m_polygon_svobs" "drought_spi_9m_polygon_place_svobs")
index=0
echo "input_folders ${input_folders[@]} - output_file_name ${output_file_name[@]}"
for fld in "${input_folders[@]}"; do
	output_file="${fld}/${output_file_name[$index]}"
	rm -f "$output_file" "${output_file}.csv"
	csv_files=($(find "$fld" -type f -name "*.csv" | sort))
	echo "csv_files ${csv_files[@]}"
	echo "output_file $output_file"
	head -n 1 "${csv_files[0]}" > "$output_file"
	echo "index -----> $index"
	for file in "${csv_files[@]}"; do
		tail -n +2 "$file" >> "$output_file"
		echo "Processed_concatenate $file to $output_file file"
	done
	index=$((index+1))
	echo "index after increment $index"
	mv "$output_file" "${output_file}.csv"
	echo "Done processing $output_file"
done

# Generate companion node_mcf files for events (input3) and event_svobs (input4)
# so local resolution resolves all Quantity, GeoCoordinates, and DroughtEvent nodes.
python3 -c '
import csv

events_csv = "output_files/events_spi_9m_polygon/events/drought_spi_9m_polygon_events.csv"
svobs_csv = "output_files/events_spi_9m_polygon/event_svobs/drought_spi_9m_polygon_svobs.csv"
events_nodes_mcf = "output_files/events_spi_9m_polygon/events/drought_spi_9m_polygon_events_nodes.mcf"
svobs_nodes_mcf = "output_files/events_spi_9m_polygon/event_svobs/drought_spi_9m_polygon_svobs_nodes.mcf"

quantities = {}
latlongs = {}
event_dcids = set()

with open(events_csv, "r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f, escapechar="\\", quotechar="\"")
    for row in reader:
        dcid = row.get("dcid", "").strip()
        if dcid:
            event_dcids.add(dcid)
        area = row.get("area", "").strip().strip("\"")
        if area.startswith("[") and area.endswith("]"):
            parts = area[1:-1].strip().split()
            if len(parts) == 2:
                val, unit = parts[0], parts[1]
                q_dcid = f"{unit}{val}"
                if q_dcid not in quantities:
                    quantities[q_dcid] = (val, unit)
        loc = row.get("startLocation", "").strip().strip("\"")
        if loc.startswith("[") and loc.endswith("]"):
            parts = loc[1:-1].strip().split()
            if len(parts) == 3 and parts[0] == "LatLong":
                lat_f = float(parts[1])
                lon_f = float(parts[2])
                lat_i = int(round(lat_f * 100000.0))
                lon_i = int(round(lon_f * 100000.0))
                ll_dcid = f"latLong/{lat_i}_{lon_i}"
                if ll_dcid not in latlongs:
                    lat_s = f"{lat_i / 100000.0:.5f}"
                    lon_s = f"{lon_i / 100000.0:.5f}"
                    latlongs[ll_dcid] = (lat_s, lon_s)

with open(svobs_csv, "r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f, escapechar="\\", quotechar="\"")
    for row in reader:
        dcid = row.get("dcid", "").strip()
        if dcid:
            event_dcids.add(dcid)

with open(events_nodes_mcf, "w", encoding="utf-8") as f:
    for q_dcid, (val, unit) in sorted(quantities.items()):
        f.write(
            f"Node: dcid:{q_dcid}\n"
            f"dcid: \"{q_dcid}\"\n"
            f"name: \"{unit} {val}\"\n"
            f"typeOf: dcid:Quantity\n"
            f"unitOfMeasure: dcid:{unit}\n"
            f"value: {val}\n\n"
        )
    for ll_dcid, (lat_s, lon_s) in sorted(latlongs.items()):
        f.write(
            f"Node: dcid:{ll_dcid}\n"
            f"dcid: \"{ll_dcid}\"\n"
            f"name: \"{lat_s},{lon_s}\"\n"
            f"typeOf: dcid:GeoCoordinates\n"
            f"latitude: \"{lat_s}\"\n"
            f"longitude: \"{lon_s}\"\n\n"
        )

with open(svobs_nodes_mcf, "w", encoding="utf-8") as f:
    for dcid in sorted(event_dcids):
        f.write(
            f"Node: dcid:{dcid}\n"
            f"typeOf: dcs:DroughtEvent\n\n"
        )
'
