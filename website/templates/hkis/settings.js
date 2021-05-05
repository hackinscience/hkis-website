{% load i18n %}
var HKIS_SETTINGS = {
    {% get_current_language as LANGUAGE_CODE %}
    LANGUAGE_CODE: "{{ LANGUAGE_CODE }}",
    PROFILE_URL: "{% if user.is_anonymous %}{% url "auth_login" %}{% else %}{% url "profile" user.id %}{% endif %}",
    LEADERBOARD_URL: "{% url "leaderboard" %}",
    CURRENT_RANK: {{ current_rank|default:999999 }},
    ID: {{object.id|default:0}},
    AUTH_LOGIN_URL: "{% url "auth_login" %}",
    IS_IMPERSONATING: {% if is_impersonating %}true{% else %}false{% endif %},
};
