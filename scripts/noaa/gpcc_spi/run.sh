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

# Reconcile historical drought events and observations with the production baseline
# (to prevent event DCID churn and Pearson refit threshold dropouts) and generate
# companion node_mcf files for events (input3) and event_svobs (input4).
python3 -c '
import csv
import io

events_csv = "output_files/events_spi_9m_polygon/events/drought_spi_9m_polygon_events.csv"
svobs_csv = "output_files/events_spi_9m_polygon/event_svobs/drought_spi_9m_polygon_svobs.csv"
place_svobs_csv = "output_files/events_spi_9m_polygon/place_svobs/drought_spi_9m_polygon_place_svobs.csv"
events_nodes_mcf = "output_files/events_spi_9m_polygon/events/drought_spi_9m_polygon_events_nodes.mcf"
svobs_nodes_mcf = "output_files/events_spi_9m_polygon/event_svobs/drought_spi_9m_polygon_svobs_nodes.mcf"

INT_COLS = ("DurationDays", "numberOfDays", "AffectedPlaceCount", "count")

def normalize_ints(row):
    for k in INT_COLS:
        if k in row and isinstance(row[k], float) and row[k].is_integer():
            row[k] = int(row[k])
    return row

def read_csv_rows(path_or_text, is_text=False):
    f = io.StringIO(path_or_text) if is_text else open(path_or_text, "r", encoding="utf-8", newline="")
    with f:
        reader = csv.DictReader(
            f, escapechar="\\", quotechar="\"", quoting=csv.QUOTE_NONNUMERIC
        )
        rows = [normalize_ints(r) for r in reader]
        return reader.fieldnames, rows

