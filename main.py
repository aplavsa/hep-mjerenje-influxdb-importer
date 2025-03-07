from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import requests
import os
from dotenv import load_dotenv
import argparse
load_dotenv()
# Define your InfluxDB 2.0 connection details
url = "http://localhost:8086"
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

measurementPlaces = []
for buyer in buyerList:
    for place in buyer["OmmList"]:
        measurementPlaces.append(place)
# print(f"measurementPlaces: {measurementPlaces}")
for place in measurementPlaces:
    month = datetime.strptime(
        args.month, date_input_format) if args.month else datetime.strptime(place["MjesecDo"], date_format)
    data_url = f"https://mjerenje.hep.hr/mjerenja/v1/api/data/omm/{place["Sifra"]}/krivulja/mjesec/{month.strftime("%m.%Y")}/smjer/{args.direction}"
    response = requests.post(
        data_url, headers={"Authorization": f"Bearer {token}"})
    if response.status_code == 200:
        print(f"Data for place {place['Sifra']} retrieved successfully")
        data = response.json()
        print(data)
        # Write data to InfluxDB
        client = InfluxDBClient(url=url, token=influxDbToken, org=org)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        for record in data:
            point = Point("preuzeta_struja" if args.direction == "P" else "predana_struja").tag("mjerno_mjesto", place["Sifra"]).field(
                "snaga", float(record["Value"].replace(",", "."))).time(datetime.strptime(record["Datum"], date_format).astimezone(tz=ZoneInfo("Europe/Berlin")), WritePrecision.NS)
            write_api.write(bucket=bucket, org=org, record=point)
    else:
        print(f"Failed to retrieve data for place {place['Sifra']}")
        print(response.text)
        print(response.status_code)
        exit(1)
