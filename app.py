from flask import Flask, render_template, url_for, request
import pyodbc
import requests
import random

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

@app.route('/')
def index():
    user_ip = request.remote_addr

    city, postal_code = get_location_from_ip(user_ip, '86c960f33f9c64') #Api token

    # Создаем соединение с базой данных
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Categories")
    categories = cursor.fetchall()

    # Получаем данные из таблицы Products
    cursor.execute("SELECT * FROM Products")
    products = cursor.fetchall()

    # Получаем данные из таблицы Inventory
    cursor.execute("SELECT * FROM Inventory")
    inventory = cursor.fetchall()

    # Закрываем соединение
    conn.close()

    filtered_categories = [category for category in categories if len(category.name.split()) <= 2][:17]

    # Выбираем случайные 8 продуктов
    random_products = random.sample(products, min(8, len(products)))

    return render_template("index.html", categories=filtered_categories, city=city, postal_code=postal_code, random_products=random_products, inventory=inventory)

if __name__ == "__main__":
    app.run(debug=True)
