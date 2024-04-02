from jinja2 import Template

def GetEmailBody(order_number, log):
    template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Order Receipt</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f9f9f9;
            color: #333;
            margin: 0;
            padding: 20px;
        }
        .receipt-container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fff;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .receipt-header {
            text-align: center;
            margin-bottom: 20px;
        }
        .receipt-header h1 {
            font-size: 24px;
            color: #333;
            margin-bottom: 10px;
        }
        .thank-you-text {
            text-align: center;
            margin-bottom: 20px;
        }
        .thank-you-text p {
            margin-bottom: 5px;
        }
        .order-details h2,
        .shipping-details h2,
        .product-details h2 {
            font-size: 20px;
            margin-bottom: 10px;
            color: #555;
        }
        ul {
            list-style-type: none;
            padding: 0;
        }
        li {
            margin-bottom: 8px;
        }
        .product-item {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        .product-item img {
            width: 100px; /* Увеличиваем размер фото */
            height: 100px; /* Увеличиваем размер фото */
            margin-right: 15px;
            border: 1px solid #ddd; /* Добавляем тонкую рамку */
            border-radius: 4px;
        }
        .product-info {
            flex-grow: 1;
        }
        .product-info h3 {
            font-size: 18px;
            margin-bottom: 5px;
            color: #333;
        }
        .product-info p {
            margin-bottom: 5px;
            color: #777;
        }
        .continue-shopping {
            display: flex;
            justify-content: flex-end;
            margin-top: 20px;
        }
        .continue-shopping a {
            background-color: #007bff;
            color: #fff;
            padding: 10px 20px;
            border-radius: 5px;
            text-decoration: none;
            transition: background-color 0.3s ease;
        }
        .continue-shopping a:hover {
            background-color: #0056b3;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #777;
        }
    </style>
</head>
<body>
        <div class="receipt-container">
            <div class="receipt-header">
                <h1>Order Receipt</h1>
            </div>
            
            <div class="thank-you-text">
                <p>Thank you for your purchase!</p>
                <p><strong>Your Order Number:</strong> {{ order_number }}</p>
            </div>
            <hr>
            <div class="order-details">
                <h2>Order Details</h2>
                <ul>
                    <li><strong>Order Number:</strong> {{ order_number }}</li>
                    <li><strong>Total Price (Tax Included):</strong> ${{ log[0]['TotalPriceTax'] }}</li>
                    <li><strong>Order Status:</strong> {{ log[0]['OrderStatus'] }}</li>
                    <li><strong>Purchase Date:</strong> {{ log[0]['PurchaseDate'].strftime('%Y-%m-%d %I:%M %p') }}</li>
                </ul>
            </div>
    
            <div class="shipping-details">
                <h2>Shipping Address</h2>
                <ul>
                    <li><strong>Address:</strong> {{ log[0]['Address1'] }} {{ log[0]['Address2'] }}</li>
                    <li><strong>City:</strong> {{ log[0]['City'] }}</li>
                    <li><strong>State:</strong> {{ log[0]['StateName'] }} ({{ log[0]['StateAbbreviation'] }})</li>
                    <li><strong>Zip Code:</strong> {{ log[0]['ZipCode'] }}</li>
                </ul>
            </div>
    
            <div class="product-details">
                <h2>Product Details</h2>
                {% for item in log %}
                <div class="product-item">
                    {% if item['ProductImageURL'].startswith('http') %}
                        <img src="{{ item['ProductImageURL'] }}" alt="{{ item['ProductName'] }}">
                    {% else %}
                        <img src="/static/userUploadPhotos/{{ item['ProductImageURL'] }}" alt="{{ item['ProductName'] }}">
                    {% endif %}
                    <div class="product-info">
                        <h3>{{ item['ProductName'] }}</h3>
                        <p><strong>Quantity:</strong> {{ item.Quantity }}</p>
                        <p><strong>Price:</strong> ${{ item['ProductPrice'] }}</p>
                        <p><strong>Description:</strong> {{ item['ProductDescription'] | truncate(length=100) }}</p>
                    </div>
                </div>
                <hr>
                {% endfor %}
            </div>
    
            <div class="footer">
                <p>If you have any questions, please contact us at support@example.com.</p>
                <p>&copy; 2024 PhonesWorld. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    template = Template(template_str)
    email_body = template.render(order_number=order_number, log=log)

    return email_body
