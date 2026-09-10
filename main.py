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

# 5. 영역 차트 그리기 (두 번째 구역)
st.divider()
with st.container():
    st.subheader(f"📊 2. {selected_movie} - 누적 관객수 변화")
    
    # Plotly를 사용해 영역 차트 생성
    fig2 = px.area(
        filtered_df,
        x='기준일자',
        y='누적관객수',
        title=f"{selected_movie} 누적 관객수 추이"
    )
    # Streamlit 화면에 그래프 출력
    st.plotly_chart(fig2, use_container_width=True)
    
    # 그래프 아래 설명 문구 자리
    st.info("💡 이 그래프로 알 수 있는 것: (시간이 지남에 따라 총관객수가 어떻게 쌓여가는지, 관객 증가세가 언제 꺾이는지 적어보세요)")

# 6. 다중 선그래프 그리기 (세 번째 구역 추가)
st.divider()
with st.container():
    st.subheader("🏆 3. 흥행 TOP 5 영화 - 누적 관객수 비교")
    
    # 누적관객수가 가장 높은 상위 5개 영화 이름만 뽑아내기
    top5_movies = movie_list[:5]
    
    # 원본 데이터(df)에서 상위 5개 영화에 해당하는 데이터만 걸러내기
    top5_df = df[df['영화명'].isin(top5_movies)]
    
    # Plotly를 사용해 다중 선 그래프 생성
    # color='영화명' 옵션을 주면 영화별로 자동으로 색상이 다르게 지정되고 범례가 생성됩니다.
    fig3 = px.line(
        top5_df,
        x='기준일자',
        y='누적관객수',
        color='영화명', 
        title="TOP 5 영화 누적 관객수 추이 비교"
    )
    
    # Streamlit 화면에 그래프 출력
    st.plotly_chart(fig3, use_container_width=True)
    
    # 그래프 아래 설명 문구 자리
    st.info("💡 이 그래프로 알 수 있는 것: (어떤 영화가 가장 빨리 100만/1000만 관객을 돌파했는지, 영화 간의 관객 동원 뒷심 차이가 어떤지 비교해서 적어보세요)")
