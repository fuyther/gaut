from flask import Flask, request, jsonify
import sqlite3
import _thread
import datetime as dt


def protect(command):
    if "drop" in command.lower():
        raise ValueError
    if command.count(";") > 1:
        raise ValueError
    return command


class EventsDB:
    def __init__(self, db):
        self.db = db

    def select(self, items, table, options=""):
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        command = protect("SELECT " + ", ".join(items) + " FROM " + table + " " + options + ";")
        return cursor.execute(command).fetchall()

    def insert(self, values, table, number_values):
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO " + table + " VALUES (" + ", ".join(["?"] * number_values) + ");", values)
        conn.commit()

    def command(self, command):
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        response = cursor.execute(protect(command)).fetchall()
        conn.commit()
        return response


app = Flask(__name__)
events = EventsDB("gaut.db")


@app.route("/authorization", methods=["POST"])
def auth():
    jsn = request.get_json(force=True)[0]
    print(jsn)
    login = protect(jsn["tel"])
    typ = jsn["type"]
    if typ == "auth":
        try:
            user = events.select(["id", "login"], "users", options='WHERE login="' + login + '"')[0]
            print(user)
            return jsonify(user)
        except Exception as e:
            print(e.__repr__())
            return jsonify([])
    elif typ == "reg":
        events.insert([login, jsn["user_type"]], "users(login, type)", 2)
        response = {"message": "success"}
        print(response)
        return jsonify(response)
    print("error")
    return jsonify({"message": "Error 400: type isn't valid"})


@app.route("/list_main", methods=["POST"])
def list_main():
    jsn = request.get_json(force=True)[0]
    print(jsn)
    day = jsn["day"]
    typ = jsn["type"]
    time1 = dt.datetime.strptime(day + " 00:00:00", "%Y-%m-%d %H:%M:%S")
    time2 = dt.datetime.strptime(day + " 23:59:59", "%Y-%m-%d %H:%M:%S")
    lst_events = events.select(("id", "name", "time_start", "time_end"), "events",
                               options="WHERE time_start>" + str(time1.timestamp()) + " AND time_start<"
                                       + str(time2.timestamp()) + " AND type='" + str(typ) +
                                       "' ORDER BY time_start DESC LIMIT 30")
    response = lst_events
    print(response)
    return jsonify(response)


@app.route("/event/<id>", methods=["GET"])
def event(id):
    response = events.select("*", "events", "WHERE id=" + str(id))[0]
    print(response)
    return jsonify(response)


@app.route("/events", methods=["POST"])
def event_list():
    jsn = request.json
    lst_events = []
    for id in jsn:
        lst_events.append(events.select(("id", "name", "time_start", "time_end"), "events", "WHERE id=" + str(id))[0])
    response = lst_events
    print(response)
    return jsonify(response)


@app.route("/insert", methods=["POST"])
def insert():
    jsn = request.json
    events.insert(jsn, "events(name, text, time_start, time_end, type)", 5)
    response = {"message": "success"}
    print(response)
    return jsonify(response)


@app.route("/custom_select", methods=["POST"])
def custom_select():
    jsn = request.json
    response = events.select(list(jsn["items"]), str(jsn["options"]))
    print(response)
    return jsonify(response)


@app.route("/custom_command", methods=["POST"])
def custom_command():
    command = request.json["command"]
    response = events.command(command)
    print(response)
    return jsonify(response)


@app.route("/sms", methods=["POST"])
def sms():
    jsn = request.get_json(force=True)[0]
    print(jsn)
    tel = jsn["tel"]
    user = list(events.select(["*"], "users", options='WHERE login="' + tel + '"')[0])
    user.append(1)
    print(user)
    return jsonify(user)


def database_input():
    try:
        while True:
            print(events.command(input()))
    except:
        database_input()


if __name__ == "__main__":
    _thread.start_new_thread(database_input, ())
    app.run(host="0.0.0.0", port=8880)
