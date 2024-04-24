def fetch_random_products_query():
    return """
    SELECT TOP 9
    p.product_id,
    p.name,
    c.name as category_name,
    p.category_id,
    p.price,
    p.description,
    i.quantity,
    p.image_url
    FROM 
        Products as p
    LEFT JOIN 
        Categories as c ON p.category_id = c.category_id
    LEFT JOIN 
        Inventory as i ON p.product_id = i.product_id
    WHERE
        i.quantity IS NOT NULL AND i.quantity > 0
    ORDER BY
        NEWID()
    """

def search_products_query(search_query):
    return """
    SELECT 
        p.product_id,
        p.name,
        c.name as category_name,
        p.category_id,
        p.price,
        p.description,
        i.quantity,
        p.image_url
    FROM 
        Products as p
    LEFT JOIN 
        Categories as c ON p.category_id = c.category_id
    LEFT JOIN 
        Inventory as i ON p.product_id = i.product_id
    WHERE
        p.name LIKE ? OR p.description LIKE ?
    """

def get_product_by_id_query(product_id):
    return """
    SELECT 
        p.product_id,
        p.name,
        c.name as category_name,
        p.category_id,
        p.price,
        p.description,
        i.quantity,
        p.image_url
    FROM 
        Products as p
    LEFT JOIN 
        Categories as c ON p.category_id = c.category_id
    LEFT JOIN 
        Inventory as i ON p.product_id = i.product_id
    WHERE
        p.product_id = ?
    """

def search_products_by_category_query(category_id):
    return """
    SELECT 
        p.product_id,
        p.name,
        c.name as category_name,
        p.category_id,
        p.price,
        p.description,
        i.quantity,
        p.image_url
    FROM 
        Products as p
    LEFT JOIN 
        Categories as c ON p.category_id = c.category_id
    LEFT JOIN 
        Inventory as i ON p.product_id = i.product_id
    WHERE
        p.category_id = ?
    """

def get_all_products_query():
    return """
    SELECT 
        p.product_id,
        p.name,
        c.name as category_name,
        p.category_id,
        p.price,
        p.description,
        i.quantity,
        p.image_url
    FROM 
        Products as p
    LEFT JOIN 
        Categories as c ON p.category_id = c.category_id
    LEFT JOIN 
        Inventory as i ON p.product_id = i.product_id
    """

def get_all_categories_query():
    return "SELECT c.category_id, c.name FROM Categories as c"

def get_filtered_categories_query():
    return "SELECT * FROM Categories WHERE LEN(name) <= 16"

def insert_product_query(name, category_id, price, description, image_url):
    return "INSERT INTO Products (name, category_id, price, description, image_url) VALUES (?, ?, ?, ?, ?)"

def get_product_id_query(name, description, price):
    return "SELECT product_id FROM Products WHERE name = ? AND description LIKE ? AND price = ?"

def insert_inventory_query(product_id, quantity):
    return "INSERT INTO Inventory (product_id, quantity) VALUES (?, ?)"

def get_image_url_query(product_id):
    return "SELECT image_url FROM Products WHERE product_id=?"

def delete_inventory_query(product_id):
    return "DELETE FROM Inventory WHERE product_id=?"

def delete_product_query(product_id):
    return "DELETE FROM Products WHERE product_id=?"

def update_product_query(name, category_id, price, description, product_id):
    return "UPDATE Products SET name=?, category_id=?, price=?, description=? WHERE product_id=?"

def get_product_by_id_query(product_id):
    return "SELECT * FROM Products AS p LEFT JOIN Inventory AS i ON p.product_id = i.product_id WHERE p.product_id = ?;"

def get_all_states_query():
    return "SELECT * FROM States"

def get_purchase_log_query(order_number):
    return """SELECT 
                p.OrderID,
                p.OrderNumber,
                p.Email,
                p.CardNumber,
                p.ExpMMYY,
                p.CardholderName,
                p.Address1,
                p.Address2,
                p.City,
                states.abbreviation AS StateAbbreviation,
                p.ZipCode,
                p.TotalPriceNoTax,
                p.TotalPriceTax,
                status.StatusID AS OrderStatusID,
                pr.Product_id as ProductID,
                p.Quantity,
                p.PurchaseDate,
                states.name AS StateName,
                status.Description AS OrderStatus,
                pr.name AS ProductName,
                pr.category_id AS ProductCategoryID,
                pr.price AS ProductPrice,
                pr.description AS ProductDescription,
                pr.image_url AS ProductImageURL
            FROM PurchaseLogs AS p
            LEFT JOIN states ON p.stateID = states.id
            LEFT JOIN Status AS status ON p.StatusID = status.StatusID
            LEFT JOIN Products AS pr ON p.productID = pr.product_id
            WHERE p.OrderNumber = ?"""

