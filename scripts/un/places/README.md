# UN Geography to Data Commons Places Mapping

This directory (`data/scripts/un/places`) contains the definitions and mappings from United Nations (UN) geography codes to **Data Commons (DC) Places**.

These mappings are used across UN data imports (e.g., UN SDG indicators, UN Data) to resolve UN geographic entities to structured nodes in the Data Commons Knowledge Graph (`BaseGeos`).

## Directory Contents

* **`un_places.csv`**: The authoritative mapping table linking UN geography codes to Data Commons identifiers (`dcid`), place types (`typeOf`), names, parent hierarchies (`containedInPlace`), and external identifiers (`wikidataId`, `UnDataCode`).
* **`un_places.tmcf`**: The Template MCF (mapping schema) that instructs the Data Commons import pipeline how to construct Place nodes in the Knowledge Graph from rows in `un_places.csv`.

---

## How UN Can Add New Places

When the UN introduces new geographic regions, administrative areas, or reporting entities that do not yet exist in Data Commons, you can propose adding them directly by creating or updating entries in **`un_places.csv`**.

Once merged, these places are imported into the Data Commons base Knowledge Graph (`BaseGeos`) and become available for entity resolution and statistical observation (`StatVarObs`) imports.

### 1. Overview of `un_places.csv` Columns

The columns in `un_places.csv` fall into two categories: **UN Reference Columns** (from the UN geography specification) and **Data Commons Mapping Columns** (used by `un_places.tmcf` to generate Place nodes).

#### UN Reference Columns
* **`CONCEPT`**: Classification concept (typically `"GEOGRAPHY"`).
* **`CODE`**: The UN geographic identifier code (e.g., `G00000010`, `G00000020`).
* **`NAME_EN`**: The original English name in the UN geographic classification.
* **`PARENT`**: The parent UN geographic code in the UN classification tree.
* **`SORT_ORDER`**: Optional display or sorting order.

#### Data Commons Mapping Columns (Used by `un_places.tmcf`)
When defining or updating a place for Data Commons, you must populate the following columns:

| Column | TMCF Property | Description & Guidelines |
| :--- | :--- | :--- |
| **`dcid`** | `dcid: C:UN->dcid` | The unique Data Commons Identifier.<br>• **Existing DC Places**: If the place already exists in Data Commons (e.g., countries like `country/AFG`), use the existing DCID.<br>• **New Places**: Format as `<prefix>/<identifier>` where `<prefix>` is lowercase and `<identifier>` is alphanumeric (with optional `_` or `/`). For UN places, use `undata-geo/<CODE>` (e.g., `undata-geo/G00000010`). Always use stable codes rather than names that may change over time. |
| **`typeOf`** | `typeOf: C:UN->typeOf` | The Data Commons class type in the Place hierarchy.<br>• **Must be a subclass of `Place`**: Never use `Place` by itself; always use a specific subclass such as `Country`, `City`, `AdministrativeArea1`, etc.<br>• **Geographic Regions**:<br>&nbsp;&nbsp;– Use **`UnGeoRegion`** if the region is specific to the UN.<br>&nbsp;&nbsp;– Use **`GeoRegion`** if the region is likely to be used by other sources outside the UN.<br>• Multiple types can be comma-separated if applicable (e.g., `Country,Country,Place`). |
| **`name`** | `name: C:UN->name` | The primary English name of the place in Data Commons (e.g., `"Abu Dhabi"`). Ensure strings with commas or spaces are quoted in the CSV.<br>• **Single Primary Name Rule**: A place should only have **one** primary name. If an existing Data Commons `dcid` is mapped to the `CODE` and already has a primary name, do not overwrite or conflict with it; instead, put the UN-specific name into **`alternateName`** if it differs from the existing name. |
| **`alternateName`** | `alternateName: C:UN->alternateName` | *(Optional)* Alternative names, spellings, or designations.<br>• **Existing DC Places**: If mapping an existing `dcid` that already has a primary name in Data Commons, place any different UN-specific name or spelling here. |
| **`containedInPlace`** | `containedInPlace: C:UN->containedInPlace` | The parent place DCID(s) in Data Commons.<br>• **Immediate Parent Only**: This should be the **immediate parent** of the place. There is no need to list all parents transitively up to Earth; longer transitive lists in the file are shown only for easier human understanding.<br>• If the UN `PARENT` code does not map to a `dcid`, set an existing Data Commons parent place in this column. |
| **`Parent_dcid`** | `containedInPlace: C:UN->Parent_dcid` | The mapped parent Data Commons DCID.<br>• If the UN `PARENT` (or `PARENT_CODE`) maps directly to a Data Commons `dcid`, set it in this **`Parent_dcid`** column.<br>• Otherwise, set an existing place DCID in **`containedInPlace`**. |
| **`UnDataCode`** | `unDataCode: C:UN->UnDataCode` | The UN Data Code property value in Data Commons, formatted as `undata-geo:<CODE>` (e.g., `undata-geo:G00000010`). |
| **`wikidataId`** | `wikidataId: C:UN->wikidataId` | *(Optional but recommended)* The Wikidata item ID (e.g., `Q889`). Providing `wikidataId` enables Data Commons to resolve additional properties such as latitude/longitude coordinates (`location`) and multilingual names (`nameWithLanguage`). |
| **`Comment`** | *N/A* | Internal comments or notes regarding the mapping (e.g., duplicate checks, special notes). |

