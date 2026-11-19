import streamlit as st
import pandas as pd
from db_functions import (
    connect_to_db,
    get_basic_info,
    get_additonal_tables
)

st.set_page_config(
    page_title="Inventory Management Dashboard",
    layout="wide"
)

# Sidebar
st.sidebar.title("Inventory Management Dashboard")
option = st.sidebar.radio("Select Option:", ["Basic Information", "Operational Tasks"])

# main space
st.title("Inventory and Supply Chain Dashboard")
db = connect_to_db()
cursor = db.cursor(dictionary=True)

# --------------------- BASIC INFORMATION PAGE ---------------------
if option == "Basic Information":
    st.header("Basic Metrics Overview")

    # get basic informations from db
    basic_info = get_basic_info(cursor)

    keys = list(basic_info.keys())

    cols = st.columns(3)
    for i in range(3):
        cols[i].metric(label=keys[i], value=basic_info[keys[i]])

    cols = st.columns(3)
    for i in range(3, 6):
        cols[i - 3].metric(label=keys[i], value=basic_info[keys[i]])

    st.divider()

    # Fetch and display detailed tables
    tables = get_additonal_tables(cursor)
    for labels, data in tables.items():
        st.header(labels)
        df = pd.DataFrame(data)
        st.dataframe(df)
        st.divider()