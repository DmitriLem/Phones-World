document.addEventListener('DOMContentLoaded', function () {
    const changeButton = document.querySelector('.btn-primary');
    const saveButton = document.querySelector('.btn-success');
    const cancelButton = document.querySelector('.btn-danger');
    const statusSelect = document.querySelector('#status');
    const orderNumber = document.querySelector('#orderNumber').value;

    let currentStatus = ''; // Переменная для хранения текущего статуса

    // Функция для обработки нажатия на кнопку Change
    changeButton.addEventListener('click', function () {
        changeButton.hidden = true;
        saveButton.hidden = false;
        cancelButton.hidden = false;
        statusSelect.hidden = false;
    
        // Сохраняем текущее значение data-status в переменной currentStatus
        currentStatus = statusSelect.dataset.status;
    });
    
    // Функция для обработки нажатия на кнопку Cancel
    cancelButton.addEventListener('click', function () {
        changeButton.hidden = false;
        saveButton.hidden = true;
        cancelButton.hidden = true;
        statusSelect.hidden = true;
    
        // Восстанавливаем предыдущий статус в select
        const options = statusSelect.options;
        for (let i = 0; i < options.length; i++) {
            if (options[i].innerText.trim() === currentStatus) {
                options[i].selected = true;
                break;
            }
        }
    });

    // Функция для обработки нажатия на кнопку Save
    saveButton.addEventListener('click', function () {
        const selectedStatus = statusSelect.options[statusSelect.selectedIndex].text;

        if (currentStatus === selectedStatus) {
            alert('Save cannot be performed. Status is already the same.');
        } else {
            // Отправляем данные на сервер с помощью fetch
            fetch('/update_status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    StatusID: statusSelect.value,
                    OrderNumber: orderNumber
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to update status');
                }
                return response.json();
            })
            .then(data => {
                //alert(data.message);
                changeButton.hidden = false;
                saveButton.hidden = true;
                cancelButton.hidden = true;
                statusSelect.hidden = true;
                const options = statusSelect.options;
                for (let i = 0; i < options.length; i++) {
                    if (options[i].innerText.trim() === currentStatus) {
                        options[i].selected = true;
                        break;
                    }
                }
                location.reload();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error occurred while updating status');
            });
        }
    });
});