# HEP Mjerenje → InfluxDB Exporter

Python skripta koja preuzima mjerne podatke o potrošnji/proizvodnji električne energije
sa [mjerenje.hep.hr](https://mjerenje.hep.hr) i sprema ih u InfluxDB bazu za vizualizaciju
u Grafani.

*A small Python script that pulls electricity consumption/production data from the HEP
(Hrvatska elektroprivreda) metering portal and writes it into InfluxDB for visualization
in Grafana.*

## How it works

1. Logs in to the HEP metering API with your portal credentials and obtains a bearer token.
2. Discovers every metering point (*mjerno mjesto*) tied to your account.
3. For each metering point, downloads the monthly load curve (*krivulja*) for the chosen
   direction — consumption or production.
4. Writes each reading to InfluxDB as a time-series point.

### Data model in InfluxDB

| InfluxDB element | Value |
|------------------|-------|
| Measurement      | `preuzeta_struja` (consumption, `P`) or `predana_struja` (production, `R`) |
| Tag              | `mjerno_mjesto` — the metering point code (*Šifra*) |
| Field            | `snaga` — power reading (float) |
| Timestamp        | Reading time, interpreted in the `Europe/Berlin` timezone |

## Requirements

- Python 3.9+ (uses `zoneinfo` from the standard library)
- A reachable InfluxDB 2.x instance (token, org, bucket)
- HEP metering portal account

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install --requirement requirements.txt
```

## Configuration

The script reads its configuration from a **`.env`** file in the project root
(loaded automatically at startup). Create it with the following variables:

```dotenv
# HEP metering portal credentials
HEP_USERNAME=<your email or username>
HEP_PASSWORD=<your password>

# InfluxDB 2.x connection
INFLUXDB_BASE_URL=http://localhost:8086
INFLUXDB_TOKEN=<your influxdb token>
INFLUXDB_ORG=<your influxdb organization>
INFLUXDB_BUCKET=<your influxdb bucket>
```

`INFLUXDB_BASE_URL` is optional and defaults to `http://localhost:8086`.

### Overriding with a custom env file

`.env` is always loaded as the base configuration. You can layer a second file on
top to override individual values — useful for per-host settings (e.g. a Raspberry
Pi) without duplicating the whole config:

```bash
python3 main.py --env-file .pi.env      # .env values, overridden by .pi.env
ENV_FILE=.pi.env python3 main.py        # same, via env var (handy for cron)
```

Only the keys present in the custom file override `.env`; everything else falls back
to `.env`.

> **Note:** `.env` (and any `*.env` file) is gitignored, so your credentials never
> get committed.

## Usage

With credentials set in `.env`, a plain run imports the most recent available month
for every metering point on the account:

```bash
python3 main.py
```

### Importing a specific month or direction

```bash
python3 main.py --month 09.2023 --direction P
```

### Options

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--month` | no | latest available month per metering point | Month to import, format `MM.YYYY` |
| `--direction` | no | `P` | `P` = consumption (*potrošnja*), `R` = production (*predaja*) |
| `--username` | no | `HEP_USERNAME` env var | Overrides the portal username for a one-off run |
| `--password` | no | `HEP_PASSWORD` env var | Overrides the portal password for a one-off run |
| `--env-file` | no | `ENV_FILE` env var | Extra env file whose values override `.env` |

If neither the env var nor the corresponding flag provides a username and password,
the script exits with an error.

## Scheduling

To keep InfluxDB updated automatically (e.g. on a Raspberry Pi), run the script from
`cron`. The following imports the current month's consumption every day at 06:00:

```cron
0 6 * * * cd /path/to/mjerenje && /path/to/venv/bin/python3 main.py >> import.log 2>&1
```

## Contributing

Contributions are welcome:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit (`git commit -am 'Add new feature'`).
5. Push (`git push origin feature-branch`).
6. Open a Pull Request.
