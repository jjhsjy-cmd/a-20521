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

# ----------------------------------------------------
# 3. 총 관객 수 분포 (히스토그램)
# ----------------------------------------------------
st.subheader("3. 총 관객 수 분포")

fig3 = px.histogram(
    df,
    x="total_audi",
    nbins=30,
    title="총 관객 수 히스토그램",
    labels={"total_audi": "총 관객 수", "count": "영화 수"},
)

fig3.update_traces(
    hovertemplate="<b>총 관객 수 구간</b>: %{x:,.0f}명대<br><b>영화 수</b>: %{y}편<extra></extra>"
)

st.plotly_chart(fig3, use_container_width=True)

# 데이터 수치 자동 계산
max_movie = df.loc[df["total_audi"].idxmax()]
max_title = max_movie["movieNm"]
max_audi = max_movie["total_audi"]

under_2m_count = (df["total_audi"] <= 2000000).sum()
total_count = len(df)
under_2m_ratio = (under_2m_count / total_count) * 100

# 그래프 해석 및 구역 분리
st.markdown("#### 💡 이 그래프로 알 수 있는 것")
st.info(
    f"대부분의 영화({under_2m_count}편, 약 {under_2m_ratio:.1f}%)가 **총 관객 수 200만 명 이하 구간**에 밀집되어 있으며, "
    f"가장 많은 관객을 동원한 영화는 **'{max_title}'**(총 관객 수 {max_audi:,.0f}명)입니다."
)

st.divider()

# ----------------------------------------------------
# 4. 개봉일 스크린 수와 총 관객 수 (산점도)
# ----------------------------------------------------
st.subheader("4. 개봉일 스크린 수와 총 관객 수의 관계")

fig4 = px.scatter(
    df,
    x="first_scrn",
    y="total_audi",
    color="genre",
    hover_name="movieNm",
    title="개봉일 스크린 수 vs 총 관객 수 (장르별 색상 구분)",
    labels={
        "first_scrn": "개봉일 스크린 수",
        "total_audi": "총 관객 수",
        "genre": "장르",
    },
)

# 마우스 호버 시 영화명, 스크린 수, 총 관객 수가 콤마 포맷팅과 함께 표시되도록 설정
fig4.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>개봉일 스크린 수: %{x:,.0f}개<br>총 관객 수: %{y:,.0f}명<extra></extra>"
)

st.plotly_chart(fig4, use_container_width=True)

# 그래프 해석 및 구역 분리
st.markdown("#### 💡 이 그래프로 알 수 있는 것")
st.info(
    "개봉일 스크린 수가 많을수록 대체로 총 관객 수가 증가하는 양의 상관관계를 보이지만, 초기 스크린 수가 적더라도 입소문 등을 통해 대형 흥행을 거둔 예외 사례도 나타납니다."
)

st.divider()

# ----------------------------------------------------
# 5. 주요 장르별 총 관객 수 (박스플롯)
# ----------------------------------------------------
st.subheader("5. 주요 장르별 총 관객 수 분포 (10편 이상 장르)")

# 영화 편수가 10편 이상인 장르만 필터링
genre_counts_all = df["genre"].value_counts()
major_genres = genre_counts_all[genre_counts_all >= 10].index
df_major = df[df["genre"].isin(major_genres)]

fig5 = px.box(
    df_major,
    x="genre",
    y="total_audi",
    color="genre",
    hover_name="movieNm",
    points="outliers",  # 이상치 점만 표시
    title="주요 장르별 총 관객 수 박스플롯",
    labels={"genre": "장르", "total_audi": "총 관객 수"},
)

# 마우스 호버 포맷 지정
fig5.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>총 관객 수: %{y:,.0f}명<extra></extra>"
)

st.plotly_chart(fig5, use_container_width=True)

# 그래프 해석 및 구역 분리
st.markdown("#### 💡 이 그래프로 알 수 있는 것")
st.info(
    "주요 장르 대부분의 중간값은 낮게 형성되어 있으나, 상자 밖으로 크게 벗어난 극단치(이상치) 점들을 통해 장르마다 독보적인 대형 흥행작들이 존재함을 알 수 있습니다."
)

