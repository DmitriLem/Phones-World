console.log('Address Valid is loaded...')

function isAddressValid() {
    console.log('Starting...')
        if(!Valid())
        {
            console.log('Error')
            event.preventDefault();
        }
}

function Valid(){
    var address1 = document.getElementById("Address1").value.trim();
    var address2 = document.getElementById("Address2").value.trim();
    var city = document.getElementById("City").value.trim();
    var zipCode = document.getElementById("Zip").value.trim();
    var StateID = document.getElementById("ddlState").value;
    var txtError = document.getElementById("spnError");

    if (address1.length < 2) {
        txtError.innerText = "Address 1 must be at least 2 characters long.";
        return false;
    }
    if (city.length < 4) {
        txtError.innerText = "City must be at least 4 characters long.";
        return false;
    }
    if (zipCode.length !== 5) {
        txtError.innerText = "Zip code must be 5 digits long.";
        return false;
    }
    txtError.innerText = "";
    console.log('Goog Job')
    return true;
}