import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 데이터 불러오기 (캐싱 적용)
# @st.cache_data를 사용하면 데이터를 한 번만 불러오고 메모리에 저장하여 앱 속도를 높입니다.
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/keep-growing-park/data-science/refs/heads/main/dataset/kobis_1year_boxoffice.csv"
    df = pd.read_csv(url)
    
    # 2. 날짜 전처리
    # 결측치가 있는 행 삭제
    df = df.dropna()
    
    # "기준일자" 컬럼을 날짜(datetime) 형식으로 변환
    df['기준일자'] = pd.to_datetime(df['기준일자'])
    
    # 기준일자 순서대로 오름차순 정렬
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

# 사용자가 영화를 선택할 수 있는 드롭다운 목록 만들기
selected_movie = st.selectbox("영화를 선택하세요 (누적관객수 많은 순):", movie_list)

# 선택한 영화의 데이터만 추려내기
filtered_df = df[df['영화명'] == selected_movie]

# 4. 선그래프 그리기 (첫 번째 구역)
st.divider() # 구역을 나누는 가로줄
with st.container():
    st.subheader(f"📈 1. {selected_movie} - 일별 관객수 변화")
    
    # Plotly를 사용해 선 그래프 생성
    fig1 = px.line(
        filtered_df, 
        x='기준일자', 
        y='해당일관객수',
        markers=True, # 데이터 포인트에 점 표시
        title=f"{selected_movie} 일별 관객수 추이"
    )
    # Streamlit 화면에 그래프 출력
    st.plotly_chart(fig1, use_container_width=True)
    
    # 그래프 아래 설명 문구 자리
    st.info("💡 이 그래프로 알 수 있는 것: (개봉 후 관객수가 어떻게 변화하고 언제 가장 많았는지 적어보세요)")

# 5. 기타 추가 그래프를 위한 구역 (두 번째 구역)
st.divider()
with st.container():
    st.subheader("📊 2. (추가할 그래프 제목)")
    st.write("여기에 앞으로 새로운 그래프와 코드를 추가하세요.")
    
    # 향후 그래프가 들어갈 빈 자리 (예시)
    # fig2 = px.bar(...) 
    # st.plotly_chart(fig2)
    
    # 그래프 아래 설명 문구 자리
    st.info("💡 이 그래프로 알 수 있는 것: (새로운 그래프에 대한 분석을 한 문장으로 적어보세요)")
