import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from typing import Optional, Tuple, List, Dict

# --- 페이지 설정 (✅ 사이드바를 항상 펼쳐진 상태로 설정) ---
st.set_page_config(
    page_title="박물관 지도 & 큐레이터",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"  # <-- 이 옵션을 추가합니다.
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
# 사이드바: 페이지 링크(멀티페이지 내비게이션)
# ─────────────────────────────────────────
st.sidebar.title("📚 메뉴")
st.sidebar.page_link("01_박물관_위치_검색.py", label="1. 박물관 위치 검색", icon="🏛️")
st.sidebar.page_link("pages/02_큐레이터_챗봇.py", label="2. 큐레이터 챗봇", icon="🗣️")
st.sidebar.page_link("pages/03_유물_돋보기.py", label="3. 유물 돋보기", icon="🖼️")
st.sidebar.page_link("pages/04_QnA_for_foreigners.py", label="4. Q&A for Foreigners", icon="❓")
st.sidebar.markdown("---")

# ─────────────────────────────────────────
# API 키 로드 및 설정
# (이하 코드는 기존과 동일하게 유지됩니다)
# ─────────────────────────────────────────
try:
    KAKAO_KEY = st.secrets["KAKAO_KEY"]
    st.sidebar.success("✅ Kakao API 키 로드 성공!")
except (KeyError, FileNotFoundError):
    KAKAO_KEY = ""
    st.sidebar.error("⚠️ `secrets.toml`에 Kakao API 키를 설정해주세요.")

st.sidebar.title("⚙️ 검색 설정")
RADIUS_M = st.sidebar.slider("검색 반경 (미터)", 1000, 20000, 5000, 500)

# ─────────────────────────────────────────
# 세션 상태 초기화
# ─────────────────────────────────────────
if "search" not in st.session_state:
    st.session_state.search = {"address": "", "lat": None, "lon": None, "museums": [], "msg_geo": "", "msg_museum": ""}

st.title("🏛️ 내 위치 기반 박물관 검색 (지도 표시)")

# (이하 Kakao API 유틸, 입력, 출력 코드 등은 모두 기존과 동일합니다)
# ... (기존 코드 생략) ...
def geocode_address_kakao(address: str, kakao_key: str) -> Tuple[Optional[Tuple[float, float]], str]:
    if not kakao_key:
        return None, "⚠️ Kakao API 키가 설정되지 않았습니다."
    if not address:
        return None, "⚠️ 주소를 입력해 주세요."
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {kakao_key}"}
    try:
        r = requests.get(url, headers=headers, params={"query": address}, timeout=20)
        r.raise_for_status()
        docs = r.json().get("documents", [])
        if not docs:
            return None, "⚠️ 주소를 찾지 못했습니다."
        lat, lon = float(docs[0]["y"]), float(docs[0]["x"])
        return (lat, lon), "✅ 주소를 좌표로 변환했습니다."
    except Exception as e:
        return None, f"❌ 지오코딩 실패: {e}"

def search_museums_around(lat: float, lon: float, kakao_key: str, radius_m: int = 5000) -> Tuple[List[Dict], str]:
    if not kakao_key:
        return [], "⚠️ Kakao API 키가 비어 있습니다."
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {kakao_key}"}
    museums = []
    try:
        params = {"query": "박물관", "x": lon, "y": lat, "radius": radius_m, "sort": "distance", "size": 15}
        r = requests.get(url, headers=headers, params=params, timeout=20)
        r.raise_for_status()
        docs = r.json().get("documents", [])
        for d in docs:
            museums.append({
                "name": d.get("place_name"),
                "address": d.get("road_address_name") or d.get("address_name"),
                "distance": int(d.get("distance") or 0),
                "lat": float(d.get("y", 0)),
                "lon": float(d.get("x", 0)),
                "url": d.get("place_url"),
            })
        if not museums:
            return [], "⚠️ 반경 내 박물관이 없습니다. 반경을 넓혀 보세요."
        return museums, f"✅ 반경 {radius_m}m 내 박물관 {len(museums)}곳을 찾았습니다."
    except Exception as e:
        return [], f"❌ 장소검색 실패: {e}"

address = st.text_input("내 주소", placeholder="예) 서울특별시 용산구 서빙고로 137", value=st.session_state.search["address"])
col1, col2 = st.columns([1, 1])
if col1.button("검색 실행", use_container_width=True, type="primary"):
    if KAKAO_KEY:
        latlon, msg = geocode_address_kakao(address, KAKAO_KEY)
        st.session_state.search["address"] = address
        st.session_state.search["msg_geo"] = msg
        if latlon:
            lat, lon = latlon
            st.session_state.search["lat"], st.session_state.search["lon"] = lat, lon
            museums, mmsg = search_museums_around(lat, lon, KAKAO_KEY, radius_m=RADIUS_M)
            st.session_state.search["museums"], st.session_state.search["msg_museum"] = museums, mmsg
        else:
            st.session_state.search["lat"], st.session_state.search["lon"] = None, None
            st.session_state.search["museums"] = []
    else:
        st.error("Kakao API 키가 없어 검색을 실행할 수 없습니다.")

if col2.button("결과 지우기", use_container_width=True):
    st.session_state.search = {"address": "", "lat": None, "lon": None, "museums": [], "msg_geo": "", "msg_museum": ""}
    st.rerun()

s = st.session_state.search
if s["msg_geo"]:
    st.info(s["msg_geo"])
if s["lat"] and s["lon"]:
    st.info(s["msg_museum"])

    m = folium.Map(location=[s["lat"], s["lon"]], zoom_start=14, tiles="OpenStreetMap")
    folium.Marker([s["lat"], s["lon"]], tooltip="기준 위치", popup=s["address"], icon=folium.Icon(color="red")).add_to(m)

    for i, x in enumerate(s["museums"], start=1):
        popup_html = f"<b>{i}. {x['name']}</b><br>주소: {x['address']}<br>거리: {x['distance']} m<br><a href='{x['url']}' target='_blank'>상세보기</a>"
        folium.Marker([x["lat"], x["lon"]], tooltip=f"{i}. {x['name']}", popup=popup_html,
                      icon=folium.Icon(color="blue", icon="info-sign")).add_to(m)

    st_folium(m, width=None, height=560, key="map")

    st.subheader("거리순 목록")
    st.dataframe(
        [{"순위": i, "박물관명": x["name"], "주소": x["address"], "거리(m)": x["distance"], "링크": x["url"]}
         for i, x in enumerate(s["museums"], start=1)],
        use_container_width=True
    )
else:
    st.caption("주소를 입력하고 **검색 실행**을 눌러 지도를 표시하세요.")

    #streamlit run 01_박물관_위치_검색.py