#Flask Application

from flask import Flask, render_template, url_for
import pyodbc

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

@app.route('/')
def index():

    # Создаем соединение с базой данных
    conn = create_connection()
    cursor = conn.cursor()

    # Пример выполнения запроса к базе данных
    cursor.execute("SELECT * FROM Categories")
    categories = cursor.fetchall()

    # Закрываем соединение
    conn.close()

    return render_template("index.html", categories=categories)

if __name__ == "__main__":
    app.run(debug=True)
    
