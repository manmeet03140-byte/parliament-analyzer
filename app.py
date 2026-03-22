import streamlit as st
import os
import json
import re
from fpdf import FPDF
from audio_recorder_streamlit import audio_recorder
from transcriber import transcribe_audio
from analyzer import analyze_speech
import database

database.init_db()

st.set_page_config(page_title="Parliamentary Speech Analyzer", page_icon="🏛️", layout="wide")

st.sidebar.title("🏛️ Navigation")
page = st.sidebar.radio("Go to:", ["Live Analyzer", "📜 Speech History Database"])

# ==========================================
# HELPER FUNCTION: GENERATE INDIVIDUAL PDF
# ==========================================
def generate_single_pdf(row):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("helvetica", size=10)
    
    # Bulletproof text cleaner
    def clean_text(text):
        if not text: return "None"
        cleaned = re.sub(r'[^\x00-\x7F]+', '', str(text)).strip()
        return cleaned if cleaned else "None"

    speech_id, timestamp, transcript, sentiment, keywords_json, promises_json, topics_json, fact_checks_json = row

    # Title
    pdf.set_font("helvetica", size=16, style="B")
    pdf.cell(0, 10, f"Parliament Speech Report #{speech_id}", align="C")
    pdf.ln(12)

    pdf.set_font("helvetica", size=10)

    topics = json.loads(topics_json) if topics_json else []
    keywords = json.loads(keywords_json) if keywords_json else []
    promises = json.loads(promises_json) if promises_json else []
    fact_checks = json.loads(fact_checks_json) if fact_checks_json else []

    # Build the single record block
    block = f"Date Recorded: {timestamp}\n"
    block += "-" * 75 + "\n\n"
    block += f"Sentiment: {clean_text(sentiment)}\n"
    block += f"Topics: {clean_text(', '.join(topics))}\n"
    block += f"Keywords: {clean_text(', '.join(keywords))}\n\n"
    
    if promises:
        block += "Promises Made:\n"
        for p in promises:
            block += f"- {clean_text(p)}\n"
        block += "\n"
        
    if fact_checks:
        block += "Fact-Check Alerts:\n"
        for f in fact_checks:
            block += f"- {clean_text(f)}\n"
        block += "\n"
        
    block += f"Transcript:\n{clean_text(transcript)}\n"

    pdf.multi_cell(0, 6, block)

    return bytes(pdf.output())

# ==========================================
# PAGE 1: LIVE ANALYZER
# ==========================================
if page == "Live Analyzer":
    st.title("🎙️ Live Speech Analyzer")
    st.markdown("Use your microphone or upload audio to analyze promises, sentiment, topics, and fact-checks.")

    tab1, tab2 = st.tabs(["🎤 Live Microphone", "📁 Upload File"])
    audio_to_analyze = None

    with tab1:
        st.write("Click the microphone to start recording. Click again to stop.")
        audio_bytes = audio_recorder(text="Click to Record", recording_color="#e81e1e", neutral_color="#6aa36f", icon_name="microphone", icon_size="2x")
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            temp_path = "live_speech.wav"
            with open(temp_path, "wb") as f:
                f.write(audio_bytes)
            audio_to_analyze = temp_path

    with tab2:
        uploaded_file = st.file_uploader("Upload Speech Audio (MP3/WAV)", type=["mp3", "wav", "m4a"])
        if uploaded_file is not None:
            st.audio(uploaded_file)
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            audio_to_analyze = temp_path

    if audio_to_analyze is not None:
        if st.button("🧠 Analyze & Save Speech"):
            with st.spinner("Analyzing text, detecting topics, and fact-checking..."):
                transcript = transcribe_audio(audio_to_analyze)
                analysis_results = analyze_speech(transcript)
                
                database.save_speech(
                    transcript, analysis_results["sentiment"], analysis_results["top_keywords"], 
                    analysis_results["promises"], analysis_results["topics"], analysis_results["fact_checks"]
                )
                
                if os.path.exists(audio_to_analyze): os.remove(audio_to_analyze)
                
            st.success("Analysis Complete & Saved to Database! ✅")
            
            st.markdown("### 🏷️ Topics Discussed:")
            if analysis_results["topics"]:
                topic_cols = st.columns(len(analysis_results["topics"]))
                for i, topic in enumerate(analysis_results["topics"]):
                    topic_cols[i].button(topic, use_container_width=True)
            else:
                st.write("No specific topics detected.")
                
            with st.expander("📝 View Full Transcript"): st.write(transcript)
                
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="Overall Sentiment", value=analysis_results["sentiment"])
                st.markdown("### 🔑 Top Keywords")
                for word in analysis_results["top_keywords"]: st.write(f"- {word.capitalize()}")
                st.markdown("### 🎯 Promises Detected")
                if analysis_results["promises"]:
                    for promise in analysis_results["promises"]: st.success(f"**Promise:** {promise.capitalize()}")
                else:
                    st.warning("No clear promises detected.")
            with col2:
                st.markdown("### ⚠️ Fact-Check Alerts")
                st.caption("Flagged claims containing specific figures, money, or statistics:")
                if analysis_results["fact_checks"]:
                    for claim in analysis_results["fact_checks"]: st.error(f"🔎 **Verify:** {claim.capitalize()}")
                else:
                    st.info("No specific numbers or statistics flagged for fact-checking.")

# ==========================================
# PAGE 2: SPEECH HISTORY DASHBOARD
# ==========================================
elif page == "📜 Speech History Database":
    st.title("📜 Parliament Speech Archive")
    st.markdown("Review past analyses, track promises, and monitor sentiment over time.")
    
    history = database.get_all_speeches()
    
    if not history:
        st.info("No speeches recorded yet. Go to the Live Analyzer to process some audio!")
    else:
        st.divider()
        
        # --- DISPLAY HISTORY UI ---
        for row in history:
            speech_id, timestamp, transcript, sentiment, keywords_json, promises_json, topics_json, fact_checks_json = row
            
            keywords = json.loads(keywords_json)
            promises = json.loads(promises_json)
            topics = json.loads(topics_json)
            fact_checks = json.loads(fact_checks_json)
            
            with st.expander(f"Speech Record #{speech_id} — 🕒 {timestamp} — Sentiment: {sentiment}"):
                
                # --- INDIVIDUAL PDF BUTTON ---
                try:
                    pdf_data = generate_single_pdf(row)
                    st.download_button(
                        label=f"📄 Download Report for Record #{speech_id}", 
                        data=pdf_data, 
                        file_name=f"speech_report_{speech_id}.pdf", 
                        mime="application/pdf", 
                        type="primary", 
                        key=f"pdf_btn_{speech_id}" # Unique key is required when making multiple buttons
                    )
                except Exception as e:
                    st.error(f"⚠️ PDF generation failed: {e}")
                
                st.markdown("---") # Visual separator
                
                if topics: st.markdown(f"**Topics:** {', '.join(topics)}")
                st.markdown(f"**Keywords:** {', '.join(keywords)}")
                if promises:
                    st.markdown("**Promises Made:**")
                    for p in promises: st.write(f"- 🎯 {p}")
                if fact_checks:
                    st.markdown("**Fact-Check Alerts:**")
                    for f in fact_checks: st.write(f"- ⚠️ {f}")
                st.markdown("**Transcript:**")
                st.caption(transcript)