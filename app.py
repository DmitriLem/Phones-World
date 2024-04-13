from flask import Flask, render_template, request, redirect, session, flash, jsonify, make_response, render_template
import pyodbc
import random
import requests
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import uuid
import decimal
from flask_caching import Cache
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import Config
from contextlib import closing
from werkzeug.exceptions import HTTPException
from emailbody import GetEmailBody
from flask import render_template

app = Flask(__name__)
app.config.from_object(Config)
cache = Cache(app)

def create_connection():
    conn = pyodbc.connect('DRIVER={' + app.config['DB_DRIVER'] + '};SERVER=' + app.config['DB_SERVER'] +
                          ';DATABASE=' + app.config['DB_DATABASE'] + ';UID=' + app.config['DB_USERNAME'] +
                          ';PWD=' + app.config['DB_PASSWORD'])
    return conn

def get_location_from_ip():
    api_token = app.config['API_TOKEN']
    user_ip = request.remote_addr
    cached_data = cache.get(user_ip)
    if cached_data:
        return cached_data

    url = f'https://ipinfo.io/?token={api_token}&ip={user_ip}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        city = data.get('city')
        postal_code = data.get('postal')
        cache.set(user_ip, (city, postal_code))
        return city, postal_code
    else:
        return '', ''

def get_filtered_categories():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Categories WHERE LEN(name) <= 16")
    filtered_categories = cursor.fetchall()
    conn.close()
    return filtered_categories

def get_nav_categories():
    cached_categories = cache.get('nav_categories')
    if cached_categories:
        return cached_categories

    filtered_categories = get_filtered_categories()
    cache.set('nav_categories', filtered_categories)
    return filtered_categories

@cache.cached(timeout=3600)
@app.route('/')
def index():
    city, postal_code = get_location_from_ip()
    random_products = get_cached_random_products()
    return render_template('index.html', year=datetime.now().year, categories=get_nav_categories(), random_products=random_products, city=city, postal_code=postal_code)

def get_cached_random_products():
    cached_products = cache.get('random_products')
    if cached_products is None:
        cached_products = fetch_random_products_from_db()
        cache.set('random_products', cached_products)
    return cached_products

def fetch_random_products_from_db():
    conn = create_connection()
    cursor = conn.cursor()
    query = """
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
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

@cache.memoize(timeout=300)
def search_products_by_name(search_query):
    conn = create_connection()
    cursor = conn.cursor()
    query = """
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
    cursor.execute(query, ('%' + search_query + '%', '%' + search_query + '%'))
    results = cursor.fetchall()
    conn.close()
    return results

@app.route('/search_by_name', methods=['GET', 'POST'])
def search_by_name():
    city, postal_code = get_location_from_ip()
    search_query = ''
    results = []
    if request.method == 'POST':
        search_query = request.form['search_query']
        results = search_products_by_name(search_query)

    return render_template('search_by_name.html', results=results, search_query=search_query, categories=get_nav_categories(), city=city, postal_code=postal_code)

@cache.cached(timeout=3600)
def get_product_by_id(product_id):
    conn = create_connection()
    cursor = conn.cursor()
    query = """
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
    cursor.execute(query, (product_id,))
    product = cursor.fetchone()
    conn.close()
    return product

@app.route('/view_product/<int:product_id>')
def view_product(product_id):
    city, postal_code = get_location_from_ip()
    product = get_product_by_id(product_id)
    return render_template('view_product.html', product=product, categories=get_nav_categories(), year=datetime.now().year, city=city, postal_code=postal_code)

@cache.memoize(timeout=3600)
def search_products_by_category(category_id):
    conn = create_connection()
    cursor = conn.cursor()
    query = """
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
    cursor.execute(query, (category_id,))
    results = cursor.fetchall()
    conn.close()
    return results

@app.route('/search/<int:category_id>')
def search_by_category(category_id):
    city, postal_code = get_location_from_ip()
    results = search_products_by_category(category_id)
    return render_template('search_results.html', year=datetime.now().year, category_id=category_id, categories=get_nav_categories(), results=results, city=city, postal_code=postal_code)

