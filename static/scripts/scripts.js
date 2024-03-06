document.addEventListener('DOMContentLoaded', function() {
    // Находим все кнопки "Add to Cart" по классу
    var addToCartButtons = document.querySelectorAll('.btn-add-to-cart');

    // Проходим по всем кнопкам и добавляем обработчик события на каждую из них
    addToCartButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            // Отменяем действие по умолчанию (предотвращаем переход по ссылке)
            event.preventDefault();

            // Получаем ID продукта из атрибута data-product-id
            var productId = button.getAttribute('data-product-id');

            // Отправляем AJAX-запрос на сервер для добавления продукта в корзину
            fetch('/add_to_cart/' + productId)
                .then(function(response) {
                    // Проверяем успешность ответа
                    if (!response.ok) {
                        throw new Error('Failed to add product to cart');
                    }
                    // Выводим сообщение об успешном добавлении продукта в корзину
                    alert('Product added to cart successfully!');
                    // Перезагружаем страницу, чтобы обновить содержимое корзины
                    location.reload();
                })
                .catch(function(error) {
                    console.error('Error:', error);
                });
        });
    });
});


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