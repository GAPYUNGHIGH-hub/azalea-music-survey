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

# 세션 스테이트 초기화
if 'voted' not in st.session_state:
    st.session_state.voted = False
if 'selected_version' not in st.session_state:
    st.session_state.selected_version = None

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
        data = worksheet.get_all_values()
        
        if len(data) <= 1:  # 헤더만 있거나 데이터 없음
            return None
        
        # 첫 행을 헤더로 사용
        headers = data[0]
        rows = data[1:]
        
        df = pd.DataFrame(rows, columns=headers)
        
        # 빈 행 제거
        df = df[df.iloc[:, 0] != '']
        
        if len(df) == 0:
            return None
            
        return df
        
    except Exception as e:
        st.error(f"데이터 로딩 실패: {str(e)}")
        return None

# 곡 소개 정보 (수정 가능)
SONG_DESCRIPTIONS = """
### 🎵 일곱 가지 〈진달래꽃〉, 어떻게 다를까요?

**버전 1 - 클래식 피아노 반주**
정통 클래식의 우아함이 돋보이는 버전입니다. 피아노의 섬세한 터치가 시의 정서를 깊이 있게 전달합니다.

**버전 2 - 현대적 어레인지**
젊은 감성으로 재해석한 버전입니다. 전통 시에 현대적 사운드를 입혀 새로운 해석을 선보입니다.

**버전 3 - 오케스트라 버전**
웅장한 오케스트라가 만들어내는 감동입니다. 풍성한 사운드가 시의 깊이를 더합니다.

**버전 4 - 재즈 스타일**
즉흥적이고 자유로운 재즈의 감성으로 해석했습니다. 스윙 리듬이 시에 새로운 생명을 불어넣습니다.

**버전 5 - 보컬 중심**
아름다운 보컬이 중심이 되는 버전입니다. 가사 하나하나에 감정을 담아 전달합니다.

**버전 6 - 전통 국악 스타일**
우리 고유의 정서가 깊이 담긴 버전입니다. 전통 악기의 울림이 시의 본래 정서를 살립니다.

**버전 7 - 어쿠스틱 버전**
따뜻한 어쿠스틱 사운드가 매력적입니다. 소박하고 진솔한 감성이 마음을 울립니다.

---

**💡 김소월의 〈진달래꽃〉이 100년 가까이 사랑받는 이유**

이별의 아픔을 담담하게, 그러나 깊이 있게 표현한 이 시는 시대를 초월한 보편적 정서를 담고 있습니다. 
각 음악 버전은 이러한 정서를 각자의 방식으로 해석하며, 시에 새로운 생명을 불어넣고 있습니다.
"""

# Google Sheets 클라이언트 초기화
client, worksheet = get_google_sheets_client()

# 앱 제목
st.title("🌸 진달래꽃 음악 선호도 조사")

# 탭 생성
tab1, tab2 = st.tabs(["📝 설문 참여", "📊 통계 결과"])

