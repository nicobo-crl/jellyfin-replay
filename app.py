import os
import json
import requests
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

CONFIG_FILE = "config.json"

# ---------------------------
# Load / Save config
# ---------------------------
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"server": "", "apikey": ""}

def save_config(server, apikey):
    cfg = {"server": server, "apikey": apikey}
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f)
    return cfg

config = load_config()

# ---------------------------
# Routes
# ---------------------------
@app.route("/")
def index():
    return render_template("index.html", server=config["server"], apikey=config["apikey"])

@app.route("/config", methods=["POST"])
def update_config():
    server = request.form["server"].strip()
    apikey = request.form["apikey"].strip()
    global config
    config = save_config(server, apikey)
    return redirect(url_for("index"))

@app.route("/api/users", methods=["GET"])
def get_users():
    server = config.get("server")
    api_key = config.get("apikey")

    if not server or not api_key:
        return jsonify({"error": "Jellyfin server URL or API key not configured."}), 400

    try:
        users_url = f"{server.rstrip('/')}/Users"
        headers = {"X-Emby-Token": api_key}
        r = requests.get(users_url, headers=headers, timeout=10)
        r.raise_for_status()
        
        all_users = r.json()
        
        # Filter out hidden system users and format the data for the frontend
        display_users = [
            {
                "Id": u["Id"],
                "Name": u["Name"],
                "PrimaryImageTag": u.get("PrimaryImageTag")
            }
            for u in all_users if not u.get("IsHidden")
        ]

        # Construct full avatar URLs
        for user in display_users:
            if user["PrimaryImageTag"]:
                user["AvatarUrl"] = f"{server.rstrip('/')}/Users/{user['Id']}/Images/Primary?tag={user['PrimaryImageTag']}&quality=90"
            else:
                user["AvatarUrl"] = None # Or a link to a default avatar image

        return jsonify(display_users)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching Jellyfin users: {e}")
        return jsonify({"error": f"Failed to connect to Jellyfin server to fetch users: {e}"}), 500
    except Exception as e:
        print(f"An unexpected error occurred while getting users: {e}")
        return jsonify({"error": f"An unexpected error occurred while getting users: {e}"}), 500

@app.route("/api/replay", methods=["GET"])
def get_replay_data():
    server = config.get("server")
    api_key = config.get("apikey")
    user_id = request.args.get("user_id") # User ID is now a required query parameter

    if not server or not api_key:
        return jsonify({"error": "Jellyfin server URL or API key not configured."}), 400
    if not user_id:
        return jsonify({"error": "A User ID must be provided to fetch replay data."}), 400

    try:
        # Get Server ID first
        system_info_url = f"{server.rstrip('/')}/System/Info"
        r_info = requests.get(system_info_url, headers={"X-Emby-Token": api_key}, timeout=10)
        r_info.raise_for_status()
        server_id = r_info.json().get("Id")
        if not server_id:
            return jsonify({"error": "Could not retrieve Jellyfin Server ID."}), 500

        limit = 20
        min_duration_s = 10
        max_duration_s = 30
        
        url = f"{server.rstrip('/')}/Users/{user_id}/Items"
        headers = {"X-Emby-Token": api_key}
        params = {
            "IncludeItemTypes": "Audio",
            "Recursive": "true",
            "SortBy": "PlayCount",
            "SortOrder": "Descending",
            "Fields": "ImageTags,AlbumId,MediaSources,Album,AlbumArtist,Artists",
            "Limit": limit
        }
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        items = r.json().get("Items", [])

        tracks = []
        for index, i in enumerate(items):
            rank = index + 1
            
            duration_s = round(max_duration_s - (max_duration_s - min_duration_s) * ((rank - 1) / (limit - 1)), 2)
            
            cover_url = ""
            image_size = 600
            if i.get('AlbumId'):
                cover_url = f"{server.rstrip('/')}/Items/{i['AlbumId']}/Images/Primary?maxWidth={image_size}&maxHeight={image_size}&api_key={api_key}"
            elif i.get('ImageTags') and i['ImageTags'].get('Primary'):
                cover_url = f"{server.rstrip('/')}/Items/{i['Id']}/Images/Primary?maxWidth={image_size}&maxHeight={image_size}&api_key={api_key}"

            endTimeTicks = int((max_duration_s + 5) * 10000000)
            preview_url = f"{server.rstrip('/')}/Audio/{i['Id']}/stream?static=true&api_key={api_key}&startTimeTicks=0&endTimeTicks={endTimeTicks}"
            
            jellyfin_link = f"{server.rstrip('/')}/web/index.html#!/details?id={i['Id']}&serverId={server_id}"

            tracks.append({
                "Id": i.get("Id"),
                "Name": i.get("Name"),
                "PlayCount": i.get("UserData", {}).get("PlayCount", 0),
                "Album": i.get("Album"),
                "Artist": i.get("AlbumArtist") or ", ".join(i.get("Artists", [])),
                "Cover": cover_url,
                "PreviewUrl": preview_url,
                "rank": rank,
                "duration": duration_s * 1000,
                "jellyfinLink": jellyfin_link,
                "serverId": server_id
            })
        
        tracks.reverse()

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to connect to Jellyfin server: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

    return jsonify(tracks)

# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)