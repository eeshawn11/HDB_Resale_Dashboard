import requests
import json
from shapely.geometry import Point, Polygon
import time
import os
import pandas as pd

resource_ids = [
    "f1765b54-a209-4718-8d38-a39237f502b3", # from Jan 2017 onwards
    "1b702208-44bf-4829-b620-4615ee19b57c", # 2015 - 2016
    "83b2fc37-ce8c-4df4-968b-370fd818138b", # Mar 2012 - 2014
    "8c00bf08-9124-479e-aeca-7cc411d884c4", # 2000 - Feb 2012
]

path = os.path.dirname(__file__)

def retrieve_data(resource_id: str, n: int):
    url_string = f"https://data.gov.sg/api/action/datastore_search?resource_id={resource_id}&limit={n}"
    try:
        response = requests.get(
            url_string, headers={"User-Agent": "Mozilla/5.0"}, timeout=20
        ).json()
        if response["success"] == True:
            print("Call success")
            return response
        elif response["success"] == False:
            print("Call failed")
    except Exception as e:
        print(f"Error occurred: {e}")
        print(e)
        print(url_string)


def get_data():
    print("Fetching data")
    content = pd.DataFrame()
    for resource_id in resource_ids:
        time.sleep(1)
        try:
            print(f"First call to {resource_id}")
            body = retrieve_data(resource_id, 1)
            limit = body["result"]["total"]
            print(f"Second call, retrieving {limit:,} records")
            body = retrieve_data(resource_id, limit)
            resource_df = pd.DataFrame(body["result"]["records"])
            content = pd.concat([content, resource_df], ignore_index=True)
        except:
            print(f"Error: {resource_id} unsuccessful")
    print(f"Retrieval complete! {content.shape[0]:,} records retrieved.")
    return content


def get_coords_df():
    return pd.read_csv(
        path+"/assets/hdb_coords.csv",
        index_col="address"
    )


def get_chloropeth():
    with open(
        path+"/assets/master-plan-2014-planning-area-boundary-no-sea.json"
    ) as f:
        return json.load(f)