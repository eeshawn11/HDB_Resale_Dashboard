import pandas as pd
import streamlit as st
import plotly.express as px
from streamlit_extras.switch_page_button import switch_page

st.set_page_config(layout="wide")

# return to home to fetch data 
if "df" not in st.session_state:
    switch_page("Home")

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
    st.markdown("## Exploratory Data Analysis")
    st.markdown(
        """
        After collecting and cleaning our data, let's have a sense of what our data looks like.
        """
    )
    st.markdown("---")

with st.container():
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
        From the yearly charts, we see prices remained relatively stable from 2000 - 2007, before prices started to rise and settle after 2013.
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

        Interestingly, we see a bimodal distribution with a second lower peak around the 80 years region. 
        I am wondering if this could perhaps be related to new buyers in their 20s who opt to purchase a resale flat instead of waiting for BTO instead?
        """
    )
    st.markdown("---")