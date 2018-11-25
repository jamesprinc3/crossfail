import datetime
import re
from typing import List

from flask import Flask, render_template, request
import googlemaps
import csv

import config

app = Flask(__name__)
gmaps = googlemaps.Client(key=config.goglemaps_api_key)

def canonicalise_station_name(station_name: str):
    if "Station" not in station_name:
        station_name += " Station"
    station_name += " UK"
    return station_name


def read_csv():
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



@app.route('/')
def hello():
    return render_template('home.html')

@app.route('/result')
def my_form_post():
    home_postcode = request.args.get('home').upper()
    work_postcode = request.args.get('work').upper()

    postcode_regex = re.compile('([Gg][Ii][Rr] 0[Aa]{2})|((([A-Za-z][0-9]{1,2})|(([A-Za-z][A-Ha-hJ-Yj-y][0-9]{1,2})|(([A-Za-z][0-9][A-Za-z])|([A-Za-z][A-Ha-hJ-Yj-y][0-9][A-Za-z]?))))\s?[0-9][A-Za-z]{2})')
    if postcode_regex.match(home_postcode) is None or postcode_regex.match(work_postcode) is None:
        return render_template('home.html', warning="Invalid input, try again!")
    try:
        response = gmaps.directions(home_postcode,
                                    work_postcode,
                                    mode="transit",
                                    arrival_time=datetime.datetime(2018, 11, 19, 9, 0, 0))

        route = response[0]['legs'][0]
        current_journey_time = route['duration']['value']

        start_address = route['start_address']
        end_address = route['end_address']

        time_csv_rows = read_csv()
        time_csv_dict = generate_dict(time_csv_rows)
        all_stations = list(set(map(lambda row: row[0], time_csv_rows)))

        matrix = gmaps.distance_matrix([start_address, end_address], all_stations)

        magic = list(zip(
            map(lambda rows: list(zip(map(lambda element: element['duration']['value'], rows['elements']), all_stations)),
                matrix['rows']), [start_address, end_address]))

        magic_sorted = list(map(lambda x: sorted(x[0], key=lambda y: y[0]), magic))

        closest_to_origin = magic_sorted[0][0][1]
        closest_to_destination = magic_sorted[1][0][1]

        if closest_to_origin == closest_to_destination:
            return render_template('bad_result.html')

        crossrail_time_in_mins = time_csv_dict[(closest_to_origin, closest_to_destination)]

        origin_to_crossrail = magic_sorted[0][0][0]
        crossrail_to_destination = magic_sorted[1][0][0]

        new_journey_time = round((origin_to_crossrail + (int(crossrail_time_in_mins) * 60) + crossrail_to_destination) / 60)

        current_journey_time_in_mins = round(current_journey_time / 60)
        saving_minutes_day = (current_journey_time_in_mins-new_journey_time)*2

        if saving_minutes_day > 0:
            saving_minutes_week = saving_minutes_day * 5
            total_hours_wasted = round((saving_minutes_week * 52)/60)

            return render_template('good_result.html',
                                   home_postcode=home_postcode,
                                   work_postcode=work_postcode,
                                   current_journey_time=current_journey_time_in_mins,
                                   crossrail_journey_time=new_journey_time,
                                   saving_minutes_day=saving_minutes_day,
                                   saving_minutes_week=saving_minutes_week,
                                   total_hours_wasted=total_hours_wasted)
        else:
            return render_template('bad_result.html')
    except Exception as e:
        render_template('home.html',
                        warning="Something went wrong, our code monkeys are aware and are trying to fix the situation")


if __name__ == '__main__':
    app.run()
