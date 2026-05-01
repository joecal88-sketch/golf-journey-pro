# ⛳ Golf Journey Pro v5.2 — Premium Edition

A premium, mobile-ready golf improvement system built around Joel C.'s pursuit of breaking 80, hitting a 300-yard driver, and reaching a 20 handicap.

Designed to feel like an app you'd pay for. Augusta-inspired theme, voice-first interactions, real video drills, GPS caddy, and Gemini-powered AI coach.

---

## 🚀 Quick Start (local)

```bash
pip install -r requirements.txt
streamlit run Home.py
```

App opens at `http://localhost:8501`.

The terminal also prints a **Network URL** (e.g. `http://192.168.x.x:8501`) — open that on your iPhone or iPad while connected to the same WiFi to test on mobile.

### 📲 Install to iPhone home screen
1. Open the Network URL in **Safari** on your iPhone (or open your Streamlit Cloud URL)
2. Tap **Share** → **Add to Home Screen**
3. App icon appears on your home screen — runs full-screen, no browser chrome

### ☁️ Deploy permanently (Streamlit Cloud)
1. Push the project folder to a public GitHub repo
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Repo: `<user>/<repo>`, Branch: `main`, Main file: `Home.py`
4. Deploy — get a permanent URL like `your-name.streamlit.app`

---

## ✨ What's in v5.2

### 🎨 Augusta-inspired premium UI
Deep masters greens, parchment cream text, Fraunces serif display headlines, glassmorphism cards, gold-flag accents. The most polished version yet.

### 🧠 Specific intelligent insights
Real, useful, voiced like a coach:
- *"You hit 7i 165 yards. PGA Tour avg with 7-iron: 176. You're at 94% of Tour."*
- *"80% of your 7i misses go right. That's likely an out-to-in path. Try the Cure The Slice drill."*
- *"You've played El Cariso 5 times. Best: 79. Weakness: Par 3s (avg +1.3 vs par)."*

### 🎯 Real digital driving range
The Practice Hub renders a true top-down range view with:
- Yardage markers every 50 yards
- A target green at PGA Tour avg carry for the selected club
- Your shot trails from tee to landing
- Mean shot dot (the cream/green sphere)
- Dispersion Index 0-100 vs Tour pros

### 📍 Smart Caddy (auto-everything)
- Auto-fetched live weather (Open-Meteo, free) per course coords
- Plays-like math: yardage adjusted for wind, temp, elevation
- Club rec from YOUR actual carries (not generic charts)
- 8 LA courses pre-loaded with lat/lon and pars
- One-tap GPS check + voice scorecard

### 📚 Real drill library
12+ curated drills with embedded YouTube videos from established teaching pros:
- Driver: slice fix (Rick Shiels), speed training (Stack)
- Irons: compression (Me & My Golf), distance control
- Wedges: 30/50/70/90 ladder (Phil), up-and-down drill
- Putting: gate drill, lag putting
- Full Swing: 3-to-1 tempo, balance finish
- Warm-up: 5-minute pre-round

Each drill has clickable **▶ Open** button, full step-by-step, and an **AI personalized breakdown** powered by Gemini.

### 🏆 40+ achievements
Across scoring, practice, streaks, distance, course mastery, short game, coach engagement, and special milestones.

### 📸 AI swing photo analysis
Upload a swing photo → Gemini Vision analyzes setup, posture, plane, balance, prescribes the top drill, and predicts what to look for in 2 weeks.

### 🎤 Voice-first
- Coach: mic input + browser TTS replies (toggleable)
- Live Round: voice scorecard
- Works on iPhone Safari and Android Chrome

### 📤 One-tap CSV import
Drop your Rapsodo session CSV, columns auto-detect, preview, import. No more manual mapping.

---

## 🗂 Pages

1. **🏠 Command Center** — Hero stats, smart insights, Tour comparison gauges, clickable stroke-saver drills
2. **🏌️ Practice Hub** — Digital range, club picker, dispersion index, CSV import
3. **📍 Live Round** — Smart Caddy with auto-GPS + auto-weather, voice scorecard, 8 LA courses
4. **🎯 Plan & Drills** — Library with videos, AI Drill Generator, Achievements view
5. **🎓 AI Coach** — Voice chat + photo swing analysis (Gemini)
6. **📈 Stats** — Score trend, by-course breakdown, hole weaknesses, vs Tour averages

---

## ⚖️ Honest limitations

- **Rapsodo auto-sync:** Not possible — Rapsodo has no public API. The CSV import is one-tap to compensate.
- **Live pin distances:** Course-map data is licensed. We give plays-like math + your saved aim points instead.
- **Auto-detected swings:** No phone can detect a golf swing reliably without a sensor. Voice + 1-tap log keeps it close to "no forms".

---

## 🔧 Tech

- **Streamlit** + **Plotly** + **Pandas** + **NumPy** + **Pillow**
- **Gemini 1.5 Flash** (chat) + **Gemini Vision** (photo)
- **Open-Meteo** API (weather, no key)
- Browser **SpeechRecognition** + **SpeechSynthesis** (voice)
- PWA via `static/manifest.json`

---

Built for Joel C. · GHIN 31.3 · Goal: Break 80, 300y driver, 20 handicap. ⛳