def write_csv_rows(path, fieldnames, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            escapechar="\\",
            quotechar="\"",
            quoting=csv.QUOTE_NONNUMERIC,
            doublequote=False,
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(normalize_ints(r))

def get_grid_cells(row):
    return {
        p.replace("dcid:", "").strip()
        for p in str(row.get("affectedPlace", "")).split(",")
        if "grid_1/" in p
    }

try:
    from google.cloud import storage
    client = storage.Client()
    base_prefix = "scripts/noaa/gpcc_spi/NOAA_GPCC_StandardardizedPrecipitationIndex"
    bucket = None
    latest_ver = None
    for b_name in ("datcom-prod-imports", "datcom-import-test"):
        try:
            b_cand = client.bucket(b_name)
            v_cand = b_cand.blob(f"{base_prefix}/latest_version.txt").download_as_text().strip()
            if v_cand:
                bucket = b_cand
                latest_ver = v_cand
                print(f"Reconciling against baseline {b_name}/{base_prefix}/{latest_ver}")
                break
        except Exception:
            continue
    if not bucket or not latest_ver:
        raise RuntimeError("Could not load latest_version.txt from GCS")

    _, b_ev_rows = read_csv_rows(
        bucket.blob(f"{base_prefix}/{latest_ver}/drought_spi_9m_polygon_events.csv").download_as_text(),
        is_text=True,
    )
    _, b_sv_rows = read_csv_rows(
        bucket.blob(f"{base_prefix}/{latest_ver}/drought_spi_9m_polygon_svobs.csv").download_as_text(),
        is_text=True,
    )
    _, b_pl_rows = read_csv_rows(
        bucket.blob(f"{base_prefix}/{latest_ver}/drought_spi_9m_polygon_place_svobs.csv").download_as_text(),
        is_text=True,
    )

    ev_fields, c_ev_rows = read_csv_rows(events_csv)
    sv_fields, c_sv_rows = read_csv_rows(svobs_csv)
    pl_fields, c_pl_rows = read_csv_rows(place_svobs_csv)

    b_ev_by_dcid = {r["dcid"]: r for r in b_ev_rows}
    c_ev_by_dcid = {r["dcid"]: r for r in c_ev_rows}
    b_cells = {r["dcid"]: get_grid_cells(r) for r in b_ev_rows}
    c_cells = {r["dcid"]: get_grid_cells(r) for r in c_ev_rows}

    c_by_sd_cell = {}
    for c_dcid, r in c_ev_by_dcid.items():
        sd = r["startDate"]
        for cell in c_cells[c_dcid]:
            c_by_sd_cell.setdefault((sd, cell), []).append(c_dcid)

    used_b = set(b_ev_by_dcid) & set(c_ev_by_dcid)
    used_c = set(used_b)
    remap_c_to_b = {}

    # Pass 1: match baseline seed cell inside current polygon on same startDate
    for b_dcid, r in b_ev_by_dcid.items():
        if b_dcid in used_b:
            continue
        sd = r["startDate"]
        idx = b_dcid.find("grid_1/")
        seed_cell = b_dcid[idx:] if idx != -1 else ""
        for c_dcid in c_by_sd_cell.get((sd, seed_cell), []):
            if c_dcid not in used_c:
                remap_c_to_b[c_dcid] = b_dcid
                used_b.add(b_dcid)
                used_c.add(c_dcid)
                break

    # Pass 2: match best overlapping grid cell set on same startDate
    for b_dcid, r in b_ev_by_dcid.items():
        if b_dcid in used_b:
            continue
        sd = r["startDate"]
        candidates = {}
        for cell in b_cells[b_dcid]:
            for c_dcid in c_by_sd_cell.get((sd, cell), []):
                if c_dcid not in used_c:
                    candidates[c_dcid] = candidates.get(c_dcid, 0) + 1
        if candidates:
            best_c = max(candidates, key=candidates.get)
            remap_c_to_b[best_c] = b_dcid
            used_b.add(b_dcid)
            used_c.add(best_c)

    reconciled_ev = {}
    for r in c_ev_rows:
        r = dict(r)
        c_dcid = r["dcid"]
        if c_dcid in remap_c_to_b:
            b_dcid = remap_c_to_b[c_dcid]
            b_row = b_ev_by_dcid[b_dcid]
            r["dcid"] = b_dcid
            r["name"] = b_row["name"]
            r["startLocation"] = b_row["startLocation"]
            if str(b_row.get("endDate", "")) > str(r.get("endDate", "")):
                r["endDate"] = b_row["endDate"]
        elif c_dcid in b_ev_by_dcid:
            b_row = b_ev_by_dcid[c_dcid]
            if str(b_row.get("endDate", "")) > str(r.get("endDate", "")):
                r["endDate"] = b_row["endDate"]
        reconciled_ev[r["dcid"]] = r

    for b_dcid, r in b_ev_by_dcid.items():
        if b_dcid not in reconciled_ev:
            reconciled_ev[b_dcid] = r

    reconciled_sv = {}
    for r in c_sv_rows:
        r = dict(r)
        c_dcid = r["dcid"]
        if c_dcid in remap_c_to_b:
            r["dcid"] = remap_c_to_b[c_dcid]
        reconciled_sv[(r["dcid"], r["observationDate"])] = r

    for r in b_sv_rows:
        k = (r["dcid"], r["observationDate"])
        if k not in reconciled_sv:
            reconciled_sv[k] = r

    reconciled_pl = {
        (r["observationAbout"], r["observationDate"], r["observationPeriod"]): r
        for r in c_pl_rows
    }
    for r in b_pl_rows:
        k = (r["observationAbout"], r["observationDate"], r["observationPeriod"])
        if k not in reconciled_pl:
            reconciled_pl[k] = r

    write_csv_rows(events_csv, ev_fields, list(reconciled_ev.values()))
    write_csv_rows(svobs_csv, sv_fields, list(reconciled_sv.values()))
    write_csv_rows(place_svobs_csv, pl_fields, list(reconciled_pl.values()))
    print(
        f"Reconciled rows -> events: {len(reconciled_ev)}, "
        f"svobs: {len(reconciled_sv)}, place_svobs: {len(reconciled_pl)}"
    )
except Exception as e:
    print(f"Warning: baseline reconciliation skipped: {e}")

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
