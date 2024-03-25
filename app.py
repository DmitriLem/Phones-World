from flask import Flask, render_template, request, redirect, session, flash, jsonify
import pyodbc #Library for connection our db
import random
import requests
from datetime import datetime
import os #Search folde
from werkzeug.utils import secure_filename
import uuid
import decimal
from flask_caching import Cache
import json

app = Flask(__name__)
app.secret_key = 'my_super_secret_key_1234567890NobodyWillGetThisKeyAnyway'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'userUploadPhotos')
app.config['CACHE_TYPE'] = 'simple'  # Используем простой кэш (можно изменить на другие типы кэша)
cache = Cache(app)

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
    user_ip = request.remote_addr

    # Create a connection to the database
    conn = create_connection()
    cursor = conn.cursor()

    # Query to fetch product details
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

    # Query to fetch all categories
    cursor.execute("SELECT * FROM Categories")
    categories = cursor.fetchall()

    # Close the database connection
    conn.close()

    # Extracting relevant information from categories
    filtered_categories = [category for category in categories if len(category[1].split()) <= 2][:17]

    # Fetch location information
    city, postal_code = get_location_from_ip(user_ip, '86c960f33f9c64')  # Api token

    return render_template('view_product.html', product=product, categories=filtered_categories, year=datetime.now().year, city=city, postal_code=postal_code)

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

