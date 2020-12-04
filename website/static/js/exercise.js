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
    var result = document.getElementById("answers-result");
    if (!result)
        return;
    var answerbox = document.getElementById("td-".concat(answer.id));
    if (!answerbox) {
        var answer_table = document.getElementById("answer-table");
        append_to_answer_table('<tr><td id="td-'.concat(answer.id).concat('">…</td> </tr>'));
        answerbox = document.getElementById("td-".concat(answer.id));
    }
    if (answer.is_corrected) {
        var answer_table = document.getElementById("answer-table");
        var div = hkis.createElement("div", {innerHTML: answer.correction_message_html});
        if (answer.is_valid) {
            console.log("Answer is valid: old_rank=", HKIS_SETTINGS.CURRENT_RANK, "new_rank=", answer.user_rank)
            document.getElementById("btn_next").className = "btn btn-primary"
            document.getElementById("submit_answer").className = "btn btn-secondary"
            answer_table.rows[0].className = "table-success";
            if (answer.user && answer.user_rank < HKIS_SETTINGS.CURRENT_RANK ) {
                div.appendChild(hkis.createElement("div", {
                    className: "alert alert-success",
                    innerHTML: interpolate(gettext('Your new <a href="%(url)s">rank</a> is: %(new_rank)s'),
                                           {url: HKIS_SETTINGS.PROFILE_URL, new_rank: answer.user_rank},
                                           true)}));
            }
            if (!answer.user) {
                div.appendChild(hkis.createElement("div", {
                    className: "alert alert-warning",
                    innerHTML: interpolate(gettext('<a href="%s">Login</a> to backup your code and progression.'), [HKIS_SETTINGS.AUTH_LOGIN_URL])
                }));
            }
            document.getElementById("solution_link").classList.remove("disabled");
        }
        else {
            answer_table.rows[0].className = "table-danger";
            var button_unhelpfull = hkis.createElement("button", {
                title: gettext("Flag this answer as particularly unhelpfull,\nIt'll be reviewed by a human."),
                className: "btn, btn-outline-danger btn-sm",
                onclick: function() {return report_as_unhelpfull(answer.id);},
                innerHTML: gettext("Report")
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
        answerbox.swapChild(div)
        unlock_button("submit_answer")
    } else {
        answerbox.innerHTML = gettext("Waiting for correction...")
    }
}

function fill_snippet(id, executed_at, output) {
    var result = document.getElementById("answers-result");
    if (!result)
        return;
    var elem = document.getElementById("td-snippet-".concat(id));
    if (!elem) {
        var answer_table = document.getElementById("answer-table");
        append_to_answer_table('<tr class="table-info"><td id="td-snippet-'.concat(id).concat('">…</td> </tr>'));
        elem = document.getElementById("td-snippet-".concat(id));
    }
    if (executed_at) {
        var pre = document.createElement("pre");
        var div = document.createElement("div");
        div.appendChild(pre);
        var content = document.createTextNode(output);
        pre.appendChild(content);
        elem.swapChild(div);
        unlock_button("submit_answer");
    } else {
        elem.innerHTML = gettext("Waiting for test run");
    }
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
        if (data.type == "snippet.update")
            fill_snippet(data.id, data.executed_at, data.output)
        if (data.type == "answer.update")
            fill_answer(data);
    };
    window.ws.onerror = function(event) {
        console.error("WebSocket error observed:", event);
    };
    window.ws.onopen = function() {
        unlock_button("submit_answer");
        unlock_button("submit_snippet");
        connected = true;
        fill_message(gettext("Connected to correction server."), "success");
        window.ws.send(JSON.stringify({type: "settings", value: HKIS_SETTINGS}));
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

        fill_message(gettext("Cannot connect to correction server, will retry in 5s…") + "<br/>" +
                     interpolate(gettext("(See the <a href='%s'#FAQ'>FAQ</a> if it persists.)"), [HKIS_SETTINGS.HELP_URL]), "warning");
        setTimeout(function(){websocket_connect(ws_location)}, 5000);
        lock_button("submit_answer", 0);
        lock_button("submit_snippet", 0);
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

function ws_submit_snippet(form) {
    var message = {"type": "snippet", "source_code": form["source_code"].value};
    lock_button("submit_snippet", 1);
    console.log("WebSocket send snippet", message);
    window.ws.send(JSON.stringify(message));

}

function ctrl_enter_handler(event) {
    if (!event.ctrlKey) return;
    if (event.code !== "Enter") return;
    console.log("Sending via Ctrl-enter");
    ws_submit_answer(document.getElementById("answer_form"));
}

var ws_protocol = window.location.protocol == "http:" ? "ws:" : "wss:";

if (!HKIS_SETTINGS.IS_IMPERSONATING) {
    window.addEventListener("DOMContentLoaded", function (event) {
        websocket_connect(ws_protocol + "//" + window.location.host + "/ws/exercises/" + HKIS_SETTINGS.ID + "/");
        document.addEventListener("keydown", ctrl_enter_handler);
    });
}