"""Streamlit web page for DJ Vibe. Run with: streamlit run app.py"""
import contextlib
import html
import io
from pathlib import Path

import streamlit as st

from src.agent import GOOD_SCORE, run_agent
from src.guardrails import check_query, logger
from src.recommender import load_songs

SONGS_PATH = Path(__file__).parent / "data" / "songs.csv"
ANSWER_MARKER = "Step 4 - ANSWER: asking DJ Vibe to explain the songs..."
EXAMPLES = [
    "chill lofi for studying on a rainy night",
    "bachata vibes for a date night",
    "songs for the gym",
]

# All the DJ styling lives here: dark studio colors, amber glow, vinyl, equalizer.
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;600&display=swap');

.stApp {
  background:
    radial-gradient(circle at 15% 0%, rgba(242,165,65,0.18), transparent 40%),
    radial-gradient(circle at 90% 20%, rgba(127,209,196,0.10), transparent 35%),
    #12121E;
}
html, body, .stApp, p, label, input { font-family: 'Inter', sans-serif; }
#MainMenu, header [data-testid="stToolbar"], footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

/* Header: vinyl, title, ON AIR, equalizer */
.hero { display: flex; align-items: center; gap: 28px; margin: 8px 0 28px; }
.vinyl {
  width: 120px; height: 120px; border-radius: 50%; flex-shrink: 0;
  background:
    radial-gradient(circle, #12121E 0 6%, #F2A541 7% 30%, #1a1a2c 31% 34%,
      #24243B 35% 45%, #1a1a2c 46% 48%, #24243B 49% 60%, #1a1a2c 61% 63%, #24243B 64% 100%);
  box-shadow: 0 0 40px rgba(242,165,65,0.35);
  animation: spin 4s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.hero h1 {
  font-family: 'Space Grotesk', sans-serif; font-size: 64px; line-height: 1; margin: 0; padding: 0;
  color: #F7F4EE; text-shadow: 0 0 24px rgba(242,165,65,0.45);
}
.hero p { color: #B9BCCB; margin: 10px 0 0; font-size: 17px; }
.onair {
  display: inline-flex; align-items: center; gap: 8px; margin-bottom: 12px;
  padding: 4px 12px; border-radius: 999px; border: 1px solid #FF5A4E;
  color: #FF8A80; font-size: 13px; font-weight: 600; letter-spacing: 2px;
}
.onair .dot { width: 9px; height: 9px; border-radius: 50%; background: #FF5A4E; animation: pulse 1.4s ease-in-out infinite; }
@keyframes pulse { 50% { opacity: 0.25; } }
.eq { display: flex; align-items: flex-end; gap: 4px; height: 28px; margin-left: 8px; }
.eq span { width: 5px; background: #F2A541; border-radius: 2px; animation: eq 1s ease-in-out infinite; }
.eq span:nth-child(2) { animation-delay: -0.4s; background: #7FD1C4; }
.eq span:nth-child(3) { animation-delay: -0.2s; }
.eq span:nth-child(4) { animation-delay: -0.7s; background: #7FD1C4; }
.eq span:nth-child(5) { animation-delay: -0.5s; }
@keyframes eq { 0%, 100% { height: 6px; } 50% { height: 28px; } }

/* Example pills and the main button */
.stButton > button {
  border-radius: 999px; border: 1px solid #3A3A5C; background: #1E1E33; color: #E6E2D8;
  transition: all 0.2s ease;
}
.stButton > button:hover { border-color: #F2A541; color: #F2A541; box-shadow: 0 0 16px rgba(242,165,65,0.35); }
.stButton > button[kind="primary"] {
  background: linear-gradient(90deg, #F2A541, #FF7A59); color: #161625; border: none;
  font-weight: 700; padding: 10px 28px; box-shadow: 0 0 24px rgba(242,165,65,0.45);
}
.stButton > button[kind="primary"]:hover { color: #161625; transform: translateY(-1px); }
.stTextInput input { border-radius: 14px; background: #1E1E33; font-size: 17px; }

/* Now Playing card */
.section-title {
  font-family: 'Space Grotesk', sans-serif; font-size: 13px; letter-spacing: 3px;
  text-transform: uppercase; color: #F2A541; margin: 28px 0 10px;
}
.now-playing {
  background: linear-gradient(135deg, #24243B, #1A1A2C); border: 1px solid #3A3A5C;
  border-radius: 20px; padding: 24px 28px; box-shadow: 0 10px 40px rgba(0,0,0,0.35);
}
.np-intro { font-size: 19px; font-style: italic; color: #F7F4EE; margin-bottom: 18px; }
.track { display: flex; gap: 16px; align-items: center; padding: 12px 0; border-top: 1px solid #33334F; }
.track-num {
  width: 36px; height: 36px; border-radius: 50%; flex-shrink: 0; display: flex; align-items: center;
  justify-content: center; background: #F2A541; color: #161625; font-weight: 700;
}
.track-title { font-family: 'Space Grotesk', sans-serif; font-size: 18px; color: #F7F4EE; }
.track-why { color: #B9BCCB; font-size: 15px; }
.np-outro { margin-top: 16px; color: #7FD1C4; font-weight: 600; }

/* Song cards with score bars */
.song-card {
  background: #1E1E33; border: 1px solid #33334F; border-radius: 16px; padding: 14px 18px; margin-bottom: 10px;
}
.song-top { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
.song-name { font-family: 'Space Grotesk', sans-serif; font-size: 17px; color: #F7F4EE; }
.song-artist { color: #9A9FB4; font-size: 14px; }
.song-score { font-weight: 700; color: #F2A541; white-space: nowrap; }
.tag { display: inline-block; margin: 8px 6px 8px 0; padding: 2px 10px; border-radius: 999px; font-size: 12px; background: #2C2C48; color: #CFCFE0; }
.bar { height: 6px; border-radius: 3px; background: #2C2C48; overflow: hidden; }
.bar div { height: 100%; border-radius: 3px; background: linear-gradient(90deg, #7FD1C4, #F2A541); }
.strong { color: #7FD1C4; font-size: 12px; font-weight: 600; margin-left: 6px; }
</style>
"""

HERO = """
<div class="hero">
  <div class="vinyl"></div>
  <div>
    <div class="onair"><span class="dot"></span>ON AIR
      <span class="eq"><span></span><span></span><span></span><span></span><span></span></span>
    </div>
    <h1>DJ Vibe</h1>
    <p>Tell me the vibe in your own words. My AI agent digs through the crate and spins the right tracks.</p>
  </div>
</div>
"""


def now_playing_html(answer: str) -> str:
    """Turn the DJ answer (intro, 🎵 lines, sign-off) into a 'Now Playing' card."""
    lines = [line.strip() for line in answer.strip().splitlines() if line.strip()]
    tracks = [line for line in lines if line.startswith("🎵")]
    if not tracks:
        # Fallback answers have no DJ format, so show them as plain lines.
        body = "<br>".join(html.escape(line) for line in lines)
        return f'<div class="now-playing"><div class="np-intro">{body}</div></div>'

    first_track = lines.index(tracks[0])
    intro = " ".join(lines[:first_track])
    outro = " ".join(line for line in lines[first_track:] if not line.startswith("🎵"))
    rows = []
    for number, track in enumerate(tracks, start=1):
        title, _, why = track.lstrip("🎵").strip().partition("|")
        rows.append(
            f'<div class="track"><div class="track-num">{number}</div><div>'
            f'<div class="track-title">{html.escape(title.strip())}</div>'
            f'<div class="track-why">{html.escape(why.strip())}</div></div></div>'
        )
    return (
        f'<div class="now-playing"><div class="np-intro">{html.escape(intro)}</div>'
        f'{"".join(rows)}<div class="np-outro">{html.escape(outro)}</div></div>'
    )


def song_card_html(song: dict, score: float) -> str:
    """One song with its genre/mood tags and a score bar out of 4."""
    width = max(0.0, min(score / 4.0, 1.0)) * 100
    strong = '<span class="strong">STRONG MATCH</span>' if score >= GOOD_SCORE else ""
    return (
        f'<div class="song-card"><div class="song-top"><div>'
        f'<span class="song-name">{html.escape(song["title"])}</span>{strong}<br>'
        f'<span class="song-artist">{html.escape(song["artist"])}</span></div>'
        f'<div class="song-score">{score:.2f} / 4</div></div>'
        f'<span class="tag">{html.escape(song["genre"])}</span><span class="tag">{html.escape(song["mood"])}</span>'
        f'<div class="bar"><div style="width:{width:.0f}%"></div></div></div>'
    )


st.set_page_config(page_title="DJ Vibe", page_icon="🎙️", layout="centered")
st.markdown(STYLE, unsafe_allow_html=True)
st.markdown(HERO, unsafe_allow_html=True)

if "query" not in st.session_state:
    st.session_state.query = ""

# Example buttons fill the text box, so a demo needs no typing.
columns = st.columns(len(EXAMPLES))
for column, example in zip(columns, EXAMPLES):
    if column.button(example, use_container_width=True):
        st.session_state.query = example

query = st.text_input("What's the vibe?", key="query", placeholder="e.g. something sad and quiet for a breakup")

if st.button("🎧 Spin it", type="primary"):
    # Guardrail: stop bad input before calling Gemini.
    problem = check_query(query)
    if problem:
        st.warning(problem)
        logger.warning("Rejected request: %r", query)
    else:
        logger.info("New request: %s", query)
        songs = load_songs(str(SONGS_PATH))

        # The agent prints its steps, so capture them to show on the page.
        printed = io.StringIO()
        with st.spinner("DJ Vibe is digging through the crate..."):
            with contextlib.redirect_stdout(printed):
                results = run_agent(query, songs)
        steps, _, answer = printed.getvalue().partition(ANSWER_MARKER)

        if "Gemini is not available" in steps:
            st.warning("Gemini is not available right now, so these picks come from the simple keyword finder.")
        elif "Out of tries" in steps:
            st.info("I couldn't find a strong match in my catalog. These are the closest songs I have.")

        st.markdown('<div class="section-title">🎙️ Now playing</div>', unsafe_allow_html=True)
        st.markdown(now_playing_html(answer), unsafe_allow_html=True)

        st.markdown('<div class="section-title">📀 Top 5 from the crate</div>', unsafe_allow_html=True)
        st.markdown("".join(song_card_html(song, score) for song, score, _ in results), unsafe_allow_html=True)

        with st.expander("🧠 Behind the decks: how the agent thought (plan, tool, check)"):
            st.code(steps.strip(), language=None, wrap_lines=True)
