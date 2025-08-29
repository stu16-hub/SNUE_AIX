
import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 페이지 설정 ---
st.set_page_config(
    page_title="🎨 이미지 기반 유물 분석기",
    page_icon="📜",
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
# ─────────────────────────────────────────
# API 키 설정 (st.secrets 사용)
# ─────────────────────────────────────────
try:
    google_api_key = st.secrets["GOOGLE_API_KEY"]
    st.sidebar.success("✅ Google API 키 로드 성공!")
except (KeyError, FileNotFoundError):
    google_api_key = ""
    st.sidebar.error("⚠️ `secrets.toml`에 Google API 키를 설정해주세요.")

# --- 메인 화면 구성 ---
st.title("🖼️ 이미지 기반 유물 돋보기")
st.markdown("유물, 예술 작품, 역사적 사진 등을 업로드하면 AI가 큐레이터처럼 설명해 드립니다.")
st.markdown("---")

# 이미지 업로더
uploaded_file = st.file_uploader(
    "분석할 이미지를 업로드하세요.",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption=f"분석 대상 이미지: {uploaded_file.name}", use_column_width=True)

    if st.button("🚀 이미지 분석 시작", type="primary"):
        if not google_api_key:
            st.error("⚠️ 사이드바에서 Google API 키를 먼저 설정해주세요.")
            st.stop()

        try:
            genai.configure(api_key=google_api_key)
            model = genai.GenerativeModel(model_name='gemini-1.5-flash')

            prompt = """
            당신은 해박한 지식을 가진 박물관의 전문 큐레이터입니다.
            주어진 이미지를 보고, 아래의 형식에 맞춰 유물 또는 예술 작품에 대해 상세하고 깊이 있게 설명해주세요.
            설명은 초등학생도 이해할 수 있도록 쉽고 흥미롭게 작성해주세요. 관련 유물이 검색되지 않을 때에는 상상에 기반해서 지어내지 말고 사실을 기반으로 정확한 정보만 제공하세요.

            **1. 명칭:** (이미지를 통해 추정되는 공식 명칭 또는 일반 명칭)

            **2. 시대와 출처:** (어느 시대에, 어디에서 만들어졌는지)

            **3. 재료 및 기법:** (무엇으로, 어떻게 만들어졌는지)

            **4. 특징과 의미:** (생김새의 특징과 그 안에 담긴 상징이나 의미)

            **5. 역사적 가치:** (이 유물이 왜 중요하고 대단한지)

            **6. 재미있는 이야기:** (이 유물과 관련된 흥미로운 일화나 사실)
            """

            with st.spinner("AI 큐레이터가 이미지를 분석하고 있습니다... 잠시만 기다려주세요."):
                response = model.generate_content([prompt, image])

                st.subheader("📊 AI 큐레이터 분석 결과")
                st.markdown(response.text)

                # 분석 결과 다운로드 버튼
                st.download_button(
                    label="📥 분석 결과 다운로드",
                    data=response.text.encode('utf-8'),
                    file_name=f"분석결과_{uploaded_file.name.split('.')[0]}.txt",
                    mime="text/plain"
                )

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
            st.info("API 키가 정확한지, 할당량이 초과되지 않았는지 확인해보세요. 문제가 지속되면 잠시 후 다시 시도해주세요.")

else:
    st.info("🖼️ 분석하고 싶은 유물이나 예술 작품 이미지를 업로드 해주세요.")
    st.markdown("""
    ### 🌟 이런 이미지를 분석할 수 있어요!
    - **한국 유물**: 고려청자, 백제 금동대향로, 신라 금관, 조선백자 등
    - **세계 유물**: 이집트 로제타석, 메소포타미아 함무라비 법전 등
    - **미술 작품**: 레오나르도 다빈치의 '모나리자', 김홍도의 '씨름' 등
    - **역사적 사진**: 흑백으로 된 옛날 사진이나 역사적 사건 현장 사진
    """)
    #streamlit run app.py