@cache.cached(timeout=300)
def get_all_products():
    conn = create_connection()
    cursor = conn.cursor()
    query = """
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
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

@app.route('/crud')
def crud():
    city, postal_code = get_location_from_ip()
    results = get_all_products()
    return render_template('crud.html', year=datetime.now().year, results=results, categories=get_nav_categories(), city=city, postal_code=postal_code)

@app.route('/add_product')
def add_product():
    city, postal_code = get_location_from_ip()
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT c.category_id, c.name FROM Categories as c")
    results = cursor.fetchall()
    conn.close()
    return render_template('add_product.html', year=datetime.now().year, results=results, categories=get_nav_categories(), city=city, postal_code=postal_code)

@app.route('/create', methods=['POST'])
def create():
    if request.method == 'POST':
        name = request.form.get('name')
        category_id = int(request.form.get('category_id'))
        price = decimal.Decimal(request.form.get('price'))
        description = request.form.get('description')
        quantity = int(request.form.get('quantity'))
        file = request.files.get('image')

        if file:
            try:
                filename = str(uuid.uuid4()) + secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                with create_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO Products (name, category_id, price, description, image_url) VALUES (?, ?, ?, ?, ?)",
                                   (name, category_id, price, description, filename))
                    cursor.execute("SELECT product_id FROM Products WHERE name = ? AND description LIKE ? AND price = ?",
                                   (name, description, price))
                    product_id = cursor.fetchone()[0]
                    cursor.execute("INSERT INTO Inventory (product_id, quantity) VALUES (?, ?)", (product_id, quantity))
                    conn.commit()
                    flash('Product added successfully!', 'success')
            except Exception as e:
                flash('Failed to add product. Error: ' + str(e), 'error')
            finally:
                conn.close()
        else:
            flash('Failed to add product. Image is required.', 'error')

    return redirect('/crud' if request.method == 'POST' else '/add_product')

@app.route('/delete/<int:product_id>', methods=['POST', 'GET'])
def delete_product(product_id):
    if request.method == 'POST':
        try:
            with create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT image_url FROM Products WHERE product_id=?", (product_id,))
                image_url = cursor.fetchone()[0]
                cursor.execute("DELETE FROM Inventory WHERE product_id=?", (product_id,))
                cursor.execute("DELETE FROM Products WHERE product_id=?", (product_id,))
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_url)
                if os.path.exists(image_path):
                    os.remove(image_path)
                flash('Product deleted successfully!', 'success')
        except Exception as e:
            flash('Failed to delete product. Error: ' + str(e), 'error')

        return redirect('/crud')

    return redirect('/crud')

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    city, postal_code = get_location_from_ip()
    conn = create_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            category_id = int(request.form.get('category_id'))
            price = decimal.Decimal(request.form.get('price'))
            description = request.form.get('description')
            cursor.execute("UPDATE Products SET name=?, category_id=?, price=?, description=? WHERE product_id=?",
                           (name, category_id, price, description, product_id))
            conn.commit()
            flash('Product updated successfully!', 'success')
        except Exception as e:
            conn.rollback()
            flash('Failed to update product. Error: ' + str(e), 'error')
        finally:
            conn.close()
        return redirect('/crud')
    
    cursor.execute("SELECT * FROM Products WHERE product_id=?", (product_id,))
    product = cursor.fetchone()
    conn.close()

    return render_template('edit_product.html', product=product, categories=get_nav_categories(), year=datetime.now().year, city=city, postal_code=postal_code)

@app.route('/Cart')
def cart():
    city, postal_code = get_location_from_ip()
    cart = session.get('cart') or {}
    products_in_cart = []
    total_items = 0
    total_price = 0
    conn = create_connection()
    cursor = conn.cursor()

    for product_id, quantity in cart.items():
        cursor.execute("SELECT * FROM Products WHERE product_id = ?", (product_id,))
        product = cursor.fetchone()
        if product:
            total_items += quantity
            total_price += quantity * product.price
            products_in_cart.append({'product': product, 'quantity': quantity})
    conn.close()
    return render_template('Cart.html', year=datetime.now().year, categories=get_nav_categories(), city=city,
                           postal_code=postal_code, cart=cart, products=products_in_cart, total_items=total_items, total_price=total_price)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity')
    if not product_id or not quantity:
        return jsonify({'error': 'No product identifier or quantity specified'}), 400
    cart = session.get('cart') or {}
    cart[product_id] = cart.get(product_id, 0) + quantity
    session['cart'] = cart
    return jsonify({'message': 'The item has been successfully added to the cart'}), 200

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    product_id = request.form.get('product_id')
    if not product_id:
        return jsonify({'error': 'No product identifier specified'}), 400
    
    cart = session.get('cart') or {}
    if product_id in cart:
        del cart[product_id]
        session['cart'] = cart
    
    return redirect('/Cart')

@app.route('/buy', methods=['GET', 'POST'])
@app.route('/buyProduct', methods=['POST'])
def buy():
    city, postal_code = get_location_from_ip()
    current_year = datetime.now().year

    if request.method == 'POST':
        product_id = request.form['productId']
        cart = {product_id: 1}
    else:
        cart = session.get('cart') or {}

    products_in_cart = []
    total_items = 0
    total_price = 0
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM States")
    states = cursor.fetchall()
    for product_id, quantity in cart.items():
        cursor.execute("SELECT * FROM Products WHERE product_id = ?", (product_id,))
        product = cursor.fetchone()
        if product:
            total_items += quantity
            total_price += quantity * product.price
            products_in_cart.append({'product': product, 'quantity': quantity})
    conn.close()
    print("Data:", products_in_cart, total_items, total_price)
    if not products_in_cart:
        return redirect("/Cart")
    return render_template('Buy.html', year=current_year, current_year=current_year, categories=get_nav_categories(),
                           city=city, postal_code=postal_code, cart_products=products_in_cart, total_items=total_items,
                           total_price=total_price, states=states)

def generate_order_number(existing_order_numbers):
    while True:
        new_order_number = random.randint(100000, 99999999)
        if new_order_number not in existing_order_numbers:
            return new_order_number
        
def calculate_total_cost(price, tax_rate):
    tax_amount = price * (float(tax_rate) / 100)
    total_cost = price + tax_amount
    return total_cost

def sendEmailReceipt(order_number, recipient_email):
    smtp_config = Config.EMAIL_CFG
    sender_email = smtp_config['sender_email']
    sender_password = smtp_config['sender_password']
    smtp_server = smtp_config['smtp_server']
    smtp_port = smtp_config['smtp_port']

    query = """SELECT 
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

    try:
        with closing(create_connection()) as conn, conn.cursor() as cursor:
            cursor.execute(query, (order_number,))
            log = cursor.fetchall()

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f'Phones World. Thank you! Your Order Receipt #{order_number}'
        html_content = GetEmailBody(order_number, log)
        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        print('Email sent successfully!')
        return True
    except Exception as e:
        print(f'Failed to send email: {e}')
        return False

