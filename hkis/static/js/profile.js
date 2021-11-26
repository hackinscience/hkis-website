window.addEventListener("DOMContentLoaded", function (event) {
    function set_lang(lang) {
        document.cookie = "django_language=" + lang + ";samesite=strict;max-age=31536000;path=/";
        window.location.reload(true);
    }

    document.querySelectorAll("button[data-lang]").forEach(function (button) {
        button.addEventListener("click", function(e) {
            set_lang(button.dataset.lang);
        });
    });
});
