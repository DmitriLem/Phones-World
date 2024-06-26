from flask import (
    Flask, render_template, request, redirect, session, flash, jsonify,
    make_response, url_for
)
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user, current_user
)
from flask_caching import Cache
from werkzeug.utils import secure_filename
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import pyodbc
import requests
import os
import uuid
import decimal
from contextlib import closing
from werkzeug.exceptions import HTTPException
from config import Config
from emailbody import GetEmailBody
from hasher import hash_password
from queries import (
    fetch_random_products_query, search_products_query, get_product_by_id_query,
    search_products_by_category_query, get_all_products_query, get_all_categories_query,
    get_filtered_categories_query, insert_product_query, get_product_id_query,
    insert_inventory_query, get_image_url_query, delete_inventory_query,
    delete_product_query, update_product_query, get_all_states_query,
    get_purchase_log_query, update_inventory_query, get_existing_order_numbers_query,
    get_tax_percentage_query, insert_purchase_log_query,
    get_purchase_log_by_order_number_query, return_order_list, return_purchase_query,
    update_purchase_logs_status_query, return_status_query, return_order_address_query,
    update_address_by_order_number, get_all_users, get_access_level, create_or_edit_user,
    get_delete_user_query
)
from utils import (
    generate_order_number,
    calculate_total_cost,
    validate_checkout_data,
    ValidAddressData,
    validate_data,
    validate_data_for_edit,
    get_time_of_day
)


app = Flask(__name__)
app.config.from_object(Config)
cache = Cache(app)

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, user_id, access_level, first_name, last_name):
        self.id = user_id
        self.access_level = access_level
        self.first_name = first_name
        self.last_name = last_name

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
    product = cursor.fetchall()
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
    if not check_access(1):
        return redirect(url_for('login'))
    city, postal_code = get_location_from_ip()
    results = get_all_products()
    return render_template('crud.html', year=datetime.now().year, results=results, categories=get_nav_categories(), city=city, postal_code=postal_code)

@app.route('/add_product')
def add_product():
    if not check_access(1):
        return redirect(url_for('login'))
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
    if not check_access(1):
        return redirect(url_for('login'))
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
    if not check_access(1):
        return redirect(url_for('login'))
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
    if not check_access(1):
        return redirect(url_for('login'))
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
    if not check_access(1):
        return redirect(url_for('login'))
    
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
    if not check_access(2):
        return redirect(url_for('login'))
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
    if not check_access(2):
        return redirect(url_for('login'))
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
    if not check_access(2):
        return redirect(url_for('login'))
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
    if not check_access(2):
        return redirect(url_for('login'))
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

@cache.cached(timeout=500)
@app.route('/user_dashboard', methods=['GET', 'POST'])
def user_dashboard():
    if not check_access(3):
        return redirect(url_for('login'))
    city, postal_code = get_location_from_ip()
    isSearching = False
    conn = create_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        isSearching = True
        userID = request.form.get('userID')
        cursor.execute(get_all_users(userID), userID)
    else:
        cursor.execute(get_all_users(None))
    results = cursor.fetchall()
    conn.close()

    return render_template('user_dashboard.html', year=datetime.now().year, isSearching=isSearching, results=results, categories=get_nav_categories(), city=city, postal_code=postal_code)

