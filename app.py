import streamlit as st
import pandas as pd
from db_functions import (
    connect_to_db,
    get_basic_info,
    get_additonal_tables,
    get_categories,
    get_suppliers,
    add_new_manual_id,
    get_all_products,
    get_product_history,
    place_reorder
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

# --------------------- OPERATIONAL TASKS PAGE ---------------------
elif option == "Operational Tasks":
    st.header("Operational Tasks")
    selected_task = st.selectbox(
        "Select a Task:", 
        ["Add New Product", "Product History", "Place Reorder", "Receive Reorder"]
    )

# --------------------- ADD NEW PRODUCT PAGE ---------------------
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

# --------------------- PRODUCT HISTORY PAGE ---------------------
    elif selected_task == "Product History":
        st.header("Product Inventory History")

        # get product list from the database
        products = get_all_products(cursor)
        product_names = [p["product_name"] for p in products]
        product_ids = [p["product_id"] for p in products]

        selected_product_name = st.selectbox(
            "Select a Product",
            options=product_names
        )

        if selected_product_name:
            selected_product_id = product_ids[product_names.index(selected_product_name)]
            history_data = get_product_history(cursor, selected_product_id)

            if history_data:
                df_history = pd.DataFrame(history_data)
                st.dataframe(df_history)
            else:
                st.info("No history available for the selected product.")

# --------------------- PLACE REORDER PAGE ---------------------
    elif selected_task == "Place Reorder":
        st.header("Place Reorder")

        products = get_all_products(cursor)
        product_names = [p["product_name"] for p in products]
        product_ids = [p["product_id"] for p in products]

        selected_product_name = st.selectbox(
            "Select a Product to Reorder",
            options=product_names
        )
        reorder_quantity = st.number_input("Reorder Quantity", min_value=1, step=1)

        if st.button("Place Reorder"):
            if not selected_product_name:
                st.error("Please select a product to reorder.")
            elif reorder_quantity <= 0:
                st.error("Reorder quantity must be greater than zero.")
            else:
                selected_product_id = product_ids[product_names.index(selected_product_name)]
                try:
                    place_reorder(cursor, db, selected_product_id, reorder_quantity)
                    st.success(f"Reorder placed for '{selected_product_name}' with quantity {reorder_quantity}.")
                except Exception as e:
                    st.error(f"Error placing reorder: {e}")