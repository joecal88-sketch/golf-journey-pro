"""AI Coach — voice chat + photo swing analysis."""
import streamlit as st
import streamlit.components.v1 as components
from cloud_storage import load_data, append_coach
from styles import COLORS

try:
    from gemini_client import generate_text, generate_with_image
    from PIL import Image
    HAS_GENAI = True
except Exception:
    HAS_GENAI = False


def _voice_widget():
    """Voice input + TTS toggle widget."""
    components.html(
        """
        <div style="background:#0F1B16;border:1px solid #1F3329;border-radius:14px;padding:14px;">
          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
            <div>
                <button id="cv-mic" style="background:linear-gradient(135deg,#0E5C3A,#137A4D);color:#F5EFE0;border:none;border-radius:99px;padding:10px 20px;font-weight:700;cursor:pointer;font-family:Inter;font-size:13px;">
                    🎙 Speak your question
                </button>
                <span id="cv-status" style="margin-left:10px;font-size:12px;color:#A8A99F;font-family:Inter;"></span>
            </div>
            <label style="font-size:12px;color:#F5EFE0;font-family:Inter;cursor:pointer;">
                <input type="checkbox" id="cv-tts" checked> 🔊 Speak Coach replies
            </label>
          </div>
          <div id="cv-text" style="margin-top:10px;padding:10px;background:#152620;border-radius:10px;color:#F5EFE0;font-family:Inter;font-size:13px;min-height:36px;"></div>
        </div>
        <script>
        const btn = document.getElementById('cv-mic');
        const status = document.getElementById('cv-status');
        const text = document.getElementById('cv-text');
        const tts = document.getElementById('cv-tts');

        btn.onclick = function() {
            if (!('webkitSpeechRecognition' in window)) { status.innerText='Voice unsupported. Use Safari/Chrome.'; return; }
            const rec = new webkitSpeechRecognition();
            rec.continuous = false;
            rec.interimResults = true;
            rec.onresult = e => {
                let s='';
                for (let i=0;i<e.results.length;i++) s += e.results[i][0].transcript+' ';
                text.innerText = s;
            };
            rec.onstart = ()=> status.innerText='🔴 listening…';
            rec.onend = ()=> { status.innerText='✓ done — copy text and paste into chat below.'; btn.disabled=false; btn.style.opacity=1; };
            rec.start();
            btn.disabled=true; btn.style.opacity=0.5;
        };

        // expose TTS for parent
        window.parent.gjSpeak = function(t) {
            if (!tts.checked) return;
            if (!('speechSynthesis' in window)) return;
            const u = new SpeechSynthesisUtterance(t);
            u.rate = 1.0; u.pitch = 1.0;
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(u);
        };
        </script>
        """,
        height=140,
    )


def _speak_js(text):
    """Inject a script that speaks the latest reply via parent's gjSpeak hook."""
    safe = text.replace("\n", " ").replace('"', "'").replace("`", "'")[:1000]
    components.html(
        f"""
        <script>
        try {{ if (window.parent.gjSpeak) window.parent.gjSpeak("{safe}"); }} catch(e) {{}}
        </script>
        """,
        height=0,
    )


