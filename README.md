# HEP Mjerenje InfluxDB Exporter

Python skripta koja kupi podatke sa mjerenje.hep.hr i ubacuje ih u InfluxDB bazu podataka za kasnije korištenje u Grafani

## Installation


```bash
pip install --requirement requirements.txt
```

## Usage

```bash
python3 main.py --username <your email or username> --password <your-password>
```

### Example

To run the script for a specific month and direction, use the following command:

```bash
python3 main.py --username <your email or username> --password <your-password> --month 09.2023 --direction P
```

- `--month` specifies the month and year in the format MM.YYYY.
- `--direction` specifies the direction of the current (P for consumption, R for production). The default is P.

### Environment Variables

Make sure to set the following environment variables in a `.env` file:

```plaintext
INFLUXDB_TOKEN=<your-influxdb-token>
INFLUXDB_ORG=<your-influxdb-organization>
INFLUXDB_BUCKET=<your-influxdb-bucket>
```


## Contributing
We welcome contributions to this project! To contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -am 'Add new feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Create a new Pull Request.

Please ensure your code adheres to our coding standards and includes appropriate tests.

Thank you for your contributions!