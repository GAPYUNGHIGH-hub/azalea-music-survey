import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import os
import json

# 페이지 설정
st.set_page_config(
    page_title="진달래꽃 음악 설문조사",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Google Sheets 연결 설정
def get_google_sheets_client():
    """Google Sheets 클라이언트를 생성하고 반환합니다."""
    try:
        # 환경 변수에서 credentials 읽기
        credentials_json = os.environ.get('GOOGLE_CREDENTIALS')
        spreadsheet_id = os.environ.get('SPREADSHEET_ID')
        
        if not credentials_json:
            st.error("GOOGLE_CREDENTIALS 환경 변수가 설정되지 않았습니다!")
            st.info("Render 대시보드 → Environment에서 GOOGLE_CREDENTIALS를 확인하세요.")
            return None, None
            
        if not spreadsheet_id:
            st.error("SPREADSHEET_ID 환경 변수가 설정되지 않았습니다!")
            st.info("Render 대시보드 → Environment에서 SPREADSHEET_ID를 확인하세요.")
            return None, None
        
        # JSON 문자열을 파이썬 딕셔너리로 변환
        try:
            credentials_dict = json.loads(credentials_json)
        except json.JSONDecodeError as e:
            st.error(f"JSON 파싱 에러: {str(e)}")
            st.info("GOOGLE_CREDENTIALS가 올바른 JSON 형식인지 확인하세요.")
            return None, None
        
        # Google Sheets API 인증
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            credentials_dict, 
            scope
        )
        
        client = gspread.authorize(credentials)
        
        # 스프레드시트 열기
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.sheet1
        
        st.success("Google Sheets 연결 성공!")
        
        return client, worksheet
        
    except gspread.exceptions.APIError as e:
        st.error(f"Google Sheets API 에러: {str(e)}")
        st.info("Google Sheets가 서비스 계정과 공유되었는지 확인하세요.")
        return None, None
    except Exception as e:
        st.error(f"Google Sheets 연결 실패: {str(e)}")
        st.info("환경 변수와 Google Sheets 공유 설정을 확인하세요.")
        return None, None

# Google Sheets 클라이언트 초기화
client, worksheet = get_google_sheets_client()

# 앱 제목
st.title("🌸 진달래꽃 음악 선호도 조사")
st.markdown("---")

# 안내 메시지
st.markdown("""
### 📖 설문 안내
- 🎵 7가지 버전의 진달래꽃을 들어보세요
- ❤️ 가장 마음에 드는 **하나의 버전**을 선택해주세요
- 👤 연령대를 선택하고 투표 버튼을 눌러주세요
""")

st.markdown("---")

# 제목
st.header("🎵 각 버전을 들어보세요")

# 음악 파일 경로 설정
music_folder = "music_files"

# 버전 정보
version_info = {
    "버전 1": "클래식 피아노 반주",
    "버전 2": "현대적 어레인지",
    "버전 3": "오케스트라 버전",
    "버전 4": "재즈 스타일",
    "버전 5": "보컬 중심",
    "버전 6": "전통 국악 스타일",
    "버전 7": "어쿠스틱 버전"
}

# 3개씩 컬럼으로 배치
cols = st.columns(3)

for i in range(1, 8):
    col_idx = (i - 1) % 3
    with cols[col_idx]:
        st.subheader(f"버전 {i}")
        st.caption(version_info.get(f"버전 {i}", ""))
        
        music_file = f"{music_folder}/version_{i}.mp3"
        
        # 파일 존재 여부 확인
        if os.path.exists(music_file):
            with open(music_file, 'rb') as audio_file:
                audio_bytes = audio_file.read()
                st.audio(audio_bytes, format='audio/mp3')
        else:
            st.error(f"파일을 찾을 수 없습니다: {music_file}")

st.markdown("---")

# 선택 폼
st.header("📝 설문 참여")

col1, col2 = st.columns(2)

with col1:
    # 버전 선택
    selected_version = st.selectbox(
        "가장 선호하는 버전을 선택하세요",
        ["선택하세요"] + [f"버전 {i}" for i in range(1, 8)],
        key="version_select"
    )

with col2:
    # 연령대 선택
    age_group = st.selectbox(
        "연령대를 선택하세요",
        ["선택하세요", "10대", "20대", "30대", "40대", "50대 이상"],
        key="age_select"
    )

# 의견 입력란
comment = st.text_area(
    "의견이나 느낀 점을 남겨주세요 (선택사항)",
    placeholder="이 버전을 선택한 이유나 전체적인 느낌을 자유롭게 작성해주세요..."
)

st.markdown("---")

# 투표 버튼
if st.button("투표하기", type="primary", use_container_width=True):
    # 입력 검증
    if selected_version == "선택하세요":
        st.error("버전을 선택해주세요!")
    elif age_group == "선택하세요":
        st.error("연령대를 선택해주세요!")
    else:
        # 데이터 저장
        try:
            if worksheet:
                # 현재 시간
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Google Sheets에 데이터 추가
                row_data = [timestamp, selected_version, age_group, comment]
                worksheet.append_row(row_data)
                
                st.success("투표가 완료되었습니다! 감사합니다!")
                st.balloons()
                
                # 입력 필드 초기화를 위한 안내
                st.info("페이지를 새로고침하면 새로운 투표를 할 수 있습니다.")
                
            else:
                st.error("Google Sheets 연결이 없어 투표를 저장할 수 없습니다.")
                st.info("위의 에러 메시지를 확인하고 관리자에게 문의하세요.")
                
        except Exception as e:
            st.error(f"투표 저장 중 오류가 발생했습니다: {str(e)}")
            st.info("잠시 후 다시 시도해주세요.")

# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    <p>🌸 진달래꽃 음악 선호도 조사 | Made with Streamlit</p>
    <p>모든 응답은 익명으로 처리됩니다</p>
</div>
""", unsafe_allow_html=True)
