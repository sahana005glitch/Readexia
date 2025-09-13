import streamlit as st
from gtts import gTTS
import os, base64, random, json, time, re
from spellchecker import SpellChecker
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import which

# Tell pydub where ffmpeg is
AudioSegment.converter = r"C:\\ffmpeg\\bin\\ffmpeg.exe"
AudioSegment.ffprobe = r"C:\\ffmpeg\\bin\\ffprobe.exe"



# ========== KID-FRIENDLY UI THEME ==========
st.markdown("""
    <style>
    /* Background */
    .stApp {
        background: linear-gradient(135deg, #FFDEE9 50%, #B5FFFC 100%);
        color: black !important;  /* default text color */
    }

    /* Title */
    h1 {
        color: #FF6F61 !important;
        font-family: "Comic Sans MS", cursive, sans-serif;
        text-align: center;
    }

    /* Subheaders */
    h2, h3 {
        color: #4A47A3 !important;
        font-family: "Comic Sans MS", cursive, sans-serif;
    }

    /* Sidebar text */
    section[data-testid="stSidebar"] * {
        color: pink !important;
        font-family: "Comic Sans MS", cursive, sans-serif;
    }

    /* Buttons */
    div.stButton > button {
        background-color: #FFD93D;
        color: black !important;
        border-radius: 15px;
        font-size: 18px;
        font-weight: bold;
        padding: 10px 20px;
        border: 2px solid #F9A602;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #FFB347;
        color: white !important;
        border: 2px solid #FF6F61;
    }

    /* Text area */
    textarea {
        border: 3px solid #FF6F61 !important;
        border-radius: 12px !important;
        background-color: #FFF9C4 !important;
        color: black !important;
        font-family: "Comic Sans MS", cursive, sans-serif !important;
        font-size: 16px !important;
    }

    /* Success message */
    .stSuccess {
        background-color: #B2FF9E !important;
        color: black !important;
        font-size: 18px;
        border-radius: 12px;
    }

    /* Error / Info messages */
    .stError, .stInfo {
        color: black !important;
        font-size: 16px;
    }

    </style>
""", unsafe_allow_html=True)


st.title("🎨 Readexia – Fun Learning App for Kids 📚")

# Progress tracking
DATA_FILE = "progress.json"
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        progress = json.load(f)
else:
    progress = {"sessions": 0, "games_won": 0, "words_learned": 0}
    with open(DATA_FILE, "w") as f:
        json.dump(progress, f)

# Sidebar menu
menu = st.sidebar.radio("Choose a feature:", ["🏠 Home", "📖 Reading Helper", "🎙 Speak → Write", "🎮 Spelling Game", "📊 Dashboard"])

# ========== HOME ==========
if menu == "🏠 Home":
    st.subheader("✨ Welcome Buddy!")
    st.write("This app helps children with learning difficulties in a fun and interactive way 🚀.")
    st.balloons()

# ========== READING HELPER ==========
elif menu == "📖 Reading Helper":
    st.subheader("📖 Reading Helper (for Dyslexia)")

    story = st.text_area("Enter your story or paragraph:",
                         "Once upon a time there was a little rabbit who loved carrots.")

    if st.button("🎧 Read My Story!"):
        tts = gTTS(text=story, lang='en')
        tts.save("story.mp3")

        audio_file = open("story.mp3", "rb")
        audio_bytes = audio_file.read()
        st.audio(audio_bytes, format="audio/mp3")

        words = story.split()
        st.markdown("### 🟨 Read-Along Highlighting")
        highlighted_text = " ".join([f"<mark>{w}</mark>" for w in words])
        st.markdown(f"<div style='font-size:20px;'>{highlighted_text}</div>", unsafe_allow_html=True)

        st.success("✅ Story is being read aloud!")
        st.snow()

        progress["sessions"] += 1
        progress["words_learned"] += len(words)
        with open(DATA_FILE, "w") as f:
            json.dump(progress, f)

