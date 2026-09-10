import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 페이지 전체를 넓게 쓰도록 설정 (그래프를 더 크게 보기 위함)
st.set_page_config(layout="wide")

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
movie_popularity = df.groupby('영화명')['누적관객수'].max().sort_values(ascending=False)
movie_list = movie_popularity.index.tolist()

selected_movie = st.selectbox("영화를 선택하세요 (누적관객수 많은 순):", movie_list)
filtered_df = df[df['영화명'] == selected_movie]

st.divider()

# 4. st.tabs를 사용하여 상단 글자 클릭형 메뉴 생성
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 일별 관객수", 
    "📊 누적 관객수", 
    "🏆 흥행 TOP 5 비교", 
    "📉 7일 이동평균선", 
    "📊 월별 총 관객수", 
    "🗓️ 캘린더 히트맵"
])

# 탭 1: 일별 관객수
with tab1:
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

# 탭 2: 누적 관객수
with tab2:
    st.subheader(f"📊 {selected_movie} - 누적 관객수 변화")
    fig2 = px.area(
        filtered_df,
        x='기준일자',
        y='누적관객수',
        title=f"{selected_movie} 누적 관객수 추이"
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.info("💡 이 그래프로 알 수 있는 것: (시간이 지남에 따라 총관객수가 어떻게 쌓여가는지 적어보세요)")

# 탭 3: 흥행 TOP 5 비교
with tab3:
    st.subheader("🏆 장기 흥행(20일 이상) TOP 5 영화 - 누적 관객수 비교")
    movie_days = df['영화명'].value_counts()
    long_run_movies = movie_days[movie_days >= 20].index
    long_run_df = df[df['영화명'].isin(long_run_movies)]
    top5_long_run_movies = long_run_df.groupby('영화명')['누적관객수'].max().sort_values(ascending=False).head(5).index
    top5_df = df[df['영화명'].isin(top5_long_run_movies)]
    
    fig3 = px.line(
        top5_df,
        x='기준일자',
        y='누적관객수',
        color='영화명',
        title="20일 이상 TOP10 진입 영화 중 누적관객수 TOP 5"
    )
    st.plotly_chart(fig3, use_container_width=True)
    st.info("💡 이 그래프로 알 수 있는 것: (꾸준히 인기를 끈 영화들의 관객 동원 속도를 비교해 보세요)")

# 탭 4: 7일 이동평균선
with tab4:
    st.subheader("📉 전체 영화 일별 총 관객수 및 7일 이동평균 추이")
    daily_total = df.groupby('기준일자')['해당일관객수'].sum().reset_index()
    daily_total['7일_이동평균'] = daily_total['해당일관객수'].rolling(window=7, min_periods=1).mean()
    
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=daily_total['기준일자'],
        y=daily_total['해당일관객수'],
        mode='lines',
        name='일별 총 관객수 (원본)',
        line=dict(color='rgba(180, 180, 180, 0.5)', width=1.5)
    ))
    fig4.add_trace(go.Scatter(
        x=daily_total['기준일자'],
        y=daily_total['7일_이동평균'],
        mode='lines',
        name='7일 이동평균',
        line=dict(color='#1f77b4', width=3)
    ))
    fig4.update_layout(
        title="일별 전체 관객수 및 7일 이동평균 흐름",
        xaxis_title="기준일자",
        yaxis_title="총 관객수",
        hovermode="x unified"
    )
    st.plotly_chart(fig4, use_container_width=True)
    st.info("💡 이 그래프로 알 수 있는 것: (주말 요동을 제거한 전체 극장가의 성수기/비수기 흐름을 확인하세요)")

# 탭 5: 월별 총 관객수
with tab5:
    st.subheader("📊 월별 전체 극장 관객수 합계")
    df_monthly = df.copy()
    df_monthly['연월'] = df_monthly['기준일자'].dt.strftime('%Y-%m')
    monthly_total = df_monthly.groupby('연월')['해당일관객수'].sum().reset_index()
    
    fig5 = px.bar(
        monthly_total,
        x='연월',
        y='해당일관객수',
        text_auto='.2s',
        labels={'연월': '월 (연-월)', '해당일관객수': '총 관객수'},
        title="월별 극장 총 관객수 집계"
    )
    fig5.update_traces(textposition='outside')
    fig5.update_layout(xaxis_type='category')
    
    st.plotly_chart(fig5, use_container_width=True)
    st.info("💡 이 그래프로 알 수 있는 것: (1년 중 어느 달에 극장 관객 수가 가장 많았는지 비교해 보세요)")

# 탭 6: 캘린더 히트맵
with tab6:
    st.subheader("🗓️ 주차 및 요일별 전체 관객수 캘린더 히트맵")
    daily_total = df.groupby('기준일자')['해당일관객수'].sum().reset_index()
    
    day_map = {0: '월', 1: '화', 2: '수', 3: '목', 4: '금', 5: '토', 6: '일'}
    daily_total['요일'] = daily_total['기준일자'].dt.dayofweek.map(day_map)
    daily_total['주차'] = daily_total['기준일자'].dt.strftime('%Y년 %W주차')
    daily_total['날짜_str'] = daily_total['기준일자'].dt.strftime('%Y-%m-%d')
    
    days_order = ['월', '화', '수', '목', '금', '토', '일']
    pivot_val = daily_total.pivot(index='요일', columns='주차', values='해당일관객수').reindex(days_order)
    pivot_date = daily_total.pivot(index='요일', columns='주차', values='날짜_str').reindex(days_order)
    
    fig6 = go.Figure(data=go.Heatmap(
        z=pivot_val.values,
        x=pivot_val.columns,
        y=pivot_val.index,
        customdata=pivot_date.values,
        colorscale='Reds',
        hovertemplate='<b>날짜: %{customdata}</b><br>요일: %{y}<br>총 관객수: %{z:,.0f}명<extra></extra>'
    ))
    
    fig6.update_layout(
        title="주차/요일별 극장 관객수 분포",
        xaxis_title="연도 및 주차",
        yaxis_title="요일",
        yaxis=dict(autorange='reversed')
    )
    st.plotly_chart(fig6, use_container_width=True)
    st.info("💡 이 그래프로 알 수 있는 것: (특정 주차나 주말/공휴일의 관객 몰림 패턴을 확인해 보세요)")
