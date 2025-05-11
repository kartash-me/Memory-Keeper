const avatarForm = document.getElementById("avatar-form")
const avatarInput = document.getElementById("avatar-input");
const avatarButton = document.getElementById("avatar-button");

avatarButton.addEventListener("click", function(event) {
    event.preventDefault();
    avatarInput.click();
});

avatarInput.addEventListener("change", function () {
    avatarForm.submit();
});
