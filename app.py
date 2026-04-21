# app.py
import json
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timezone
import pytz

app = Flask(__name__)

# JSON file to store data
data_file = "data_store.json"


# Load data from JSON file
def load_data():
    try:
        with open(data_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


# Save data to JSON file
def save_data(data):
    with open(data_file, "w") as f:
        json.dump(data, f, indent=4)


@app.route("/")
def index():
    entries = load_data()
    user_timezone = request.args.get("timezone", "UTC")
    try:
        local_tz = pytz.timezone(user_timezone)
    except pytz.UnknownTimeZoneError:
        local_tz = timezone.utc

    # Convert UTC time to local time for display
    for entry in entries:
        utc_time = datetime.strptime(
            f"{entry['date']} {entry['time']}", "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=timezone.utc)
        local_time = utc_time.astimezone(local_tz)
        entry["display_date"] = local_time.strftime("%Y-%m-%d")
        entry["display_day"] = local_time.strftime("%a")  # Day abbreviation
    return render_template("index.html", entries=entries)


@app.route("/new-log", methods=["GET", "POST"])
def new_log():
    if request.method == "POST":
        username = request.form.get("username").lower()
        date = request.form.get("date")
        time = request.form.get("time")
        diary = request.form.get("diary")
        categories = request.form.getlist("category")
        user_timezone = request.form.get("timezone", "UTC")

        try:
            local_tz = pytz.timezone(user_timezone)
        except pytz.UnknownTimeZoneError:
            local_tz = timezone.utc

        # Combine date and time into a single UTC datetime
        local_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").replace(
            tzinfo=local_tz
        )
        utc_datetime = local_datetime.astimezone(timezone.utc)

        log_id = f"{username}{utc_datetime.strftime('%Y%m%d%H%M%S')}"
        date_created = utc_datetime.strftime("%Y-%m-%d %H:%M:%S")

        entry = {
            "log_id": log_id,
            "username": username,
            "date": utc_datetime.strftime("%Y-%m-%d"),
            "time": utc_datetime.strftime("%H:%M:%S"),
            "diary": diary,
            "categories": categories,
            "date_created": date_created,
            "date_modified": date_created,
        }

        data = load_data()
        data.append(entry)
        save_data(data)

        return redirect(url_for("index"))

    return render_template(
        "new-log.html",
        username="User",
        current_date=datetime.now().strftime("%Y-%m-%d"),
        current_time=datetime.now().strftime("%H:%M"),
    )


@app.route("/edit-record/<log_id>", methods=["GET", "POST"])
def edit_record(log_id):
    data = load_data()
    entry = next((item for item in data if item["log_id"] == log_id), None)
    user_timezone = request.args.get("timezone", "UTC")

    try:
        local_tz = pytz.timezone(user_timezone)
    except pytz.UnknownTimeZoneError:
        local_tz = timezone.utc

    if request.method == "POST":
        if entry:
            entry["date"] = request.form.get("date")
            entry["time"] = request.form.get("time")
            entry["diary"] = request.form.get("diary")
            entry["categories"] = request.form.getlist("category")
            entry["date_modified"] = datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            save_data(data)
        return redirect(url_for("index"))

    # Convert UTC to local time for editing
    utc_time = datetime.strptime(
        f"{entry['date']} {entry['time']}", "%Y-%m-%d %H:%M:%S"
    ).replace(tzinfo=timezone.utc)
    local_time = utc_time.astimezone(local_tz)
    entry["display_date"] = local_time.strftime("%Y-%m-%d")
    entry["display_time"] = local_time.strftime("%H:%M")

    return render_template("edit-record.html", entry=entry)


@app.route("/delete-entry/<log_id>", methods=["POST"])
def delete_entry(log_id):
    data = load_data()
    data = [entry for entry in data if entry["log_id"] != log_id]
    save_data(data)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
