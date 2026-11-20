import streamlit as st
import pandas as pd
from db_functions import (
    connect_to_db,
    get_basic_info,
    get_additonal_tables,
    get_categories,
    get_suppliers,
    add_new_manual_id
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

elif option == "Operational Tasks":
    st.header("Operational Tasks")
    selected_task = st.selectbox(
        "Select a Task:", 
        ["Add New Product", "Product History", "Place Reorder", "Receive Reorder"]
    )

    if selected_task == "Add New Product":
        st.header("Add New Product")
        categories = get_categories(cursor)
        suppliers = get_suppliers(cursor)

        with st.form("Add_Product_Form"):
            product_name = st.text_input("Product Name")
            product_category = st.selectbox("Category", categories)
            product_price = st.number_input("Price", min_value=0.0)
            product_stock_quantity = st.number_input("Stock Quantity", min_value=0, step=1)
            product_reorder_level = st.number_input("Reorder Level", min_value=0, step=1)
            
            supplier_ids = [s["supplier_id"] for s in suppliers]
            supplier_names = [s["supplier_name"] for s in suppliers]

            supplier_id = st.selectbox(
                "Supplier",
                options=supplier_ids,
                format_func=lambda x: f"{x} - {supplier_names[supplier_ids.index(x)]}"
            )

            submitted = st.form_submit_button("Add Product")

            if submitted:
                if not product_name:
                    st.error("Please enter a product name.")
                else:
                    try:
                        # Extract the supplier_id from the selected option
                        add_new_manual_id(
                            cursor, 
                            db, 
                            product_name, 
                            product_category, 
                            product_price, 
                            product_stock_quantity, 
                            product_reorder_level, 
                            supplier_id
                        )
                        st.success(f"Product '{product_name}' added successfully!")
                    except Exception as e:
                        st.error(f"Error adding the Product: {e}")