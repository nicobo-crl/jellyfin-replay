
# 🎵 Jellyfin Replay - A Visual Music Countdown

**Jellyfin Replay** is a dynamic and highly visual web application that creates a personalized "Spotify Wrapped" style experience for your Jellyfin music library. Built with Python and the Flask web framework, it connects to your Jellyfin server to fetch your top 20 most-played songs and presents them in an immersive, full-screen countdown.

The application starts with your #20 track and builds up to your #1 song, creating a grand finale. After the countdown, it displays a summary screen with your complete Top 20 list and your most-listened-to artists.

---

## ✨ Features

- **Immersive Visual Player:** A sleek, full-screen interface that makes your album art the star of the show.
- **Dynamic, Artwork-Based Backgrounds:** The background is a beautifully animated, morphing gradient created by extracting a palette of dominant colors from each song's cover art.
- **Cinematic Transitions:** The background artfully crossfades between color palettes as the songs change.
- **Auto-Playing Previews:** Each track auto-plays a short preview with smooth fade-in and fade-out effects.
- **Progressive Countdown:** The preview duration for each song gradually increases as the rank gets higher, making the #1 song feel like a true finale.
- **Interactive Controls:**
  - Click anywhere on the background to toggle pause/resume.
  - Use stylish navigation buttons or keyboard arrow keys to skip tracks.
  - A direct link on each track opens the full song in your Jellyfin web player.
- **Final Summary Screen:** After the #1 song finishes, the app transitions to a summary view displaying your full Top 20 list and your top 4 most-listened-to artists.
- **Easy Configuration:** Simple web UI to enter and save your Jellyfin server URL and API Key.

---

## 🛠️ Getting Started

Follow these instructions to get your own Jellyfin Replay instance running locally.

### Prerequisites

- **Python 3:** Make sure you have Python 3 installed. You can check with `python3 --version`.
- **Jellyfin Server:** A running Jellyfin server with a music library that has been listened to.

### Installation & Setup

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/nicobo-crl/jellyfin-replay.git
    cd jellyfin-replay
    ```

2.  **Install Dependencies:**
    It's recommended to use a virtual environment.
    ```bash
    # Create and activate a virtual environment (optional but recommended)
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

    # Install the required Python packages
    pip install Flask requests
    ```

3.  **Run the Application:**
    ```bash
    python3 app.py
    ```
    The application will start, and you should see output similar to this:
    ```
     * Running on http://127.0.0.1:5000
    ```

4.  **Configure in Your Browser:**
    - Open your web browser and navigate to `http://127.0.0.1:5000`.
    - You will be prompted to enter your Jellyfin server URL and an API Key.
        - **Server URL:** Use your server's local network IP address (e.g., `http://192.168.1.100:8096`), not `localhost`, so the browser can load the cover art.
        - **API Key:** Generate an API Key in your Jellyfin Dashboard under `API Keys`.
    - Click **Save**.

5.  **Get Your Replay!**
    - Once the configuration is saved, click the **Get Replay** button to start your personalized music countdown.

## 🔧 Technical Details

- **Backend:** [Python 3](https://www.python.org/) with [Flask](https://flask.palletsprojects.com/) for the web server and routing.
- **API Communication:** The `requests` library is used to communicate with the Jellyfin API to fetch top tracks and artists.
- **Frontend:** A single, dynamic HTML template powered by standard HTML, CSS, and JavaScript. No complex frontend frameworks are needed.
- **Visuals:**
    - **Color Extraction:** A JavaScript function running on a `<canvas>` element extracts a 4-color palette from each album cover image.
    - **Animated Background:** The extracted colors are applied to CSS variables, which power a multi-layered, morphing gradient animation. A crossfade effect is used for smooth transitions between song palettes.
- **Configuration:** Server details are saved locally in a `config.json` file in the project's root directory.

---

## 🤝 Contributing

Contributions are welcome! If you have ideas for new features or improvements, feel free to fork the repository, make your changes, and submit a pull request.

## 📄 License

This project is open-source and available under the Apache 2.0 Licence
