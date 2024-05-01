import random
from datetime import datetime

def generate_order_number(existing_order_numbers):
    while True:
        new_order_number = random.randint(100000, 99999999)
        if new_order_number not in existing_order_numbers:
            return new_order_number
        
def calculate_total_cost(price, tax_rate):
    tax_amount = price * (float(tax_rate) / 100)
    total_cost = price + tax_amount
    return total_cost

def validate_checkout_data(data):
    required_fields = ['emailAddress', 'cardNum', 'mm', 'yy', 'cardName', 'inputAddress', 'inputCity', 'inputState', 'inputZip', 'product_id[]', 'quantity[]']
    for field in required_fields:
        if field not in data:
            return False
    return True

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

def validate_data(fName, lName, username, password, access_lvl_id):
    if not all([fName, lName, username, password]) or \
            len(fName) < 2 or len(lName) < 2 or \
            len(username) < 3 or len(password) < 6 or \
            not access_lvl_id:
        return False
    return True

def validate_data_for_edit(fName, lName, username, password, access_lvl_id):
    if not fName:
        print("Ошибка: Имя не указано.")
        return False
    if not lName:
        print("Ошибка: Фамилия не указана.")
        return False
    if not username:
        print("Ошибка: Имя пользователя не указано.")
        return False
    if not access_lvl_id:
        print("Ошибка: Уровень доступа не выбран.")
        return False
    
    if len(fName) < 2:
        print("Ошибка: Имя слишком короткое (минимум 2 символа).")
        return False
    if len(lName) < 2:
        print("Ошибка: Фамилия слишком короткая (минимум 2 символа).")
        return False
    if len(username) < 3:
        print("Ошибка: Имя пользователя должно содержать не менее 3 символов.")
        return False
    if password and len(password) < 6:
        print("Ошибка: Пароль должен содержать не менее 6 символов.")
        return False
    
    return True

def get_time_of_day():
    current_time = datetime.now().time()
    if current_time.hour < 12:
        return "morning"
    elif 12 <= current_time.hour < 17:
        return "afternoon"
    elif 17 <= current_time.hour < 21:
        return "evening"
    else:
        return "night"