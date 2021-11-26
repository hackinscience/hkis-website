const settings = document.getElementsByTagName('body')[0].dataset;

if (typeof Element.prototype.swapChild === 'undefined') {
    Object.defineProperty(Element.prototype, 'swapChild', {
      configurable: true,
      enumerable: false,
      value: function(newChild) {
          while (this.firstChild) this.removeChild(this.lastChild);
          this.appendChild(newChild);
      }
  });
}

var hkis = {
    createElement: function(tagName, attrs, dataset) {
        el = document.createElement(tagName)
        for (const property in attrs)
            el[property] = attrs[property]
        if (typeof dataset != "undefined")
            for (const property in dataset)
                el.dataset[property] = dataset[property]
        return el
    }
}

function append_to_answer_table(html) {
    if (document.querySelectorAll("#answer-table tr").length)
        document.querySelectorAll("#answer-table tr")[0].insertAdjacentHTML("beforebegin", html);
    else
        document.querySelectorAll("#answer-table")[0].insertAdjacentHTML("afterbegin", html);
}

function report_as_unhelpfull(answer_id) {
    if (confirm(gettext("This will send this answer to a human for manual review, so it can be enhanced, are you sure?")))
        window.ws.send(JSON.stringify({type: "is_unhelpfull", answer_id: answer_id}));
    return false;
}

function fill_answer(answer) {
    var wording_div = document.getElementById("wording");
    var answer_div = document.getElementById("answer-message");
    var answer_box = document.getElementById("answer-box");

    var tab = new bootstrap.Tab(document.querySelector("#tab-correction"));
    tab.show();

    if (!answer.is_corrected) {
        answer_box.className = "hkis-callout hkis-callout-info";
        answer_box.innerHTML = gettext("Waiting for correction...")
        return;
    }
    var div = hkis.createElement("div", {innerHTML: answer.correction_message_html});
    if (answer.is_valid) {
        answer_box.className = "hkis-callout hkis-callout-success";
        console.log("Answer is valid: old_rank=", settings.currentRank, "new_rank=", answer.user_rank)
        try {
            document.getElementById("btn_next").className = "btn btn-primary"
        } catch {}
        document.getElementById("submit_answer").className = "btn btn-secondary"
        if (answer.user && answer.user_rank < parseInt(settings.currentRank) ) {
            div.appendChild(hkis.createElement("div", {
                className: "alert alert-success",
                innerHTML: interpolate(gettext('Your new <a href="%(url)s">rank</a> is: %(new_rank)s'),
                                       {url: settings.leaderboardUrl, new_rank: answer.user_rank},
                                       true)}));
        }
        if (!answer.user) {
            div.appendChild(hkis.createElement("div", {
                className: "alert alert-warning",
                innerHTML: interpolate(gettext('<a href="%s">Login</a> to backup your code and progression.'), [settings.authLoginUrl])
            }));
        }
        document.getElementById("solution_link").classList.remove("disabled");
    }
    else {
        answer_box.className = "hkis-callout hkis-callout-failure";
        var button_unhelpfull = hkis.createElement("button", {
            title: gettext("Flag this answer as particularly unhelpfull,\nIt'll be reviewed by a human."),
            className: "btn, btn-outline-danger btn-sm",
            onclick: function() {return report_as_unhelpfull(answer.id);},
            innerHTML: gettext("Report as unhelpfull")
        }, {
            toggle: "tooltip"
        });

        if (answer.is_unhelpfull) {
            button_unhelpfull.disabled = true;
            button_unhelpfull.innerHTML = gettext("Reported")
            button_unhelpfull.title = gettext("Thanks for the feedback!")
        }
        div.appendChild(button_unhelpfull);
    }
    answer_box.swapChild(div)
    unlock_button("submit_answer")
}

function fill_message(message, type) {
    /* type in {"success", "danger", "warning", "info" } */
    console.log("[" + type + "]" + message);
    var answer_table = document.getElementById("answer-table");
    if (!answer_table)
        return;
    var first_row = answer_table.getElementsByTagName("tr")[0];
    var first_cell = null;
    if (first_row)
        first_cell = first_row.getElementsByTagName("td")[0];
    var html = '<div class="alert alert-' + type + '">' + message + "</td> </tr>";
    if (first_cell && !first_cell.id)
        first_cell.innerHTML = html
    else
        append_to_answer_table("<tr><td>" + html + "</td></tr>");
}

