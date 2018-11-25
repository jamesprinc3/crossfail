import csv
import json
from typing import List

import requests

import config


def find_crossrail_station_distances(home, work, crossrail_stations):
    locations = list()
    locations.append({'id': 'home', 'coords': {"lat": home['lat'], "lng": home['lng']}})
    locations.append({'id': 'work', 'coords': {"lat": work['lat'], "lng": work['lng']}})
    for crossrail_station in crossrail_stations:
        locations.append({'id': crossrail_station['name'],
                          'coords': {
                              "lat": crossrail_station['lat'],
                              "lng": crossrail_station['lng']
                          }})

    arrival_searches = dict()

    one_to_many = list()
    one_to_many.append({
            "id": "closest_to_home",
            "arrival_location_ids": list(map(lambda s: s['name'], crossrail_stations)),
            "departure_location_id": "home",
            "transportation": {
              "type": "public_transport"
            },
            "arrival_time_period": "weekday_morning",
            "travel_time": 7200,
            "properties": [
              "travel_time"
            ]
          })

    many_to_one = list()
    many_to_one.append({
            "id": "closest_to_work",
            "arrival_location_id": "work",
            "departure_location_ids": list(map(lambda s: s['name'], crossrail_stations)),
            "transportation": {
              "type": "public_transport"
            },
            "arrival_time_period": "weekday_morning",
            "travel_time": 7200,
            "properties": [
              "travel_time"
            ]
          })

    arrival_searches['one_to_many'] = one_to_many
    arrival_searches['many_to_one'] = many_to_one

    request_dict = dict()
    request_dict['locations'] = locations
    request_dict['arrival_searches'] = arrival_searches

    headers = {'X-Application-Id': config.traveltime_app_id,
               'X-Api-Key': config.traveltime_api_key,
               'Content-Type': 'application/json'}

    resp = requests.post("https://api.traveltimeapp.com/v4/time-filter/fast",
                         json=request_dict,
                         headers=headers)

    return resp

def read_cr_lat_lng_csv():
    with open('crossrail_lat_lng.csv', 'r') as csvfile:
        lst = list()
        lines = csvfile.readlines()[1:]
        for line in lines:
            row = line.strip().split(',')
            lst.append({'name': row[0], 'lat': float(row[2]), 'lng': float(row[3])})
        return lst


def canonicalise_station_name(station_name: str):
    if "Station" not in station_name:
        station_name += " Station"
    return station_name


def read_time_csv():
    with open('time_matrix.csv', 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        lst = list()
        for row in reader:
            start = canonicalise_station_name(row[0])
            end = canonicalise_station_name(row[1])
            lst.append([start, end, row[2]])
        return lst


def generate_dict(rows: List[List[str]]):
    the_dict = {}
    for row in rows:
        the_dict[(row[0], row[1])] = row[2]
    return the_dict

def find_crossrail_time(home_lat_lng, work_lat_lng):
    crossrail_stations = read_cr_lat_lng_csv()
    distances = json.loads(find_crossrail_station_distances(home_lat_lng, work_lat_lng, crossrail_stations).content)

    results = list(map(lambda r: (r['search_id'], (sorted(r['locations'], key=lambda l: l['properties']['travel_time']))), distances['results']))
    closest_to_home = list(filter(lambda r: r[0] == "closest_to_home", results))[0][1][0]
    closest_to_work = list(filter(lambda r: r[0] == "closest_to_work", results))[0][1][0]

    if closest_to_home['id'] == closest_to_work['id']:
        return -100, closest_to_home['id'], closest_to_work['id']

    time_csv_rows = read_time_csv()
    time_csv_dict = generate_dict(time_csv_rows)
    time_on_crossrail = time_csv_dict[(closest_to_home['id'], closest_to_work['id'])]

    home_to_crossrail = closest_to_home['properties']['travel_time']
    work_to_crossrail = closest_to_work['properties']['travel_time']

    crossrail_journey_time = round((int(home_to_crossrail) + (int(time_on_crossrail)*60) + int(work_to_crossrail))/60)

    return crossrail_journey_time, closest_to_home['id'], closest_to_work['id']
