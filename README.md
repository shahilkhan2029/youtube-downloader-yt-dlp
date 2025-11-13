# 🎬 YouTube Downloader Web App  
*A simple yet powerful Flask-based web app to download YouTube videos and playlists using [yt-dlp](https://github.com/yt-dlp/yt-dlp).*

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.x-black)
![yt-dlp](https://img.shields.io/badge/yt--dlp-Latest-green)
![License](https://img.shields.io/badge/License-MIT-orange)

---

## 🧠 Overview
This project provides a **browser-based interface** for `yt-dlp`, allowing users to:
- Download single YouTube videos or full playlists  
- Choose between different qualities or extract audio only  
- Auto-handle H.264 re-encoding and audio merging  
- Monitor real-time download progress  
- (Optionally) use **browser cookies** to bypass login or age-restriction prompts

The app can run entirely **locally** — no need for deployment or hosting.

---

## 🚀 Features
✅ Download **single videos** or **entire playlists**  
✅ Supports **MP4, MP3, M4A** and more  
✅ View **live progress** for each task  
✅ **Multi-task queue** system using threading  
✅ Auto-detects **browser cookies** for authentication  
✅ Upload custom `cookies.txt` file (for YouTube sign-in bypass)  
✅ Simple, clean, responsive web UI  

---

## 🧩 Project Structure
```
YT_Downloader/
├── app.py                # Flask backend
│── index.html        # Frontend UI
├── downloads/            # Downloaded videos/audio files
├── install.bat         # to install all required modules.
├── run.bat    # Windows launch script
└── README.md             # Project documentation
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/YT_Downloader.git
cd YT_Downloader
```

### 2️⃣ Create a Virtual Environment (Recommended)
```bash
python -m venv venv
venv\Scripts\activate      # On Windows
# or
source venv/bin/activate   # On Linux/Mac
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

If you don’t have `requirements.txt`, install manually:
```bash
pip install flask yt-dlp browser_cookie3
```

### 4️⃣ Run the App
```bash
python app.py
```

or simply double-click **`run.bat`** (Windows only).

The app will start on:
```
http://127.0.0.1:5000
```

---

## 💡 Usage

1. Open the web app in your browser  
2. Paste any YouTube video or playlist URL  
3. Select format:
   - **Best Quality**
   - **Audio Only (MP3/M4A)**
   - **Custom Resolution (e.g. 720p)**
4. (Optional) Upload `cookies.txt` if the video requires sign-in  
5. Click **Download** and watch progress in real time  
6. When done, files are available in the **downloads/** folder  

---

## 🧱 Cookie Authentication (Fix “Sign in to confirm” Error)

Some videos require login or CAPTCHA verification.  
You can authenticate in two ways:

### Option 1 — Auto Cookie Extraction
If you’re logged in to YouTube on Chrome/Edge/Firefox **and** running the app on your local machine:
1. Close all Chrome tabs (to unlock the cookie database).  
2. Run `app.py` from the same user account.  
3. The app will automatically try to extract your logged-in session cookies via `browser_cookie3`.

### Option 2 — Manual Cookie Upload
1. Install the **Get cookies.txt** browser extension  
2. While signed in to YouTube, open the video page  
3. Export cookies to a file named `cookies.txt`  
4. Upload it in the app before downloading  

✅ Works perfectly to bypass the  
`Sign in to confirm you’re not a bot` error.

---

## 🧰 Technologies Used
| Tool | Purpose |
|------|----------|
| **Flask** | Backend web framework |
| **yt-dlp** | Core video/audio downloader |
| **HTML / JS / CSS (Bootstrap)** | Frontend interface |
| **browser_cookie3** | Local browser cookie extraction |
| **Threading Queue** | Parallel task management |

---



## ⚡ Troubleshooting

### ❌ “Sign in to confirm you’re not a bot”
- Use **cookies.txt** from your browser
- Or close Chrome before running the app (to unlock cookies)
- Ensure the app runs under the same user session as your browser

### ❌ `Could not copy Chrome cookie database`
- Exit Chrome completely  
- Or use **manual export cookies.txt** method

---

## 📜 License
This project is licensed under the **MIT License** — feel free to modify and distribute.

---

## 👨‍💻 Author
**Shahil Khan**  
📍 Nagaur, Rajasthan  
🎥 [Instagram](https://www.instagram.com/shahilkhan20__/) | 💻 [GitHub](https://github.com/shahilkhan2029)

> If you like this project, ⭐ star the repo and share it!
