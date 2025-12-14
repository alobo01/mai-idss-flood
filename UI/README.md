## UI Database + Data Utilities

This README documents the database schema and helper scripts added in this UI workspace. Frontend (React) and backend (FastAPI) instructions will live in their own README files to be created separately; refer to those once available.

### Schema overview
Schema is initialized by `database/init/01-schema.sql` (mounted by `docker-compose.yml` to Postgres on container start). Tables and relationships:

```mermaid
erDiagram
	raw_data {
		date DATE PK
		daily_precip DOUBLE
		daily_temp_avg DOUBLE
		daily_snowfall DOUBLE
		daily_humidity DOUBLE
		daily_wind DOUBLE
		soil_deep_30d DOUBLE
		target_level_max DOUBLE
		hermann_level DOUBLE
		grafton_level DOUBLE
		created_at TIMESTAMPTZ
	}

	predictions {
		date DATE PK
		predicted_level DOUBLE
		flood_probability DOUBLE
		created_at TIMESTAMPTZ
	}

	zones {
		zone_id VARCHAR(4) PK
		name TEXT
		river_proximity DECIMAL(3,2)
		elevation_risk DECIMAL(3,2)
		pop_density DECIMAL(3,2)
		crit_infra_score DECIMAL(3,2)
		hospital_count INTEGER
		critical_infra BOOLEAN
	}

	zip_zones {
		zip_code CHAR(5) PK
		zone_id VARCHAR(4) FK
	}

	zip_geojson {
		zip_code CHAR(5) PK
		geojson JSONB
		created_at TIMESTAMPTZ
	}

	zones ||--o{ zip_zones : "maps"
	zip_zones ||--|| zip_geojson : "geojson per ZIP"
	raw_data ||--|| predictions : "by date"
```

Notes:
- `zones` and `zip_zones` are seeded via the init SQL; `zip_geojson` is created empty for later inserts.
- `raw_data` and `predictions` are keyed by `date`; `predictions.flood_probability` is constrained to 0–1.

### Scripts
- `UI/scripts/fetch_and_store_zip_geojson.py`: pulls ZIP polygons from the ArcGIS endpoint and upserts into `zip_geojson`. Optional `--output` writes the GeoJSON file too. Environment defaults match `docker-compose.yml` (`host localhost`, port `5439`, db `flood_prediction`, user `flood_user`, password `flood_password`).
- `UI/scripts/load_raw_dataset.py`: loads `database/demo_data/raw_dataset.csv` into `raw_data` with upserts on `date`.

### Database export/import
- **Scripts**: `UI/scripts/db_export.sh` and `UI/scripts/db_import.sh` — helpers to export and import the `flood_prediction` database from the running Postgres container.
- **Export (host file)**: `./UI/scripts/db_export.sh [output-file] [container-name]`
	- Default `output-file`: `flood_prediction.dump`
	- Default `container-name`: `flood-postgres`
	- Example: `./UI/scripts/db_export.sh mybackup.dump`
- **Import (from host file)**: `./UI/scripts/db_import.sh [dump-file] [container-name]`
	- Default `dump-file`: `flood_prediction.dump`
	- Example: `./UI/scripts/db_import.sh mybackup.dump`
- **What they do**: `db_export.sh` runs `pg_dump -Fc` inside the container and writes a Postgres custom-format dump to the host (streamed). `db_import.sh` streams the dump back into the container and runs `pg_restore -d flood_prediction`.
- **docker-compose alternatives**: if you prefer not to use the scripts, run these from the `UI/` directory:

```bash
docker compose exec -T postgres pg_dump -U flood_user -d flood_prediction -Fc > flood_prediction.dump
docker compose exec -T postgres pg_restore -U flood_user -d flood_prediction -v < flood_prediction.dump
```

- **Notes**: pass the container name if your compose project uses a different name; make the scripts executable with `chmod +x UI/scripts/*.sh`.


### Running with docker-compose
From `UI/`:
```bash
docker compose up
```
The init SQL at `database/init/01-schema.sql` will be applied automatically on first start (mounted into `/docker-entrypoint-initdb.d`).

### Running scripts locally
Install dependencies (if not already available):
```bash
pip install psycopg2-binary requests
```

Fetch and store ZIP geojson:
```bash
python UI/scripts/fetch_and_store_zip_geojson.py --output Data/zip_zones.geojson
```

Load the sample raw dataset:
```bash
python UI/scripts/load_raw_dataset.py --csv UI/database/demo_data/raw_dataset.csv
```

### Data
- Sample raw data CSV: `UI/database/demo_data/raw_dataset.csv` (dates, weather, target levels, river gauges).

### Frontend / Backend docs
- Frontend (React) and backend (FastAPI) documentation will be provided in their respective README files (to be added). Refer there for build/run steps once available.
