import streamlit as st
import requests
import pandas as pd
import datetime
import pytz

# 페이지 기본 설정
st.set_page_config(page_title="일일 박스오피스", page_icon="🍿", layout="wide")

# 한국 시간 기준으로 '어제' 날짜 계산
kst = pytz.timezone('Asia/Seoul')
today_kst = datetime.datetime.now(kst)
yesterday_kst = today_kst - datetime.timedelta(days=1)
target_dt = yesterday_kst.strftime('%Y%m%d')

# API 데이터를 가져오고 1시간(3600초) 동안 캐시(기억)하여 중복 호출 방지
@st.cache_data(ttl=3600)
def fetch_box_office(date, api_key):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {
        "key": api_key,
        "targetDt": date
    }
    
    try:
        # API에 요청 보내기
        response = requests.get(url, params=params)
        response.raise_for_status()  # 네트워크 오류 시 예외 발생
        data = response.json()
    except requests.exceptions.RequestException:
        return {"error": "네트워크 통신에 실패했습니다. 인터넷 연결이나 KOBIS 서버 상태를 확인해 주세요."}
    
    # 인증키 오류 등 API 자체에서 보내는 에러 메시지(faultInfo) 확인
    if "faultInfo" in data:
        message = data["faultInfo"].get("message", "알 수 없는 오류가 발생했습니다.")
        return {"error": f"API 오류가 발생했습니다: {message} (인증키를 확인해 주세요)"}
    
    # 정상적인 데이터 응답인지 확인
    if "boxOfficeResult" not in data or "dailyBoxOfficeList" not in data["boxOfficeResult"]:
        return {"error": "데이터 형식이 잘못되었습니다. 영화진흥위원회 API의 응답 형식이 변경되었을 수 있습니다."}
        
    movies = data["boxOfficeResult"]["dailyBoxOfficeList"]
    
    # 데이터가 비어있는 경우
    if not movies:
        return {"error": f"{yesterday_kst.strftime('%Y년 %m월 %d일')}의 박스오피스 데이터가 아직 집계되지 않았거나 제공되지 않습니다."}
        
    return {"movies": movies}

# 메인 화면 구성
st.title("🍿 어제의 박스오피스")
st.write(f"조회 날짜: **{yesterday_kst.strftime('%Y년 %m월 %d일')}** (한국 시간 기준)")

# 스트림릿 비밀 금고(secrets)에서 API 키 불러오기
try:
    kobis_key = st.secrets["KOBIS_KEY"]
except KeyError:
    st.error("Streamlit Cloud의 Secrets 설정에 'KOBIS_KEY'가 없습니다. 환경 설정을 확인해 주세요.")
    st.stop() # 실행 중지

# 데이터 가져오기
result = fetch_box_office(target_dt, kobis_key)

# 에러가 발생했다면 안내 메시지를 띄우고 중지
if "error" in result:
    st.warning(result["error"])
    st.stop()

# 정상적으로 불러온 영화 목록
movies_data = result["movies"]

# 판다스 데이터프레임으로 변환
df = pd.DataFrame(movies_data)

# 숫자형 데이터가 문자열로 오기 때문에 정수로 변환 (계산 및 정렬을 위해)
numeric_columns = ['rank', 'audiCnt', 'audiAcc', 'scrnCnt']
for col in numeric_columns:
    df[col] = pd.to_numeric(df[col])

# 순위(rank)를 기준으로 오름차순 정렬
df = df.sort_values('rank')

st.divider()

# 1위 영화 지표 카드 표시
top1 = df.iloc[0]
st.header(f"🏆 1위: {top1['movieNm']}")

# 3개의 열을 만들어 지표 카드 배치
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("일일 관객수", f"{top1['audiCnt']:,}명")
with col2:
    st.metric("누적 관객수", f"{top1['audiAcc']:,}명")
with col3:
    st.metric("스크린수", f"{top1['scrnCnt']:,}개")

st.divider()

# 관객수 상위 5편 막대그래프
st.subheader("📊 상위 5편 일일 관객수")
top5 = df.head(5)
# 그래프를 그리기 위해 영화명을 인덱스로 설정
chart_data = top5[['movieNm', 'audiCnt']].set_index('movieNm')
st.bar_chart(chart_data)

st.divider()

# 전체 표(테이블) 표시
st.subheader("📋 전체 순위 (Top 10)")
# 표에 보여줄 컬럼만 선택하고 이름 변경
display_df = df[['rank', 'movieNm', 'openDt', 'audiCnt', 'audiAcc', 'scrnCnt']].copy()
display_df.columns = ['순위', '영화명', '개봉일', '일일 관객수', '누적 관객수', '스크린수']

# 인덱스를 숨기고 화면에 표 출력
st.dataframe(display_df, hide_index=True, use_container_width=True)
