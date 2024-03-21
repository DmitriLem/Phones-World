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

        if (cardType != '' && cardNumberInput.value.length >= 15) {
            cardNumberValue.style.display = 'none';
            cardNum1.style.display = 'block';
            cardNum2.style.display = 'block';
            cardNum3.style.display = 'block';
            cardNum4.style.display = 'block';
            btnChange.style.display = 'block';
        }

    });
});
