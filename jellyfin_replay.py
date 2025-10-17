import os
import json
from datetime import datetime
import requests
from flask import Flask, render_template_string, request, redirect, url_for

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
# HTML template
# ---------------------------
template = """
<!DOCTYPE html>
<html>
<head>
  <title>Jellyfin Replay</title>
  <style>
    :root {
      --bg-color-1: #111;
      --bg-color-2: #111;
      --bg-color-3: #111;
      --bg-color-4: #111;
    }

    body { 
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      color: #eee; 
      text-align:center; 
      margin:0; 
      padding:0; 
      background-color: #000;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
      cursor: pointer;
    }
    
    @keyframes morph-background {
        0%   { background-position: 0% 50%, 100% 50%, 0% 100%, 100% 0%; }
        50%  { background-position: 50% 0%, 50% 100%, 100% 50%, 0% 50%; }
        100% { background-position: 0% 50%, 100% 50%, 0% 100%, 100% 0%; }
    }

    body::before {
      content: ''; position: absolute; inset: 0; z-index: -1;
      background: radial-gradient(circle at 10% 20%, var(--bg-color-1), transparent 35%),
                  radial-gradient(circle at 80% 15%, var(--bg-color-2), transparent 35%),
                  radial-gradient(circle at 20% 80%, var(--bg-color-3), transparent 35%),
                  radial-gradient(circle at 90% 85%, var(--bg-color-4), transparent 35%);
      background-size: 200% 200%; filter: blur(140px);
      transition: background 2s ease-in-out; animation: morph-background 30s linear infinite;
    }

    .top-bar {
      position: absolute; top: 10px; left: 50%; transform: translateX(-50%); padding: 10px; z-index: 100;
      background: rgba(0, 0, 0, 0.2); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; cursor: default;
    }
    
    input, .top-bar button { 
      padding:8px; margin:5px; border-radius:8px; border:1px solid rgba(255,255,255,0.2);
      outline:none; background: rgba(0,0,0,0.3); color: #fff;
    }
    .top-bar button { cursor: pointer; background: rgba(255,255,255,0.2); }
    .top-bar button:hover { background: rgba(255,255,255,0.3); }

    .carousel-container { display: flex; align-items: center; justify-content: center; z-index: 10; transition: opacity 0.5s ease-out; }
    .nav-button {
      background-color: rgba(0, 0, 0, 0.2); backdrop-filter: blur(10px); color: white;
      border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 50%;
      cursor: pointer; font-size: 32px; margin: 0 50px;
      width: 70px; height: 70px; line-height: 65px;
      transition: background-color 0.3s, transform 0.3s; z-index: 50;
    }
    .nav-button:hover { background-color: rgba(0, 0, 0, 0.4); transform: scale(1.1); }
    .track-card {
      width:600px; height:600px; border-radius:30px; overflow:hidden;
      box-shadow: 0 25px 60px rgba(0,0,0,0.6); transition: transform 0.4s, box-shadow 0.4s;
      background-size:cover; background-position:center; position:relative;
      display: flex; align-items: flex-end; background-color: #333;
    }
    .track-info {
      background: rgba(0,0,0,0.5); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
      color:#fff; font-size:16px; position:absolute; bottom:0;
      width:100%; text-align:center; padding: 20px 0; z-index: 10;
    }
    .track-name-container { display: flex; justify-content: center; align-items: center; gap: 10px; }
    .track-name { font-weight: bold; font-size: 1.5em; }
    .track-artist, .track-album { font-size: 1.1em; color: #ddd; }
    .jellyfin-link svg { width: 1.2em; height: 1.2em; fill: rgba(255, 255, 255, 0.6); transition: fill 0.3s, transform 0.3s; }
    .jellyfin-link:hover svg { fill: rgba(255, 255, 255, 1); transform: scale(1.1); }

    .rank-container {
        position: fixed; bottom: 30px; right: 40px; z-index: 5; text-align: right;
        transition: opacity 0.5s ease-out;
    }
    .rank-display {
        font-size: 120px; font-weight: 900; color: rgba(255, 255, 255, 0.6);
        text-shadow: 0 0 20px rgba(0,0,0,0.7); line-height: 1; font-family: 'Poppins', 'Helvetica Neue', sans-serif;
    }
    .rank-playcount {
        font-size: 24px; font-weight: 600; color: rgba(255, 255, 255, 0.5);
        text-shadow: 0 0 10px rgba(0,0,0,0.5); margin-top: -10px;
    }

    #timeline-container {
        position: fixed; bottom: 0; left: 0; width: 100%; height: 5px;
        background: rgba(255, 255, 255, 0.2); z-index: 100; transition: opacity 0.5s ease-out;
    }
    #timeline-bar { height: 100%; width: 0%; background: #fff; transition: width 0.1s linear; }

    /* List View Styles */
    #list-view-container {
        display: none; opacity: 0; z-index: 20; width: 90%; max-width: 800px; height: 80vh;
        background: rgba(0, 0, 0, 0.3); backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px;
        padding: 20px; flex-direction: column; transition: opacity 0.5s ease-in;
    }
    #list-view-container h2 { margin-top: 0; }
    #replay-button { font-size: 1em; padding: 10px 20px; cursor: pointer; background: rgba(255,255,255,0.2); border: none; border-radius: 10px; color: #fff; margin-bottom: 20px; }
    #track-list { overflow-y: auto; text-align: left; }
    .list-item { display: flex; align-items: center; padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.1); }
    .list-item-cover { width: 60px; height: 60px; border-radius: 8px; margin-right: 15px; }
    .list-item-info { flex-grow: 1; }
    .list-item-title { font-weight: bold; }
    .list-item-artist { font-size: 0.9em; color: #ccc; }
    .list-item-rank { font-size: 1.5em; font-weight: bold; margin-right: 15px; }
    .list-item-playcount { font-size: 0.9em; color: #ccc; text-align: right; }

  </style>
</head>
<body>
  <canvas id="color-thief" style="display:none;"></canvas>

  <div class="top-bar">
    <form action="/config" method="post" style="display:inline;">
      <input type="text" name="server" placeholder="Server URL" value="{{ server }}" required>
      <input type="text" name="apikey" placeholder="API Key" value="{{ apikey }}" required>
      <button type="submit">Save</button>
    </form>
    <form action="/replay" method="get" style="display:inline;">
      <input type="hidden" name="user_id" value="23fe68794ee1415db28073061646c169">
      <button type="submit">Get Replay</button>
    </form>
  </div>

  {% if tracks %}
  <main id="carousel-container" class="carousel-container">
    <button id="prevBtn" class="nav-button">&lt;</button>
    <div id="main-track-card" class="track-card">
      <div class="track-info">
        <div class="track-name-container">
            <div id="track-name" class="track-name"></div>
            <a id="jellyfin-link" href="#" target="_blank" class="jellyfin-link" title="Listen on Jellyfin">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M10 6v2H5v11h11v-5h2v6a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h6zm11-3v8h-2V6.413l-7.793 7.794-1.414-1.414L17.585 5H13V3h8z"/></svg>
            </a>
        </div>
        <div id="track-artist" class="track-artist"></div>
        <div id="track-album" class="track-album"></div>
      </div>
      <audio id="preview-audio" preload="auto"></audio>
    </div>
    <button id="nextBtn" class="nav-button">&gt;</button>
  </main>
  
  <div id="rank-container" class="rank-container">
      <div id="rank-display" class="rank-display"></div>
      <div id="rank-playcount" class="rank-playcount"></div>
  </div>

  <div id="list-view-container">
      <h2>Top 20 Replay</h2>
      <button id="replay-button">Play Again</button>
      <div id="track-list"></div>
  </div>
  
  <div id="timeline-container">
      <div id="timeline-bar"></div>
  </div>

  <script>
    const FADE_DURATION = 800;

    const tracks = {{ tracks|tojson }};
    let currentTrackIndex = 0;
    let isPaused = false;
    let isChanging = false;
    let animationFrameId = null;
    let startTime = 0;
    let pausedTime = 0;
    let currentSongDuration = 20000;

    const carouselContainer = document.getElementById('carousel-container');
    const trackNameEl = document.getElementById('track-name');
    const trackArtistEl = document.getElementById('track-artist');
    const trackAlbumEl = document.getElementById('track-album');
    const rankContainer = document.getElementById('rank-container');
    const rankDisplayEl = document.getElementById('rank-display');
    const rankPlayCountEl = document.getElementById('rank-playcount');
    const jellyfinLinkEl = document.getElementById('jellyfin-link');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const colorCanvas = document.getElementById('color-thief');
    const colorCtx = colorCanvas.getContext('2d', { willReadFrequently: true });
    const timelineContainer = document.getElementById('timeline-container');
    const timelineBar = document.getElementById('timeline-bar');
    const root = document.documentElement;
    const audio = document.getElementById('preview-audio');
    const listViewContainer = document.getElementById('list-view-container');
    const replayButton = document.getElementById('replay-button');

    function getPalette(img, colorCount = 4) {
        colorCanvas.width = img.width; colorCanvas.height = img.height;
        colorCtx.drawImage(img, 0, 0, img.width, img.height);
        const pixels = colorCtx.getImageData(0, 0, img.width, img.height).data;
        const colorMap = {};
        for (let i = 0; i < pixels.length; i += 4) {
            let key = (pixels[i] >> 5 << 10) | (pixels[i+1] >> 5 << 5) | (pixels[i+2] >> 5);
            if(colorMap[key]) colorMap[key].count++; else colorMap[key] = {r:pixels[i],g:pixels[i+1],b:pixels[i+2],count:1};
        }
        const sorted = Object.values(colorMap).sort((a, b) => b.count - a.count);
        const filtered = sorted.filter(c => (c.r+c.g+c.b)>150 && (c.r+c.g+c.b)<700);
        return (filtered.length >= colorCount ? filtered : sorted).slice(0, colorCount).map(c => `rgb(${c.r},${c.g},${c.b})`);
    }

    function updateBackground(palette) {
        root.style.setProperty('--bg-color-1', palette[0] || '#111');
        root.style.setProperty('--bg-color-2', palette[1] || '#222');
        root.style.setProperty('--bg-color-3', palette[2] || '#333');
        root.style.setProperty('--bg-color-4', palette[3] || '#444');
    }

    function fadeAudio(targetVolume, duration, onComplete) {
        const startVolume = audio.volume;
        const step = (targetVolume - startVolume) / (duration / 20);
        const fade = setInterval(() => {
            let currentVolume = audio.volume + step;
            if ((step > 0 && currentVolume >= targetVolume) || (step < 0 && currentVolume <= targetVolume)) {
                audio.volume = targetVolume;
                clearInterval(fade);
                if (targetVolume === 0) audio.pause();
                if (onComplete) onComplete();
            } else { audio.volume = currentVolume; }
        }, 20);
    }
    
    function showTrack(index) {
      isChanging = false;
      const track = tracks[index];
      currentSongDuration = track.duration;
      document.getElementById('main-track-card').style.backgroundImage = `url('${track.Cover}')`;
      trackNameEl.textContent = track.Name;
      trackArtistEl.textContent = track.Artist;
      trackAlbumEl.textContent = `Album: ${track.Album || 'Unknown'}`;
      rankDisplayEl.textContent = `#${track.rank}`;
      rankPlayCountEl.textContent = `${track.PlayCount} Plays`;
      jellyfinLinkEl.href = track.jellyfinLink;
      
      const img = new Image();
      img.crossOrigin = "Anonymous";
      img.src = track.Cover;
      img.onload = () => updateBackground(getPalette(img, 4));
      img.onerror = () => updateBackground(['#111', '#222', '#333', '#444']);
      
      audio.src = track.PreviewUrl;
      audio.load();
      audio.play().then(() => { fadeAudio(1, FADE_DURATION); }).catch(e => {});

      startTime = Date.now();
      if(animationFrameId) cancelAnimationFrame(animationFrameId);
      animateTimeline();
    }
    
    function animateTimeline() {
        if(isPaused) {
            animationFrameId = requestAnimationFrame(animateTimeline);
            return;
        }
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / currentSongDuration, 1);
        timelineBar.style.width = `${progress * 100}%`;
        
        if (progress >= 1) {
            if (currentTrackIndex === tracks.length - 1) { // Is it the #1 song?
                fadeAudio(0, FADE_DURATION, showListView);
            } else {
                changeTrack('next');
            }
        } else {
            animationFrameId = requestAnimationFrame(animateTimeline);
        }
    }

    function changeTrack(direction) {
        if (isChanging || (direction === 'next' && currentTrackIndex === tracks.length -1) || (direction === 'prev' && currentTrackIndex === 0)) return;
        isChanging = true;
        cancelAnimationFrame(animationFrameId);
        fadeAudio(0, FADE_DURATION, () => {
            currentTrackIndex = (direction === 'next')
                ? (currentTrackIndex + 1) % tracks.length
                : (currentTrackIndex - 1 + tracks.length) % tracks.length;
            showTrack(currentTrackIndex);
        });
    }

    function showListView() {
        carouselContainer.style.opacity = '0';
        rankContainer.style.opacity = '0';
        timelineContainer.style.opacity = '0';

        const trackList = document.getElementById('track-list');
        trackList.innerHTML = ''; // Clear previous list
        
        const sortedTracks = [...tracks].reverse(); // Show #1 first

        sortedTracks.forEach(track => {
            const item = document.createElement('div');
            item.className = 'list-item';
            item.innerHTML = `
                <div class="list-item-rank">${track.rank}</div>
                <img src="${track.Cover}" class="list-item-cover">
                <div class="list-item-info">
                    <div class="list-item-title">${track.Name}</div>
                    <div class="list-item-artist">${track.Artist} - ${track.Album || 'Unknown'}</div>
                </div>
                <div class="list-item-playcount">${track.PlayCount} Plays</div>
            `;
            trackList.appendChild(item);
        });

        listViewContainer.style.display = 'flex';
        setTimeout(() => listViewContainer.style.opacity = '1', 50);
    }
    
    function resetView() {
        listViewContainer.style.opacity = '0';
        setTimeout(() => {
            listViewContainer.style.display = 'none';
            carouselContainer.style.opacity = '1';
            rankContainer.style.opacity = '1';
            timelineContainer.style.opacity = '1';
            currentTrackIndex = 0;
            showTrack(0);
        }, 500);
    }

    // --- Event Listeners ---
    nextBtn.addEventListener('click', () => changeTrack('next'));
    prevBtn.addEventListener('click', () => changeTrack('prev'));
    document.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowRight') changeTrack('next');
      else if (e.key === 'ArrowLeft') changeTrack('prev');
    });

    document.body.addEventListener('click', (e) => {
        if (e.target.closest('.top-bar, .nav-button, .jellyfin-link, .list-view-container')) return;
        
        isPaused = !isPaused;

        if (isPaused) {
            pausedTime = Date.now();
            if(!audio.paused) audio.pause();
        } else {
            startTime += (Date.now() - pausedTime);
            if(audio.paused) audio.play().catch(e => {});
        }
    });
    
    replayButton.addEventListener('click', resetView);

    // Initial load
    if (tracks.length > 0) {
      showTrack(0);
    }
  </script>
  {% endif %}

</body>
</html>
"""

# ---------------------------
# Routes
# ---------------------------
@app.route("/")
def index():
    return render_template_string(template, server=config["server"], apikey=config["apikey"], tracks=None)

@app.route("/config", methods=["POST"])
def update_config():
    server = request.form["server"].strip()
    apikey = request.form["apikey"].strip()
    global config
    config = save_config(server, apikey)
    return redirect(url_for("index"))

@app.route("/replay")
def replay():
    server = config.get("server")
    api_key = config.get("apikey")
    user_id = request.args.get("user_id") or "23fe68794ee1415db28073061646c169"

    if not server or not api_key:
        return redirect(url_for("index"))

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
        
        tracks.reverse()

    except Exception as e:
        print(f"Error fetching replay: {e}")
        tracks = []

    return render_template_string(template, server=server, apikey=api_key, tracks=tracks)

# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)