---

### 2. Step-by-Step Guide to Adding a Place

1. **Check Existing Places in Data Commons**:
   * Before adding a new place, search the [Data Commons Graph Browser](https://datacommons.org/browser/) to verify whether the entity already exists.
   * If it exists, map the UN code to the existing Data Commons `dcid` (e.g., `country/AFG`).

2. **Add a Row to `un_places.csv`**:
   * Create a new row in `un_places.csv` with your UN geography values (`CONCEPT`, `CODE`, `NAME_EN`, `PARENT`).
   * Define the **`dcid`**: Use `undata-geo/<CODE>` for new UN-specific geographic entities, or the existing DCID for established places.
   * Specify the **`typeOf`**:
     * Must be a subclass of `Place` such as `Country`, `City`, `AdministrativeArea1`, etc. (do not use `Place` by itself).
     * For regional groupings, use **`UnGeoRegion`** if the place is specific to the UN, or **`GeoRegion`** if it is likely to be used by other sources outside the UN.
   * Provide the **`name`** and **`alternateName`** values:
     * **For New Places (`undata-geo/<CODE>`)**: Provide the primary English name in **`name`**.
     * **For Existing Places (`country/AFG`, etc.)**: A place should only have one primary name. If the existing Data Commons place already has a primary name and the UN-specific name is different, put the UN-specific name into **`alternateName`** instead of changing `name`.
   * Define Parent Hierarchy (**`Parent_dcid`** & **`containedInPlace`**):
     * Specify the **immediate parent** only; there is no need to list all parents transitively.
     * If the UN `PARENT` code maps to a Data Commons `dcid`, set it in the **`Parent_dcid`** column.
     * Else, set any other existing place DCID in the **`containedInPlace`** column.
   * Fill in **`UnDataCode`** (`undata-geo:<CODE>`) and **`wikidataId`** (if available).

3. **Validate the CSV using the `dc-import` Tool**:
   * To validate `un_places.csv`, run the **`dc-import` tool** as described in the [Data Commons Import Tool Documentation](https://github.com/datacommonsorg/import#using-import-tool).
   * Check the generated reports and logs for any validation **errors or warnings** (such as schema syntax issues, missing columns, or unresolvable node references).
   * Also ensure that:
     * Text fields containing commas or special characters are properly enclosed in double quotes (`"`).
     * There are no duplicate `dcid` entries across the file.
     * Every parent DCID referenced in `Parent_dcid` or `containedInPlace` exists in Data Commons or is defined in this CSV.

4. **Submit a Pull Request**:
   * Submit your changes to `un_places.csv` via a Pull Request.
   * Once reviewed and merged, the Data Commons pipeline will ingest the new places into the base Knowledge Graph (`BaseGeos`), making them resolvable for subsequent statistical data imports.

---

## Reference: Template MCF Schema (`un_places.tmcf`)

The `un_places.tmcf` file defines how rows in `un_places.csv` are converted into Data Commons `Place` nodes:

```tmcf
Node: E:UN->E0
typeOf: C:UN->typeOf
dcid: C:UN->dcid
name: C:UN->name
alternateName: C:UN->alternateName
unDataCode: C:UN->UnDataCode
containedInPlace: C:UN->containedInPlace
containedInPlace: C:UN->Parent_dcid
wikidataId: C:UN->wikidataId
```

When the import pipeline executes, each row in `un_places.csv` generates a corresponding node (`E0`) in Data Commons with the properties specified above.
