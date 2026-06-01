from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import requests
import os
from dotenv import load_dotenv
import argparse

# Pre-parse --env-file before building the main parser, whose defaults are read
# from the environment. Load .env as the base config, then let a custom env file
# (via --env-file or the ENV_FILE env var) override individual values.
env_parser = argparse.ArgumentParser(add_help=False)
env_parser.add_argument('--env-file', required=False, default=os.getenv("ENV_FILE"),
                        help='additional .env file whose values override .env')
env_args, _ = env_parser.parse_known_args()

load_dotenv(dotenv_path=".env")
if env_args.env_file:
    load_dotenv(dotenv_path=env_args.env_file, override=True)

# Define your InfluxDB 2.0 connection details
url = os.getenv("INFLUXDB_BASE_URL", "http://localhost:8086")
influxDbToken = os.getenv("INFLUXDB_TOKEN")
org = os.getenv("INFLUXDB_ORG")
bucket = os.getenv("INFLUXDB_BUCKET")
# Parse command line arguments
parser = argparse.ArgumentParser(
    description='HEP mjerni podaci', parents=[env_parser])
parser.add_argument('--username', required=False, default=os.getenv("HEP_USERNAME"),
                    help='username (default: HEP_USERNAME env var)')
parser.add_argument('--password', required=False, default=os.getenv("HEP_PASSWORD"),
                    help='password (default: HEP_PASSWORD env var)')
parser.add_argument('--direction', required=False, default='P',
                    help='smjer struje (P ili R) - default P - P oznacava potrosnju, R proizvodnju')
parser.add_argument('--month', required=False,
                    help='mjesec za koji se preuzimaju podaci, format: MM.YYYY gdje je MM mjesec, a YYYY godina')

args = parser.parse_args()

if not args.username or not args.password:
    parser.error(
        "username and password are required (set HEP_USERNAME/HEP_PASSWORD in the env file or pass --username/--password)")

# Define date format
date_input_format = "%m.%Y"
date_format = "%Y-%m-%dT%H:%M:%S"
username = args.username
password = args.password


def login(username, password):
    # Log in and return an authenticated session. The API sets an `accessToken`
    # cookie on the session, which is sent automatically on subsequent requests.
    session = requests.Session()
    login_url = "https://mjerenje.hep.hr/mjerenja/v1/api/user/login"
    login_data = {
        "Username": username,
        "Password": password
    }
    response = session.post(login_url, json=login_data)

    # Check if the login was successful before parsing the response
    if response.status_code != 200:
        print("Login failed")
        print(response.text)
        exit(1)

    print("Login successful")
    # The response body is the buyer list (KupacList) directly.
    buyerList = response.json()
    return session, buyerList


session, buyerList = login(username, password)

measurementPlaces = []
for buyer in buyerList:
    for place in buyer["OmmList"]:
        measurementPlaces.append(place)
# print(f"measurementPlaces: {measurementPlaces}")


def write_power_data(org, bucket, args, date_format, location_code, data, write_api):
    for record in data:
        point = Point("preuzeta_struja" if args.direction == "P" else "predana_struja").tag("mjerno_mjesto", location_code).field(
            "snaga", float(record["Value"].replace(",", "."))).time(datetime.strptime(record["Datum"], date_format).astimezone(tz=ZoneInfo("Europe/Berlin")), WritePrecision.NS)
        write_api.write(bucket=bucket, org=org, record=point)


def get_data(place, location_code, month_formatted, direction):
    data_url = f"https://mjerenje.hep.hr/mjerenja/v1/api/data/omm/{location_code}/krivulja/mjesec/{month_formatted}/smjer/{direction}"
    response = session.post(data_url)
    if response.status_code != 200:
        print(f"Failed to retrieve data for place {place['Sifra']}")
        print(response.text)
        print(response.status_code)
        exit(1)
    return response


def retrieve_data(month: datetime, place, direction: str, write_api):
    location_code = place["Sifra"]
    month_formatted = month.strftime("%m.%Y")
    # url
    response = get_data(place, location_code,
                        month_formatted, direction)
    print(f"Data for place {place['Sifra']} retrieved successfully")
    data = response.json()
    # print(data)
    # Write data to InfluxDB
    write_power_data(org, bucket, args, date_format,
                     location_code, data, write_api)


with InfluxDBClient(url=url, token=influxDbToken, org=org) as client:
    write_api = client.write_api(write_options=SYNCHRONOUS)
    for place in measurementPlaces:
        month = datetime.strptime(
            args.month, date_input_format) if args.month else datetime.strptime(place["MjesecDo"], date_format)
        retrieve_data(month, place, args.direction, write_api)
