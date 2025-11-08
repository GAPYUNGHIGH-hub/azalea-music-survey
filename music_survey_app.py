import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import os
import json
import plotly.express as px
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(
    page_title="진달래꽃 음악 설문조사",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Google Sheets 연결 설정
@st.cache_resource
def get_google_sheets_client():
    """Google Sheets 클라이언트를 생성하고 반환합니다."""
    try:
        credentials_json = os.environ.get('GOOGLE_CREDENTIALS')
        spreadsheet_id = os.environ.get('SPREADSHEET_ID')
        
        if not credentials_json or not spreadsheet_id:
            return None, None
        
        credentials_dict = json.loads(credentials_json)
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            credentials_dict, 
            scope
        )
        
        client = gspread.authorize(credentials)
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.sheet1
        
        return client, worksheet
        
    except Exception as e:
        st.error(f"Google Sheets 연결 실패: {str(e)}")
        return None, None

# Google Sheets에서 데이터 가져오기
def get_survey_data(worksheet):
    """Google Sheets에서 설문 데이터를 가져와 DataFrame으로 반환합니다."""
    try:
        if worksheet is None:
            return None
        
        # 모든 데이터 가져오기
        data = worksheet.get_all_records()
        
        if not data:
            return None
        
        df = pd.DataFrame(data)
        return df
        
    except Exception as e:
        st.error(f"데이터 로딩 실패: {str(e)}")
        return None

# 곡 소개 정보
SONG_DESCRIPTIONS = {
    "버전 1": {
        "title": "버전 1 - 클래식 피아노 반주",
        "description": """
        전통적인 클래식 스타일의 피아노 반주가 돋보이는 버전입니다.
        
        **특징:**
        - 🎹 우아한 피아노 멜로디
        - 🎼 정통 클래식 편곡
        - 💎 절제되고 품격 있는 표현
        
        **어울리는 상황:**
        조용한 오후, 독서할 때, 차분한 분위기를 원할 때
        """
    },
    "버전 2": {
        "title": "버전 2 - 현대적 어레인지",
        "description": """
        현대적 감각이 돋보이는 세련된 편곡 버전입니다.
        
        **특징:**
        - 🎸 현대적인 악기 편성
        - 🎵 젊은 감성의 멜로디 라인
        - ✨ 신선하고 참신한 해석
        
        **어울리는 상황:**
        카페에서, 드라이브할 때, 활기찬 분위기
        """
    },
    "버전 3": {
        "title": "버전 3 - 오케스트라 버전",
        "description": """
        웅장한 오케스트라 편성으로 장엄함을 더한 버전입니다.
        
        **특징:**
        - 🎻 풍성한 현악 앙상블
        - 🎺 웅장한 관악기 하모니
        - 🎼 드라마틱한 다이내믹
        
        **어울리는 상황:**
        감동적인 순간, 특별한 기념일, 영화 같은 분위기
        """
    },
    "버전 4": {
        "title": "버전 4 - 재즈 스타일",
        "description": """
        즉흥적이고 자유로운 재즈 감성이 담긴 버전입니다.
        
        **특징:**
        - 🎺 즉흥적인 솔로 연주
        - 🥁 스윙감 넘치는 리듬
        - 🎷 자유롭고 세련된 해석
        
        **어울리는 상황:**
        재즈바에서, 저녁 시간, 여유로운 주말
        """
    },
    "버전 5": {
        "title": "버전 5 - 보컬 중심",
        "description": """
        아름다운 보컬이 중심이 되는 감성적인 버전입니다.
        
        **특징:**
        - 🎤 섬세한 보컬 표현
        - 💝 감성적인 가사 전달
        - 🌟 진심이 느껴지는 해석
        
        **어울리는 상황:**
        혼자 있는 시간, 감정에 젖고 싶을 때, 조용한 밤
        """
    },
    "버전 6": {
        "title": "버전 6 - 전통 국악 스타일",
        "description": """
        우리 고유의 정서가 담긴 전통 국악 버전입니다.
        
        **특징:**
        - 🎼 전통 악기의 깊은 울림
        - 🏯 한국적 정서와 멋
        - 🌸 진달래꽃의 본래 의미 강조
        
        **어울리는 상황:**
        전통 문화를 느끼고 싶을 때, 명절, 차분한 명상
        """
    },
    "버전 7": {
        "title": "버전 7 - 어쿠스틱 버전",
        "description": """
        따뜻한 어쿠스틱 사운드가 매력적인 버전입니다.
        
        **특징:**
        - 🎸 따뜻한 어쿠스틱 기타
        - 🍂 소박하고 진솔한 느낌
        - 💫 자연스러운 감성
        
        **어울리는 상황:**
        캠핑장에서, 친구들과 함께, 편안한 일상
        """
    }
}

# Google Sheets 클라이언트 초기화
client, worksheet = get_google_sheets_client()

# 앱 제목
st.title("🌸 진달래꽃 음악 선호도 조사")

# 탭 생성
tab1, tab2, tab3 = st.tabs(["📝 설문 참여", "📊 통계 결과", "ℹ️ 곡 소개"])

