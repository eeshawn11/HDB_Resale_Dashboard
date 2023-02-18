import pandas as pd
import streamlit as st
import requests
import json
from shapely.geometry import Point, Polygon
import time
import os

st.set_page_config(layout="wide")

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


@st.experimental_memo(show_spinner=False, ttl=2_630_000)  # dataset is updated monthly
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


@st.experimental_memo(max_entries=1)
def get_coords_df():
    return pd.read_csv(
        path+"/assets/hdb_coords.csv",
        index_col="address"
    )


@st.experimental_singleton
def get_chloropeth():
    with open(
        path+"/assets/master-plan-2014-planning-area-boundary-no-sea.json"
    ) as f:
        return json.load(f)

with st.spinner("Fetching data..."):
    df = get_data()
    hdb_coordinates = get_coords_df()

if "geo_df" not in st.session_state:
    st.session_state.geo_df = get_chloropeth()


def get_planning_areas():
    planning_areas = []
    polygons = []
    for i in range(len(st.session_state.geo_df["features"])):
        planning_areas.append(
            st.session_state.geo_df["features"][i]["properties"]["PLN_AREA_N"]
        )
        try:
            polygons.append(
                Polygon(
                    st.session_state.geo_df["features"][i]["geometry"]["coordinates"][0]
                )
            )
        except:
            polygons.append(
                Polygon(
                    st.session_state.geo_df["features"][i]["geometry"]["coordinates"][
                        0
                    ][0]
                )
            )
    return planning_areas, polygons

def generate_point(coordinates):
    return Point(coordinates[1], coordinates[0])

def check_polygons(point):
    for index, area in enumerate(polygons):
        if area.contains(point):
            return planning_areas[index]

def find_unique_locations(dataframe) -> dict:
    town_map = {}
    for address in dataframe["address"].unique():
        point = generate_point(list(hdb_coordinates.loc[address]))
        town_map[address] = check_polygons(point)
    return town_map

with st.sidebar:
    st.markdown(
        """
        Created by Shawn

        - Happy to connect on [LinkedIn](https://www.linkedin.com/in/shawn-sing/)
        - Check out my other projects on [GitHub](https://github.com/eeshawn11/)
        """
    )

with st.container():
    st.title("Singapore HDB Resale Price from 2000")
    st.markdown(
        """
        This dashboard is inspired by [Inside Airbnb](http://insideairbnb.com/) and various other dashboards I've come across on the web. 
        As a new data professional, this is an ongoing project to document my learning with using Streamlit and various Python libraries 
        to create an interactive dashboard. While this could perhaps be more easily created using PowerBI or Tableau, I am also taking the 
        opportunity to explore the various Python plotting libraries and understand their documentation.

        The project is rather close to heart since I've been looking out for a resale flat after getting married in mid-2022, although with 
        the recent surge in resale prices as of 2022, it still remains out of reach. Hopefully this dashboard can help contribute to my 
        eventual purchase decision, although that may also require adding in various datasets beyond the current historical information.

        Data from the dashboard is retrieved from Singapore's [Data.gov.sg](https://data.gov.sg/), a free portal with access to publicly-available 
        datasets from over 70 public agencies made available under the terms of the [Singapore Open Data License](https://data.gov.sg/open-data-licence). 
        In particular, we dive into the HDB resale flat prices [dataset](https://data.gov.sg/dataset/resale-flat-prices), while town boundaries 
        in the chloropeth map are retrieved from [Master Plan 2014 Planning Area Boundary](https://data.gov.sg/dataset/master-plan-2014-planning-area-boundary-no-sea).
        """
    )

st.markdown("---")

with st.container():
    st.markdown("## Background")
    st.markdown(
        """
        The [Housing & Development Board (HDB)](https://www.hdb.gov.sg/cs/infoweb/homepage) is Singapore's public housing authority, responsible for 
        planning and developing affordable accommodation for residents in Singapore. First established in 1960, over 1 million flats have since been completed 
        in 23 towns and 3 estates across the island.

        Aspiring homeowners generally have a few options when they wish to purchase their first home, either purchasing a new flat directly from HDB, or 
        purchasing an existing flat from the resale market.
        
        While new flats have been constantly developed to meet the needs of the growing population, HDB has been operating on a Build To Order (BTO) 
        since 2001. As the name suggests, the scheme allows the government to build based on actual demand, requiring new developments to meet 
        a minimum application rate before a tender for construction is called. This generally requires a waiting period of around 3 - 4 years for completion.

        However, 2 years of stoppages and disruptions during COVID caused delays to various projects, lengthening the wait time to around 5 years. This
        caused many people to turn to the resale market instead. Since these are existing developments, resale transactions can usually be expected to 
        complete within 6 months or so, which is a significant reduction in wait time. This surge in demand has also caused a sharp increase in resale prices,
        with many flats even crossing the S$1 million mark.
        """
    )

