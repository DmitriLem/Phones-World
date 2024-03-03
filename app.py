from flask import Flask, render_template, url_for, request, redirect
import pyodbc
import requests
import random
from datetime import datetime

app = Flask(__name__)

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
        return ''

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
        i.quantity != NULL OR i.quantity > 0
    """
    cursor.execute(query)
    random_products = cursor.fetchall()
    conn.close()

    # Фильтруем категории
    filtered_categories = [category for category in categories if len(category.name.split()) <= 2][:17]

    # Получаем данные о местоположении
    city, postal_code = get_location_from_ip(user_ip, '86c960f33f9c64') #Api token

    return render_template('search_by_name.html', results=results, search_query=search_query, categories=filtered_categories, random_products=random_products, city=city, postal_code=postal_code)

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
            i.quantity != NULL OR i.quantity > 0
        """
        cursor.execute(query)
        random_products = cursor.fetchall()
        conn.close()

        # Фильтруем категории
        filtered_categories = [category for category in categories if len(category.name.split()) <= 2][:17]

        # Получаем данные о местоположении
        city, postal_code = get_location_from_ip(user_ip, '86c960f33f9c64') #Api toke

        return render_template('search_by_name.html', results=results, categories=filtered_categories, random_products=random_products, city=city, postal_code=postal_code)

    return render_template('search_by_name.html')

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

        return render_template('search_by_name.html', results=results)

    return render_template('search_by_name.html')

    if request.method == 'POST':
        search_query = request.form['search_query']

        # Создаем соединение с базой данных
        conn = create_connection()
        cursor = conn.cursor()

        # Запрос SQL для поиска продуктов по имени
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
            p.name LIKE ?
        """
        cursor.execute(query, ('%' + search_query + '%',))
        results = cursor.fetchall()

        # Закрываем соединение
        conn.close()

        return render_template('search_by_name.html', results=results)

    return render_template('search_by_name.html')

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
        i.quantity != NULL OR i.quantity > 0
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

if __name__ == "__main__":
    app.run(debug=True)
