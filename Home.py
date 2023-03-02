import pandas as pd
import streamlit as st
from shapely.geometry import Point, Polygon
import fetch as f

st.set_page_config(
    page_title="HDB Resale Price Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Report a bug": "https://github.com/eeshawn11/HDB_Resale_Dashboard/issues",
        "About": "Thanks for dropping by!"
        }
    )

@st.cache_data(show_spinner=False, max_entries=1, ttl=2_630_000)  # dataset is updated monthly
def load_data():
    df = f.get_data()
    hdb_coordinates = f.get_coords_df()
    geo_df = f.get_chloropeth()
    return df, hdb_coordinates, geo_df

with st.spinner("Fetching data..."):
    df, hdb_coordinates, geo_df = load_data()

if "geo_df" not in st.session_state:
        st.session_state.geo_df = geo_df

if "df_raw" not in st.session_state:
    st.session_state.df_raw = df.head(10).copy()

@st.cache_data(show_spinner=False)
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

planning_areas, polygons = get_planning_areas()

@st.cache_data(show_spinner=False)
def generate_point(coordinates):
    return Point(coordinates[1], coordinates[0])

def check_polygons(point):
    for index, area in enumerate(polygons):
        if area.contains(point):
            return planning_areas[index]

@st.cache_data(show_spinner=False)
def find_unique_locations(dataframe) -> dict:
    town_map = {}
    for address in dataframe["address"].unique():
        point = generate_point(list(hdb_coordinates.loc[address]))
        town_map[address] = check_polygons(point)
    return town_map


@st.cache_data(ttl=2_630_000, show_spinner="Transforming data...")
def transform_data(df):
    df["address"] = df["block"] + " " + df["street_name"]
    df_merged = df.merge(hdb_coordinates, how="left", on="address")
    df_merged.rename(columns={"month": "date"}, inplace=True)
    df_merged["date"] = pd.to_datetime(df_merged["date"], format="%Y-%m", errors="raise")
    df_merged["year"] = df_merged.date.dt.year
    df_merged["remaining_lease"] = df_merged["lease_commence_date"].astype(int) + 99 - df_merged["date"].dt.year
    df_merged = df_merged.rename(columns={'town': 'town_original'})
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
    columns = ['town', 'flat_type', 'flat_model', 'floor_area_sqm', 'price_per_sqm', 'date', 'year', 'remaining_lease', 'lease_commence_date', 'storey_range', 'address', 'latitude', 'longitude', 'resale_price']
    df_merged = df_merged.loc[:, columns]
    return df_merged

if "df" not in st.session_state:
    st.session_state.df = transform_data(df)

with st.sidebar:
    st.markdown(
        """
        Created by [**Shawn Sing**](https://www.linkedin.com/in/shawn-sing/)

        - Project source [**code**](https://github.com/eeshawn11/HDB_Resale_Dashboard/)
        - Check out my other projects on [**GitHub**](https://github.com/eeshawn11/)
        """
    )

with st.container():
    st.title("Singapore HDB Resale Price from 2000")
    st.image("./assets/nathan-oh-PWIOX6atM4w-unsplash.jpg")
    st.markdown("<p style='text-align: center;'>Photo by <a href='https://unsplash.com/fr/@nathanohk' target='_blank'>Nathan Oh</a> on <a href='https://unsplash.com/photos/PWIOX6atM4w' target='_blank'>Unsplash</a></p>", unsafe_allow_html=True)
  
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