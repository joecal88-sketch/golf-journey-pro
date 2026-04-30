"""AI Coach — Gemini text + vision, voice in/out, smart fallback."""
import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import base64
from cloud_storage import load_data, append_note, update_settings
from weekly_summary import get_summary
from insights import gap_to_break_80, miss_pattern, stroke_saver_plan


def _ask_gemini(api_key: str, system_prompt: str, user_prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0.6, "maxOutputTokens": 700},
    }
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
    r.raise_for_status()
    j = r.json()
    return j["candidates"][0]["content"]["parts"][0]["text"]


def _ask_gemini_vision(api_key: str, system_prompt: str, user_prompt: str, image_bytes: bytes, mime: str = "image/jpeg") -> str:
    """Send an image + prompt to Gemini for swing analysis."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    b64 = base64.b64encode(image_bytes).decode("ascii")
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{
            "role": "user",
            "parts": [
                {"text": user_prompt},
                {"inline_data": {"mime_type": mime, "data": b64}},
            ],
        }],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 900},
    }
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
    r.raise_for_status()
    j = r.json()
    return j["candidates"][0]["content"]["parts"][0]["text"]


def _smart_fallback(question: str, mode: str, context: str) -> str:
    q = question.lower()
    if mode == "Pre-Round Warm-up":
        return (
            "**5-MINUTE WARM-UP for El Cariso (or any par 70):**\n\n"
            "1. **Putts (90 sec)** — 5 putts at 3 ft, 5 at 6 ft, 5 lag putts (30 ft+).\n"
            "2. **Wedges (60 sec)** — 5 half-shots at 50 yds with PW. Just feel rhythm.\n"
            "3. **Mid-iron (60 sec)** — 3 7-irons. Three-quarter swings only.\n"
            "4. **Fairway/Hybrid (45 sec)** — 3 swings with 5H or 3W. Don't grip-and-rip.\n"
            "5. **Driver (45 sec)** — 3 swings, focus on tempo, not power.\n\n"
            "Then walk to the first tee. Take a deep breath. Aim small. Trust the warm-up."
        )
    if mode == "On-Course Caddie":
        if any(k in q for k in ["165", "uphill", "wind"]):
            return (
                "**165 yards uphill, 10 mph headwind:**\n\n"
                "- Plays like ~180 yds (10% wind + 10 yds elevation).\n"
                "- Your 5H carries 175 — take the **5-Hybrid**.\n"
                "- Aim slightly right of pin; the headwind will push it back.\n"
                "- Choke down a half inch for control.\n"
                "- Commit to the swing. Don't decel."
            )
        return (
            "Tell me **distance + wind + elevation + lie** and I'll give you a club.\n"
            "Example: '150 to pin, 10 mph from the left, slight uphill, ball above feet.'"
        )
    if "slice" in q or "right" in q:
        return (
            "**Slice fix — your bias is right (-3.7° path on driver):**\n\n"
            "- **Grip:** rotate left hand so 2-3 knuckles show at address.\n"
            "- **Drill:** Headcover under right armpit, 20 half-swings.\n"
            "- **Drill:** Gate drill — two tees outside heel and toe, hit 15 without hitting tees.\n"
            "- **Path fix:** feel like you swing the clubhead OUT to right field after impact.\n"
            "- **Speed:** pause 1 second at top before firing — kills your over-the-top move."
        )
    if "putt" in q or "3-putt" in q:
        return (
            "**Putting fix — you average 32 putts/round:**\n\n"
            "- **Lag drill:** 10/20/30/40 ft, 3 balls each, finish within 3 ft of next tee.\n"
            "- **Gate drill:** 4 ft, 2 tees barely wider than ball — make 25 in a row.\n"
            "- **Eye position:** drop a ball from your nose — it should land on top of the ball.\n"
            "- **Tempo:** 2:1 ratio, backstroke twice as long as the forward stroke."
        )
    return (
        f"**Your stats:** {context}\n\n"
        "Ask me about a specific issue, e.g. '*driver slicing right*' or '*150 yards uphill in wind*'."
    )


# ──────────────────────────────────────────────────────────────────────
def render():
    st.markdown(
        """
        <div class="page-header">
            <div>
                <div class="page-eyebrow">AI · LIVE COACHING</div>
                <div class="page-title">AI Coach</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    settings = load_data().get("settings", {})
    saved_key = settings.get("gemini_key", "")

    if saved_key:
        st.markdown(
            f"""
            <div class="data-card" style="border-left:3px solid #00D4AA;margin-bottom:10px;">
                <div style="font-size:13px;color:#DDD;">✅ Gemini API connected — full live coaching enabled.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("🔑 Gemini API Setup (already configured)"):
        st.markdown("Free key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey).")
        new_key = st.text_input("Gemini API key", value=saved_key, type="password", help="Starts with AIzaSy...")
        if st.button("Save API Key"):
            update_settings({"gemini_key": new_key})
            st.success("✓ API key saved.")
            st.rerun()

    tab1, tab2 = st.tabs(["💬 Chat & Voice", "📸 Swing Photo Analysis"])

    with tab1:
        _render_chat(saved_key)
    with tab2:
        _render_swing_vision(saved_key)


def _render_chat(saved_key):
    mode = st.radio(
        "Coaching Mode",
        ["💪 Practice Coach", "📍 On-Course Caddie", "🏃 Pre-Round Warm-up"],
        horizontal=True,
    )
    mode_map = {
        "💪 Practice Coach": "Practice Coach",
        "📍 On-Course Caddie": "On-Course Caddie",
        "🏃 Pre-Round Warm-up": "Pre-Round Warm-up",
    }
    mode_key = mode_map[mode]

    # ── Voice mic that pipes into the question box ──
    st.caption("🎙 Tap the mic below to speak — your voice converts to text in the question box.")
    components.html(_voice_input_widget(), height=170)

    # Build context
    summary = get_summary()
    gap = gap_to_break_80()
    mp = miss_pattern()
    plan = stroke_saver_plan()
    context = (
        f"Player: Joel C. | GHIN: 31.3 | Avg: {summary.get('avg_score') or '—'} | "
        f"Best: {summary.get('best_score') or '—'} | Rounds: {summary.get('rounds_count')} | "
        f"Last 5 avg: {gap.get('avg') or '—'} | Driver speed: {summary.get('latest_espeed') or 97} mph | "
        f"Miss bias: {mp.get('bias') or 'unknown'} | Goals: Break 80, 300yd driver, 20 hcp"
    )
    if plan:
        context += f"\nTop stroke-savers: {', '.join(p['area'] for p in plan[:3])}."

    placeholder = {
        "💪 Practice Coach": "My driver is slicing right — what drill should I do?",
        "📍 On-Course Caddie": "165 yards uphill, 10 mph wind in my face — what club?",
        "🏃 Pre-Round Warm-up": "Build me a 15-minute warm-up before my round at El Cariso.",
    }[mode]

    question = st.text_area("Your question (paste voice transcript here)", placeholder=placeholder, height=110, key="coach_q")

    cA, cB = st.columns([3, 1])
    ask_clicked = cA.button("⛳ Ask Coach", use_container_width=True)
    speak_back = cB.checkbox("🔊 Speak", value=True, help="Coach reads the answer aloud")

    if ask_clicked:
        if not question.strip():
            st.warning("Type or speak a question first.")
            return
        with st.spinner("Coach is thinking..."):
            if saved_key:
                try:
                    system_prompt = (
                        "You are Joel's elite PGA-certified golf coach. Direct, practical, no fluff. "
                        "Reply in 5-7 short bullet points. Always include 1-2 specific drills with rep counts. "
                        "Use his exact stats and miss patterns from the player context. "
                        "He plays El Cariso, Scholl Canyon, Van Nuys Par 3, DeBell, Brookside, Griffith Park, Rancho Park. "
                        f"Current mode: {mode_key}. Bag: Mizuno ST-Z 230 driver, Callaway Rogue 3W, Callaway Edge 5H, "
                        "Mizuno JPX925 HM 5-PW, Kirkland 52/56/60 wedges, TaylorMade Spider putter."
                    )
                    user_prompt = f"PLAYER CONTEXT:\n{context}\n\nQUESTION: {question}"
                    answer = _ask_gemini(saved_key, system_prompt, user_prompt)
                except Exception as e:
                    answer = _smart_fallback(question, mode_key, context) + f"\n\n*(Gemini API error: {e})*"
            else:
                answer = _smart_fallback(question, mode_key, context)

        st.markdown(
            f"""
            <div class="data-card" style="border-left:3px solid #00D4AA;margin-top:14px;">
                <div style="font-size:11px;color:#00D4AA;letter-spacing:2px;text-transform:uppercase;margin-bottom:10px;font-weight:700;">⛳ COACH'S ANSWER</div>
                <div style="font-size:14px;color:#DDD;line-height:1.8;white-space:pre-wrap;">{answer}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if speak_back:
            components.html(_speech_synthesis_widget(answer), height=60)
        append_note(f"[{mode_key}] Q: {question}\nA: {answer}", kind="coach")

    # History
    notes = [n for n in load_data().get("notes", []) if n.get("kind") == "coach"]
    if notes:
        st.markdown('<div class="section-label" style="margin-top:24px;">CONVERSATION HISTORY</div>', unsafe_allow_html=True)
        for n in reversed(notes[-5:]):
            st.markdown(
                f"""
                <div class="data-card">
                    <div style="font-size:11px;color:#888;margin-bottom:8px;">{n.get('date','')[:19]}</div>
                    <div style="font-size:13px;color:#CCC;white-space:pre-wrap;line-height:1.7;">{n.get('text','')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_swing_vision(saved_key):
    st.markdown('<div class="section-label">SWING PHOTO ANALYSIS · POWERED BY GEMINI VISION</div>', unsafe_allow_html=True)
    st.caption(
        "Snap a photo at the **top of your backswing** (best) or **at impact** with the camera "
        "**face-on** or **down-the-line** behind you. Gemini will analyze posture, alignment, and key positions."
    )

    upload = st.file_uploader(
        "Upload swing photo",
        type=["jpg", "jpeg", "png", "webp"],
        help="Best result with full-body, well-lit photo from face-on or down-the-line angles.",
    )

    angle = st.selectbox("Camera angle", ["Down-the-line (behind player)", "Face-on (in front of player)", "Other / Selfie"])
    swing_phase = st.selectbox("Swing phase captured", ["Top of backswing", "Impact", "Address / Setup", "Follow-through", "Not sure"])
    pain_point = st.text_input("What you want help with (optional)", placeholder="e.g. I keep slicing the driver")

    if upload is not None and st.button("🔍 Analyze swing", use_container_width=True):
        if not saved_key:
            st.error("Need a Gemini API key. Add one in the setup expander above.")
            return
        with st.spinner("Coach is reviewing your swing..."):
            try:
                img_bytes = upload.getvalue()
                mime = upload.type or "image/jpeg"

                system = (
                    "You are an elite PGA-level golf coach giving a swing analysis. "
                    "Analyze the photo carefully. Be specific, technical, and useful — but honest if the photo "
                    "is too low-quality, too dark, doesn't show the full body, or isn't a golf swing photo at all. "
                    "Use this exact format:\n\n"
                    "**📸 Photo Quality:** (one line — good/okay/poor and why)\n\n"
                    "**🏌️ What I See:** (3-5 bullets describing posture, grip, alignment, ball position, weight, club position)\n\n"
                    "**✅ Strengths:** (1-3 bullets)\n\n"
                    "**⚠️ Issues:** (2-4 bullets — most impactful first)\n\n"
                    "**🎯 Top 2 Drills:** (each with name + 2-line how-to + rep count)\n\n"
                    "**📈 Expected Result:** (one line — what improving this fixes)\n\n"
                    "If the photo is unanalyzable, say so plainly and ask for a better angle."
                )
                user = (
                    f"Player context:\n"
                    f"- Joel C., GHIN 31.3, avg score 79.8, miss bias right (-3.7° driver path)\n"
                    f"- Goals: Break 80, 300-yard driver, get to 20 hcp\n"
                    f"- Camera angle: {angle}\n"
                    f"- Swing phase user says is captured: {swing_phase}\n"
                    f"- Pain point: {pain_point or 'general swing review'}\n\n"
                    "Now analyze the attached photo."
                )
                answer = _ask_gemini_vision(saved_key, system, user, img_bytes, mime=mime)

                # Show photo + analysis
                st.image(upload, caption="Your swing", use_container_width=True)
                st.markdown(
                    f"""
                    <div class="data-card" style="border-left:3px solid #00D4AA;margin-top:14px;">
                        <div style="font-size:11px;color:#00D4AA;letter-spacing:2px;text-transform:uppercase;margin-bottom:10px;font-weight:700;">⛳ COACH'S SWING ANALYSIS</div>
                        <div style="font-size:14px;color:#DDD;line-height:1.8;white-space:pre-wrap;">{answer}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                append_note(f"[Swing Vision · {angle} · {swing_phase}]\n{answer}", kind="coach")
            except Exception as e:
                st.error(f"Swing analysis failed: {e}")
                st.info(
                    "Make sure your Gemini API key is valid and the photo is under 4 MB. "
                    "If you keep seeing this, try a different angle or smaller image."
                )


# ──────────────────────────────────────────────────────────────────────
def _voice_input_widget():
    """Mic button that puts speech-to-text into clipboard for paste into question box."""
    return """
    <div style="font-family:Inter,sans-serif;background:#0F0F0F;border:1px solid #222;border-radius:14px;padding:14px;display:flex;gap:14px;align-items:center;">
      <button id="micBtn" style="background:linear-gradient(135deg,#00D4AA,#00B894);color:#000;border:none;border-radius:50%;width:54px;height:54px;font-size:22px;cursor:pointer;">🎙</button>
      <div style="flex:1;">
        <div id="status" style="color:#999;font-size:12px;">Tap mic, ask anything, then tap "📋 Copy" and paste into the question box.</div>
        <div id="transcript" style="margin-top:6px;color:#00D4AA;font-size:13px;font-weight:600;font-family:monospace;min-height:18px;"></div>
      </div>
      <button id="copyBtn" style="background:#222;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:12px;cursor:pointer;">📋 Copy</button>
    </div>
    <script>
    (function(){
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      const btn = document.getElementById('micBtn');
      const status = document.getElementById('status');
      const out = document.getElementById('transcript');
      const copyBtn = document.getElementById('copyBtn');
      if (!SR) {
        status.textContent = "Voice not supported here. Try Safari (iPhone) or Chrome (Android).";
        btn.disabled = true; btn.style.opacity = .5; return;
      }
      const rec = new SR();
      rec.continuous = true; rec.interimResults = false; rec.lang = 'en-US';
      let listening = false;
      let txt = '';
      btn.onclick = () => {
        if (!listening) { rec.start(); listening = true; status.textContent="Listening… tap to stop."; btn.style.background="linear-gradient(135deg,#FF3B30,#CC2A20)"; }
        else { rec.stop(); listening = false; status.textContent="Stopped. Copy and paste below."; btn.style.background="linear-gradient(135deg,#00D4AA,#00B894)"; }
      };
      rec.onresult = (e) => {
        for (let i = e.resultIndex; i < e.results.length; i++) {
          if (e.results[i].isFinal) txt += ' ' + e.results[i][0].transcript;
        }
        out.textContent = txt.trim();
      };
      copyBtn.onclick = () => {
        navigator.clipboard.writeText(txt.trim());
        copyBtn.textContent = '✓ Copied';
        setTimeout(() => copyBtn.textContent = '📋 Copy', 1400);
      };
    })();
    </script>
    """


def _speech_synthesis_widget(text: str):
    """Auto-plays answer as speech via browser TTS."""
    safe = (text or "").replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
    return f"""
    <div style="font-family:Inter,sans-serif;color:#999;font-size:11px;">🔊 Coach is speaking...</div>
    <script>
    (function(){{
      const txt = `{safe}`;
      if (!('speechSynthesis' in window)) return;
      // Strip markdown asterisks for nicer reading
      const clean = txt.replace(/\\*\\*/g, '').replace(/\\*/g, '').replace(/\\#/g, '');
      const u = new SpeechSynthesisUtterance(clean);
      u.rate = 1.05; u.pitch = 1.0;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
    }})();
    </script>
    """