def validate_checkout_data(data):
    required_fields = ['emailAddress', 'cardNum', 'mm', 'yy', 'cardName', 'inputAddress', 'inputCity', 'inputState', 'inputZip', 'product_id[]', 'quantity[]']
    for field in required_fields:
        if field not in data:
            return False
    return True

@app.route('/proceed_checkout', methods=['POST'])
def proceed_checkout():
    data = request.form
    if not validate_checkout_data(data):
        return jsonify({'error': 'Invalid request data'}), 400

    email = data['emailAddress']
    card_number = data['cardNum']
    expiration_month = data['mm']
    expiration_year = data['yy']
    cardholder_name = data['cardName']
    address = data['inputAddress']
    address2 = data['inputAddress2']
    city = data['inputCity']
    state_id = data['inputState']
    zip_code = data['inputZip']
    total_price = float(data.get('total_price', 0))
    product_ids = data.getlist('product_id[]')
    quantities = data.getlist('quantity[]')
    product_quantity_pairs = list(zip(product_ids, quantities))

    conn = create_connection()
    cursor = conn.cursor()

    try:
        for product_id, quantity in product_quantity_pairs:
            update_query = "UPDATE Inventory SET Quantity = Quantity - ? WHERE Product_ID = ?"
            cursor.execute(update_query, (quantity, product_id))

        cursor.execute("SELECT OrderNumber FROM PurchaseLogs")
        existing_order_numbers = [row[0] for row in cursor.fetchall()]
        new_order_number = generate_order_number(existing_order_numbers)
        cursor.execute("SELECT tax_percentage FROM States WHERE id = ?", (state_id,))
        tax = cursor.fetchone()[0]

        for product_id, quantity in product_quantity_pairs:
            total_with_tax = calculate_total_cost(total_price, tax)
            insert_query = "INSERT INTO PurchaseLogs (OrderNumber, Email, CardNumber, ExpMMYY, " \
                            "CardholderName, Address1, Address2, City, StateID, ZipCode, " \
                            "TotalPriceNoTax, TotalPriceTax, StatusID, ProductID, Quantity, PurchaseDate) " \
                            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            cursor.execute(insert_query, (new_order_number, email, card_number,
                                          f"{expiration_month}/{expiration_year}", cardholder_name, address, address2, city,
                                          state_id, zip_code, total_price, total_with_tax, 1, product_id, quantity,
                                          datetime.now()))

        conn.commit()
        is_email_sent = sendEmailReceipt(new_order_number, email)
        print('Is email sent?', is_email_sent)
    except pyodbc.Error as e:
        print(f'Error during checkout: {e}')
        return jsonify({'error': 'An error occurred during checkout'}), 500
    finally:
        conn.close()

    response = make_response(redirect('/receipt'))
    response.set_cookie('new_order_number', str(new_order_number))
    return response

