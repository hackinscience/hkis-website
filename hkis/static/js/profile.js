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

    $('#team_selector').select2(
        {
            tags: true,
            minimumInputLength: 2,
            placeholder: "Create or join a team by typing its name.",
            width: '30em',
            ajax: {
                url: "/api/teams/",
                processResults: function (data) {
                    // Transforms the top-level key of the response object from 'items' to 'results'
                    results = [];
                    for (i in data.results) {
                        results.push({"id": data.results[i].name, "text": data.results[i].name})
                    }
                    return {
                        results: results
                    };
                }
            },
        });
});