def _chat_tab():
    if "coach_msgs" not in st.session_state:
        st.session_state["coach_msgs"] = []

    _voice_widget()

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # Render history
    for m in st.session_state["coach_msgs"]:
        if m["role"] == "user":
            st.markdown(
                f"""
                <div style="display:flex;justify-content:flex-end;margin:8px 0;">
                  <div style="background:{COLORS['fairway']};color:{COLORS['cream']};padding:12px 16px;border-radius:18px 18px 4px 18px;max-width:78%;font-size:14px;line-height:1.5;">
                    {m['text']}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="display:flex;justify-content:flex-start;margin:8px 0;">
                  <div style="background:{COLORS['bg_3']};color:{COLORS['cream']};padding:12px 16px;border-radius:18px 18px 18px 4px;max-width:78%;font-size:14px;line-height:1.6;border:1px solid {COLORS['border']};white-space:pre-line;">
                    {m['text']}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    msg = st.chat_input("Ask your coach…")
    if msg:
        st.session_state["coach_msgs"].append({"role": "user", "text": msg})
        if not HAS_GENAI:
            st.session_state["coach_msgs"].append({"role": "assistant", "text": "Gemini not installed."})
        else:
            try:
                d = load_data()
                profile = d.get("profile", {})
                rounds = d.get("rounds", []) or []
                shots = d.get("practice_shots", []) or []
                avg = round(sum(r.get("score", 0) for r in rounds[-5:]) / max(len(rounds[-5:]), 1), 1) if rounds else "—"
                ctx = (
                    f"You are an elite golf coach for {profile.get('name', 'the player')}, "
                    f"GHIN handicap {profile.get('ghin', 31)}. Recent 5-round avg: {avg}. "
                    f"Career goal: break 80, 300y driver. They have {len(rounds)} logged rounds and {len(shots)} practice shots. "
                    f"Be direct, specific, and actionable. Cite numbers when possible. No fluff."
                )
                with st.spinner("Coach is thinking…"):
                    reply = generate_text(msg, system=ctx)
                st.session_state["coach_msgs"].append({"role": "assistant", "text": reply})
                append_coach({"type": "chat", "q": msg, "a": reply})
                _speak_js(reply)
            except Exception as e:
                st.session_state["coach_msgs"].append({"role": "assistant", "text": f"Coach is offline: {e}"})
        st.rerun()


def _photo_tab():
    st.markdown(f"<div style='color:{COLORS['cream_dim']};font-size:14px;margin-bottom:14px;'>Upload a swing photo (any phase: address, top, impact, finish). Coach will analyze and prescribe drills.</div>", unsafe_allow_html=True)
    f = st.file_uploader("Drop swing photo", type=["jpg", "jpeg", "png", "heic"], label_visibility="collapsed", key="photo_up")
    if f:
        try:
            from PIL import Image
            img = Image.open(f)
            st.image(img, caption="Your swing", use_container_width=True)
            if st.button("🔍 Analyze with AI Coach", type="primary", use_container_width=True):
                if not HAS_GENAI:
                    st.error("Gemini library missing.")
                else:
                    try:
                        d = load_data()
                        profile = d.get("profile", {})
                        prompt = (
                            f"You're an elite golf coach. Analyze this swing photo for "
                            f"{profile.get('name', 'the player')} (handicap {profile.get('ghin', 31)}). "
                            f"Structure your reply EXACTLY:\n\n"
                            f"**📸 Photo Quality:** [usable / not — if blurry/wrong angle, say what to retake]\n\n"
                            f"**👀 What I See:** [phase of swing + 2-3 key observations]\n\n"
                            f"**✅ Strengths:** [bullet list, 2-3 items]\n\n"
                            f"**⚠️ Issues:** [bullet list, 2-3 items, prioritized]\n\n"
                            f"**🎯 Top Drill:** [ONE specific drill with brief steps]\n\n"
                            f"**📈 Expected Result:** [what improvement they should see in 2 weeks]\n\n"
                            f"Be direct, no hedging."
                        )
                        # Convert PIL Image to bytes
                        import io as _io
                        buf = _io.BytesIO()
                        img.convert("RGB").save(buf, format="JPEG", quality=85)
                        img_bytes = buf.getvalue()
                        with st.spinner("Coach is analyzing your swing…"):
                            text = generate_with_image(prompt, img_bytes, mime="image/jpeg")
                        st.markdown(
                            f"""
                            <div class="insight-card gold" style="margin-top:14px;">
                                <div class="title">🎓 Coach Analysis</div>
                                <div class="body" style="white-space:pre-line;">{text}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        append_coach({"type": "photo_analysis", "result": text})
                    except Exception as e:
                        st.error(f"Vision analysis failed: {e}")
        except Exception as e:
            st.error(f"Could not read photo: {e}")


def render():
    st.markdown(
        f"""
        <div style="margin:8px 0 22px;">
            <div style="font-size:11px;color:{COLORS['flag']};letter-spacing:0.25em;text-transform:uppercase;font-weight:800;">🎓 AI COACH</div>
            <h1 style="margin:6px 0 4px;font-size:42px;">Talk to your Coach</h1>
            <div style="color:{COLORS['cream_dim']};font-size:15px;">Voice chat. Photo swing analysis. Powered by Gemini.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(["💬 Chat & Voice", "📸 Photo Swing Analysis"])
    with tab1: _chat_tab()
    with tab2: _photo_tab()
