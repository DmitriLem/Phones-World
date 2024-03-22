document.addEventListener('DOMContentLoaded', function() {
    const cardNumberInput = document.getElementById('cardNum');
    const cvvInput = document.getElementById('CVV');

    const cardNum1 = document.getElementById('cardNum1');
    const cardNum2 = document.getElementById('cardNum2');
    const cardNum3 = document.getElementById('cardNum3');
    const cardNum4 = document.getElementById('cardNum4');
    const btnChange = document.getElementById('divBtnChange');

    cardNumberInput.addEventListener('input', function() {
        const cardNumberValue = this.value.replace(/\s/g, ''); // Удаление пробелов из значения поля

        cardNumberInput.maxLength = 16;
        cvvInput.value = '';
        cvvInput.maxLength = 3;

        // Определение типа карты по первой цифре и отображение соответствующего изображения
        let cardType = '';
        if (/^4/.test(cardNumberValue)) {
            cardType = 'visa';
        } else if (/^5[1-5]/.test(cardNumberValue)) {
            cardType = 'mc';
        } else if (/^6(?:011|5[0-9]{2})/.test(cardNumberValue)) {
            cardType = 'disc';
        } else if (/^3[47]/.test(cardNumberValue)) {
            cardType = 'amerExp';
            cardNumberInput.maxLength = 15;
            cvvInput.maxLength = 4;
        }

        // Показать изображение для определенного типа карты и скрыть остальные
        const cardImages = ['visa', 'mc', 'disc', 'amerExp'];
        cardImages.forEach(image => {
            const imgElement = document.getElementById(image);
            if (image === cardType) {
                imgElement.style.display = 'block';
            } else {
                imgElement.style.display = 'none';
            }
        });

        // Разбить номер карты на четыре части и заполнить скрытые поля
        const chunks = cardNumberValue.match(/.{1,4}/g) || [];
        for (let i = 0; i < 4; i++) {
            const chunk = chunks[i] || '';
            document.getElementById(`cardNum${i + 1}`).value = chunk;
        }

        if (cardType === 'amerExp' && cardNumberInput.value.length === 15) {
            cardNumberInput.style.display = 'none'; // Скрыть поле ввода номера карты
            cardNum1.style.display = 'block';
            cardNum2.style.display = 'block';
            cardNum3.style.display = 'block';
            cardNum4.style.display = 'block';
            btnChange.style.display = 'block';
        } else if ((cardType === 'visa' || cardType === 'mc' || cardType === 'disc') && cardNumberInput.value.length === 16) {
            cardNumberInput.style.display = 'none'; // Скрыть поле ввода номера карты
            cardNum1.style.display = 'block';
            cardNum2.style.display = 'block';
            cardNum3.style.display = 'block';
            cardNum4.style.display = 'block';
            btnChange.style.display = 'block';
        } else {
            cardNumberInput.style.display = 'block'; // Показать поле ввода номера карты, если условие не выполняется
            cardNum1.style.display = 'none';
            cardNum2.style.display = 'none';
            cardNum3.style.display = 'none';
            cardNum4.style.display = 'none';
            btnChange.style.display = 'none';
        }
        

    });
});

function ChangeCardNum() {
    const cardNumberInput = document.getElementById('cardNum');
    const cvvInput = document.getElementById('CVV');

    const cardNum1 = document.getElementById('cardNum1');
    const cardNum2 = document.getElementById('cardNum2');
    const cardNum3 = document.getElementById('cardNum3');
    const cardNum4 = document.getElementById('cardNum4');
    const btnChange = document.getElementById('divBtnChange');
    const visaElement = document.getElementById('visa');
    const mcElement = document.getElementById('mc');
    const discElement = document.getElementById('disc');
    const amerExpElement = document.getElementById('amerExp');

            console.log('Start Cleaning');

            cardNumberInput.style.display = 'block'; // Показать поле ввода номера карты, если условие не выполняется
            cardNum1.style.display = 'none';
            cardNum2.style.display = 'none';
            cardNum3.style.display = 'none';
            cardNum4.style.display = 'none';
            btnChange.style.display = 'none';
            cardNumberInput.maxLength = 16;
            cvvInput.value = '';
            cvvInput.maxLength = 3;
            cardNumberInput.value = '';
            cardNum1.value = '';
            cardNum2.value = '';
            cardNum3.value = '';
            cardNum4.value = '';
            visaElement.style.display = 'none';
            mcElement.style.display = 'none';
            discElement.style.display = 'none';
            amerExpElement.style.display = 'none';
}

function AllowOnlyNumbers(e) {
    // Получаем код клавиши
    var key = e.keyCode || e.which;

    // Разрешаем ввод только цифр (коды клавиш от 48 до 57 соответствуют цифрам 0-9)
    if (key < 48 || key > 57) {
        e.preventDefault();
        return false;
    }
    return true;
}

