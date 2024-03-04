from flask import Flask, render_template, request, redirect, session, flash
import pyodbc
import random
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'my_super_secret_key_1234567890NobodyWillGetThisKeyAnyway'

# Функция для создания соединения с базой данных
def create_connection():
    server = 'dbinventory.cz84gqqau37j.us-east-2.rds.amazonaws.com'  # Имя вашего сервера MSSQL
    database = 'Inventory'  # Имя вашей базы данных MSSQL
    username = 'admin'  # Ваше имя пользователя MSSQL
    password = 'NtFqQ4Ap'  # Ваш пароль MSSQL
    driver = 'ODBC Driver 17 for SQL Server'  # Драйвер для MSSQL, убедитесь, что он установлен

    # Создаем строку подключения
    conn = pyodbc.connect('DRIVER={' + driver + '};SERVER=' + server +
                          ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
    return conn

# Функция для определения местоположения пользователя по IP
def get_location_from_ip(ip_address, api_token):
    url = f'https://ipinfo.io/?token={api_token}&ip={ip_address}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        city = data.get('city')
        postal_code = data.get('postal')
        return city, postal_code
    else:
        return '', ''

@app.route('/')
def index():
    user_ip = request.remote_addr

    # Создаем соединение с базой данных
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Categories")
    categories = cursor.fetchall()

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
        i.quantity IS NOT NULL AND i.quantity > 0
    """
    cursor.execute(query)
    results = cursor.fetchall()

    # Закрываем соединение
    conn.close()

    filtered_categories = [category for category in categories if len(category.name.split()) <= 2][:17]

    city, postal_code = get_location_from_ip(user_ip, '86c960f33f9c64') #Api token

    # Выбираем случайные продукты из результатов
    random_products = random.sample(results, min(9, len(results)))

    return render_template('index.html', year=datetime.now().year, categories=filtered_categories, random_products=random_products, city=city, postal_code=postal_code)

@app.route('/search_by_name', methods=['GET', 'POST'])
def search_by_name():
    search_query = ''

    if request.method == 'POST':
        search_query = request.form['search_query']

        # Создаем соединение с базой данных
        conn = create_connection()
        cursor = conn.cursor()

        # Запрос SQL для поиска продуктов по имени и описанию
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

        # Закрываем соединение
        conn.close()

        # Получаем данные для всех категорий и случайных продуктов
        user_ip = request.remote_addr
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Categories")
        categories = cursor.fetchall()
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
            i.quantity IS NOT NULL AND i.quantity > 0
        """
        cursor.execute(query)
        random_products = cursor.fetchall()
        conn.close()

        # Фильтруем категории
        filtered_categories = [category for category in categories if len(category.name.split()) <= 2][:17]

        # Получаем данные о местоположении
        city, postal_code = get_location_from_ip(user_ip, '86c960f33f9c64') #Api token

        return render_template('search_by_name.html', results=results, search_query=search_query, categories=filtered_categories, random_products=random_products, city=city, postal_code=postal_code)

    return render_template('search_by_name.html')

@app.route('/view_product/<int:product_id>')
def view_product(product_id):
    # Создаем соединение с базой данных
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

    # Закрываем соединение
    conn.close()

    return render_template('view_product.html', product=product)

@app.route('/search/<int:category_id>')
def search_by_category(category_id):
    user_ip = request.remote_addr

    # Создаем соединение с базой данных
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Categories")
    categories = cursor.fetchall()

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

    # Закрываем соединение
    conn.close()

    filtered_categories = [category for category in categories if len(category.name.split()) <= 2][:17]

    city, postal_code = get_location_from_ip(user_ip, '86c960f33f9c64') #Api token

    return render_template('search_results.html', year=datetime.now().year, category_id=category_id, categories=filtered_categories, results=results, city=city, postal_code=postal_code)

@app.route('/cart')
def cart():
    if 'cart' not in session:
        session['cart'] = {}

    user_ip = request.remote_addr

    # Создаем соединение с базой данных
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Categories")
    categories = cursor.fetchall()

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
        i.quantity IS NOT NULL AND i.quantity > 0
    """
    cursor.execute(query)
    results = cursor.fetchall()

    # Получаем данные для корзины после закрытия соединения и курсора
    cart_details = []
    total_items = 0
    total_price = 0
    for product_id, quantity in session['cart'].items():
        cursor.execute("SELECT * FROM Products WHERE product_id=?", (product_id,))
        product = cursor.fetchone()
        if product:
            total_items += quantity
            total_price += product.price * quantity
            cart_details.append((product, quantity))

    # Закрываем соединение и курсор
    cursor.close()
    conn.close()

    filtered_categories = [category for category in categories if len(category.name.split()) <= 2][:17]

    city, postal_code = get_location_from_ip(user_ip, '86c960f33f9c64') #Api token

    # Выбираем случайные продукты из результатов
    random_products = random.sample(results, min(9, len(results)))

    return render_template('cart.html', cart_details=cart_details, total_items=total_items, total_price=total_price, city=city, postal_code=postal_code, categories=filtered_categories, random_products=random_products)


@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = {}

    session['cart'][product_id] = session['cart'].get(product_id, 0) + 1

    flash('Product added to cart successfully!', 'success')
    return redirect('/cart')

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'cart' in session and product_id in session['cart']:
        del session['cart'][product_id]
        flash('Product removed from cart successfully!', 'success')

    return redirect('/cart')

if __name__ == "__main__":
    app.run(debug=True)
