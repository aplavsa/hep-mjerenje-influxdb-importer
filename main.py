from datetime import datetime
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
args = parser.parse_args()
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
print(f"measurementPlaces: {measurementPlaces}")
for place in measurementPlaces:
    data_url = f"https://mjerenje.hep.hr/mjerenja/v1/api/data/omm/{place["Sifra"]}/krivulja/mjesec/02.2025/smjer/P"
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
            point = Point("preuzeta_struja").tag("mjerno_mjesto", place["Sifra"]).field(
                "snaga", float(record["Value"].replace(",", "."))).time(datetime.strptime(record["Datum"], date_format), WritePrecision.NS)
            write_api.write(bucket=bucket, org=org, record=point)
    else:
        print(f"Failed to retrieve data for place {place['Sifra']}")
        print(response.text)
        print(response.status_code)
        exit(1)
# # Create an InfluxDB client
# client = InfluxDBClient(url=url, token=token, org=org)

# # Write data to InfluxDB
# write_api = client.write_api(write_options=SYNCHRONOUS)
# point = Point("measurement_name").tag("tag_key", "tag_value").field(
#     "field_key", 1.0).time(datetime.utcnow(), WritePrecision.NS)
# write_api.write(bucket=bucket, org=org, record=point)

# # Query data from InfluxDB
# query_api = client.query_api()
# query = f'from(bucket: "{bucket}") |> range(start: -1h)'
# tables = query_api.query(query, org=org)

# for table in tables:
#     for record in table.records:
#         print(record)

# # Close the client
# client.close()
