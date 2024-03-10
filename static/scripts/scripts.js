function confirmDelete(productName, product_id) {
    if (confirm(`Are you sure you want to delete "${productName}" from the database?`)) {
        var userInput = prompt("Enter the product name to confirm deletion:");
        if (userInput === productName) {
            // Показываем загрузочный оверлей
            document.getElementById('loading-overlay').style.display = 'block';

            // Отправляем POST-запрос на сервер для удаления продукта
            fetch(`/delete/${product_id}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({}) // Пустое тело запроса
            })
            .then(response => {
                if (response.ok) {
                    // Успешное удаление, перезагружаем страницу
                    window.location.reload();
                } else {
                    // Возникла ошибка при удалении, показываем сообщение об ошибке
                    alert('Failed to delete product. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to delete product. Please try again.');
            });
        } else {
            alert("The entered product name does not match, deletion canceled.");
        }
    }
}

// Функция для отображения оверлея
function showOverlay() {
    document.getElementById('loading-overlay').style.display = 'block';
}

// Функция для скрытия оверлея
function hideOverlay() {
    document.getElementById('loading-overlay').style.display = 'none';
}

// Функция для выполнения действия с кнопки
function performAction(button) {
    // Показываем оверлей перед выполнением действия
    showOverlay();

    // Здесь можно добавить код для выполнения соответствующего действия,
    // например, создание продукта, изменение продукта, добавление в корзину и т. д.

    // После завершения операции скрываем оверлей
    hideOverlay();
}

// Функция для добавления товара в корзину
function addToCart(productId, quantity) {
    const data = {
        'product_id': productId,
        'quantity': quantity
    };
    console.log('Start fetching')
    fetch('/add_to_cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => {
        if (!response.ok) {
            console.log('Error1')
            throw new Error('Произошла ошибка при добавлении товара в корзину');
        }
        return response.json();
    })
    .then(data => {
        console.log('Good1')
        alert(data.message); // Показать сообщение об успешном добавлении
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('Произошла ошибка. Пожалуйста, попробуйте еще раз.');
    });
}