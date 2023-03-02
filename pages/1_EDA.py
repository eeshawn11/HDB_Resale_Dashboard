import pandas as pd
import streamlit as st
import plotly.express as px
import altair as alt
from streamlit_extras.switch_page_button import switch_page
import matplotlib.pyplot as plt
import seaborn as sns
sns.set()

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

def add_marker(base_chart, nearest, tooltip_y_val:str, tooltip_y_title:str, tooltip_y_format:str):
    '''
    Adds a selector indicator and rule to altair chart
    '''
    # selectors that tell us the x-value of the cursor
    selector = (
        base_chart.mark_point(color="red")
        .encode(
            x="date",
            opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
            tooltip=[
                alt.Tooltip("date", title="Transaction Period", format="%b-%y"),
                alt.Tooltip(
                    tooltip_y_val, title=tooltip_y_title, format=tooltip_y_format
                ),
            ]
        )
        .add_selection(nearest)
    )

    # draw a rule at location of selection
    rule = (
        base_chart.mark_rule(color="gray")
        .encode(x="date")
        .transform_filter(nearest)
    )

    return selector, rule

# return to home to fetch data 
if "df" not in st.session_state or "df_raw" not in st.session_state:
    switch_page("Home")

# flat type distribution
flat_type_df = st.session_state.df[["flat_type", "floor_area_sqm"]].copy()
flat_type_df["flat_type"] = flat_type_df["flat_type"].replace({"MULTI-GENERATION": "EXECUTIVE*", "EXECUTIVE": "EXECUTIVE*"})

with pd.option_context("display.float_format", "${:,.2f}".format):
    resale_price_table = st.session_state.df.groupby(["town", "flat_type"]).resale_price.median().reset_index()
    resale_price_pivot = pd.pivot(resale_price_table, index="town", columns="flat_type", values="resale_price")
resale_table_columns = ["1 ROOM", "2 ROOM", "3 ROOM", "4 ROOM", "5 ROOM", "EXECUTIVE", "MULTI-GENERATION"]

flat_order = {
    "flat_type": resale_table_columns
}

resale_plot = px.histogram(
    st.session_state.df.sort_values(by="year"),
    x="resale_price",
    color="flat_type",
    opacity=0.8,
    nbins=200,
    barmode="overlay",
    title="Distribution of Resale Price",
    category_orders=flat_order
).update_layout(
    xaxis_title="Resale Price (S$)",
    yaxis_title="Frequency",
    height=450,
    legend={
        "orientation": "h",
        "y": 1.12,
        "x": 0.2,
        "title": None
    }
)

resale_plot_animated = px.histogram(
    st.session_state.df.sort_values(by="year"),
    x="resale_price",
    animation_frame="year",
    color="flat_type",
    range_x=[st.session_state.df.resale_price.min(), st.session_state.df.resale_price.max()],
    range_y=[0, 1500],
    title="Distribution of Resale Price by Year",
    opacity=0.8,
    barmode="overlay",
    category_orders=flat_order
).update_layout(
    xaxis_title="Resale Price (S$)",
    yaxis_title="Frequency",
    height=550,
    legend={
        "orientation": "h",
        "y": 1.12,
        "x": 0.2,
        "title": None
    }
)

remaining_lease_plot = px.histogram(
    st.session_state.df.sort_values(by="year"),
    x="remaining_lease",
    opacity=0.8,
    title="Distribution of Remaining Lease (Years)",
    color_discrete_sequence=['dodgerblue'],
    histnorm="percent"
).update_layout(
    xaxis_title="Remaining Lease",
    yaxis_title="Frequency",
    height=450,
)

flat_type_selector = alt.selection_multi(empty="all", fields=["flat_type"])

flat_base = alt.Chart(
    flat_type_df,
).add_selection(flat_type_selector)

flat_type_plot = (
    flat_base.mark_bar()
    .encode(
        alt.X("count()", axis=alt.Axis(title="Transactions")),
        alt.Y("flat_type:N", axis=alt.Axis(title="Flat Type")),
        color=alt.condition(
            flat_type_selector, "flat_type:N", alt.value("lightgray"), legend=None
        ),
        tooltip=[
            alt.Tooltip("flat_type", title="Flat Type"),
            alt.Tooltip("count()", title="Transactions", format=","),
        ],
    )
    .properties(height=250, title="Transactions by Flat Type")
)