@app.route('/crud')
def crud():
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
    """
    cursor.execute(query)
    results = cursor.fetchall()

    # Закрываем соединение
    conn.close()

    filtered_categories = [category for category in categories if len(category.name.split()) <= 2][:17]

    city, postal_code = get_location_from_ip(user_ip, '86c960f33f9c64') #Api token

    return render_template('crud.html', year=datetime.now().year, results=results, categories=filtered_categories, city=city, postal_code=postal_code)

@app.route('/add_product')
def add_product():
    user_ip = request.remote_addr

    # Создаем соединение с базой данных
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Categories")
    categories = cursor.fetchall()

    query = """
    SELECT 
        c.category_id,
        c.name
    FROM 
        Categories as c
    """
    cursor.execute(query)
    results = cursor.fetchall()

    # Закрываем соединение
    conn.close()

    filtered_categories = [category for category in categories if len(category.name.split()) <= 2][:17]

    city, postal_code = get_location_from_ip(user_ip, '86c960f33f9c64') #Api token

    return render_template('add_product.html', year=datetime.now().year, results=results, categories=filtered_categories, city=city, postal_code=postal_code)

@app.route('/create', methods=['POST'])
def create():
    if request.method == 'POST':
        # Получаем данные из формы
        name = request.form.get('name')
        category_id = int(request.form.get('category_id'))
        price = decimal.Decimal(request.form.get('price'))  # Преобразуем строку в десятичное число
        description = request.form.get('description')
        quantity = int(request.form.get('quantity'))
        
        # Получаем файл изображения
        file = request.files.get('image')
        
        # Проверяем, что файл был загружен
        if file:
            # Генерируем уникальное имя для изображения
            filename = str(uuid.uuid4()) + secure_filename(file.filename)
            # Сохраняем изображение в папке static/userUploadPhotos
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Соединяемся с базой данных и выполняем запрос
            conn = create_connection()
            cursor = conn.cursor()
            try:
                # Добавляем новый продукт
                cursor.execute("INSERT INTO Products (name, category_id, price, description, image_url) VALUES (?, ?, ?, ?, ?)", (name, category_id, price, description, filename))
                
                # Получаем product_id нового продукта, который только что был добавлен.
                cursor.execute("SELECT product_id FROM Products WHERE name = ? AND description LIKE ? AND price = ?", (name, description, price))
                product_id = cursor.fetchone()[0]
                
                # Добавляем quantity в таблицу Inventory, где должен быть привязан product_id
                cursor.execute("INSERT INTO Inventory (product_id, quantity) VALUES (?, ?)", (product_id, quantity))
                
                conn.commit()
                flash('Product added successfully!', 'success')
            except Exception as e:
                conn.rollback()
                print(e)
                flash('Failed to add product. Error: ' + str(e), 'error')
            finally:
                conn.close()
            
            return redirect('/crud')  # Перенаправляем пользователя обратно на страницу CRUD после добавления продукта
        else:
            flash('Failed to add product. Image is required.', 'error')
            return redirect('/add_product')
    else:
        return redirect('/add_product')

@app.route('/delete/<int:product_id>', methods=['POST', 'GET'])
def delete_product(product_id):
    if request.method == 'POST':
        # Создаем соединение с базой данных
        conn = create_connection()
        cursor = conn.cursor()

        try:
            # Получаем image_url продукта, который мы собираемся удалить
            cursor.execute("SELECT image_url FROM Products WHERE product_id=?", (product_id,))
            image_url = cursor.fetchone()[0]

            # Удаляем запись из таблицы Inventory
            cursor.execute("DELETE FROM Inventory WHERE product_id=?", (product_id,))

            # Удаляем запись из таблицы Products
            cursor.execute("DELETE FROM Products WHERE product_id=?", (product_id,))

            # Формируем путь к файлу изображения для удаления
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_url)

            # Проверяем, существует ли файл изображения
            if os.path.exists(image_path):
                # Удаляем файл изображения
                os.remove(image_path)

            conn.commit()
            flash('Product deleted successfully!', 'success')
        except Exception as e:
            conn.rollback()
            print(e)
            flash('Failed to delete product. Error: ' + str(e), 'error')
        finally:
            conn.close()

        return redirect('/crud')
    else:
        return redirect('/crud')

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    user_ip = request.remote_addr
    city, postal_code = get_location_from_ip(user_ip, '86c960f33f9c64') #Api token
    # Создаем соединение с базой данных
    conn = create_connection()
    cursor = conn.cursor()

    # Получаем данные о продукте из базы данных
    cursor.execute("SELECT * FROM Products WHERE product_id=?", (product_id,))
    product = cursor.fetchone()

    # Получаем категории из базы данных
    cursor.execute("SELECT * FROM Categories")
    categories = cursor.fetchall()
    filtered_categories = [category for category in categories if len(category.name.split()) <= 2][:17]

    # Закрываем соединение с базой данных
    conn.close()

    if request.method == 'POST':
        # Получаем данные из формы редактирования продукта
        name = request.form.get('name')
        category_id = int(request.form.get('category_id'))
        price = decimal.Decimal(request.form.get('price'))
        description = request.form.get('description')

        # Выполняем обновление данных о продукте в базе данных
        conn = create_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("UPDATE Products SET name=?, category_id=?, price=?, description=? WHERE product_id=?",
                           (name, category_id, price, description, product_id))
            conn.commit()
            flash('Product updated successfully!', 'success')
        except Exception as e:
            conn.rollback()
            print(e)
            flash('Failed to update product. Error: ' + str(e), 'error')
        finally:
            conn.close()

        return redirect('/crud')  # Перенаправляем пользователя обратно на страницу CRUD после обновления продукта

    return render_template('edit_product.html', product=product, categories=filtered_categories, year=datetime.now().year,city=city, postal_code=postal_code)

@app.route('/Cart')
def cart():
    user_ip = request.remote_addr

    # Получаем содержимое корзины из кэша
    cart = cache.get('cart') or {}
    products_in_cart = []
    print("Cart:", cart)
    total_items = 0
    total_price = 0

    # Создаем соединение с базой данных
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Categories")
    categories = cursor.fetchall()

    for product_id, quantity in cart.items():
        cursor.execute("SELECT * FROM Products WHERE product_id = ?", (product_id,))
        product = cursor.fetchone()  # Замените product = cursor.fetchone() на products_in_cart.append(...) 
        if product:
            total_items += quantity
            total_price += quantity * product.price
            products_in_cart.append({'product': product, 'quantity': quantity})

    # Закрываем соединение
    conn.close()

    filtered_categories = [category for category in categories if len(category.name.split()) <= 2][:17]

    city, postal_code = get_location_from_ip(user_ip, '86c960f33f9c64')  # Api token

    return render_template('Cart.html', year=datetime.now().year, categories=filtered_categories, city=city,
                           postal_code=postal_code, cart=cart, products=products_in_cart, total_items=total_items, total_price=total_price)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity')
    
    if not product_id or not quantity:
        return jsonify({'error': 'No product identifier or quantity specified'}), 400
    
    # Получаем текущее состояние корзины из кэша
    cart = cache.get('cart') or {}
    
    # Добавляем товар в корзину или увеличиваем количество, если товар уже есть в корзине
    cart[product_id] = cart.get(product_id, 0) + quantity
    
    # Сохраняем обновленное состояние корзины в кэше
    cache.set('cart', cart)
    
    return jsonify({'message': 'The item has been successfully added to the cart'}), 200

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():

    product_id = request.form.get('product_id')
    print(product_id, type(product_id))

    if not product_id:
        return jsonify({'error': 'No product identifier specified'}), 400

    # Получаем текущее состояние корзины из кэша
    cart = cache.get('cart') or {}

    # Удаляем товар из корзины, если он там есть
    if product_id in cart:
        del cart[product_id]

    # Сохраняем обновленное состояние корзины в кэше
    cache.set('cart', cart)

    return redirect('/Cart')

@app.route('/buy', methods=['GET'])
def buy():
    current_year = datetime.now().year
    cart = cache.get('cart') or {}
    products_in_cart = []
    print("Cart:", cart)
    total_items = 0
    total_price = 0
    
    # Retrieve user's IP address
    user_ip = request.remote_addr
    # Create a connection to the database
    conn = create_connection()
    cursor = conn.cursor()
    
    # Fetch categories from the database
    cursor.execute("SELECT * FROM Categories")
    categories = cursor.fetchall()
    
    cursor.execute("SELECT * FROM States")
    states = cursor.fetchall()

    for product_id, quantity in cart.items():
        cursor.execute("SELECT * FROM Products WHERE product_id = ?", (product_id,))
        product = cursor.fetchone()  # Замените product = cursor.fetchone() на products_in_cart.append(...) 
        if product:
            total_items += quantity
            total_price += quantity * product.price
            products_in_cart.append({'product': product, 'quantity': quantity})

    # Close the database connection
    conn.close()

    # Filter categories
    filtered_categories = [category for category in categories if len(category.name.split()) <= 2][:17]
    # Get user's city and postal code from IP
    city, postal_code = get_location_from_ip(user_ip, '86c960f33f9c64')  # Api token

    print("Data:", products_in_cart, total_items, total_price)
    
    if not products_in_cart:
        return redirect("/Cart")

    return render_template('Buy.html', year=current_year, current_year=current_year, categories=filtered_categories,
                           city=city, postal_code=postal_code, cart_products=products_in_cart, total_items=total_items,
                           total_price=total_price, states=states)

def generate_order_number(existing_order_numbers):
    # Генерация нового уникального OrderNumber
    while True:
        new_order_number = random.randint(100000, 99999999)  # Генерация случайного числа от 100000 до 99999999
        if new_order_number not in existing_order_numbers:
            return new_order_number
        
def calculate_total_cost(price, tax_rate):
    tax_amount = price * (float(tax_rate) / 100)
    total_cost = price + tax_amount
    return total_cost

@app.route('/proceed_checkout', methods=['POST'])
def proceed_checkout():
    
    email = request.form.get('emailAddress')
    card_number = request.form.get('cardNum')
    expiration_month = request.form.get('mm')
    expiration_year = request.form.get('yy')
    cvv = request.form.get('CVV')
    cardholder_name = request.form.get('cardName')
    address = request.form.get('inputAddress')
    address2 = request.form.get('inputAddress2')
    city = request.form.get('inputCity')
    state = request.form.get('inputState')
    zip_code = request.form.get('inputZip')
    total_price_str = request.form.get('total_price')
    total_price = float(request.form.get('total_price', 0))  # Получение total_price из формы
    state_tax_percentage = float(request.form.get('inputState', 0))  # Получение state.tax_percentage из формы
    
    product_ids = request.form.getlist('product_id[]')
    quantities = request.form.getlist('quantity[]')
    # Объединение ID продуктов и количества в пары
    product_quantity_pairs = list(zip(product_ids, quantities))

    print('Ready to sent the data.')
    
    conn = create_connection()
    cursor = conn.cursor()

        # Получение всех существующих OrderNumber из таблицы PurchaseLogs
    cursor.execute("SELECT OrderNumber FROM PurchaseLogs")
    existing_order_numbers = [row[0] for row in cursor.fetchall()]

        # Генерация нового уникального OrderNumber
    new_order_number = generate_order_number(existing_order_numbers)

    cursor.execute(f"SELECT tax_percentage FROM States Where id = {state}")
    tax = [row[0] for row in cursor.fetchall()]

        # Цикл для обновления количества товаров и вставки данных о покупке
    for product_id, quantity in product_quantity_pairs:
        # SQL-запрос для уменьшения количества товара
        update_query = f"UPDATE Inventory SET Quantity = Quantity - {quantity} WHERE Product_ID = {product_id}"
        cursor.execute(update_query)
        print(cursor.rowcount)  # Выводит количество измененных строк (должно быть больше 0, если запрос отработал успешно)
        print('State tax percent from site:',state_tax_percentage, 'State tax percent from db:', tax)

        tax_rate = tax[0]  # Получаем единственное значение налога из списка
        total_with_tax = calculate_total_cost(total_price, tax_rate)

        print(total_with_tax)

            # SQL-запрос для вставки данных о покупке в таблицу PurchaseLogs с новым OrderNumber
        insert_query = f"INSERT INTO PurchaseLogs (OrderNumber, Email, CardNumber, ExpMMYY, " \
                        f"CardholderName, Address1, Address2, City, StateID, ZipCode, " \
                        f"TotalPriceNoTax, TotalPriceTax, StatusID, ProductID, Quantity, PurchaseDate) " \
                        f"VALUES ({new_order_number}, '{email}', '{card_number}', " \
                        f"'{expiration_month}/{expiration_year}', '{cardholder_name}', " \
                        f"'{address}', '{address2}', '{city}', {state}, '{zip_code}', " \
                        f"{total_price}, {total_with_tax:2f}, {1}, {product_id}, {quantity}, GETDATE())"
        cursor.execute(insert_query)
        conn.commit()  # Подтверждение изменений после каждой итерации цикла

        # Закрытие соединения
    conn.close()

    return redirect('/receipt')

@app.route('/receipt', methods=['GET'])
def receipt():

    #Create all logic here too (Show receipt with all data)
    #I'll do it when finish the proceed_checkout

    return render_template('receipt.html')

@app.route('/buyProduct', methods=['POST'])
def buyProduct():
    current_year = datetime.now().year
    product_id = request.form.get('productId')
    print(product_id)
    cart = {product_id: 1}
    products_in_cart = []
    print("Cart:", cart)
    total_items = 0
    total_price = 0
    
    # Retrieve user's IP address
    user_ip = request.remote_addr
    # Create a connection to the database
    conn = create_connection()
    cursor = conn.cursor()
    
    # Fetch categories from the database
    cursor.execute("SELECT * FROM Categories")
    categories = cursor.fetchall()
    
    cursor.execute("SELECT * FROM States")
    states = cursor.fetchall()

    for product_id, quantity in cart.items():
        cursor.execute("SELECT * FROM Products WHERE product_id = ?", (product_id,))
        product = cursor.fetchone()  # Замените product = cursor.fetchone() на products_in_cart.append(...) 
        if product:
            total_items += quantity
            total_price += quantity * product.price
            products_in_cart.append({'product': product, 'quantity': quantity})

    # Close the database connection
    conn.close()

    # Filter categories
    filtered_categories = [category for category in categories if len(category.name.split()) <= 2][:17]
    # Get user's city and postal code from IP
    city, postal_code = get_location_from_ip(user_ip, '86c960f33f9c64')  # Api token

    print("Data:", products_in_cart, total_items, total_price)
    
    if not products_in_cart:
        return redirect("/Cart")

    return render_template('Buy.html', year=current_year, current_year=current_year, categories=filtered_categories,
                           city=city, postal_code=postal_code, cart_products=products_in_cart, total_items=total_items,
                           total_price=total_price, states=states)


if __name__ == "__main__":
    app.run(debug=True)
