import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 데이터 불러오기 (캐싱 적용)
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/keep-growing-park/data-science/refs/heads/main/dataset/kobis_1year_boxoffice.csv"
    df = pd.read_csv(url)
    
    # 2. 날짜 전처리
    df = df.dropna()
    df['기준일자'] = pd.to_datetime(df['기준일자'])
    df = df.sort_values(by='기준일자')
    
    return df

# 앱 화면의 제목 설정
st.title("🎬 영화 관객수 분석 대시보드")

# 데이터 불러오기 함수 실행
df = load_data()

# 3. 영화 선택 기능
# 각 영화별 최대 '누적관객수'를 기준으로 내림차순 정렬하여 영화명 목록 생성
movie_popularity = df.groupby('영화명')['누적관객수'].max().sort_values(ascending=False)
movie_list = movie_popularity.index.tolist()

# 설정 구역 만들기 (영화 선택 및 그래프 선택)
st.subheader("⚙️ 분석 옵션 설정")
selected_movie = st.selectbox("영화를 선택하세요 (누적관객수 많은 순):", movie_list)

# 보고 싶은 그래프를 선택할 수 있는 라디오 버튼 추가
graph_choice = st.radio(
    "보고 싶은 그래프를 선택하세요:",
    ["📈 1. 일별 관객수 변화 (선그래프)", 
     "📊 2. 누적 관객수 변화 (영역차트)", 
     "🏆 3. 흥행 TOP 5 비교 (다중 선그래프)"]
)

# 선택한 영화의 데이터만 추려내기
filtered_df = df[df['영화명'] == selected_movie]

st.divider() # 구역을 나누는 가로줄

# 4. 사용자가 선택한 그래프만 화면에 보여주기
if graph_choice == "📈 1. 일별 관객수 변화 (선그래프)":
    with st.container():
        st.subheader(f"📈 {selected_movie} - 일별 관객수 변화")
        fig1 = px.line(
            filtered_df, 
            x='기준일자', 
            y='해당일관객수',
            markers=True,
            title=f"{selected_movie} 일별 관객수 추이"
        )
        st.plotly_chart(fig1, use_container_width=True)
        st.info("💡 이 그래프로 알 수 있는 것: (개봉 후 관객수가 어떻게 변화하고 언제 가장 많았는지 적어보세요)")

elif graph_choice == "📊 2. 누적 관객수 변화 (영역차트)":
    with st.container():
        st.subheader(f"📊 {selected_movie} - 누적 관객수 변화")
        fig2 = px.area(
            filtered_df,
            x='기준일자',
            y='누적관객수',
            title=f"{selected_movie} 누적 관객수 추이"
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.info("💡 이 그래프로 알 수 있는 것: (시간이 지남에 따라 총관객수가 어떻게 쌓여가는지, 관객 증가세가 언제 꺾이는지 적어보세요)")

elif graph_choice == "🏆 3. 흥행 TOP 5 비교 (다중 선그래프)":
    with st.container():
        st.subheader("🏆 장기 흥행(20일 이상) TOP 5 영화 - 누적 관객수 비교")
        
        # 1. 영화별로 TOP10에 등장한 일수(데이터 행 개수) 계산
        movie_days = df['영화명'].value_counts()
        
        # 2. 20일 이상 등장한 영화 이름만 추출
        long_run_movies = movie_days[movie_days >= 20].index
        
        # 3. 원본 데이터에서 20일 이상 등장한 영화들만 남기기
        long_run_df = df[df['영화명'].isin(long_run_movies)]
        
        # 4. 남은 롱런 영화들 중에서 누적관객수가 가장 높은 상위 5개 영화 고르기
        top5_long_run_movies = long_run_df.groupby('영화명')['누적관객수'].max().sort_values(ascending=False).head(5).index
        
        # 5. 그래프를 그리기 위해 최종 5개 영화의 데이터만 걸러내기
        top5_df = df[df['영화명'].isin(top5_long_run_movies)]
        
        # 6. Plotly를 사용해 다중 선 그래프 생성
        fig3 = px.line(
            top5_df,
            x='기준일자',
            y='누적관객수',
            color='영화명', # 영화별로 다른 색상과 범례 표시
            title="20일 이상 TOP10 진입 영화 중 누적관객수 TOP 5"
        )
        st.plotly_chart(fig3, use_container_width=True)
        
        # 그래프 아래 설명 문구 자리
        st.info("💡 이 그래프로 알 수 있는 것: (반짝 흥행이 아닌 꾸준히 인기를 끈 영화들 중, 어떤 영화가 관객을 가장 가파르게 모았는지 비교해 보세요)")