st.markdown("---")

with st.container():
    st.markdown("## Data Retrieval & Transformation")
    st.markdown(
        "We utilise the Data.gov.sg API to extract our required data. Let's check out the dataset to see what it includes."
    )
    st.dataframe(df.head(3), use_container_width=True)
    st.markdown(
        """
        The dataset provides key information regarding the resale transactions since 2012, including location, flat type and lease information. The information 
        is generally clean, although we will still need to perform some transformations for use in our visualisations.

        Notes from the dataset:
        
        > - The data excludes any transactions that may not reflect the full market price such as resale between relatives or resale of part shares.
        >
        > - Transactions from March 2012 onwards are based on the date of registration, while those before are based on the date of approval.
        """
    )
    st.markdown(
        f"Checking the shape of the dataframe, we currently have `{df.shape[0]:,}` rows, each of which represents a unique resale transaction."
    )

st.markdown("---")

if "df" not in st.session_state:
    with st.spinner("Transforming data..."):
        df["address"] = df["block"] + " " + df["street_name"]
        df_merged = df.merge(hdb_coordinates, how="left", on="address")
        df_merged.rename(columns={"month": "date"}, inplace=True)
        df_merged["date"] = pd.to_datetime(df_merged["date"], format="%Y-%m", errors="raise")
        df_merged["year"] = df_merged.date.dt.year
        df_merged["remaining_lease"] = df_merged["lease_commence_date"].astype(int) + 99 - df_merged["date"].dt.year
        df_merged = df_merged.rename(columns={'town': 'town_original'})
        planning_areas, polygons = get_planning_areas()
        town_map = find_unique_locations(df_merged)
        df_merged["town"] = df_merged["address"].map(town_map)
        df_merged["price_per_sqm"] = df_merged["resale_price"].astype(float) / df_merged["floor_area_sqm"].astype(float)
        # changing dtypes to reduce space when storing in session_state
        df_merged[["town_original", "flat_type", "flat_model", "storey_range", "town", "address", "year"]] = (df_merged[["town_original", "flat_type", "flat_model", "storey_range", "town", "address", "year"]]
                                                                                                                .astype("category"))
        df_merged["resale_price"] = df_merged["resale_price"].astype(float).astype("int32")
        df_merged[["latitude", "longitude"]] = df_merged[["latitude", "longitude"]].astype("float32")
        df_merged[["floor_area_sqm", "remaining_lease"]] = df_merged[["floor_area_sqm", "remaining_lease"]].astype(float).astype("int16")
        df_merged["price_per_sqm"] = df_merged["price_per_sqm"].astype("float16")

        st.session_state.df = df_merged

with st.container():
    st.markdown(
        """
        - Combining `block` and `street_name` into a new `address` column, I then utilised a free [OneMap API](https://www.onemap.gov.sg/docs/) provided by the Singapore Land Authority to retrieve the `latitude` and `longitude` coordinates of these addresses for plotting onto a map.
        - The older datasets did not include a `remaining_lease` column, but it's easy to calculate based on the standard 99-year HDB leases.
        - The `town` column does not correspond fully to the planning areas within the choropeth, so we'll check and rename towns within the dataset based the choropeth.        
        - There are transactions in HDB blocks that have since been [reacquired]((https://www.hdb.gov.sg/residential/living-in-an-hdb-flat/sers-and-upgrading-programmes/sers/sers-projects/completed-sers-projects)) by the state, such as 1A & 2A Woodlands Centre Road, which do not show up in the OneMap API, but interestingly are still appearing in Google Maps. This meant having to extract a list of these locations and looking up their *approximate* location manually.
        """
    )


st.markdown("---")

with st.container():
    st.markdown(
        """
        After performing the transformations on the data, notice the new columns that have been added and we are ready to move on with visualisations.
        """
    )
    st.dataframe(st.session_state.df.head(3), use_container_width=True)

try:
    st.session_state.df = st.session_state.df.drop(columns=["town_original", "_id", "block", "street_name"])
except:
    pass