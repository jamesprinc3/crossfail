import datetime

import googlemaps
import pandas as pd
import requests

import config
import main
import json

gmaps = googlemaps.Client(key=config.goglemaps_api_key)


def canonicalise_station_name(station_name: str):
    if "JLE" in station_name:
        station_name = station_name.replace("JLE", "")
    if "Station" not in station_name:
        station_name += " Station"
    station_name += " UK"
    return station_name


df = pd.read_csv("tfl_data.csv")

underground_journeys = df.loc[df["SubSystem"] == "LUL"]
underground_journeys = underground_journeys.loc[underground_journeys["StartStn"] != "Unstarted"]
underground_journeys = underground_journeys.loc[underground_journeys["EndStation"] != "Unfinished"]
underground_journeys["JourneyTimeMinutes"] = underground_journeys.ExTime - underground_journeys.EntTime
popular_routes = underground_journeys.groupby(['StartStn', 'EndStation'])['StartStn', 'EndStation'].count().sort_values(
    by='StartStn', ascending=False)
avg_times = underground_journeys.groupby(['StartStn', 'EndStation'])['JourneyTimeMinutes'].mean()

# TODO: handle unstarted/unfinished data?

routes_with_saving = 0
total_gdp_saved = 0
average_london_hourly_wage = 30000/2000



# for index, row in popular_routes.iterrows():
#     if routes_with_saving > 10:
#         break
#     start_station = canonicalise_station_name(index[0])
#     end_station = canonicalise_station_name(index[1])
#
#     (saving_per_journey, closest_to_origin, closest_to_destination, current_journey_time_in_mins, new_journey_time) = \
#         main.will_it_be_faster(start_station, end_station)
#
#     if saving_per_journey > 0:
#         sampled_journeys_saved = row['StartStn']
#         estimated_weekly_journeys_saved = sampled_journeys_saved * 20
#         estimated_weekly_minutes_saved = estimated_weekly_journeys_saved * saving_per_journey
#         estimated_yearly_minutes_saved = estimated_weekly_minutes_saved * 52
#
#         estimated_gdp_saved = (estimated_yearly_minutes_saved/60)*average_london_hourly_wage
#         total_gdp_saved += estimated_gdp_saved
#
#         print(start_station, end_station, saving_per_journey, estimated_weekly_journeys_saved, total_gdp_saved)
#         routes_with_saving += 1




# print(df)
# print(underground_journeys)
print(popular_routes)
# print(avg_times)