# ========== SPEAK → WRITE ==========
# ========== SPEAK → WRITE ==========
elif menu == "🎙 Speak → Write":
    st.subheader("🎙 Speak → Write (for Dysgraphia)")

    uploaded_file = st.file_uploader("🎤 Upload your audio", type=["mp3", "wav", "m4a"])

    if uploaded_file is not None:
        import os, tempfile

        # detect extension
        ext = os.path.splitext(uploaded_file.name)[1] or ".wav"

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmpfile:
            tmpfile.write(uploaded_file.read())
            tmp_path = tmpfile.name

        try:
            # load with pydub
            sound = AudioSegment.from_file(tmp_path, format=ext.replace(".", ""))
            st.audio(tmp_path)
            st.success("✅ Audio loaded successfully! Now transcribing...")

            # speech-to-text
            recognizer = sr.Recognizer()
            with sr.AudioFile(tmp_path) as source:
                audio_data = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(audio_data)
                    st.write("📝 Transcript:", text)

                    # spell correction
                    spell = SpellChecker()
                    corrected = " ".join([spell.correction(word) or word for word in text.split()])
                    st.markdown(f"<div style='background:#FFF176;padding:15px;border-radius:10px;font-size:18px;'>✨ {corrected}</div>", unsafe_allow_html=True)

                    st.success("✅ Your speech is converted to text!")

                except sr.UnknownValueError:
                    st.error("❌ Could not understand audio")
                except sr.RequestError:
                    st.error("⚠️ Speech Recognition API not available")

        except Exception as e:
            st.error(f"⚠️ Error processing audio: {e}")


# ========== SPELLING GAME ==========
# ======= Spelling Game (replace existing section) =======
elif menu == "🎮 Spelling Game":
    st.subheader("🎮 Fun Spelling Game")

    # word list (you can expand)
    WORD_LIST = ["rabbit", "carrot", "friend", "happy", "school", "mango", "elephant"]

    # initialize session state keys if missing
    if "target" not in st.session_state:
        st.session_state["target"] = None
    if "scrambled" not in st.session_state:
        st.session_state["scrambled"] = []
    if "assembled" not in st.session_state:
        st.session_state["assembled"] = ""

    # Start a new round (button or if no active target)
    new_round = st.button("🔁 New Word")
    if new_round or st.session_state["target"] is None:
        tgt = random.choice(WORD_LIST)
        st.session_state["target"] = tgt
        letters = list(tgt)
        random.shuffle(letters)
        st.session_state["scrambled"] = letters
        st.session_state["assembled"] = ""

    # show scrambled letters
    if st.session_state["scrambled"]:
        st.write("🔤 Unscramble the letters:")
        # show letters as buttons so kids can click to assemble
        cols = st.columns(len(st.session_state["scrambled"]))
        for i, letter in enumerate(st.session_state["scrambled"]):
            # give each button a unique key so Streamlit doesn't mix them up
            if cols[i].button(letter, key=f"letter_{i}"):
                st.session_state["assembled"] += letter

        st.markdown("**Assembled:** " + (st.session_state["assembled"] or "—"))
        # backspace / clear controls
        colb1, colb2 = st.columns([1,1])
        if colb1.button("⌫ Backspace"):
            st.session_state["assembled"] = st.session_state["assembled"][:-1]
        if colb2.button("🗑 Clear"):
            st.session_state["assembled"] = ""

        # allow typed input too (optional)
        typed = st.text_input("Or type your answer here (press Submit):")
        if typed:
            st.session_state["assembled"] = typed

        # Submit check
        if st.button("Submit"):
            clean_guess = st.session_state["assembled"].strip().lower()
            clean_target = st.session_state["target"].strip().lower()

            if clean_guess == clean_target:
                st.success("🎉 Correct! You did it! 🎈")
                st.balloons()
                # update progress
                progress["games_won"] = progress.get("games_won", 0) + 1
                with open(DATA_FILE, "w") as f:
                    json.dump(progress, f)
                # prepare next round (set target None so New Word is auto-chosen)
                st.session_state["target"] = None
                st.session_state["scrambled"] = []
                st.session_state["assembled"] = ""
            else:
                st.error("❌ Oops! Try again...")
                # optionally reveal hint: first letter
                st.info(f"Hint: The word starts with '{st.session_state['target'][0]}'")



# ========== DASHBOARD ==========
elif menu == "📊 Dashboard":
    st.subheader("📊 Your Progress")
    st.write("✨ Sessions Completed:", progress["sessions"])
    st.write("✨ Words Learned:", progress["words_learned"])
    st.write("✨ Games Won:", progress["games_won"])
