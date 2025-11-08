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
        
        data = worksheet.get_all_values()
        
        if len(data) <= 1:
            return None
        
        headers = data[0]
        rows = data[1:]
        
        clean_headers = []
        for i, h in enumerate(headers):
            if h.strip() == '':
                clean_headers.append(f'미사용{i}')
            else:
                clean_headers.append(h.strip())
        
        seen = {}
        final_headers = []
        for h in clean_headers:
            if h in seen:
                seen[h] += 1
                final_headers.append(f"{h}_{seen[h]}")
            else:
                seen[h] = 0
                final_headers.append(h)
        
        if len(final_headers) > 4:
            final_headers = final_headers[:4]
            rows = [row[:4] for row in rows]
        
        df = pd.DataFrame(rows, columns=final_headers)
        df = df[df.iloc[:, 0].astype(str).str.strip() != '']
        
        if len(df) == 0:
            return None
            
        return df
        
    except Exception as e:
        st.error(f"데이터 로딩 실패: {str(e)}")
        return None

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
    
    # 버전 정보 (작곡가 포함)
    version_info = {
        "버전 1",
        "버전 2",
        "버전 3",
        "버전 4",
        "버전 5",
        "버전 6",
        "버전 7"
    }
    
    # 3개씩 컬럼으로 배치
    cols = st.columns(3)
    
    for i in range(1, 8):
        col_idx = (i - 1) % 3
        with cols[col_idx]:
            st.subheader(f"버전 {i}")
            info = version_info.get(f"버전 {i}", {})
            st.caption(f"**{info.get('composer', '')}**")
            st.caption(info.get('style', ''))
            
            music_file = f"{music_folder}/version_{i}.mp3"
            
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
            if len(df.columns) >= 4:
                comment_col = df.columns[3]
                version_col = df.columns[1]
                
                comment_data = df[comment_col].astype(str).str.strip()
                recent_data = df[(comment_data != '') & (comment_data != 'nan')]
                
                if len(recent_data) > 0:
                    display_count = min(5, len(recent_data))
                    recent_comments = recent_data.tail(display_count)
                    
                    for idx in recent_comments.index:
                        version = recent_comments.loc[idx, version_col]
                        comment_text = recent_comments.loc[idx, comment_col]
                        
                        if comment_text and str(comment_text).strip() and str(comment_text) != 'nan':
                            st.info(f"**{version}** 💭 {comment_text}")
                else:
                    st.info("아직 등록된 감상이 없습니다. 첫 번째가 되어주세요! 🌟")
            else:
                st.warning("데이터 구조를 확인 중입니다...")
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
                    
                    st.session_state.voted = True
                    st.session_state.selected_version = selected_version
                    
                    st.info("💡 아래에서 김소월 시인과 일곱 작곡가에 대한 자세한 이야기를 확인하세요!")
                else:
                    st.error("Google Sheets 연결이 없어 투표를 저장할 수 없습니다.")
                    
            except Exception as e:
                st.error(f"투표 저장 중 오류가 발생했습니다: {str(e)}")
    
    # 투표 완료 후 상세 정보 표시
    if st.session_state.voted:
        st.markdown("---")
        st.markdown("""
        <div style='background: linear-gradient(135deg, #fff8e1 0%, #fffbf0 100%); 
                    padding: 20px; 
                    border-radius: 10px; 
                    border-left: 5px solid #ffc107;
                    margin-top: 30px;'>
            <h3 style='color: #f57c00; margin-top: 0;'>🎁 투표 감사 선물</h3>
            <p style='color: #6c757d;'>김소월 시인과 일곱 작곡가의 이야기를 만나보세요!</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 8개 탭으로 구성
        reward_tabs = st.tabs([
            "🌸 김소월",
            "🎹 버전1",
            "🎼 버전2", 
            "🎹 버전3",
            "🎵 버전4",
            "🤘 버전5",
            "🎸 버전6",
            "🎤 버전7"
        ])
        
        # 탭 1: 김소월 시인
        with reward_tabs[0]:
            st.markdown("""
            ### 🌸 작시자 김소월 (金素月, 1902~1934)
            
            **본명:** 김정식  
            **출생:** 평안북도 구성
            
            #### 생애
            남산학교를 거쳐 오산학교 중학부에 다니던 중 3·1운동 직후 한때 퇴교가 되어, 
            배재고등보통학교에 입학하여 졸업하였습니다. 일본 도쿄산과대학 전문부에 입학하였으나 
            곧 관동대지진으로 중퇴하고 귀국했습니다.
            
            귀국 후 할아버지가 경영하는 광산 일을 도우며 고생했으나, 광산업의 실패로 가세가 크게 
            기울어졌습니다. 그 후 작품 활동은 저조했으며 생활고가 겹쳐서 생에 대한 의욕을 잃었고, 
            1934년 고향 곡산에서 32세의 나이에 세상을 떠났습니다.
            
            ---
            
            ### 💔 "여인의 한(恨)" - 진달래꽃을 짓게 된 사연
            
            소월에게는 어렸을 때부터 따르던 숙모(계희영)가 있었습니다. 숙모는 80세에 
            『내가 기른 소월』(장문각, 1969)이라는 책을 남겼는데, 이 책에서 진달래꽃의 
            창작 배경을 밝혔습니다.
            
            #### 이야기의 시작
            소월의 외삼촌 경삼은 9살 때 7년이나 연상의 처녀에게 장가를 갔습니다. 
            일본 유학을 간 사이, 부인은 남편 없는 시집에서 낮에는 농사를 짓고 
            밤에는 베를 짜서 달마다 학비를 보내주었습니다.
            
            15년이 지나 남편이 귀국하여 신의주의 고보에 교사로 취직했지만, 
            젊은 여인과 새 살림을 차렸다는 소문이 들려왔습니다.
            
            소월의 어머니가 확인하러 갔지만, 동생은 "그런 말씀 하시려거든 내 집에 
            다시는 오지 마세요"라며 귀담아 듣지 않았습니다.
            
            #### 진달래꽃의 탄생
            본부인은 원망도 하지 않고 잠잠히 시집에서 며느리의 도리를 다하면서 
            남편이 돌아오기만 기다렸습니다.
            
            **숙모 계희영 씨는 그 책에서, 원망도 미움도 모르고 진정으로 남편을 사랑하는 
            본부인의 마음이 너무나 고와서 소월이 시를 한편 썼는데, 그게 바로 
            〈진달래꽃〉이었다고 했습니다.**
            
            소월의 외삼촌 경삼은 본부인을 버린 후 일 년이 못 되어 세상을 떠났다고 합니다.
            """)
        
        # 탭 2: 버전 1 - 김동진
        with reward_tabs[1]:
            st.markdown("""
            ### 🎹 버전 1 - 김동진 작곡 (1954년)
            
            **작곡가:** 김동진 (1913~2009)  
            **출생:** 평남 안주  
            **장르:** 클래식 가곡
            
            #### 작곡가 소개
            평양 숭실 전문학교 영문과를 졸업하고, 일본 고등음악학교 기악과를 졸업했습니다. 
            평양의 중앙 교향악단과 합창단 지휘자로 근무했으며, 1954년 초대 예술원 회원이 되었습니다. 
            신창악 운동의 선구자이며, 경희대학교 음대 교수 및 합창단을 역임했습니다.
            
            #### 곡의 탄생 배경
            1954년 작곡가는 영화음악과 씨름하고 있었는데, 김소월의 생애를 영화화할 때 
            제작측의 위촉으로 이 곡을 만들게 되었습니다.
            
            1959년 영화 "사노라면 잊을 날이 있으오리다" 제작을 계획했으나 중단되었고, 
            1962년 전응주 감독이 김진규, 최은희, 도금봉, 허장강 등과 소월의 일대기를 
            극화한 픽션 "불러도 대답없는 이름이요"를 제작·발표했습니다. 
            김동진의 곡은 이 영화의 삽입곡으로 사용되었습니다.
            
            #### 대표작
            - 교향시 『제레악』
            - 칸타타 『승리의 길』, 『조국』
            - 가곡 『신청전』, 『봄이 오면』, 『가고파』, 『내 마음』 등
            """)
        
        # 탭 3: 버전 2 - 김달성
        with reward_tabs[2]:
            st.markdown("""
            ### 🎼 버전 2 - 김달성 작곡
            
            **작곡가:** 김달성 (1921~2010)  
            **출생:** 함경북도 함흥  
            **장르:** 현대 예술가곡
            
            #### 학력 및 경력
            - 함흥사범학교 졸업
            - 1951년 서울대학교 음악대학 작곡과 졸업
            - 1961년 오스트리아 빈국립음악대학 작곡·현대음악과 졸업
            - 한양대학교·서울대학교 교수 역임
            - 단국대학교 교수 및 예술대 학장 역임
            - 한국음악협회 이사, 한국음악학회 부회장 역임
            
            #### 작곡 세계
            김소월, 김영랑, 윤동주, 서정주 등 한국 대표 시인들의 작품에 곡을 붙여 
            수많은 예술 가곡을 작곡했습니다.
            
            #### 수상
            이러한 공로를 인정받아 삼일문화상, 보관문화훈장을 받았습니다.
            """)
        
        # 탭 4: 버전 3 - 김순남
        with reward_tabs[3]:
            st.markdown("""
            ### 🎹 버전 3 - 김순남 작곡 (1940년대)
            
            **작곡가:** 김순남 (1917~1983)  
            **본명:** 김혁명  
            **출생:** 서울  
            **장르:** 민족주의 노선
            
            #### 학력
            일본의 동경국립음악학교를 중퇴하고 동경제국음악학교를 졸업했습니다. 
            당시 스승 중 하나는 창작에서 민족주의 노선을 취하면서 동시에 사회주의 사상에 
            경도되어 있던 인물이었습니다. 김순남의 작곡 성향도 강한 영향을 받았습니다.
            
            #### 데뷔
            1943년 당시 일본의 금지 작곡가 그룹인 신흥작곡가 연맹의 5주년 기념음악제에서 
            피아노 소나타를 발표하면서 데뷔했습니다.
            
            #### 활동
            1945년 이후에는 남로당에 가입하여 "인민항쟁가" 등을 작곡했고, 
            윤이상, 나운영, 김희조, 장일남 등에게 영향을 주었으며, 
            민중음악 구사나 기법 등을 개발했습니다.
            
            #### 말년
            결핵에 걸리면서 창작을 포기해야 했고, 평양과 함흥 등지로 옮겨 다니며 
            오랫동안 투병 생활을 했습니다. 1970년대 이후에는 북한의 공식 출판물에서도 
            이름이 거의 언급되지 않게 되었고, 1983년경 신포에서 세상을 떠난 것으로 추정됩니다.
            """)
        
        # 탭 5: 버전 4 - 윤학준
        with reward_tabs[4]:
            st.markdown("""
            ### 🎵 버전 4 - 윤학준 작곡
            
            **작곡가:** 윤학준  
            **현직:** 충청북도교육문화원 교육연구사  
            **장르:** 합창곡
            
            #### 대표작
            - 한국 가곡 **『마중』** - 성악가들의 필수 레퍼토리
            - 합창곡 **『진달래꽃』**
            - 성가합창곡 **『내 맘에 한 노래 있어』**
            - 동요 **『꼭 안아줄래요』**
            
            #### 경력
            과거 초등학교 교사로도 활동했으며, 따뜻하고 감성적인 선율로 
            많은 사랑을 받고 있습니다.
            """)
        
        # 탭 6: 버전 5 - 노바소닉
        with reward_tabs[5]:
            st.markdown("""
            ### 🤘 버전 5 - 김진표 작곡, 노바소닉 (1999년)
            
            **작곡가:** 김진표  
            **밴드:** 노바소닉 (NOVASONIC)  
            **발표:** 1999년 첫 정규앨범  
            **장르:** 뉴메탈, 헤비메탈, 하드록
            
            #### 노바소닉 소개
            대한민국의 뉴메탈 밴드입니다. N.EX.T의 기타리스트이기도 했던 김세황을 주축으로 
            김영석, 이수용으로 결성되었고, 패닉의 멤버이기도 했던 김진표를 영입하여 
            1999년 첫 번째 정규앨범을 냈습니다.
            
            #### 음악적 특징
            - 김진표의 날카로운 래핑
            - 헤비메탈과 하드록에 중점을 준 사운드
            - 김세황의 독특한 리듬을 구사하는 기타 플레이
            
            #### 〈진달래꽃〉의 재해석
            작곡가 김진표가 '진달래꽃' 곡을 만들어 노바소닉에게 부르게 했습니다. 
            노래 가사가 시의 원본과 달리 많이 변형되었는데, 시대가 변하고 노래의 유형도 
            변하면서 일어나는 자연스러운 현상입니다.
            
            **전통 시를 현대적 록 사운드로 재해석한 파격적인 시도였습니다.**
            """)
        
        # 탭 7: 버전 6 - 마야
        with reward_tabs[6]:
            st.markdown("""
            ### 🎸 버전 6 - 우지민 작곡, 마야 (2003년)
            
            **작곡가:** 우지민  
            **가수:** 마야  
            **발표:** 2003년  
            **장르:** 록 발라드
            
            #### 곡의 특징
            김소월의 동명 시를 바탕으로 만들어진 이 노래는 애절한 이별의 정서를 
            **강렬한 록 사운드**와 **마야의 힘 있는 목소리**로 표현해 큰 사랑을 받았으며, 
            마야의 대표곡 중 하나입니다.
            
            #### 음악적 해석
            마야의 '진달래꽃'은 김소월 시의 서정적 감성과 민족적 '한(恨)'을 
            현대적으로 재해석한 록 발라드입니다.
            
            - **원작 시:** 절제된 슬픔
            - **노래:** 감정을 직설적으로 표현
            
            청자에게 깊은 울림을 주며, 실제로 **교과서에도 실릴 만큼** 
            대중성과 예술성을 인정받았습니다.
            
            #### 평가
            마야의 시원한 가창력과 곡의 드라마틱한 편곡이 돋보이는 작품입니다.
            """)
        
        # 탭 8: 버전 7 - 윤상/정훈희
        with reward_tabs[7]:
            st.markdown("""
            ### 🎤 버전 7 - 윤상 작곡, 정훈희 노래 (2002년)
            
            **작곡가:** 윤상  
            **가수:** 정훈희  
            **곡명:** 『소월에게 묻기를』  
            **수록:** 윤상 4집 앨범 『이사』(2002년)  
            **장르:** 세련된 발라드
            
            #### 곡의 탄생
            이 곡은 김소월의 시 '진달래꽃'을 모티브로 삼아, 시 속 화자의 순수한 이별 감정에 
            윤상 특유의 섬세하면서도 세련된 멜로디와 감성을 더했습니다.
            
            #### 가사의 의미
            『소월에게 묻기를』은 원시의 구절 **"나 보기가 역겨워 가실 때에는 
            말없이 고이 보내 드리우리다"**에서 출발하여, 남겨진 자의 고통, 
            이해되지 않는 이별의 이유에 대해 김소월 시인에게 직접 묻는 형식을 취하고 있습니다.
            
            #### 윤상의 선택
            윤상은 이 곡의 감정을 스스로 소화하기 어렵다고 판단해 
            선배 가수 **정훈희**에게 노래를 부탁했으며, 정훈희의 목소리가 
            곡의 깊이와 슬픔을 더욱 섬세하게 드러내 줍니다.
            
            #### 곡의 정서
            곡 전반에는 **절제, 상실, 그리고 세월을 견디는 성숙한 사랑과 이별의 한**이 
            담겨 있으며, 비슷한 테마의 '진달래꽃'과 비교해 한층 더 내면의 갈등과 
            슬픔을 탐구하는 곡입니다.
            """)

# ===== 탭 2: 통계 결과 =====
with tab2:
    st.markdown("---")
    st.header("📊 실시간 투표 통계")
    
    if worksheet:
        df = get_survey_data(worksheet)
        
        if df is not None and len(df) > 0:
            if len(df.columns) >= 3:
                version_col = df.columns[1]
                age_col = df.columns[2]
                comment_col = df.columns[3] if len(df.columns) >= 4 else None
                
                total_votes = len(df)
                st.metric("총 투표 수", f"{total_votes}표")
                
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🎵 버전별 득표 현황")
                    
                    version_counts = df[version_col].value_counts().sort_index()
                    
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
                    
                    st.markdown("#### 득표율")
                    for version, count in version_counts.items():
                        percentage = (count / total_votes) * 100
                        st.progress(percentage / 100)
                        st.write(f"{version}: {count}표 ({percentage:.1f}%)")
                
                with col2:
                    st.subheader("👥 연령대별 선호도")
                    
                    age_version_crosstab = pd.crosstab(df[age_col], df[version_col])
                    
                    fig2 = px.imshow(
                        age_version_crosstab,
                        labels=dict(x="버전", y="연령대", color="득표수"),
                        title='연령대별 버전 선호도',
                        color_continuous_scale='Blues',
                        aspect='auto'
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                    
                    st.markdown("#### 연령대별 참여 현황")
                    age_counts = df[age_col].value_counts()
                    for age, count in age_counts.items():
                        percentage = (count / total_votes) * 100
                        st.write(f"{age}: {count}명 ({percentage:.1f}%)")
                
                st.markdown("---")
                
                most_voted = version_counts.idxmax()
                most_votes = version_counts.max()
                st.success(f"🏆 현재 1위: **{most_voted}** ({most_votes}표)")
                
                if comment_col:
                    st.markdown("---")
                    st.subheader("💬 최근 참여자 감상")
                    
                    comment_data = df[comment_col].astype(str).str.strip()
                    recent_comments_df = df[(comment_data != '') & (comment_data != 'nan')]
                    
                    if len(recent_comments_df) > 0:
                        display_count = min(10, len(recent_comments_df))
                        recent_comments = recent_comments_df.tail(display_count)
                        
                        for idx in recent_comments.index:
                            version = recent_comments.loc[idx, version_col]
                            comment_text = recent_comments.loc[idx, comment_col]
                            if comment_text and str(comment_text).strip() and str(comment_text) != 'nan':
                                st.info(f"**{version}** 💭 {comment_text}")
                    else:
                        st.info("아직 등록된 감상이 없습니다.")
            else:
                st.error("데이터 컬럼이 부족합니다. Google Sheets를 확인해주세요.")
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
