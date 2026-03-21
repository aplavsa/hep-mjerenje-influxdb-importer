from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import requests
import os
from dotenv import load_dotenv
import argparse
load_dotenv(dotenv_path=".pi.env", override=True)
# Define your InfluxDB 2.0 connection details
url = os.getenv("INFLUXDB_BASE_URL", "http://localhost:8086")
influxDbToken = os.getenv("INFLUXDB_TOKEN")
org = os.getenv("INFLUXDB_ORG")
bucket = os.getenv("INFLUXDB_BUCKET")
# Parse command line arguments
parser = argparse.ArgumentParser(description='HEP mjerni podaci')
parser.add_argument('--username', required=True, help='username')
parser.add_argument('--password', required=True, help='password')
parser.add_argument('--direction', required=False, default='P',
                    help='smjer struje (P ili R) - default P - P oznacava potrosnju, R proizvodnju')
parser.add_argument('--month', required=False,
                    help='mjesec za koji se preuzimaju podaci, format: MM.YYYY gdje je MM mjesec, a YYYY godina')

args = parser.parse_args()

# Define date format
date_input_format = "%m.%Y"
date_format = "%Y-%m-%dT%H:%M:%S"
username = args.username
password = args.password


def get_token(username, password):
    # Perform a POST request to the login endpoint
    login_url = "https://mjerenje.hep.hr/mjerenja/v1/api/user/login"
    login_data = {
        "Username": username,
        "Password": password
    }
    response = requests.post(login_url, json=login_data)

    buyerList = response.json()["KupacList"]

    print(f"KupacList: {buyerList}")

    token = response.json()["Token"]

    print(f"Token: {token}")

    # Check if the login was successful
    if response.status_code == 200:
        print("Login successful")
        # Extract token or other necessary information from the response if needed
        # token = response.json().get("token")
    else:
        print("Login failed")
        print(response.text)
        exit(1)
    return token, buyerList


token, buyerList = get_token(username, password)

measurementPlaces = []
for buyer in buyerList:
    for place in buyer["OmmList"]:
        measurementPlaces.append(place)
# print(f"measurementPlaces: {measurementPlaces}")


def write_power_data(org, bucket, args, date_format, location_code, data, client):
    write_api = client.write_api(write_options=SYNCHRONOUS)
    for record in data:
        point = Point("preuzeta_struja" if args.direction == "P" else "predana_struja").tag("mjerno_mjesto", location_code).field(
            "snaga", float(record["Value"].replace(",", "."))).time(datetime.strptime(record["Datum"], date_format).astimezone(tz=ZoneInfo("Europe/Berlin")), WritePrecision.NS)
        write_api.write(bucket=bucket, org=org, record=point)


def get_data(token, place, location_code, month_formatted, direction):
    data_url = f"https://mjerenje.hep.hr/mjerenja/v1/api/data/omm/{location_code}/krivulja/mjesec/{month_formatted}/smjer/{direction}"
    response = requests.post(
        data_url, headers={"Authorization": f"Bearer {token}"})
    if response.status_code != 200:
        print(f"Failed to retrieve data for place {place['Sifra']}")
        print(response.text)
        print(response.status_code)
        exit(1)
    return response


def retrieve_data(month: datetime, place, direction: str):
    location_code = place["Sifra"]
    month_formatted = month.strftime("%m.%Y")
    # url
    response = get_data(token, place, location_code,
                        month_formatted, direction)
    print(f"Data for place {place['Sifra']} retrieved successfully")
    data = response.json()
    # print(data)
    # Write data to InfluxDB
    client = InfluxDBClient(url=url, token=influxDbToken, org=org)
    write_power_data(org, bucket, args, date_format,
                     location_code, data, client)


for place in measurementPlaces:
    # parameters
    month = datetime.strptime(
        args.month, date_input_format) if args.month else datetime.strptime(place["MjesecDo"], date_format)
    location_code = place["Sifra"]
    month_formatted = month.strftime("%m.%Y")
    direction = args.direction
    # url
    response = get_data(token, place, location_code,
                        month_formatted, direction)
    print(f"Data for place {place['Sifra']} retrieved successfully")
    data = response.json()
    # print(data)
    # Write data to InfluxDB
    client = InfluxDBClient(url=url, token=influxDbToken, org=org)
    write_power_data(org, bucket, args, date_format,
                     location_code, data, client)