@login_manager.user_loader
def load_user(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, AccessLevel, FirstName, LastName FROM Users WHERE id=?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        user_id, access_level, first_name, last_name = user_data
        return User(user_id, access_level, first_name, last_name)
    return None

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = hash_password(request.form['password'])

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, AccessLevel, FirstName, LastName, PasswordHash FROM Users WHERE username=?", (username,)) # 0 1 2 3 4 (4 - password)
    user_data = cursor.fetchone()
        
    if user_data and user_data[4] == password:
        user = User(user_data[0], user_data[1], user_data[2], user_data[3])
        login_user(user)
        conn.close()
        return redirect('/hub')
    else:
        flash('Incorrect username or password. Try Again.', 'Error')
        conn.close()
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add_new_user', methods=['GET', 'POST'])
def add_new_user():
    if not check_access(3):
        return redirect(url_for('login'))
    if request.method == 'POST':
        print('POST')
        fName = request.form.get('firstName').strip()
        lName = request.form.get('lastName').strip()
        username = request.form.get('username').strip()
        password = hash_password(request.form.get('password').strip())
        access_lvl_id = request.form.get('Access')
        valid = validate_data(fName, lName, username, password, access_lvl_id)
        if valid:
            with create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(create_or_edit_user(False), (fName, lName, username, password, access_lvl_id))
                conn.commit()
        else:
            flash("Error")

        return redirect('/user_dashboard')

    city, postal_code = get_location_from_ip()
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(get_access_level())
    access = cursor.fetchall()
    conn.close()
    return render_template('add_new_user.html', access=access, year=datetime.now().year, categories=get_nav_categories(), city=city, postal_code=postal_code)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if not check_access(3):
        return redirect(url_for('login'))
    if request.method == 'POST':
        print('Post')
        try:
            fName = request.form.get('firstName').strip()
            lName = request.form.get('lastName').strip()
            username = request.form.get('username').strip()
            password = request.form.get('password').strip()
            access_lvl_id = request.form.get('Access')
            if access_lvl_id is None or access_lvl_id == 'None':
                conn = create_connection()
                cursor = conn.cursor()
                cursor.execute('Select AccessLevel from Users Where ID = ?', (user_id))
                result = cursor.fetchone()
                access_lvl_id = result[0]
                conn.close()
            print("FName:", fName)
            print("LName:", lName)
            print("Username:", username)
            print("Password:", password)
            print("Access Level ID:", access_lvl_id)
            valid = validate_data_for_edit(fName, lName, username, password, access_lvl_id)
            print('IsValid? ',valid)
            if valid:
                print('inside if')
                conn = create_connection()
                cursor = conn.cursor()
                if password:
                    password = hash_password(password)
                    cursor.execute('UPDATE Users SET OldHashPassword = PasswordHash WHERE ID = ?',
                                (user_id))
                    cursor.execute('UPDATE Users SET firstName = ?, lastName = ?, Username = ?, passwordHash = ?, AccessLevel = ? WHERE ID = ?',
                                (fName, lName, username, password, access_lvl_id, user_id))
                else:
                    cursor.execute('UPDATE Users SET firstName = ?, lastName = ?, Username = ?, AccessLevel = ? WHERE ID = ?',
                                (fName, lName, username, access_lvl_id, user_id))
                conn.commit()
                conn.close()
                return redirect('/user_dashboard')
            else:
                flash("Invalid data. Please check your input.")
        except Exception as e:
            print('Error:', e)

        return redirect('/user_dashboard')

    city, postal_code = get_location_from_ip()
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(get_access_level())
    access = cursor.fetchall()
    cursor.execute('Select* From Users Where ID = ?',(user_id))
    result = cursor.fetchall()
    conn.close()
    return render_template('edit_user.html', access=access, year=datetime.now().year, categories=get_nav_categories(), city=city, postal_code=postal_code,result=result)
    
@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not check_access(3):
        return redirect(url_for('login'))
    print(user_id)
    if request.method == 'POST':
        print('Post method')
        try:
            with create_connection() as conn:
                cursor = conn.cursor()
                query = get_delete_user_query()
                cursor.execute(query, (user_id,))
        except Exception as e:
            print(e)
            flash('Failed to delete user. Error: ' + str(e), 'error')

    return redirect('/user_dashboard')

@app.route('/hub', methods=['GET'])
def hub():

    if not check_access(1):
        return redirect(url_for('login'))

    user = {
        'FirstName': current_user.first_name,
        'LastName': current_user.last_name,
        'AccessLevel': current_user.access_level
    }

    return render_template('hub.html', user=user, time = get_time_of_day())

def check_access(access_level):
    if not current_user.is_authenticated:
        return False
    return current_user.access_level >= access_level

if __name__ == "__main__":
    app.run(debug=True)
