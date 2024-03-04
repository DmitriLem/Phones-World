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