st.divider()

# ----------------------------------------------------
# 6. 스크린 수, 첫 주 관객 수, 총 관객 수의 관계 (버블 차트)
# ----------------------------------------------------
st.subheader("6. 스크린 수, 첫 주 관객 수, 총 관객 수의 관계 (버블 차트)")

fig6 = px.scatter(
    df,
    x="first_scrn",
    y="total_audi",
    size="first_week_audi",
    color="genre",
    hover_name="movieNm",
    size_max=50,
    title="개봉일 스크린 수 vs 총 관객 수 (버블 크기: 개봉 첫 주 관객 수)",
    labels={
        "first_scrn": "개봉일 스크린 수",
        "total_audi": "총 관객 수",
        "first_week_audi": "개봉 첫 주 관객 수",
        "genre": "장르",
    },
)

# 마우스 호버 시 상세 정보가 함께 표시되도록 설정
fig6.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>개봉일 스크린 수: %{x:,.0f}개<br>총 관객 수: %{y:,.0f}명<br>개봉 첫 주 관객 수: %{marker.size:,.0f}명<extra></extra>"
)

st.plotly_chart(fig6, use_container_width=True)

# 그래프 해석 및 구역 분리
st.markdown("#### 💡 이 그래프로 알 수 있는 것")
st.info(
    "개봉일 스크린 수가 많을수록 개봉 첫 주 관객 수(버블 크기)와 최종 총 관객 수가 모두 커지는 경향을 보이며, 초기 집객력이 최종 흥행 성과에 결정적인 영향을 미침을 알 수 있습니다."
)

st.divider()

# ----------------------------------------------------
# 7. 제작 국가 및 장르별 영화 편수 (선버스트)
# ----------------------------------------------------
st.subheader("7. 제작 국가 및 장르별 영화 편수 (선버스트)")

fig7 = px.sunburst(
    df,
    path=["nation", "genre"],
    title="제작 국가 및 장르별 영화 편수 계층 구조 (크기: 영화 편수)",
)

# 마우스 호버 시 국가/장르명과 영화 편수가 보이도록 설정
fig7.update_traces(
    hovertemplate="<b>%{label}</b><br>영화 편수: %{value}편<extra></extra>"
)

st.plotly_chart(fig7, use_container_width=True)

# 그래프 해석 및 구역 분리
st.markdown("#### 💡 이 그래프로 알 수 있는 것")
st.info(
    "제작 국가별로 시장에 공급되는 영화의 장르적 다양성과 중심 장르의 구성 비중 차이를 계층적으로 명확하게 파악할 수 있습니다."
)

st.divider()

# ----------------------------------------------------
# 8. 10위권 체류 날수와 총 관객 수 (산점도)
# ----------------------------------------------------
st.subheader("8. 10위권에 오래 머문 영화는 총 관객도 많은가")

fig8 = px.scatter(
    df,
    x="days_in_top10",
    y="total_audi",
    hover_name="movieNm",
    title="10위권에 오래 머문 영화는 총 관객도 많은가",
    labels={
        "days_in_top10": "10위권에 머문 날수",
        "total_audi": "총 관객 수",
    },
)

# 마우스 호버 시 영화명, 체류 날수, 총 관객 수가 표시되도록 설정
fig8.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>10위권 머문 날수: %{x}일<br>총 관객 수: %{y:,.0f}명<extra></extra>"
)

st.plotly_chart(fig8, use_container_width=True)

# 그래프 해석 및 구역 분리
st.markdown("#### 💡 이 그래프로 알 수 있는 것")
st.info(
    "10위권에 오랜 기간 머무른 영화일수록 총 관객 수가 대체로 높아지므로, 박스오피스 상위권 유지 기간과 흥행 규모 간에는 강한 양의 상관관계가 존재함을 알 수 있습니다."
)

st.divider()