@app.route('/receipt', methods=['GET'])
def receipt():
    city, postal_code = get_location_from_ip()
    order_number = request.cookies.get('new_order_number')
    if not order_number:
        return render_template('error.html', message='Order number not found'), 404

    try:
        with create_connection() as conn, conn.cursor() as cursor:
            insert_query = """
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
            cursor.execute(insert_query, (order_number,))
            log = cursor.fetchall()
    except Exception as e:
        return render_template('error.html', message=str(e)), 500

    if not log:
        return render_template('error.html', message='Order not found'), 404

    return render_template('receipt.html', year=datetime.now().year, categories=get_nav_categories(), city=city,
                           postal_code=postal_code, order_number=order_number, log=log)

@app.route('/OrderCheck', methods=['GET'])
def orderCheck():
    city, postal_code = get_location_from_ip()
    return render_template('enter_orderNum.html', year=datetime.now().year, categories=get_nav_categories(), city=city,
                           postal_code=postal_code)

@app.route('/CheckingOrderNumber', methods=['POST'])
def checkingOrderNumber():
    order_number = request.form['orderNumber']
    session['order_number'] = order_number
    return redirect('/OrderInfo')
    
@app.route('/OrderInfo', methods=['GET'])
def showOrderInfo():
    order_number = session.get('order_number')
    if not order_number:
        flash('Invalid order number', 'error')
        return redirect('/CheckingOrderNumber')
    session.pop('order_number', None)
    city, postal_code = get_location_from_ip()
    conn = create_connection()
    cursor = conn.cursor()
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
        WHERE p.OrderNumber = ?
    """
    cursor.execute(query, (order_number,))
    log = cursor.fetchall()
    conn.close()

    return render_template('order_Info.html', order_number=order_number, year=datetime.now().year, categories=get_nav_categories(), city=city,
                           postal_code=postal_code, log=log)

@app.errorhandler(HTTPException)
def handle_exception(e):
    return render_template('error.html', error=str(e)), e.code

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

@cache.cached(timeout=500)
@app.route('/manageOrders', methods=['GET', 'POST'])
def manage_orders():
    city, postal_code = get_location_from_ip()
    isPost = False
    conn = create_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.form
        order_number = data['orderNumber']
        isPost = True
        query = return_order_list(isPost)
        cursor.execute(query, (order_number,))
    else:
        query = return_order_list(isPost)
        cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return render_template('manageOrders.html', results=results, isPost=isPost, year=datetime.now().year, categories=get_nav_categories(), city=city,
                           postal_code=postal_code)

@cache.cached(timeout=500)
@app.route('/more_order_info/<int:orderNumber>', methods=['GET'])
def more_order_info(orderNumber):
    city, postal_code = get_location_from_ip()
    conn = create_connection()
    cursor = conn.cursor()
    query = return_purchase_query(True)
    cursor.execute(query, (orderNumber,))
    results = cursor.fetchall()
    cursor.execute("Select * from Status")
    status = cursor.fetchall()
    conn.close()

    return render_template('more_order_information.html', results=results, status=status, year=datetime.now().year, categories=get_nav_categories(), city=city,
                           postal_code=postal_code)

@app.route('/update_status', methods=['POST'])
def update_status():
    data = request.get_json()
    orderId = data['orderId']
    newStatus = request.form.get('new_status')
    print(data)
    print(orderId)
    print(newStatus)

    return jsonify({'message': 'Status updated successfully'}), 200

if __name__ == "__main__":
    app.run(debug=True)