function websocket_connect(ws_location) {
    var connected = false;
    fill_message(gettext("Connecting to correction server…"), "info");
    window.ws = new WebSocket(ws_location);
    window.ws.onmessage = function(e) {
        var data = JSON.parse(e.data);
        console.log("WebSocket recv:", data);
        if (data.type == "answer.update")
            fill_answer(data);
    };
    window.ws.onerror = function(event) {
        console.error("WebSocket error observed:", event);
    };
    window.ws.onopen = function() {
        unlock_button("submit_answer");
        connected = true;
        fill_message(gettext("Connected to correction server."), "success");
        window.ws.send(JSON.stringify({type: "settings", value: {LANGUAGE_CODE: settings.languageCode}}));
        document.querySelectorAll("td.answer-cell").forEach(function(answer) {
            if (answer.dataset.isCorrected == "True") return ;
            console.log("Need to correct answer number", answer.dataset.answerId);
            window.ws.send(JSON.stringify({"type": "recorrect", "id": Number(answer.dataset.answerId)}));
        });
    };
    window.ws.onclose = function(event) {
        console.log("onclose", event);
        if (connected)
            fill_message(gettext("Connection to correction server lost, will retry in 5s…"), "warning");
        else

        fill_message(gettext("Cannot connect to correction server, will retry in 5s…"), "warning");
        setTimeout(function(){websocket_connect(ws_location)}, 5000);
        lock_button("submit_answer", 0);
    };
}

function ws_submit_answer(form) {
    var message = {"type": "answer", "source_code": form["source_code"].value};
    lock_button("submit_answer", 1);
    console.log("WebSocket send answer", message);
    window.ws.send(JSON.stringify(message));

}

function unlock_button(button_id) {
    document.getElementById(button_id).removeAttribute("disabled");
}

function lock_button(button_id, unlock_after_seconds) {
    document.getElementById(button_id).setAttribute("disabled", true);
    if (unlock_after_seconds)
        setTimeout(function(){unlock_button(button_id);}, unlock_after_seconds * 1000);
}

function close_answer_box(event) {
    var instructions_tab = document.querySelector('#tab-instructions');
    var tab = new bootstrap.Tab(instructions_tab);
    tab.show();
}

function shortcuts_handler(event) {
    if (event.ctrlKey && event.code == "Enter") {
        console.log("Sending via Ctrl-enter");
        ws_submit_answer(document.getElementById("answer_form"));
        return ;
    }
    if (event.code == "Escape") {
        close_answer_box();
    }
}

var ws_protocol = window.location.protocol == "http:" ? "ws:" : "wss:";

if (settings.isImpersonating == "false") {
    window.addEventListener("DOMContentLoaded", function (event) {
        websocket_connect(ws_protocol + "//" + window.location.host + "/ws/exercises/" + settings.exerciseId + "/");
        document.addEventListener("keydown", shortcuts_handler);
    });
}

function shared_answer(answer_id, is_shared, csrf_token) {
    var data = {
        "is_shared": is_shared,
    };
    var xhr = new XMLHttpRequest();
    xhr.open('PATCH', "/api/answers/".concat(answer_id, "/"), false);
    xhr.setRequestHeader("Content-type", "application/json");
    xhr.setRequestHeader("cache-control", "no-cache");
    xhr.setRequestHeader("X-CSRFToken", csrf_token);
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            document.getElementById("btn-".concat(answer_id, "-share")).style.display = is_shared ? "none" : "";
            document.getElementById("btn-".concat(answer_id, "-unshare")).style.display = is_shared ? "" : "none";
        }
    };
    xhr.send(JSON.stringify(data));
}

function delete_answer(answer_id, csrf_token) {
    if (!confirm(gettext("Are you sure you want to delete this answer?")))
        return;
    var xhr = new XMLHttpRequest();
    xhr.open('DELETE', "/api/answers/".concat(answer_id, "/"), false);
    xhr.setRequestHeader("Content-type", "application/json");
    xhr.setRequestHeader("cache-control", "no-cache");
    xhr.setRequestHeader("X-CSRFToken", csrf_token);
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 204) {
            document.getElementById("btn-".concat(answer_id, "-delete")).style.display = "none";
        }
    }
    xhr.send();
}

window.addEventListener("DOMContentLoaded", function (event) {
    if (document.getElementById("submit_answer")) {
        document.getElementById("submit_answer").addEventListener("click", function(e) {e.preventDefault(); ws_submit_answer(document.getElementById("answer_form")); return false;});
    }
    document.querySelectorAll("button[data-share]").forEach(function (button) {
        button.addEventListener("click", function(e) {
            shared_answer(button.dataset.share, true, settings.csrfToken);
        });
    });
    document.querySelectorAll("button[data-unshare]").forEach(function (button) {
        button.addEventListener("click", function(e) {
            shared_answer(button.dataset.unshare, false, settings.csrfToken);
        });
    });
    document.querySelectorAll("button[data-delete]").forEach(function (button) {
        button.addEventListener("click", function(e) {
            delete_answer(button.dataset.delete, settings.csrfToken);
        });
    });
})