# ===== 탭 1: 설문 참여 =====
with tab1:
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
        selected_version = st.selectbox(
            "가장 선호하는 버전을 선택하세요",
            ["선택하세요"] + [f"버전 {i}" for i in range(1, 8)],
            key="version_select"
        )
    
    with col2:
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
        if selected_version == "선택하세요":
            st.error("버전을 선택해주세요!")
        elif age_group == "선택하세요":
            st.error("연령대를 선택해주세요!")
        else:
            try:
                if worksheet:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    row_data = [timestamp, selected_version, age_group, comment]
                    worksheet.append_row(row_data)
                    
                    st.success("투표가 완료되었습니다! 감사합니다!")
                    st.balloons()
                    
                    st.info("💡 '곡 소개' 탭에서 각 버전에 대한 자세한 설명을 확인하세요!")
                    
                    # 투표한 버전의 소개 표시
                    if selected_version in SONG_DESCRIPTIONS:
                        st.markdown("---")
                        st.subheader(f"🎵 {selected_version} 소개")
                        song_info = SONG_DESCRIPTIONS[selected_version]
                        st.markdown(song_info["description"])
                else:
                    st.error("Google Sheets 연결이 없어 투표를 저장할 수 없습니다.")
                    
            except Exception as e:
                st.error(f"투표 저장 중 오류가 발생했습니다: {str(e)}")

# ===== 탭 2: 통계 결과 =====
with tab2:
    st.markdown("---")
    st.header("📊 실시간 투표 통계")
    
    if worksheet:
        df = get_survey_data(worksheet)
        
        if df is not None and len(df) > 0:
            # 총 투표 수
            total_votes = len(df)
            st.metric("총 투표 수", f"{total_votes}표")
            
            st.markdown("---")
            
            # 두 개의 컬럼으로 나누기
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🎵 버전별 득표 현황")
                
                # 버전별 득표수 계산
                version_counts = df['선택한 버전'].value_counts().sort_index()
                
                # 막대 그래프
                fig1 = px.bar(
                    x=version_counts.index,
                    y=version_counts.values,
                    labels={'x': '버전', 'y': '득표수'},
                    title='버전별 득표수',
                    color=version_counts.values,
                    color_continuous_scale='Viridis'
                )
                fig1.update_layout(showlegend=False)
                st.plotly_chart(fig1, use_container_width=True)
                
                # 득표율 표시
                st.markdown("#### 득표율")
                for version, count in version_counts.items():
                    percentage = (count / total_votes) * 100
                    st.progress(percentage / 100)
                    st.write(f"{version}: {count}표 ({percentage:.1f}%)")
            
            with col2:
                st.subheader("👥 연령대별 선호도")
                
                # 연령대별 버전 선호도
                age_version_crosstab = pd.crosstab(df['연령대'], df['선택한 버전'])
                
                # 히트맵
                fig2 = px.imshow(
                    age_version_crosstab,
                    labels=dict(x="버전", y="연령대", color="득표수"),
                    title='연령대별 버전 선호도',
                    color_continuous_scale='Blues',
                    aspect='auto'
                )
                st.plotly_chart(fig2, use_container_width=True)
                
                # 연령대별 투표 수
                st.markdown("#### 연령대별 참여 현황")
                age_counts = df['연령대'].value_counts()
                for age, count in age_counts.items():
                    percentage = (count / total_votes) * 100
                    st.write(f"{age}: {count}명 ({percentage:.1f}%)")
            
            st.markdown("---")
            
            # 최다 득표 버전
            most_voted = version_counts.idxmax()
            most_votes = version_counts.max()
            st.success(f"🏆 현재 1위: **{most_voted}** ({most_votes}표)")
            
            # 최근 의견
            if '의견' in df.columns and not df['의견'].isna().all():
                st.markdown("---")
                st.subheader("💬 최근 참여자 의견")
                recent_comments = df[df['의견'].notna()]['의견'].tail(5).tolist()
                for i, comment in enumerate(reversed(recent_comments), 1):
                    if comment and str(comment).strip():
                        st.info(f"💭 {comment}")
        else:
            st.info("아직 투표 데이터가 없습니다. 첫 번째 투표자가 되어주세요!")
    else:
        st.warning("Google Sheets 연결이 필요합니다.")

# ===== 탭 3: 곡 소개 =====
with tab3:
    st.markdown("---")
    st.header("🎵 7가지 버전 소개")
    
    st.markdown("""
    진달래꽃을 다양한 스타일로 재해석한 7가지 버전을 소개합니다.
    각 버전마다 독특한 매력과 감성이 담겨 있으니, 자세히 읽어보시고 투표해주세요!
    """)
    
    st.markdown("---")
    
    # 각 버전의 상세 소개
    for i in range(1, 8):
        version_key = f"버전 {i}"
        if version_key in SONG_DESCRIPTIONS:
            song_info = SONG_DESCRIPTIONS[version_key]
            
            with st.expander(f"🎵 {song_info['title']}", expanded=(i == 1)):
                st.markdown(song_info['description'])
                
                # 해당 버전 다시 듣기
                music_file = f"music_files/version_{i}.mp3"
                if os.path.exists(music_file):
                    with open(music_file, 'rb') as audio_file:
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format='audio/mp3')
            
            if i < 7:
                st.markdown("---")

# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    <p>🌸 진달래꽃 음악 선호도 조사 | Made with Streamlit</p>
    <p>모든 응답은 익명으로 처리됩니다</p>
    <p><strong>기획 및 제작: 남소영</strong></p>
</div>
""", unsafe_allow_html=True)
