"""
진달래꽃 음악 선호도 조사 앱 (Google Sheets 연동 버전)
데이터를 Google Sheets에 영구 저장합니다.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(
    page_title="진달래꽃 음악 선호도 조사",
    page_icon="🌸",
    layout="wide"
)

# Google Sheets 연동 여부 확인
USE_GOOGLE_SHEETS = False
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    import json
    
    # Streamlit Secrets에서 자격증명 가져오기
    if "gcp_service_account" in st.secrets:
        USE_GOOGLE_SHEETS = True
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        SPREADSHEET_ID = st.secrets.get("spreadsheet_id", "")
except Exception as e:
    st.warning(f"Google Sheets 연동이 비활성화되었습니다. 로컬 저장소를 사용합니다.")
    USE_GOOGLE_SHEETS = False

# Google Sheets 함수들
def append_to_sheets(age_group, preferred_version):
    """Google Sheets에 데이터 추가"""
    try:
        service = build('sheets', 'v4', credentials=credentials)
        sheet = service.spreadsheets()
        
        values = [[
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            age_group,
            str(preferred_version)
        ]]
        
        body = {'values': values}
        
        result = sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range='응답!A:C',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        return True
    except Exception as e:
        st.error(f"Google Sheets 저장 실패: {str(e)}")
        return False

def read_from_sheets():
    """Google Sheets에서 데이터 읽기"""
    try:
        service = build('sheets', 'v4', credentials=credentials)
        sheet = service.spreadsheets()
        
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='응답!A2:C'  # 헤더 제외
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            return pd.DataFrame(columns=['timestamp', 'age_group', 'preferred_version'])
        
        df = pd.DataFrame(values, columns=['timestamp', 'age_group', 'preferred_version'])
        df['preferred_version'] = pd.to_numeric(df['preferred_version'])
        
        return df
    except Exception as e:
        st.error(f"Google Sheets 읽기 실패: {str(e)}")
        return pd.DataFrame(columns=['timestamp', 'age_group', 'preferred_version'])

# 로컬 저장소 함수들 (fallback)
def init_local_storage():
    """세션 상태에 로컬 저장소 초기화"""
    if 'responses' not in st.session_state:
        st.session_state.responses = []

def save_local_response(age_group, preferred_version):
    """세션 상태에 응답 저장"""
    if 'responses' not in st.session_state:
        st.session_state.responses = []
    
    st.session_state.responses.append({
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'age_group': age_group,
        'preferred_version': preferred_version
    })

def get_local_responses():
    """세션 상태에서 응답 가져오기"""
    if 'responses' not in st.session_state or not st.session_state.responses:
        return pd.DataFrame(columns=['timestamp', 'age_group', 'preferred_version'])
    
    return pd.DataFrame(st.session_state.responses)

# 통합 저장/읽기 함수
def save_response(age_group, preferred_version):
    """응답 저장 (Google Sheets 또는 로컬)"""
    if USE_GOOGLE_SHEETS:
        return append_to_sheets(age_group, preferred_version)
    else:
        save_local_response(age_group, preferred_version)
        return True

def get_responses():
    """응답 가져오기 (Google Sheets 또는 로컬)"""
    if USE_GOOGLE_SHEETS:
        return read_from_sheets()
    else:
        return get_local_responses()

def get_statistics():
    """통계 데이터 계산"""
    df = get_responses()
    
    if df.empty:
        return pd.DataFrame(), pd.DataFrame(), 0
    
    # 전체 통계
    total_df = df.groupby('preferred_version').size().reset_index(name='count')
    total_df['preferred_version'] = total_df['preferred_version'].astype(int)
    
    # 연령대별 통계
    age_group_df = df.groupby(['age_group', 'preferred_version']).size().reset_index(name='count')
    age_group_df['preferred_version'] = age_group_df['preferred_version'].astype(int)
    
    # 전체 응답 수
    total_responses = len(df)
    
    return total_df, age_group_df, total_responses

# 메인 앱
def main():
    init_local_storage()
    
    # 제목
    st.title("🌸 진달래꽃 음악 선호도 조사")
    st.markdown("### 김소월의 '진달래꽃' 7가지 버전 중 가장 좋아하는 버전을 선택해주세요")
    
    # Google Sheets 상태 표시
    if USE_GOOGLE_SHEETS:
        st.success("✅ Google Sheets 연동 활성화 - 데이터가 영구 저장됩니다")
    else:
        st.info("ℹ️ 로컬 저장소 사용 중 - 페이지 새로고침 시 데이터가 초기화됩니다")
    
    # 탭 생성
    tab1, tab2 = st.tabs(["📝 설문 참여", "📊 통계 보기"])
    
    # 탭 1: 설문 참여
    with tab1:
        st.markdown("---")
        
        # 나이대 선택
        age_groups = ["10대", "20대", "30대", "40대", "50대", "60대", "70대", "80대", "90대"]
        age_group = st.selectbox(
            "연령대를 선택해주세요:",
            age_groups,
            index=None,
            placeholder="연령대 선택..."
        )
        
        st.markdown("---")
        st.markdown("### 🎵 각 버전을 들어보시고 가장 선호하는 버전을 선택해주세요")
        
        # MP3 파일 경로 설정
        music_dir = Path("music_files")
        music_dir.mkdir(exist_ok=True)
        
        # 7개의 음악 파일 정보
        music_versions = [
            {"id": 1, "name": "버전 1", "file": "version_1.mp3"},
            {"id": 2, "name": "버전 2", "file": "version_2.mp3"},
            {"id": 3, "name": "버전 3", "file": "version_3.mp3"},
            {"id": 4, "name": "버전 4", "file": "version_4.mp3"},
            {"id": 5, "name": "버전 5", "file": "version_5.mp3"},
            {"id": 6, "name": "버전 6", "file": "version_6.mp3"},
            {"id": 7, "name": "버전 7", "file": "version_7.mp3"},
        ]
        
        # 음악 파일 표시 (3열로 배치)
        cols_per_row = 3
        for i in range(0, len(music_versions), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(music_versions):
                    version = music_versions[i + j]
                    with col:
                        st.markdown(f"**{version['name']}**")
                        file_path = music_dir / version['file']
                        
                        if file_path.exists():
                            with open(file_path, 'rb') as audio_file:
                                audio_bytes = audio_file.read()
                                st.audio(audio_bytes, format='audio/mp3')
                        else:
                            st.info(f"'{version['file']}' 파일을 music_files 폴더에 넣어주세요")
        
        st.markdown("---")
        
        # 선호 버전 선택
        preferred_version = st.radio(
            "가장 마음에 드는 버전을 선택해주세요:",
            options=[v['id'] for v in music_versions],
            format_func=lambda x: f"버전 {x}",
            horizontal=True,
            index=None
        )
        
        # 제출 버튼
        if st.button("✅ 제출하기", type="primary", use_container_width=True):
            if age_group is None:
                st.error("연령대를 선택해주세요!")
            elif preferred_version is None:
                st.error("선호하는 버전을 선택해주세요!")
            else:
                if save_response(age_group, preferred_version):
                    st.success(f"✨ 응답이 성공적으로 저장되었습니다! ({age_group}, 버전 {preferred_version})")
                    st.balloons()
                else:
                    st.error("응답 저장에 실패했습니다. 다시 시도해주세요.")
    
    # 탭 2: 통계 보기
    with tab2:
        st.markdown("---")
        
        total_df, age_group_df, total_responses = get_statistics()
        
        if total_responses == 0:
            st.info("아직 설문 응답이 없습니다. 첫 번째 응답자가 되어주세요! 🎉")
            return
        
        # 전체 통계 표시
        st.markdown(f"### 📈 전체 통계 (총 {total_responses}명 응답)")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 전체 선호도 바 차트
            if not total_df.empty:
                # 백분율 계산
                total_df['percentage'] = (total_df['count'] / total_responses * 100).round(1)
                
                fig_total = px.bar(
                    total_df,
                    x='preferred_version',
                    y='count',
                    text='percentage',
                    labels={'preferred_version': '버전', 'count': '응답 수'},
                    title='전체 선호도 분포',
                    color='count',
                    color_continuous_scale='Viridis'
                )
                
                fig_total.update_traces(
                    texttemplate='%{text}%',
                    textposition='outside'
                )
                
                fig_total.update_layout(
                    xaxis=dict(tickmode='linear', tick0=1, dtick=1),
                    yaxis_title="응답 수",
                    xaxis_title="버전",
                    showlegend=False,
                    height=400
                )
                
                st.plotly_chart(fig_total, use_container_width=True)
        
        with col2:
            # 원형 차트
            if not total_df.empty:
                fig_pie = px.pie(
                    total_df,
                    values='count',
                    names='preferred_version',
                    title='전체 비율',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                
                fig_pie.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hovertemplate='버전 %{label}<br>%{value}명 (%{percent})<extra></extra>'
                )
                
                fig_pie.update_layout(height=400)
                
                st.plotly_chart(fig_pie, use_container_width=True)
        
        st.markdown("---")
        
        # 연령대별 통계
        st.markdown("### 👥 연령대별 선호도 분석")
        
        if not age_group_df.empty:
            # 히트맵 데이터 준비
            pivot_df = age_group_df.pivot(
                index='age_group',
                columns='preferred_version',
                values='count'
            ).fillna(0)
            
            # 연령대 순서 정렬
            age_order = ["10대", "20대", "30대", "40대", "50대", "60대", "70대", "80대", "90대"]
            pivot_df = pivot_df.reindex([age for age in age_order if age in pivot_df.index])
            
            # 히트맵
            fig_heatmap = px.imshow(
                pivot_df,
                labels=dict(x="버전", y="연령대", color="응답 수"),
                x=[f"버전 {i}" for i in pivot_df.columns],
                y=pivot_df.index,
                color_continuous_scale='YlOrRd',
                aspect="auto",
                title="연령대별 선호도 히트맵"
            )
            
            fig_heatmap.update_layout(height=500)
            
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
            st.markdown("---")
            
            # 연령대별 그룹화 바 차트
            fig_grouped = px.bar(
                age_group_df,
                x='age_group',
                y='count',
                color='preferred_version',
                barmode='group',
                labels={'age_group': '연령대', 'count': '응답 수', 'preferred_version': '버전'},
                title='연령대별 선호도 상세',
                color_continuous_scale='Viridis'
            )
            
            fig_grouped.update_layout(
                xaxis={'categoryorder': 'array', 'categoryarray': age_order},
                height=500,
                legend_title_text='버전'
            )
            
            st.plotly_chart(fig_grouped, use_container_width=True)
            
            st.markdown("---")
            
            # 상세 데이터 테이블
            with st.expander("📋 상세 데이터 보기"):
                # 각 연령대별 통계
                st.markdown("#### 연령대별 선호도 분포")
                display_df = pivot_df.copy()
                display_df.columns = [f"버전 {col}" for col in display_df.columns]
                display_df['총합'] = display_df.sum(axis=1)
                st.dataframe(display_df, use_container_width=True)
                
                # 버전별 연령대 분포
                st.markdown("#### 버전별 연령대 분포")
                version_age_df = age_group_df.pivot(
                    index='preferred_version',
                    columns='age_group',
                    values='count'
                ).fillna(0)
                version_age_df.index = [f"버전 {i}" for i in version_age_df.index]
                version_age_df['총합'] = version_age_df.sum(axis=1)
                st.dataframe(version_age_df, use_container_width=True)
                
                # CSV 다운로드
                responses_df = get_responses()
                if not responses_df.empty:
                    csv = responses_df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 전체 데이터 다운로드 (CSV)",
                        data=csv,
                        file_name=f"survey_data_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )

if __name__ == "__main__":
    main()
