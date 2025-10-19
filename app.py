import os
import json
from datetime import datetime
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

@app.route("/api/replay", methods=["GET"])
def get_replay_data():
    server = config.get("server")
    api_key = config.get("apikey")
    user_id = request.args.get("user_id") or "23fe68794ee1415db28073061646c169" # Default User ID

    if not server or not api_key:
        return jsonify({"error": "Jellyfin server URL or API key not configured."}), 400

    try:
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
            
            # Calculate progressive duration
            duration_s = round(max_duration_s - (max_duration_s - min_duration_s) * ((rank - 1) / (limit - 1)), 2)
            
            cover_url = ""
            image_size = 600
            if i.get('AlbumId'):
                cover_url = f"{server.rstrip('/')}/Items/{i['AlbumId']}/Images/Primary?maxWidth={image_size}&maxHeight={image_size}&api_key={api_key}"
            elif i.get('ImageTags') and i['ImageTags'].get('Primary'):
                cover_url = f"{server.rstrip('/')}/Items/{i['Id']}/Images/Primary?maxWidth={image_size}&maxHeight={image_size}&api_key={api_key}"

            endTimeTicks = int((max_duration_s + 5) * 10000000)
            preview_url = f"{server.rstrip('/')}/Audio/{i['Id']}/stream?static=true&api_key={api_key}&startTimeTicks=0&endTimeTicks={endTimeTicks}"
            
            jellyfin_link = f"{server.rstrip('/')}/web/index.html#!/item?id={i['Id']}"

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
                "jellyfinLink": jellyfin_link
            })
        
        tracks.reverse() # We still reverse here to get rank 1 first in the frontend

    except requests.exceptions.RequestException as e:
        print(f"Error fetching replay from Jellyfin: {e}")
        return jsonify({"error": f"Failed to connect to Jellyfin server: {e}"}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

    return jsonify(tracks)

# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)