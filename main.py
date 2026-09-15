import pandas as pd
import plotly.express as px
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="영화 데이터 그래프 도감 - 분포와 관계", layout="wide")

st.title("영화 데이터 그래프 도감 - 분포와 관계")


# 데이터 불러오기 및 전처리
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"
    df = pd.read_csv(url)

    # 장르 전처리: 세로막대 기호(|)로 여러 개 적힌 경우 첫 번째 장르만 추출
    if "genre" in df.columns:
        df["genre"] = (
            df["genre"].fillna("미상").astype(str).apply(lambda x: x.split("|")[0].strip())
        )

    return df


df = load_data()

# ----------------------------------------------------
# 1. 장르별 영화 편수 (도넛 그래프)
# ----------------------------------------------------
st.subheader("1. 장르별 영화 편수 분포")

genre_counts = df["genre"].value_counts().reset_index()
genre_counts.columns = ["genre", "count"]

fig1 = px.pie(
    genre_counts,
    names="genre",
    values="count",
    hole=0.4,
    title="장르별 영화 편수",
)

# 마우스 호버 시 편수와 비율이 함께 표시되도록 설정
fig1.update_traces(
    textinfo="label+percent",
    hovertemplate="<b>%{label}</b><br>편수: %{value}편<br>비율: %{percent}<extra></extra>",
)

st.plotly_chart(fig1, use_container_width=True)

# 그래프 해석 및 구역 분리
st.markdown("#### 💡 이 그래프로 알 수 있는 것")
st.info(
    "1년간 박스오피스 상위권에 오른 영화 중 드라마와 액션 등 특정 장르가 전체의 과반을 차지하며 높은 시장 비중을 보입니다."
)

st.divider()

# ----------------------------------------------------
# 2. 장르 및 영화별 총 관객 수 (트리맵)
# ----------------------------------------------------
st.subheader("2. 장르 및 영화별 총 관객 수 분포")

fig2 = px.treemap(
    df,
    path=[px.Constant("전체 영화"), "genre", "movieNm"],
    values="total_audi",
    title="장르 및 영화별 총 관객 수 (크기: 총 관객 수)",
)

# 마우스 호버 시 영화명(또는 장르명)과 총 관객 수가 보이도록 설정
fig2.update_traces(
    hovertemplate="<b>%{label}</b><br>총 관객 수: %{value:,.0f}명<extra></extra>"
)

st.plotly_chart(fig2, use_container_width=True)

# 그래프 해석 및 구역 분리
st.markdown("#### 💡 이 그래프로 알 수 있는 것")
st.info(
    "장르 내부에서도 특정 초대형 흥행작 몇 편이 전체 관객 수의 상당 부분을 차지하는 양극화 현상을 확인할 수 있습니다."
)

st.divider()