# ===== 탭 1: 설문 참여 =====
with tab1:
    st.markdown("---")
    
    # 감성적인 안내 메시지
    st.markdown("""
    <div style='background: linear-gradient(135deg, #ffeef8 0%, #fff5f7 100%); 
                padding: 30px; 
                border-radius: 15px; 
                border-left: 5px solid #ff69b4;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                margin-bottom: 30px;'>
        <h3 style='color: #d63384; margin-top: 0;'>🌸 김소월 〈진달래꽃〉은 왜 100년 가까이 다양한 음악으로 다시 태어났을까요?</h3>
        <p style='font-size: 1.1em; line-height: 1.8; color: #495057; margin-bottom: 20px;'>
            이 궁금증을 함께 탐구하기 위해 여러분의 소중한 의견을 듣고자 합니다.<br>
            일곱 곡을 들어보신 뒤, <strong>가장 마음에 닿은 버전을 선택</strong>하고 <strong>한 줄 감상</strong>을 남겨주세요.
        </p>
        <p style='font-size: 0.95em; color: #6c757d; margin-bottom: 0;'>
            <em>💡 응답은 학습 탐구 목적에만 사용됩니다.</em>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 제목
    st.header("🎵 일곱 가지 버전을 들어보세요")
    
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
    st.header("📝 당신의 선택을 들려주세요")
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_version = st.selectbox(
            "💝 가장 마음에 닿은 버전",
            ["선택하세요"] + [f"버전 {i}" for i in range(1, 8)],
            key="version_select"
        )
    
    with col2:
        age_group = st.selectbox(
            "👤 연령대",
            ["선택하세요", "10대", "20대", "30대", "40대", "50대 이상"],
            key="age_select"
        )
    
    # 의견 입력란
    comment = st.text_area(
        "✍️ 한 줄 감상을 남겨주세요",
        placeholder="이 버전을 선택한 이유, 느낌, 떠오른 생각 등을 자유롭게 작성해주세요...",
        height=100
    )
    
    # 다른 사람들의 의견 실시간 표시
    st.markdown("---")
    st.subheader("💬 다른 참여자들의 감상")
    
    if worksheet:
        df = get_survey_data(worksheet)
        if df is not None and len(df) > 0:
            # 컬럼명 확인 (첫 4개 컬럼 사용)
            cols_list = df.columns.tolist()
            if len(cols_list) >= 4:
                comment_col = cols_list[3]  # 4번째 컬럼 (의견)
                version_col = cols_list[1]  # 2번째 컬럼 (선택한 버전)
                
                # 의견이 있는 데이터만 필터링
                recent_data = df[df[comment_col].notna() & (df[comment_col] != '')]
                
                if len(recent_data) > 0:
                    # 최근 5개 의견 표시
                    recent_comments = recent_data.tail(5)
                    
                    for idx, row in recent_comments.iterrows():
                        version = row[version_col]
                        comment_text = row[comment_col]
                        
                        if comment_text and str(comment_text).strip():
                            st.info(f"**{version}** 💭 {comment_text}")
                else:
                    st.info("아직 등록된 감상이 없습니다. 첫 번째가 되어주세요! 🌟")
        else:
            st.info("아직 등록된 감상이 없습니다. 첫 번째가 되어주세요! 🌟")
    
    st.markdown("---")
    
    # 투표 버튼
    if st.button("🗳️ 투표하기", type="primary", use_container_width=True):
        if selected_version == "선택하세요":
            st.error("💝 버전을 선택해주세요!")
        elif age_group == "선택하세요":
            st.error("👤 연령대를 선택해주세요!")
        elif not comment or not comment.strip():
            st.error("✍️ 한 줄 감상을 작성해주세요!")
        else:
            try:
                if worksheet:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    row_data = [timestamp, selected_version, age_group, comment]
                    worksheet.append_row(row_data)
                    
                    st.success("✅ 투표가 완료되었습니다! 감사합니다!")
                    st.balloons()
                    
                    # 세션 스테이트 업데이트
                    st.session_state.voted = True
                    st.session_state.selected_version = selected_version
                    
                    st.info("💡 아래에서 일곱 가지 버전에 대한 자세한 설명을 확인하세요!")
                else:
                    st.error("Google Sheets 연결이 없어 투표를 저장할 수 없습니다.")
                    
            except Exception as e:
                st.error(f"투표 저장 중 오류가 발생했습니다: {str(e)}")
    
    # 투표 완료 후 곡 소개 표시 (보상)
    if st.session_state.voted:
        st.markdown("---")
        st.markdown("""
        <div style='background: linear-gradient(135deg, #fff8e1 0%, #fffbf0 100%); 
                    padding: 20px; 
                    border-radius: 10px; 
                    border-left: 5px solid #ffc107;
                    margin-top: 30px;'>
            <h3 style='color: #f57c00; margin-top: 0;'>🎁 투표 감사 선물</h3>
            <p style='color: #6c757d;'>일곱 가지 버전에 대한 자세한 해설을 확인하세요!</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(SONG_DESCRIPTIONS)

# ===== 탭 2: 통계 결과 =====
with tab2:
    st.markdown("---")
    st.header("📊 실시간 투표 통계")
    
    if worksheet:
        df = get_survey_data(worksheet)
        
        if df is not None and len(df) > 0:
            # 컬럼명 가져오기
            cols_list = df.columns.tolist()
            
            if len(cols_list) >= 3:
                version_col = cols_list[1]  # 2번째 컬럼 (선택한 버전)
                age_col = cols_list[2]      # 3번째 컬럼 (연령대)
                comment_col = cols_list[3] if len(cols_list) >= 4 else None  # 4번째 컬럼 (의견)
                
                # 총 투표 수
                total_votes = len(df)
                st.metric("총 투표 수", f"{total_votes}표")
                
                st.markdown("---")
                
                # 두 개의 컬럼으로 나누기
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🎵 버전별 득표 현황")
                    
                    # 버전별 득표수 계산
                    version_counts = df[version_col].value_counts().sort_index()
                    
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
                    age_version_crosstab = pd.crosstab(df[age_col], df[version_col])
                    
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
                    age_counts = df[age_col].value_counts()
                    for age, count in age_counts.items():
                        percentage = (count / total_votes) * 100
                        st.write(f"{age}: {count}명 ({percentage:.1f}%)")
                
                st.markdown("---")
                
                # 최다 득표 버전
                most_voted = version_counts.idxmax()
                most_votes = version_counts.max()
                st.success(f"🏆 현재 1위: **{most_voted}** ({most_votes}표)")
                
                # 최근 의견
                if comment_col and comment_col in df.columns:
                    st.markdown("---")
                    st.subheader("💬 최근 참여자 감상")
                    recent_comments_df = df[df[comment_col].notna() & (df[comment_col] != '')]
                    
                    if len(recent_comments_df) > 0:
                        recent_comments = recent_comments_df.tail(10)
                        for idx, row in recent_comments.iterrows():
                            version = row[version_col]
                            comment_text = row[comment_col]
                            if comment_text and str(comment_text).strip():
                                st.info(f"**{version}** 💭 {comment_text}")
                    else:
                        st.info("아직 등록된 감상이 없습니다.")
            else:
                st.error("Google Sheets의 컬럼 구조를 확인해주세요.")
        else:
            st.info("아직 투표 데이터가 없습니다. 첫 번째 투표자가 되어주세요!")
    else:
        st.warning("Google Sheets 연결이 필요합니다.")

# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em; padding: 20px;'>
    <p>🌸 진달래꽃 음악 선호도 조사</p>
    <p style='font-size: 0.85em; color: #aaa;'>모든 응답은 익명으로 처리되며 학습 탐구 목적으로만 사용됩니다</p>
    <p style='margin-top: 15px;'><strong style='color: #d63384; font-size: 1.1em;'>기획 및 제작: 남소영</strong></p>
</div>
""", unsafe_allow_html=True)