function ValidData() {
    const emailAddressInput = document.getElementById('emailAddress');
    const cardNumberInput = document.getElementById('cardNum');
    const mmSelect = document.getElementById('mm');
    const yySelect = document.getElementById('yy');
    const cvvInput = document.getElementById('CVV');
    const cardNameInput = document.getElementById('cardName');
    const inputAddress1Input = document.getElementById('inputAddress');
    const inputCityInput = document.getElementById('inputCity');
    const inputStateSelect = document.getElementById('inputState');
    const inputZipInput = document.getElementById('inputZip');
    const txtErrorLabel = document.getElementById('txtError');

    // Проверка наличия данных и фокус на контроле при ошибке
    if (emailAddressInput.value.trim() === '') {
        txtErrorLabel.textContent = 'Error: Email is empty';
        emailAddressInput.focus();
        return false;
    }
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(emailAddressInput.value.trim())) {
        txtErrorLabel.textContent = 'Error: Invalid email format';
        emailAddressInput.focus();
        return false;
    }
    if (cardNumberInput.value.trim() === '') {
        txtErrorLabel.textContent = 'Error: Card Number is empty';
        cardNumberInput.focus();
        return false;
    }
    if (
        cardNumberInput.value.trim().charAt(0) !== '4' && // не Visa
        cardNumberInput.value.trim().charAt(0) !== '5' && // не MasterCard
        cardNumberInput.value.trim().charAt(0) !== '6' && // не Discovery
        (cardNumberInput.value.trim().charAt(0) !== '3' || (!cardNumberInput.value.trim().startsWith('34') && !cardNumberInput.value.trim().startsWith('37'))) // не American Express
    ) 
    {
        txtErrorLabel.textContent = 'Error: Invalid card number';
        cardNumberInput.focus();
        return false;
    }
    if (mmSelect.value.trim() === '' || yySelect.value.trim() === '') {
        txtErrorLabel.textContent = 'Error: Please select month and year';
        mmSelect.focus();
        return false;
    }
    
    // Проверка корректности mm/yy
    const selectedMonth = parseInt(mmSelect.value.trim(), 10);
    const selectedYear = parseInt(yySelect.value.trim(), 10);
    const currentYear = new Date().getFullYear(); // Получаем текущий год (четырехзначный формат)
    const currentMonth = new Date().getMonth() + 1; // Получаем текущий месяц (1-12)
    
    // Проверяем, что выбранный месяц находится в диапазоне от 01 до 12 и год больше или равен текущему году
    if (isNaN(selectedMonth) || selectedMonth < 1 || selectedMonth > 12 ||
        isNaN(selectedYear) || selectedYear < currentYear) {
        txtErrorLabel.textContent = 'Error: Please select a valid month and year';
        mmSelect.focus();
        return false;
    }

    // Если выбранный год равен текущему году, проверяем, что месяц истечения карты больше или равен текущему месяцу
    if (selectedYear === currentYear && selectedMonth < currentMonth) {
        txtErrorLabel.textContent = 'Error: Please select a valid month and year';
        mmSelect.focus();
        return false;
    }

    if (cvvInput.value.trim() === '') {
        txtErrorLabel.textContent = 'Error: CVV is empty';
        cvvInput.focus();
        return false;
    }
    if ((cvvInput.value.trim().length !== 4 && cardNumberInput.value.trim().charAt(0) === '3') || (cvvInput.value.trim().length !== 3 && cardNumberInput.value.trim().charAt(0) !== '3')) {
        txtErrorLabel.textContent = (cardNumberInput.value.trim().charAt(0) === '3') ? 'Error: CVV is not 4 length' : 'Error: CVV is not 3 length';
        cvvInput.focus();
        return false;
    }    
    if (cardNameInput.value.trim() === '') {
        txtErrorLabel.textContent = 'Error: Name is empty';
        cardNameInput.focus();
        return false;
    }
    if (inputAddress1Input.value.trim() === '') {
        txtErrorLabel.textContent = 'Error: Address is empty';
        inputAddress1Input.focus();
        return false;
    }
    if (inputCityInput.value.trim() === '') {
        txtErrorLabel.textContent = 'Error: City is empty';
        inputCityInput.focus();
        return false;
    }
    if (inputStateSelect.value.trim() === '') {
        txtErrorLabel.textContent = 'Error: Please select state';
        inputStateSelect.focus();
        return false;
    }
    if (inputZipInput.value.trim() === '') {
        txtErrorLabel.textContent = 'Error: Zip is empty';
        inputZipInput.focus();
        return false;
    }
    if (inputZipInput.value.trim().length !== 5) {
        txtErrorLabel.textContent = 'Error: Zip is not 5 length';
        inputZipInput.focus();
        return false;
    }

    // Проверка номера карты и CVV в зависимости от типа карты
    const cardType = cardNumberInput.value.trim().charAt(0);
    if ((cardType === '4' && cardNumberInput.value.trim().length !== 16) || // Visa
        (cardType === '5' && cardNumberInput.value.trim().length !== 16) || // MasterCard
        (cardType === '6' && cardNumberInput.value.trim().length !== 16) || // Discovery
        ((cardType === '3' && (cardNumberInput.value.trim().startsWith('34') || cardNumberInput.value.trim().startsWith('37'))) && cardNumberInput.value.trim().length !== 15)) { // AmericanExpress
        txtErrorLabel.textContent = 'Error: Card Number is not valid';
        cardNumberInput.focus();
        return false;
    }

    // Проверка длины CVV в зависимости от типа карты
    const cvvLength = (cardType === '3' && (cardNumberInput.value.trim().startsWith('34') || cardNumberInput.value.trim().startsWith('37'))) ? 4 : 3;
    if (cvvInput.value.trim().length !== cvvLength) {
        txtErrorLabel.textContent = `Error: CVV is not ${cvvLength} length`;
        cvvInput.focus();
        return false;
    }

    return true;
}


function validateForm() {
    // Выполните все проверки данных здесь
    if (ValidData()) {
        // Здесь можно добавить код для отправки данных формы на сервер
        alert('Form submitted successfully!');
        // Очистка формы после успешной отправки
        document.getElementById('txtError').innerText = ''; // Очищаем сообщение об ошибке
        document.getElementById('paymentForm').reset(); // Очищаем все поля формы
        ChangeCardNum(); // Сброс отображения номера карты и изображений типа карты
    }
}
