import streamlit as st
import google.generativeai as genai

# --- 상단 메뉴 숨기기 및 사이드바 기본 펼침 ---
st.set_page_config(
    page_title="큐레이터 챗봇", 
    page_icon="🗣️", 
    layout="wide",
    initial_sidebar_state="expanded"
)
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

# ─────────────────────────────────────────
# API 키 로드 및 모델 설정
# ─────────────────────────────────────────
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
    st.sidebar.success("✅ Google API 키 로드 성공!")
except (KeyError, FileNotFoundError):
    API_KEY = ""
    st.sidebar.error("⚠️ `secrets.toml`에 Google API 키를 설정해주세요.")

st.sidebar.title("🧠 모델 설정")
temperature = st.sidebar.slider("창의성(temperature)", 0.0, 1.0, 0.5, 0.1) # 창의성 기본값을 0.5로 약간 낮춤
reset_btn = st.sidebar.button("대화 초기화", use_container_width=True, type="secondary")

# ─────────────────────────────────────────
# ✅ 시스템 프롬프트 (신뢰성 강화)
# ─────────────────────────────────────────
SYSTEM_INSTRUCTION = """
너는 박물관의 전문 큐레이터 챗봇이다. 너의 가장 중요한 임무는 사용자가 미술 작품이나 유물에 대해 질문했을 때, '신뢰할 수 있는 정보'에 기반하여 풍부하고 깊이 있는 해설을 제공하는 것이다.

**[매우 중요한 원칙: 답변의 신뢰성]**
1.  **사실 기반 응답**: 너의 모든 답변은 반드시 박물관 공식 자료, 학술 논문, 저명한 미술사 서적 등 검증된 출처에 기반해야 한다.
2.  **불확실성 명시**: 만약 학계에서 의견이 갈리거나 명확하게 밝혀지지 않은 사실에 대해 설명할 때는, "이 부분에 대해서는 여러 학설이 있습니다" 또는 "~라고 추정됩니다" 와 같이 불확실하다는 점을 명확히 밝혀야 한다.
3.  **정보 부재 시 인정**: 모르는 정보나 확인할 수 없는 내용에 대해서는 절대 추측해서 답변하지 않는다. 대신 "죄송하지만 해당 정보에 대한 신뢰할 수 있는 자료를 찾을 수 없었습니다"라고 솔직하게 답변해야 한다.

**[해설 스타일]**
위의 신뢰성 원칙을 지키는 선에서, 아래 스타일을 자연스럽게 엮어 설명하라:
-   **스토리텔링**: 작품에 얽힌 흥미로운 이야기나 작가의 삶을 사실에 기반하여 풀어낸다.
-   **맥락 제공**: 작품이 만들어진 시대적 배경, 미술 사조 등을 함께 설명하여 이해를 돕는다.
-   **전문적 분석**: 작품에 사용된 상징, 기법 등을 전문가의 시각으로 분석한다.
-   **대화 유도**: 설명 마지막에는 항상 사용자가 추가 질문을 할 수 있도록 자연스럽게 대화를 이끈다.
"""

# ─────────────────────────────────────────
# 세션 상태: 멀티턴 대화 저장
# ─────────────────────────────────────────
if "curator_msgs" not in st.session_state or reset_btn:
    st.session_state.curator_msgs = [
        {"role": "assistant", "content": "안녕하세요! 저는 신뢰할 수 있는 정보를 바탕으로 유물과 예술 작품을 설명해 드리는 큐레이터 챗봇입니다. 무엇이든 물어보세요."}
    ]

# ─────────────────────────────────────────
# Gemini 모델 준비
# ─────────────────────────────────────────
model = None
if API_KEY:
    try:
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            system_instruction=SYSTEM_INSTRUCTION
        )
    except Exception as e:
        st.error(f"모델 초기화 중 오류: {e}")

# ─────────────────────────────────────────
# 유틸: Streamlit 히스토리 → Gemini history 포맷 변환
# ─────────────────────────────────────────
def to_gemini_history(streamlit_msgs):
    history = []
    for m in streamlit_msgs:
        role = "user" if m["role"] == "user" else "model"
        history.append({"role": role, "parts": [m["content"]]})
    return history

# ─────────────────────────────────────────
# UI
# ─────────────────────────────────────────
st.title("🗣️ 큐레이터 챗봇")
st.caption("전시/유물에 대해 질문하면 큐레이터처럼 깊이 있게 해설해 드려요. (예: '신라 금관의 특징 알려줘')")

# 기존 대화 렌더링
for m in st.session_state.curator_msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# 입력창
if user_text := st.chat_input("질문을 입력하세요…"):
    # 1) 사용자 메시지 반영
    st.session_state.curator_msgs.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    # 2) 모델 응답 생성
    if not model:
        answer = "⚠️ API 키가 없어 응답을 생성할 수 없습니다. `secrets.toml` 파일을 확인해주세요."
    else:
        try:
            gemini_history = to_gemini_history(st.session_state.curator_msgs[:-1])
            chat = model.start_chat(history=gemini_history)
            resp = chat.send_message(
                user_text,
                generation_config=genai.types.GenerationConfig(temperature=temperature)
            )
            answer = resp.text.strip()
            if not answer:
                answer = "죄송해요, 지금은 답변을 생성하지 못했어요. 다시 시도해 주세요."
        except Exception as e:
            answer = f"오류가 발생했어요: {e}"

    # 3) 모델 응답 보관 + 출력
    st.session_state.curator_msgs.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)

# 첫 화면 도움말
if len(st.session_state.curator_msgs) == 1:
    st.info("예시) '이집트 미라 전시를 볼 때 어떤 점을 주의하면 좋을까?' '고려청자의 대표 문양과 제작 기법은?'", icon="💡")