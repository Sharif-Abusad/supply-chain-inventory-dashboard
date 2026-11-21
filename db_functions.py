import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()


def connect_to_db():
    """
    Establish a connection to the MySQL database using environment variables.

    Returns:
        mysql.connector.connection.MySQLConnection: Active database connection.
    """
    # Retrieve database credentials securely from environment variables
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

    return conn


def get_basic_info(cursor):
    """
    Retrieve key inventory and supply chain metrics for the dashboard.

    Args:
        cursor: MySQL dictionary cursor used to execute SQL queries.

    Returns:
        dict: Dictionary containing summary metrics and their values.
    """

    # Define SQL queries for each dashboard summary metric
    queries = {
        # Count the total number of suppliers registered in the database
        "Total Suppliers": """
            SELECT COUNT(*) AS count FROM suppliers
        """,

        # Count the total number of products available in the inventory
        "Total Products": """
            SELECT COUNT(*) AS count FROM products
        """,

        # Count the number of unique product categories
        "Total Categories Dealing": """
            SELECT COUNT(DISTINCT category) AS count FROM products
        """,

        # Calculate the total sales value over the last three months
        # Multiply the sold quantity by the product price
        "Total Sale Value (Last 3 Months)": """
            SELECT 
                ROUND(
                    SUM(ABS(se.change_quantity) * p.price),
                    2
                ) AS total_sales_value_in_last_3_months
            FROM stock_entries AS se
            JOIN products AS p
                ON p.product_id = se.product_id
            WHERE se.change_type = 'Sale'
                AND se.entry_date < '2026-01-01'
                AND se.entry_date >= (
                    SELECT DATE_SUB(MAX(entry_date), INTERVAL 3 MONTH)
                    FROM stock_entries
                    WHERE entry_date < '2026-01-01'
                );
        """,

        # Calculate the total restocking value over the last three months
        # Multiply the restocked quantity by the product price
        "Total Restock Value (Last 3 Months)": """
            SELECT 
                ROUND(
                    SUM(ABS(se.change_quantity) * p.price),
                    2
                ) AS total_restock_value_in_last_3_months
            FROM stock_entries AS se
            JOIN products AS p
                ON p.product_id = se.product_id
            WHERE se.change_type = 'Restock'
                AND se.entry_date < '2026-01-01'
                AND se.entry_date >= (
                    SELECT DATE_SUB(MAX(entry_date), INTERVAL 3 MONTH)
                    FROM stock_entries
                    WHERE entry_date < '2026-01-01'
                );
        """,

        # Count products below their reorder level
        # Exclude products that already have a pending reorder request
        "Below Reorder & No Pending Reorders": """
            SELECT COUNT(*) AS below_reorder
            FROM products p
            WHERE p.stock_quantity < p.reorder_level
              AND p.product_id NOT IN (
                  SELECT DISTINCT product_id
                  FROM reorders
                  WHERE status = 'Pending'
              )
        """
    }

    # Execute each query and store the resulting metric
    results = {}

    for label, query in queries.items():
        cursor.execute(query)
        row = cursor.fetchone()

        # Extract the metric value from the returned dictionary
        results[label] = list(row.values())[0]

    return results


def get_additonal_tables(cursor):
    """
    Retrieve detailed datasets required for dashboard tables.

    Args:
        cursor: MySQL dictionary cursor used to execute SQL queries.

    Returns:
        dict: Dictionary containing supplier, inventory, and reorder data.
    """

    # Define queries for the detailed dashboard tables
    queries = {
        # Retrieve supplier contact information
        "Suppliers Contact Details": """
            SELECT supplier_name, contact_name, email, phone
            FROM suppliers
        """,

        # Retrieve product inventory details along with supplier information
        # Join products with suppliers to identify each product's supplier
        "Products with Supplier and Stock": """
            SELECT
                p.product_name,
                s.supplier_name,
                p.stock_quantity,
                p.reorder_level
            FROM products p
            JOIN suppliers s ON p.supplier_id = s.supplier_id
            ORDER BY p.product_name ASC
        """,

        # Identify products whose current stock is at or below the reorder threshold
        "Products Needing Reorder": """
            SELECT product_name, stock_quantity, reorder_level
            FROM products
            WHERE stock_quantity <= reorder_level
        """
    }

    # Execute each query and store all returned rows
    tables = {}

    for label, query in queries.items():
        cursor.execute(query)
        tables[label] = cursor.fetchall()

    return tables


