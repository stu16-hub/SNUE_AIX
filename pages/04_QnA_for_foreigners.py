
import streamlit as st
import google.generativeai as genai
from openai import OpenAI

# --- 페이지 설정 ---
st.set_page_config(
    page_title="Museum Q&A",
    page_icon="❓",
    layout="wide"
)

# --- ✅ 자동 생성된 상단 메뉴를 숨기는 CSS 코드 ---
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# 사이드바: 내비게이션 & API 키 설정
# ─────────────────────────────────────────
st.sidebar.title("📚 메뉴")
st.sidebar.page_link("01_박물관_위치_검색.py", label="1. 박물관 위치 검색", icon="🏛️")
st.sidebar.page_link("pages/02_큐레이터_챗봇.py", label="2. 큐레이터 챗봇", icon="🗣️")
st.sidebar.page_link("pages/03_유물_돋보기.py", label="3. 유물 돋보기", icon="🖼️")
st.sidebar.page_link("pages/04_QnA_for_foreigners.py", label="4. Q&A for Foreigners", icon="❓")
st.sidebar.markdown("---")


st.sidebar.title("🔐 API Keys")
st.sidebar.info("Solar API 키를 입력하면 더 정확한 답변을 제공합니다.")
try:
    google_api_key = st.secrets.get("GOOGLE_API_KEY")
    solar_api_key = st.secrets.get("SOLAR_API_KEY")
    if google_api_key:
        st.sidebar.success("Google API Key loaded!")
    if solar_api_key:
        st.sidebar.success("Solar API Key loaded!")
except (KeyError, FileNotFoundError):
    google_api_key = None
    solar_api_key = None

google_api_key_input = st.sidebar.text_input("Google API Key (Optional)", type="password", value=google_api_key or "")
solar_api_key_input = st.sidebar.text_input("Solar API Key (Recommended)", type="password", value=solar_api_key or "")
st.sidebar.markdown("[Upstage Solar API 키 발급받기](https://console.upstage.ai/services/solar)")


# ─────────────────────────────────────────
# 다국어 Q&A 데이터
# ─────────────────────────────────────────
translations = {
    "English": {
        "title": "❓ Q&A for Visitors",
        "info": "Here are some frequently asked questions to help you plan your visit.",
        "qna": [
            {"q": "What are the museum's opening hours?", "a": "The museum is open from 10:00 AM to 6:00 PM on Tuesdays, Thursdays, and Fridays. On Wednesdays and Saturdays, it's open until 7:00 PM. On Sundays and holidays, it closes at 6:00 PM. Last admission is 30 minutes before closing."},
            {"q": "Is there an admission fee?", "a": "Admission to the main exhibition halls is free. Special exhibitions may require a paid ticket."},
            {"q": "When is the museum closed?", "a": "The museum is closed on January 1st, Seollal (Lunar New Year's Day), Chuseok (Korean Thanksgiving Day), and every Monday."},
            {"q": "Are there guided tours in English?", "a": "Yes, English guided tours are available. Please check the official website for the latest schedule. Audio guides in English can also be rented."},
            {"q": "How do I get to the museum?", "a": "Take Subway Line 4 or the Gyeongui-Jungang Line to Ichon Station and use Exit 2. The museum is connected via an underpass called the 'Museum Path'."}
        ],
        "chat_title": "💬 Ask a Question in Real-Time",
        "chat_placeholder": "Ask anything about the museum, e.g., 'Are there any cafes inside?'"
    },
    # 다른 언어 번역 데이터는 공간 절약을 위해 생략 (기존 코드와 동일)
}

# --- 메인 화면 구성 ---

lang_option = st.selectbox("Select Language", options=list(translations.keys()))
content = translations[lang_option]
st.title(content["title"])
st.info(content["info"])

for item in content["qna"]:
    with st.expander(f"**{item['q']}**"):
        st.markdown(item['a'])

st.markdown("---")
st.header(content["chat_title"])

# -----------------------------------------
# 실시간 채팅 기능
# -----------------------------------------
SYSTEM_PROMPT = """
You are a friendly and helpful AI assistant for the National Museum of Korea.
Your primary goal is to answer visitor questions accurately.

**CRITICAL INSTRUCTIONS:**
1.  Your **primary source of truth** is the official National Museum of Korea website: https://www.museum.go.kr/
2.  You may supplement this with information from other highly reliable sources (e.g., Korea Tourism Organization, major news articles about the museum).
3.  If you use information from a source other than the official museum website, you **must mention the source** (e.g., 'According to the Korea Tourism Organization...').
4.  Do not make up information or guess. If you cannot find a reliable answer, you must state: "I cannot find that information on the official museum website. For the most accurate details, please check the information desk at the museum or visit the official website."
5.  Keep your answers concise and easy to understand for tourists.
6.  Respond in the language of the user's question.
"""

if "qna_messages" not in st.session_state:
    st.session_state.qna_messages = []

# 모델 선택 로직
client = None
model_name = ""
if solar_api_key_input:
    client = OpenAI(api_key=solar_api_key_input, base_url="https://api.upstage.ai/v1/solar")
    model_name = "solar-1-mini-chat"
    st.info("🤖 Solar 모델로 답변합니다.")
elif google_api_key_input:
    try:
        genai.configure(api_key=google_api_key_input)
        client = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)
        model_name = "gemini-1.5-flash"
        st.info("🤖 Gemini 모델로 답변합니다.")
    except Exception as e:
        st.error(f"Google 모델 초기화 오류: {e}")
        client = None

# 이전 대화 내용 표시
for message in st.session_state.qna_messages:
    role = message["role"]
    avatar_url = "https://www.harpersbazaar.co.kr/resources/online/online_image/2025/07/04/1f9f0dc0-bab9-4d50-8d68-cc5deebd7924.jpg" if role == "assistant" else None
    with st.chat_message(role, avatar=avatar_url):
        st.markdown(message["content"])

# 사용자 입력 처리
if prompt := st.chat_input(content["chat_placeholder"]):
    if not client:
        st.error("API 키가 설정되지 않았습니다. 사이드바에서 API 키를 입력해주세요.")
    else:
        st.session_state.qna_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="https://www.harpersbazaar.co.kr/resources/online/online_image/2025/07/04/1f9f0dc0-bab9-4d50-8d68-cc5deebd7924.jpg"):
            with st.spinner("AI가 답변을 생성 중입니다..."):
                try:
                    answer = ""
                    history_for_model = [{"role": m["role"], "content": m["content"]} for m in st.session_state.qna_messages]

                    if model_name == "solar-1-mini-chat":
                        # Solar 모델 호출
                        system_message = {"role": "system", "content": SYSTEM_PROMPT}
                        response = client.chat.completions.create(
                            model=model_name,
                            messages=[system_message] + history_for_model
                        )
                        answer = response.choices[0].message.content
                    elif model_name == "gemini-1.5-flash":
                        # Gemini 모델 호출
                        chat = client.start_chat(history=[
                            {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
                            for m in st.session_state.qna_messages[:-1]
                        ])
                        response = chat.send_message(prompt)
                        answer = response.text
                    
                    st.markdown(answer)
                    st.session_state.qna_messages.append({"role": "assistant", "content": answer})

                except Exception as e:
                    st.error(f"답변 생성 중 오류가 발생했습니다: {e}")