def update_inventory_query(product_id, quantity):
    return "UPDATE Inventory SET Quantity = Quantity - ? WHERE Product_ID = ?"

def get_existing_order_numbers_query():
    return "SELECT OrderNumber FROM PurchaseLogs"

def get_tax_percentage_query(state_id):
    return "SELECT tax_percentage FROM States WHERE id = ?"

def insert_purchase_log_query(order_number, email, card_number, exp_mm_yy, cardholder_name, address1, address2, city, state_id, zip_code, total_price_no_tax, total_price_tax, status_id, product_id, quantity, purchase_date):
    return "INSERT INTO PurchaseLogs (OrderNumber, Email, CardNumber, ExpMMYY, CardholderName, Address1, Address2, City, StateID, ZipCode, TotalPriceNoTax, TotalPriceTax, StatusID, ProductID, Quantity, PurchaseDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

def get_purchase_log_by_order_number_query(order_number):
    return """
        SELECT 
            p.OrderID,
            p.OrderNumber,
            p.Email,
            p.CardNumber,
            p.ExpMMYY,
            p.CardholderName,
            p.Address1,
            p.Address2,
            p.City,
            states.abbreviation AS StateAbbreviation,
            p.ZipCode,
            p.TotalPriceNoTax,
            p.TotalPriceTax,
            status.StatusID AS OrderStatusID,
            pr.Product_id as ProductID,
            p.Quantity,
            p.PurchaseDate,
            states.name AS StateName,
            status.Description AS OrderStatus,
            pr.name AS ProductName,
            pr.category_id AS ProductCategoryID,
            pr.price AS ProductPrice,
            pr.description AS ProductDescription,
            pr.image_url AS ProductImageURL
        FROM PurchaseLogs AS p
        LEFT JOIN states ON p.stateID = states.id
        LEFT JOIN Status AS status ON p.StatusID = status.StatusID
        LEFT JOIN Products AS pr ON p.productID = pr.product_id
        WHERE p.OrderNumber = ?
    """

def get_purchase_log_by_order_number_query(order_number):
    return """
        SELECT 
            p.OrderID,
            p.OrderNumber,
            p.Email,
            p.CardNumber,
            p.ExpMMYY,
            p.CardholderName,
            p.Address1,
            p.Address2,
            p.City,
            states.abbreviation AS StateAbbreviation,
            p.ZipCode,
            p.TotalPriceNoTax,
            p.TotalPriceTax,
            status.StatusID AS OrderStatusID,
            pr.Product_id as ProductID,
            p.Quantity,
            p.PurchaseDate,
            states.name AS StateName,
            status.Description AS OrderStatus,
            pr.name AS ProductName,
            pr.category_id AS ProductCategoryID,
            pr.price AS ProductPrice,
            pr.description AS ProductDescription,
            pr.image_url AS ProductImageURL
        FROM PurchaseLogs AS p
        LEFT JOIN states ON p.stateID = states.id
        LEFT JOIN Status AS status ON p.StatusID = status.StatusID
        LEFT JOIN Products AS pr ON p.productID = pr.product_id
        WHERE p.OrderNumber = ?
    """

