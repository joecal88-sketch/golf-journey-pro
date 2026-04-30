# ⛳ Golf Journey Pro v4.1 — Seamless Edition

Joel C.'s personal golf improvement system. Built to feel like a published app — Rapsodo R-Cloud + TheStack quality, mobile-first, premium dark UI, voice-first interactions.

---

## 🚀 Quick Start

```bash
pip install -r requirements.txt
streamlit run Home.py
```

App opens at **http://localhost:8501**.

The terminal also prints a **Network URL** (e.g. `http://192.168.x.x:8501`) — open that on your iPhone or iPad while connected to the same WiFi.

### 📲 Install to iPhone home screen (PWA)
1. Open the Network URL in **Safari** on your iPhone
2. Tap the **Share** button → **Add to Home Screen**
3. App icon appears on your home screen — launches full-screen, no browser chrome

---

## ✨ What's New in v4.1

### 📲 PWA — Install Like a Real App
Manifest, icons, and meta tags so the app installs to your iPhone/iPad home screen and runs full-screen.

### 🎤 Voice-First Everything
- **Coach:** mic input + browser TTS replies (toggle "Speak responses")
- **Live Round:** voice scorecard — say "hole 1 four, hole 2 par, hole 3 bogey"
- Works on iPhone Safari and Android Chrome

### 📍 Auto-GPS + Live Weather
Live Round now auto-detects your location and pulls real-time wind/temp/humidity from Open-Meteo. **8 LA courses pre-loaded** with lat/lon (El Cariso, Scholl Canyon, Van Nuys Par 3, DeBell, Brookside #1, Griffith Wilson, Griffith Harding, Rancho Park).

### 🎯 Practice Hub Redesigned
- Clickable club picker (full bag including Mizuno JPX925 HM 5i–PW)
- Driving-range-style dispersion map (target circle, tour ellipse vs your ellipse)
- **Dispersion Index 0–100** vs Tour pros

### 📸 AI Photo Swing Analysis
Upload a swing photo → Gemini Vision analyzes setup, posture, plane, balance, and prescribes drills.

### 🤖 AI-Generated Drill Cards
Replaced broken YouTube embeds with personalized AI drill cards — text + diagram + voice script.

### 🔑 Gemini Key Baked In
Works out of the box. No setup needed for AI features.

### Plus everything from v4.0
Stroke-Saver Engine, Plays-Like Caddy, 17 achievements, vs-PGA-Tour benchmarks, hole-by-hole scorecard, streak tracker, weekly summaries.

---

## 📂 Pages

1. **🏠 Command Center** — KPIs, gap-to-break-80, stroke-saver plan, full bag clickable
2. **🏌️ Practice Hub** — My Bag picker + dispersion map, session log, Rapsodo CSV import
3. **📍 Live Round** — GPS + auto-weather, voice scorecard, plays-like caddy, 8 LA courses
4. **⚡ Speed Training** — TheStack 4 protocols, Foundation phase tracking
5. **🎯 Roadmap & Drills** — Stroke-saver roadmap, drill library with AI cards, AI drill generator, achievements
6. **🎓 AI Coach** — Voice in/out chat + photo swing analysis (Gemini Vision)
7. **📈 Performance** — Score trend, by-course breakdown, putts/GIR/fairways

---

## 💾 Data

All data persists in `golf_data.json`. First launch seeds sample rounds, speed sessions, and practice shots. Delete `golf_data.json` to reset.

---

## 🔧 Tech

- **Streamlit** + **Plotly** + **Pandas** + **Pillow**
- **Gemini 1.5 Flash** (text) + **Gemini Vision** (photo)
- **Open-Meteo** API (weather, no key)
- Browser **SpeechRecognition** + **SpeechSynthesis** (voice)
- PWA via `static/manifest.json` + service worker
- Premium CSS theme (Inter font, gradient accents, mobile-first)

---

Built for Joel C. · GHIN 31.3 · Goal: Break 80, 300-yard driver, 20 handicap. ⛳
