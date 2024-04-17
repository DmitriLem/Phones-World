from flask import Flask, render_template, request, redirect, session, flash, jsonify, make_response, render_template, url_for
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
from queries import (
    fetch_random_products_query,
    search_products_query,
    get_product_by_id_query,
    search_products_by_category_query,
    get_all_products_query,
    get_all_categories_query,
    get_filtered_categories_query,
    insert_product_query,
    get_product_id_query,
    insert_inventory_query,
    get_image_url_query,
    delete_inventory_query,
    delete_product_query,
    update_product_query,
    get_all_states_query,
    get_purchase_log_query,
    update_inventory_query,
    get_existing_order_numbers_query,
    get_tax_percentage_query,
    insert_purchase_log_query,
    get_purchase_log_by_order_number_query,
    return_order_list,
    return_purchase_query,
    update_purchase_logs_status_query,
    return_status_query,
    return_order_address_query,
    update_address_by_order_number
)
from contextlib import closing
from werkzeug.exceptions import HTTPException
from emailbody import GetEmailBody

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
    filtered_categories_query = get_filtered_categories_query()
    cursor.execute(filtered_categories_query)
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
    query = fetch_random_products_query()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

@cache.memoize(timeout=300)
def search_products_by_name(search_query):
    conn = create_connection()
    cursor = conn.cursor()
    query = search_products_query(search_query)
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
    query = get_product_by_id_query(product_id)
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
    query = search_products_by_category_query(category_id)
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
    query = get_all_products_query()
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
    categories_query = get_all_categories_query()
    cursor.execute(categories_query)
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
                    cursor.execute(insert_product_query(name, category_id, price, description, filename), (name, category_id, price, description, filename))
                    cursor.execute(get_product_id_query(name, description, price), (name, description, price))
                    product_id = cursor.fetchone()[0]
                    cursor.execute(insert_inventory_query(product_id, quantity), (product_id, quantity))
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
                cursor.execute(get_image_url_query(product_id), (product_id,))
                image_url = cursor.fetchone()[0]
                cursor.execute(delete_inventory_query(product_id), (product_id,))
                cursor.execute(delete_product_query(product_id), (product_id,))
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
            cursor.execute(update_product_query(name, category_id, price, description, product_id), (name, category_id, price, description, product_id))
            conn.commit()
            flash('Product updated successfully!', 'success')
        except Exception as e:
            conn.rollback()
            flash('Failed to update product. Error: ' + str(e), 'error')
        finally:
            conn.close()
        return redirect('/crud')

    cursor.execute(get_product_by_id_query(product_id), (product_id,))
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
        cursor.execute(get_product_by_id_query(product_id), (product_id,))
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
    states_query = get_all_states_query()
    cursor.execute(states_query)
    states = cursor.fetchall()
    for product_id, quantity in cart.items():
        cursor.execute(get_product_by_id_query(product_id), (product_id,))
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

    query = get_purchase_log_query(order_number)

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
            cursor.execute(update_inventory_query(product_id, quantity), (quantity, product_id))

        cursor.execute(get_existing_order_numbers_query())
        existing_order_numbers = [row[0] for row in cursor.fetchall()]
        new_order_number = generate_order_number(existing_order_numbers)
        cursor.execute(get_tax_percentage_query(state_id), (state_id,))
        tax = cursor.fetchone()[0]

        for product_id, quantity in product_quantity_pairs:
            total_with_tax = calculate_total_cost(total_price, tax)
            cursor.execute(insert_purchase_log_query(new_order_number, email, card_number, f"{expiration_month}/{expiration_year}",
                                                      cardholder_name, address, address2, city, state_id, zip_code,
                                                      total_price, total_with_tax, 1, product_id, quantity, datetime.now()))


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
            insert_query = get_purchase_log_by_order_number_query(order_number)
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
    query = get_purchase_log_by_order_number_query(order_number)
    cursor.execute(query, (order_number,))
    log = cursor.fetchall()
    conn.close()

    return render_template('order_Info.html', order_number=order_number, year=datetime.now().year, categories=get_nav_categories(), city=city,
                           postal_code=postal_code, log=log)