def return_order_list(isPost):
    query = """
    WITH RankedPurchaseLogs AS (
    SELECT 
        p.OrderID,
        p.OrderNumber,
        p.Email,
        p.CardNumber,
        p.ExpMMYY,
        p.CardholderName,
        p.Address1,
        p.Address2,
        p.City,
        states.abbreviation AS StateAbbreviation,
        p.ZipCode,
        p.TotalPriceNoTax,
        p.TotalPriceTax,
        status.StatusID AS OrderStatusID,
        pr.Product_id AS ProductID,
        p.Quantity,
        p.PurchaseDate,
        states.name AS StateName,
        status.Description AS OrderStatus,
        pr.name AS ProductName,
        pr.category_id AS ProductCategoryID,
        pr.price AS ProductPrice,
        pr.description AS ProductDescription,
        pr.image_url AS ProductImageURL,
        ROW_NUMBER() OVER(PARTITION BY p.OrderNumber ORDER BY p.OrderID) AS RowNum
    FROM PurchaseLogs AS p
    LEFT JOIN states ON p.stateID = states.id
    LEFT JOIN Status AS status ON p.StatusID = status.StatusID
    LEFT JOIN Products AS pr ON p.productID = pr.product_id
)
SELECT 
    OrderID,
    OrderNumber,
    Email,
    CardNumber,
    ExpMMYY,
    CardholderName,
    Address1,
    Address2,
    City,
    StateAbbreviation,
    ZipCode,
    TotalPriceNoTax,
    TotalPriceTax,
    OrderStatusID,
    ProductID,
    Quantity,
    PurchaseDate,
    StateName,
    OrderStatus,
    ProductName,
    ProductCategoryID,
    ProductPrice,
    ProductDescription,
    ProductImageURL
FROM RankedPurchaseLogs
WHERE RowNum = 1
    """
    if isPost:
        query += """
        AND OrderNumber = ?
        """
    return query

def return_purchase_query(isPost):
    query = """
    SELECT 
            p.OrderID,
            p.OrderNumber,
            p.Email,
            p.CardNumber,
            p.ExpMMYY,
            p.CardholderName,
            p.Address1,
            p.Address2,
            p.City,
            states.abbreviation AS StateAbbreviation,
            p.ZipCode,
            p.TotalPriceNoTax,
            p.TotalPriceTax,
            status.StatusID AS OrderStatusID,
            pr.Product_id as ProductID,
            p.Quantity,
            p.PurchaseDate,
            states.name AS StateName,
            status.Description AS OrderStatus,
            pr.name AS ProductName,
            pr.category_id AS ProductCategoryID,
            pr.price AS ProductPrice,
            pr.description AS ProductDescription,
            pr.image_url AS ProductImageURL
        FROM PurchaseLogs AS p
        LEFT JOIN states ON p.stateID = states.id
        LEFT JOIN Status AS status ON p.StatusID = status.StatusID
        LEFT JOIN Products AS pr ON p.productID = pr.product_id
    """
    if isPost:
        query += """
        WHERE p.OrderNumber = ?
        """
    return query

def return_status_query():
    return "Select * from Status"

def update_purchase_logs_status_query(status_id, order_number):
    return "UPDATE PurchaseLogs SET StatusID = ? WHERE OrderNumber = ?;"

def return_order_address_query():
    query = """
    SELECT 
            p.OrderID,
            p.OrderNumber,
            p.Address1,
            p.Address2,
            p.City,
            p.ZipCode,
            s.id as StatesID,
            s.abbreviation AS StateAbbreviation
        FROM PurchaseLogs AS p
        LEFT JOIN states as s ON p.stateID = s.id
        WHERE p.OrderNumber = ?
    """
    return query

def update_address_by_order_number(state_id):
    if state_id == 'None' or state_id is None or state_id == '':
        query = f"UPDATE PurchaseLogs SET Address1 = ?, Address2 = ?, City = ?, ZipCode = ? WHERE OrderNumber = ?"
    else:
        query = f"UPDATE PurchaseLogs SET Address1 = ?, Address2 = ?, City = ?, StateID = ?, ZipCode = ? WHERE OrderNumber = ?"
    
    return query

def get_all_users(userID):
    query = f"Select u.ID, u.Username, u.PasswordHash, a.AccessLevelID, a.AccessLevelName, u.FirstName, u.LastName, u.OldHashPassword from Users as u Left Join AccessLevels as a ON u.AccessLevel = a.AccessLevelID"
    if userID:
        query += " Where u.ID = ?"
    return query

def get_access_level():
    query = f"Select * from AccessLevels"
    return query

def create_or_edit_user(id):
    if id:
        query = 'UPDATE users SET firstName=?, lastName=?, username=?, passwordHash=?, accessLevel=? WHERE ID=?;'
    else:
        query = 'INSERT INTO users (firstName, lastName, username, passwordHash, accessLevel) VALUES (?, ?, ?, ?, ?);'
    return query

def edit_user_query(isHashPassword):
    if isHashPassword:
        query = 'UPDATE users SET firstName=?, lastName=?, username=?, passwordHash=?, accessLevel=? WHERE ID=?;'
    else:
        query = 'UPDATE users SET firstName=?, lastName=?, username=?, accessLevel=? WHERE ID=?;'

    print(query)
    return query

def get_delete_user_query():
    return "DELETE FROM Users WHERE ID=?"