def get_categories(cursor):
    """
    Retrieve distinct product categories from the products table.

    Args:
        cursor (mysql.connector.cursor.MySQLCursorDict): Cursor object with dictionary=True.

    Returns:
        list: List of distinct product categories.
    """
    query = """
        SELECT DISTINCT category 
        FROM products 
        ORDER BY category ASC
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    categories = [row['category'] for row in rows]
    return categories


def get_suppliers(cursor):
    """
    Retrieve distinct supplier names from the suppliers table.

    Args:
        cursor (mysql.connector.cursor.MySQLCursorDict): Cursor object with dictionary=True.

    Returns:
        list: List of distinct supplier names.
    """
    query = """
        SELECT 
            supplier_id, 
            supplier_name 
        FROM suppliers 
        ORDER BY supplier_name ASC
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    return rows


def add_new_manual_id(cursor, db, p_name, p_category, p_price, p_stock_quantity, p_reorder_level, p_supplier_id):
    """
    Add a new product to the products table with a manually specified product_id.

    Args:
        cursor (mysql.connector.cursor.MySQLCursorDict): Cursor object with dictionary=True.
        db (mysql.connector.connection.MySQLConnection): Database connection object.
        p_name (str): Name of the product.
        p_category (str): Category of the product.
        p_price (float): Price of the product.
        p_stock_quantity (int): Stock quantity of the product.
        p_reorder_level (int): Reorder level of the product.
        p_supplier_id (int): Supplier ID associated with the product.

    Returns:
        None
    """
    proc_call = "call AddNewProductManualID(%s, %s, %s, %s, %s, %s)"
    params = (p_name, p_category, p_price, p_stock_quantity, p_reorder_level, p_supplier_id)
    cursor.execute(proc_call, params)
    db.commit()


def get_all_products(cursor):
    """
    Retrieve all products from the products table.

    Args:
        cursor (mysql.connector.cursor.MySQLCursorDict): Cursor object with dictionary=True.

    Returns:
        list: List of dictionaries containing product details.
    """
    query = """
        SELECT 
            product_id, 
            product_name 
        FROM products 
        ORDER BY product_name ASC
    """
    cursor.execute(query)
    return cursor.fetchall()


def get_product_history(cursor, product_id):
    """
    Retrieve the product history for a specific product.

    Args:
        cursor (mysql.connector.cursor.MySQLCursorDict): Cursor object with dictionary=True.
        product_id (int): The ID of the product for which to retrieve history.

    Returns:
        list: List of dictionaries containing stock entry history for the specified product.
    """
    query = """
        SELECT * 
        FROM product_inventory_history 
        WHERE product_id = %s 
        ORDER BY record_date DESC
    """
    cursor.execute(query, (product_id,))
    return cursor.fetchall()


def place_reorder(cursor, db, product_id, reorder_quantity):
    """
    Place a reorder for a specific product.

    Args:
        cursor (mysql.connector.cursor.MySQLCursorDict): Cursor object with dictionary=True.
        db (mysql.connector.connection.MySQLConnection): Database connection object.
        product_id (int): The ID of the product to reorder.
        reorder_quantity (int): The quantity to reorder.

    Returns:
        None
    """
    query = """
        INSERT INTO reorders (reorder_id, product_id, reorder_quantity, status, reorder_date)
        SELECT 
            MAX(reorder_id)+1, 
            %s, 
            %s, 
            'Ordered', 
            CURDATE()
        FROM reorders
    """
    params = (product_id, reorder_quantity)
    cursor.execute(query, params)
    db.commit()