@app.errorhandler(HTTPException)
def handle_exception(e):
    return render_template('error.html', error=str(e)), e.code

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
    cursor.execute(return_status_query())
    status = cursor.fetchall()
    query = return_purchase_query(True)
    cursor.execute(query, (orderNumber,))
    results = cursor.fetchall()
    conn.close()

    return render_template('more_order_information.html', results=results, status=status, year=datetime.now().year, categories=get_nav_categories(), city=city,
                           postal_code=postal_code)

@app.route('/update_status', methods=['POST'])
def update_status():
    try:
        data = request.get_json()
        status_id = data.get('StatusID')
        order_number = data.get('OrderNumber')
        conn = create_connection()
        cursor = conn.cursor()
        update_query = update_purchase_logs_status_query(status_id, order_number)
        cursor.execute(update_query, (status_id, order_number))
        conn.commit()
        conn.close()
        print('Commit')
        return jsonify({'message': 'Status updated successfully'}), 200
    except Exception as e:
        if 'conn' in locals() and conn:
            cursor.execute("ROLLBACK;")
            conn.close()
            print('Exception')
        return jsonify({'error': str(e)}), 500

@app.route('/update_order_address', methods=['GET'])
def update_order_address():
    order_number = request.args.get('orderNumber')
    city, postal_code = get_location_from_ip()
    conn = create_connection()
    cursor = conn.cursor()
    query = return_order_address_query()
    cursor.execute(query, (order_number))
    data = cursor.fetchall()
    cursor.execute(get_all_states_query())
    states = cursor.fetchall()
    conn.close()

    return render_template('change_order_address.html', order_number=order_number, data=data, states=states, year=datetime.now().year, categories=get_nav_categories(), city=city,
                           postal_code=postal_code)

@app.route('/update_address', methods=['POST'])
def update_address():
    order_number = request.form.get('orderNumber')
    address1 = request.form.get('Address1')
    address2 = request.form.get('Address2')
    city = request.form.get('City')
    state_id = request.form.get('ddlState')
    zip_code = request.form.get('Zip')

    if ValidAddressData(order_number, address1, address2, city, state_id, zip_code):
        try:
            conn = create_connection()
            cursor = conn.cursor()
            query = update_address_by_order_number(state_id)
            if state_id == 'None' or state_id is None or state_id == '':
                cursor.execute(query, (address1, address2, city, zip_code, order_number))
            else:
                cursor.execute(query, (address1, address2, city, state_id, zip_code, order_number))
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            print('Error:', e)
        finally:
            conn.close()
            return redirect(url_for('more_order_info', orderNumber=order_number))

    return redirect(url_for('manage_orders'))

def ValidAddressData(order_number, address1, address2, city, state_id, zip_code):
    print(f"Address 1: {address1}")
    print(f"Address 2: {address2}")
    print(f"City: {city}")
    print(f"State ID: {state_id}")
    print(f"Zip Code: {zip_code}")
    print(f"OrderNumber: {order_number}")
    if not order_number:
        print("Error: Order_Number should not be empty.")
        return False
    if not address1:
        print("Error: Address1 should not be empty.")
        return False
    if not city:
        print("Error: City should not be empty.")
        return False
    if not zip_code:
        print("Error: ZipCode should not be empty.")
        return False
    if len(address1) < 2:
        print("Error: Address1 should contain at least two characters.")
        return False
    if len(city) < 4:
        print("Error: City should contain at least four characters.")
        return False
    if len(zip_code) != 5:
        print("Error: ZipCode should contain exactly five digits.")
        return False
    if not zip_code.isdigit():
        print("Error: ZipCode should be a digits.")
        return False
    return True

if __name__ == "__main__":
    app.run(debug=True)