floor_area_plot = (
    flat_base.mark_bar(opacity=0.8, binSpacing=0)
    .encode(
        alt.X(
            "floor_area_sqm:Q",
            bin=alt.Bin(step=5),
            axis=alt.Axis(title="Floor Area (sqm)"),
        ),
        alt.Y("count()", stack=None, axis=alt.Axis(title="Count")),
        alt.Color("flat_type:N", legend=None),
    )
    .transform_filter(flat_type_selector)
    .properties(
        height=250,
        title="Distribution of Floor Area by Flat Type"
    )
)

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
    st.markdown("## Data Retrieval")
    st.markdown(
        "We utilise the Data.gov.sg API to extract our required data. Let's check out the dataset to see what it includes."
    )
    st.dataframe(st.session_state.df_raw.head(3), use_container_width=True)
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
        f"Checking the shape of the dataframe, we currently have `{st.session_state.df.shape[0]:,}` rows, each of which represents a unique resale transaction."
    )

st.markdown("---")

with st.container():
    st.markdown("## Data Transformation")
    st.markdown(
        """
        - Combining `block` and `street_name` into a new `address` column, I then utilised a free [OneMap API](https://www.onemap.gov.sg/docs/) provided by the Singapore Land Authority to retrieve the `latitude` and `longitude` coordinates of these addresses for plotting onto a map.
        - The older datasets did not include a `remaining_lease` column, but it's easy to calculate based on the standard 99-year HDB leases.
        - The `town` column does not correspond fully to the planning areas within the choropeth, so we'll check and rename towns within the dataset based the choropeth.        
        - There are transactions in HDB blocks that have since been [reacquired]((https://www.hdb.gov.sg/residential/living-in-an-hdb-flat/sers-and-upgrading-programmes/sers/sers-projects/completed-sers-projects)) by the state, such as 1A & 2A Woodlands Centre Road, which do not show up in the OneMap API, but interestingly are still appearing in Google Maps. This meant having to extract a list of these locations and looking up their *approximate* location manually.

        Checking out the new dataframe after transformation:
        """
    )
    st.dataframe(st.session_state.df.head(3), use_container_width=True)

st.markdown("---")

with st.container():
    st.markdown("## Exploratory Data Analysis")
    st.markdown("##### Median Resale Price Across Towns and Flat Types")
    st.markdown(
        """
        Applying some Excel style conditional formatting, we get a sense of some of the pricier towns based on the median resale prices. 
        """
    )
    st.dataframe(
        resale_price_pivot.style.background_gradient(
                axis=None,
                subset=resale_table_columns, 
                vmin=resale_price_table.resale_price.min()
            ).format(
                na_rep="-",
                precision=0,
                thousands=","
            ).applymap(
                lambda x: 'color: transparent; background-color: transparent' if pd.isnull(x) else ''
            ),
        use_container_width=True)

with st.container():
    resale_tab, resale_tab_animated = st.tabs(["Resale Price", "Resale Price (Yearly)"])
    st.markdown(
        """
        Across the past 2 decades, the distribution of resale prices across the flat types generally exhibit a right skew. 
        HDBs are public housing after all and the government would want to try to keep prices affordable, although we do see a growing trend of 'million dollar flats' as evidenced by the long tail.
        
        Interestingly, 3 ROOM and 4 ROOM flats in particular have a bimodal distribution. 
        From the yearly charts, we see prices remained relatively stable from 2000 - 2007, before prices started to rise and settled after 2013.
        """
    )
    st.markdown("---")

with resale_tab:
    st.plotly_chart(resale_plot, use_container_width=True)

with resale_tab_animated:
    st.plotly_chart(resale_plot_animated, use_container_width=True)

with st.container():
    st.plotly_chart(remaining_lease_plot, use_container_width=True)
    st.markdown(
        """
        Given the 99-year leases for HDB flats, it should be unsurprising to see a spike in transactions for flats with over 90 years lease remaining.
        These flats are new BTOs that become available on the market after the 5-year Minimum Occupation Period (MOP).

        Interestingly, we see a bimodal distribution with a second lower peak closer to the 80 years region. 
        I am wondering if this could perhaps be related to new buyers in their 20s who opt to purchase a resale flat instead of waiting for BTO instead?
        """
    )
    st.markdown("---")

with st.container():
    st.markdown("Click to filter by flat types, hold shift to select multiple options.")
    # use_container_width currently does not seem to work for concatenated charts
    st.altair_chart(flat_type_plot | floor_area_plot, use_container_width=True)
    st.markdown("\* Includes Multi-Generation flats")
    st.markdown("---")