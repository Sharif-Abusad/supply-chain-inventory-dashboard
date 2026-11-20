use supply_chain;
select * from products;
select * from reorders;
select * from shipments;
select * from stock_entries;
select * from suppliers;

-- 1  Total Suppliers
SELECT COUNT(*) AS total_suppliers FROM suppliers;

-- 2  Total Products
SELECT COUNT(*) AS total_products FROM products;

-- 3  Total Categories Dealing
SELECT COUNT(DISTINCT category) AS total_categories FROM products;

-- 4  Total sales value made in last 3 months (quantity * price)
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

-- 5  Total restock value made in last 3 months (quantity * price)
SELECT 
	ROUND(
		SUM(
			ABS(se.change_quantity) * p.price
		), 
	2
) AS total_restock_value_in_last_3_months
FROM stock_entries AS se
JOIN products AS p
	ON p.product_id = se.product_id
WHERE se.change_type = "Restock"
AND se.entry_date < '2026-01-01'
AND se.entry_date >= (
	SELECT DATE_SUB(MAX(entry_date), INTERVAL 3 MONTH) 
    FROM stock_entries
    WHERE entry_date < '2026-01-01'
);

-- 6 Below Reorder and No Pending Reorders
SELECT COUNT(*) AS products_to_reorder
FROM products as p
WHERE p.stock_quantity < p.reorder_level
AND product_id NOT IN (
	SELECT DISTINCT product_id
    FROM reorders
    WHERE status = "Pending"
);

-- 7  Suppliers with their contact details
SELECT supplier_name, contact_name, email, phone FROM suppliers;

-- 8  Products with their suppliers and current stock
SELECT p.product_name, s.supplier_name, p.stock_quantity, p.reorder_level
FROM products AS p
JOIN suppliers AS s
	ON p.supplier_id = s.supplier_id
ORDER BY p.product_name ASC;

-- 9  Products needing reorder
SELECT product_id, product_name, stock_quantity, reorder_level
FROM products
WHERE stock_quantity <= reorder_level;

-- 10  Add a new product to the database
DELIMITER $$
CREATE PROCEDURE AddNewProductManualID(
	IN p_name VARCHAR(255),
    IN p_category VARCHAR(100),
    IN p_price DECIMAL(10, 2),
    IN p_stock INT,
    IN p_reorder INT,
    IN p_supplier int
)
BEGIN
	DECLARE new_prod_id INT;
    DECLARE new_shipment_id INT;
    DECLARE new_entry_id INT;
    
    # make changes in product table
    # generate the product_id
    SELECT MAX(product_id)+1 INTO new_prod_id FROM products;    
    INSERT INTO products(product_id, product_name, category, price, stock_quantity, reorder_level, supplier_id)
    VALUES(new_prod_id, p_name, p_category, p_price, p_stock, p_reorder, p_supplier);
    
    
    # make changes in shipment table
	# generate the shipment_id
    SELECT MAX(shipment_id)+1 INTO new_shipment_id FROM shipments;    
    INSERT INTO shipments (shipment_id, product_id, supplier_id, quantity_received, shipment_date)
    VALUES(new_shipment_id, new_prod_id, p_supplier, p_stock, CURDATE());
	
    
    # make changes in stock_entries
    # generate  the entry_id
    SELECT MAX(entry_id)+1 INTO new_entry_id FROM stock_entries;    
    INSERT INTO stock_entries(entry_id, product_id, change_quantity, change_type, entry_date)
    VALUES(new_entry_id, new_prod_id, p_stock, "Restock", CURDATE());
    
END $$
DELIMITER ;

CALL AddNewProductManualID('Smart Watch', 'Electronics', 99.99, 100, 25, 5);

SELECT * FROM products WHERE product_name = 'Smart Watch';
SELECT * FROM shipments WHERE product_id = 201;
SELECT * FROM stock_entries WHERE product_id = 201;

-- 11  Product History [finding shipments, sales and purchases for a product]
CREATE OR REPLACE VIEW product_inventory_history AS
SELECT 
    pih.product_id,
    pih.record_type,
    pih.record_date,
    pih.record_quantity,
    pih.change_type,
    p.supplier_id    
FROM
(
    SELECT
        product_id,
        "Shipment" AS record_type,
        shipment_date AS record_date,
        quantity_received AS record_quantity,
        null AS change_type
    FROM shipments
    UNION ALL
    SELECT 
        product_id,
        "Stock Entry" AS record_type,
        entry_date AS record_date,
        change_quantity AS record_quantity,
        change_type
    FROM stock_entries
) AS pih
JOIN products AS p
    ON p.product_id = pih.product_id;

SELECT * FROM product_inventory_history
WHERE product_id = 201
ORDER BY record_date DESC;