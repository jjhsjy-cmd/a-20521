import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# ---------------------------------------------------------
# 1. 페이지 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="다이아몬드 가격 예측 데이터 분석 보고서",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 2. 데이터 로드 및 전처리 파이프라인 (캐싱 적용)
# ---------------------------------------------------------
@st.cache_data
def load_and_preprocess_data(file_path="diamonds.csv"):
    raw_df = pd.read_csv(file_path)
    raw_count = len(raw_df)

    # 1단계: 중복 제거 (146건)
    df_dedup = raw_df.drop_duplicates().reset_index(drop=True)
    dup_removed = raw_count - len(df_dedup)

    # 2단계: 치수 0값(19건) 및 극단적 오기입 이상치(y>30 or z>30, 3건) 제거
    cond_zero = (df_dedup["x"] == 0) | (df_dedup["y"] == 0) | (df_dedup["z"] == 0)
    cond_outlier = (df_dedup["y"] > 30) | (df_dedup["z"] > 30)
    df_clean = df_dedup[~(cond_zero | cond_outlier)].reset_index(drop=True)
    outlier_removed = len(df_dedup) - len(df_clean)

    # 3단계: 4C 범주형 순서 지정 및 원-핫 인코딩 (최하위 등급 Fair, J, I1을 기준선으로 제외)
    cut_order = ["Fair", "Good", "Very Good", "Premium", "Ideal"]
    color_order = ["J", "I", "H", "G", "F", "E", "D"]
    clarity_order = ["I1", "SI2", "SI1", "VS2", "VS1", "VVS2", "VVS1", "IF"]

    df_model = df_clean.copy()
    df_model["cut"] = pd.Categorical(df_model["cut"], categories=cut_order, ordered=True)
    df_model["color"] = pd.Categorical(df_model["color"], categories=color_order, ordered=True)
    df_model["clarity"] = pd.Categorical(df_model["clarity"], categories=clarity_order, ordered=True)

    dummies = pd.get_dummies(df_model[["cut", "color", "clarity"]], drop_first=True, dtype=int)
    log_carat = np.log(df_model["carat"]).rename("log_carat")
    log_price = np.log(df_model["price"]).rename("log_price")

    processed_df = pd.concat([log_carat, dummies, log_price, df_model["price"]], axis=1)

    summary_info = {
        "raw_count": raw_count,
        "dup_removed": dup_removed,
        "zero_count": int(cond_zero.sum()),
        "extreme_count": int(cond_outlier.sum()),
        "outlier_removed": outlier_removed,
        "clean_count": len(df_clean),
        "cut_order": cut_order,
        "color_order": color_order,
        "clarity_order": clarity_order
    }
    return raw_df, df_clean, processed_df, summary_info


# ---------------------------------------------------------
# 3. 모델 학습 및 평가 파이프라인 (계층적 8:2 분할)
# ---------------------------------------------------------
@st.cache_resource
def train_and_evaluate_model(processed_df):
    X = processed_df.drop(columns=["log_price", "price"])
    y_log = processed_df["log_price"]
    y_usd = processed_df["price"]

    # 가격 분위수 기반 계층적 8:2 분할 (교차검증 미사용)
    price_bins = pd.qcut(y_log, q=10, labels=False)
    X_train, X_test, y_train_log, y_test_log, y_train_usd, y_test_usd = train_test_split(
        X, y_log, y_usd,
        test_size=0.2,
        random_state=42,
        stratify=price_bins
    )

    model = LinearRegression()
    model.fit(X_train, y_train_log)

    # Duan's Smearing 보정 계수 (훈련셋 기준)
    train_pred_log = model.predict(X_train)
    smearing_factor = float(np.mean(np.exp(y_train_log - train_pred_log)))
    train_pred_usd = np.exp(train_pred_log) * smearing_factor

    # 테스트셋 예측
    test_pred_log = model.predict(X_test)
    test_pred_usd = np.exp(test_pred_log) * smearing_factor

    metrics = {
        "train_size": len(X_train),
        "test_size": len(X_test),
        "intercept": float(model.intercept_),
        "smearing": smearing_factor,
        "train_r2_log": r2_score(y_train_log, train_pred_log),
        "train_rmse_log": np.sqrt(mean_squared_error(y_train_log, train_pred_log)),
        "train_r2_usd": r2_score(y_train_usd, train_pred_usd),
        "train_rmse_usd": np.sqrt(mean_squared_error(y_train_usd, train_pred_usd)),
        "train_mae_usd": mean_absolute_error(y_train_usd, train_pred_usd),
        "test_r2_log": r2_score(y_test_log, test_pred_log),
        "test_rmse_log": np.sqrt(mean_squared_error(y_test_log, test_pred_log)),
        "test_r2_usd": r2_score(y_test_usd, test_pred_usd),
        "test_rmse_usd": np.sqrt(mean_squared_error(y_test_usd, test_pred_usd)),
        "test_mae_usd": mean_absolute_error(y_test_usd, test_pred_usd),
        "test_mape_usd": float(np.mean(np.abs((y_test_usd - test_pred_usd) / y_test_usd)) * 100),
        "neg_preds": int((test_pred_usd <= 0).sum())
    }

    coef_df = pd.DataFrame({
        "Feature": X.columns,
        "Coefficient": model.coef_,
        "Multiplier": np.exp(model.coef_)
    })

    eval_df = pd.DataFrame({
        "Actual_Log": y_test_log.values,
        "Pred_Log": test_pred_log,
        "Actual_USD": y_test_usd.values,
        "Pred_USD": test_pred_usd,
        "Residual_Log": y_test_log.values - test_pred_log
    })

    return model, list(X.columns), metrics, coef_df, eval_df


# ---------------------------------------------------------
# 4. 데이터 로드 실행
# ---------------------------------------------------------
try:
    raw_df, df_clean, processed_df, info = load_and_preprocess_data("diamonds.csv")
    model, feature_cols, metrics, coef_df, eval_df = train_and_evaluate_model(processed_df)
except FileNotFoundError:
    st.error("⚠️ `diamonds.csv` 파일을 찾을 수 없습니다. GitHub 저장소 루트 경로에 `diamonds.csv`를 함께 업로드해 주세요.")
    st.stop()

# ---------------------------------------------------------
# 5. 사이드바 구성
# ---------------------------------------------------------
st.sidebar.title("💎 분석 보고서 목차")
page = st.sidebar.radio(
    "이동할 섹션을 선택하세요:",
    [
        "1. 프로젝트 개요 및 데이터 정제",
        "2. 탐색적 분석(EDA) 및 변수 선정",
        "3. 로그-로그 선형 회귀 모델링",
        "4. 실시간 다이아몬드 가격 예측기"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "**모델 요약 스펙**\n"
    f"- 정제 데이터: **{info['clean_count']:,}건**\n"
    "- 독립변수: **4C (18개 피처)**\n"
    "- 변환: **log(carat) & log(price)**\n"
    "- 분할 비율: **Train 80% : Test 20%**\n"
    f"- Test $R^2$ (USD): **{metrics['test_r2_usd']:.4f}**"
)

# ---------------------------------------------------------
# 페이지 1: 프로젝트 개요 및 데이터 정제
# ---------------------------------------------------------
if page == "1. 프로젝트 개요 및 데이터 정제":
    st.title("💎 캐글 다이아몬드 가격 예측 데이터 분석 보고서")
    st.markdown("원본 데이터의 무결성 점검부터 이상치 제거, 피처 엔지니어링 및 로그-로그 다중 선형 회귀 모델 구축까지의 전 과정을 정리한 인터랙티브 보고서입니다.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("원본 데이터 행 수", f"{info['raw_count']:,}건")
    col2.metric("중복 제거", f"-{info['dup_removed']:,}건", "완전 중복 행")
    col3.metric("이상치 제거", f"-{info['outlier_removed']:,}건", "0값 19건 + 오기입 3건")
    col4.metric("최종 정제 데이터", f"{info['clean_count']:,}건", "원본 대비 99.69% 유지")

    st.markdown("---")
    st.subheader("1) 데이터 정제 단계별 처리 내역")
    cleaning_table = pd.DataFrame({
        "단계": ["원본 (diamonds.csv)", "1단계: 중복 제거", "2단계: 이상치 제거", "3단계: 최종 피처 변환"],
        "행 수": ["53,940건", "53,794건", "53,772건", "53,772건"],
        "제거/변화": ["-", "-146건", "-22건", "컬럼 10개 → 20개"],
        "상세 처리 근거": [
            "수치형 7개 + 범주형 3개 (결측치 NaN 0건)",
            "모든 컬럼 값이 완전히 동일한 중복 행 제거",
            "물리적 불가능 치수(x, y, z = 0) 19건 및 소수점 오기입(y=58.9, z=31.8) 3건 삭제",
            "log(carat), log(price) 변환 및 cut·color·clarity 원-핫 인코딩 적용"
        ]
    })
    st.table(cleaning_table)

    st.subheader("2) 극단적 이상치(3건) 삭제 근거 — 물리적 밀도 및 오타 검증")
    st.markdown(
        "다이아몬드의 비중($3.51\\text{ g/cm}^3$)과 기하학적 비율을 역산하면, `y > 30` 또는 `z > 30`으로 기록된 3건은 현실에 존재할 수 없는 **100% 데이터 입력 오타**입니다. "
        "전체 데이터의 0.04%에 불과하므로 인위적 대체값 보정 대신 삭제를 선택했습니다."
    )
    outlier_evidence = pd.DataFrame({
        "기록된 캐럿": ["2.00 ct", "0.51 ct", "0.51 ct"],
        "기록된 치수 (x × y × z)": ["8.09 × 58.90 × 8.06 mm", "5.12 × 5.15 × 31.80 mm", "5.15 × 31.80 × 5.12 mm"],
        "치수 기반 추정 무게": ["약 39.1 ct", "약 8.5 ct", "약 8.5 ct"],
        "오타 원인 진단": [
            "바로 옆 depth 값(58.9)을 y 컬럼에 잘못 복사·기입",
            "정상 깊이 3.18mm의 소수점 자릿수 오기입 (31.8)",
            "소수점 오기입(31.8)과 동시에 y와 z 컬럼 위치 뒤바뀜"
        ]
    })
    st.table(outlier_evidence)

    st.subheader("3) 최종 전처리 완료 데이터 미리보기 (`diamonds_preprocessed_4c_log.csv`)")
    st.dataframe(processed_df.head(10), use_container_width=True)

# ---------------------------------------------------------
# 페이지 2: 탐색적 분석(EDA) 및 변수 선정
# ---------------------------------------------------------
elif page == "2. 탐색적 분석(EDA) 및 변수 선정":
    st.title("📊 탐색적 데이터 분석(EDA) 및 4C 독립변수 선정 근거")

    st.subheader("1) 종속변수(price) 분포와 로그 변환의 필요성")
    col1, col2 = st.columns(2)
    with col1:
        fig_raw = px.histogram(
            df_clean, x="price", nbins=50,
            title=f"원본 Price 분포 (우편향, Skewness = {df_clean['price'].skew():.2f})",
            labels={"price": "가격 (USD)"}, color_discrete_sequence=["#d95f02"]
        )
        st.plotly_chart(fig_raw, use_container_width=True)
    with col2:
        fig_log = px.histogram(
            processed_df, x="log_price", nbins=50,
            title=f"로그 변환 log(Price) 분포 (대칭화, Skewness = {processed_df['log_price'].skew():.2f})",
            labels={"log_price": "log(Price)"}, color_discrete_sequence=["#1b9e77"]
        )
        st.plotly_chart(fig_log, use_container_width=True)

    st.markdown("---")
    st.subheader("2) 독립변수와 가격 간 상관관계 및 심슨의 역설")
    corr_summary = pd.DataFrame({
        "순위": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "변수명": ["carat", "y", "x", "z", "color", "clarity", "table", "cut", "depth"],
        "피어슨 상관계수 (r)": ["+0.922", "+0.889", "+0.887", "+0.882", "-0.172", "-0.146", "+0.127", "-0.052", "-0.011"],
        "스피어만 상관계수 (ρ)": ["+0.963", "+0.963", "+0.964", "+0.959", "-0.150", "-0.211", "+0.171", "-0.092", "+0.010"],
        "해석 및 특징": [
            "가장 강력한 핵심 설명변수 (비선형 지수 상승 관계)",
            "carat과 다중공선성(r=0.95~0.98) 매우 높음",
            "carat과 다중공선성(r=0.95~0.98) 매우 높음",
            "carat과 다중공선성(r=0.95~0.98) 매우 높음",
            "교란 효과(큰 캐럿일수록 최상급 드뭄)로 단순 상관은 음수",
            "교란 효과로 단순 상관은 음수 (동일 캐럿 내에서는 강하게 상승)",
            "선형 상관 매우 약함",
            "교란 효과로 단순 상관은 미약한 음수",
            "선형 상관 거의 없음"
        ]
    })
    st.table(corr_summary)

    st.info(
        "💡 **왜 4C(`carat, cut, color, clarity`)만 독립변수로 선택했나요?**\n"
        "- 상관계수 상위 4개(`carat, x, y, z`)만 쓰면 크기 정보만 중복되고 품질 등급(`cut, color, clarity`)이 누락되어 오차가 급증합니다.\n"
        "- 반면 `x, y, z, depth, table`을 제외하고 **4C만 남기면 다중공선성(VIF < 10)이 완벽히 해소**되면서도 전체 9개 변수와 대등한 설명력을 유지합니다."
    )

    st.subheader("3) Carat & Price 로그 변환 조합별 선형 회귀 성능 비교")
    log_comp = pd.DataFrame({
        "실험 케이스": [
            "Case 1: 원본 carat + 원본 price",
            "Case 2: log(carat) + 원본 price",
            "Case 3: 원본 carat + log(price)",
            "Case 4: log(carat) + log(price) [최종 채택]"
        ],
        "실제 달러($) R²": ["0.9152", "0.7836", "-379.4 (폭발)", "0.9567"],
        "RMSE ($)": ["$1,147.8", "$1,833.5", "$76,873.1", "$820.5"],
        "MAE ($)": ["$798.9", "$1,419.3", "$2,617.3", "$398.9"],
        "음수($0 이하) 예측": ["1,021건", "1,841건", "0건", "0건"],
        "판정": [
            "곡선 관계 미반영 및 음수 예측 발생",
            "곡률 방향 불일치로 성능 급락",
            "역변환 시 고캐럿 가격 지수 폭발",
            "직선 관계 일치, 오차 절반 감소, 음수 예측 0건"
        ]
    })
    st.table(log_comp)

# ---------------------------------------------------------
# 페이지 3: 로그-로그 선형 회귀 모델링
# ---------------------------------------------------------
elif page == "3. 로그-로그 선형 회귀 모델링":
    st.title("📈 로그-로그 다중 선형 회귀 모델 학습 및 평가")
    st.markdown(
        f"- **데이터 분할:** 교차검증 없이 가격 분위수 기준 **계층적 8 : 2 분할** (훈련 `{metrics['train_size']:,}건` / 테스트 `{metrics['test_size']:,}건`)\n"
        f"- **역변환 편향 보정:** Duan's Smearing Factor = `{metrics['smearing']:.5f}` 적용"
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Test R² (로그 스케일)", f"{metrics['test_r2_log']:.4f}", f"Train: {metrics['train_r2_log']:.4f}")
    c2.metric("Test R² (실제 달러 기준)", f"{metrics['test_r2_usd']:.4f}", f"Train: {metrics['train_r2_usd']:.4f}")
    c3.metric("Test MAE (평균 절대 오차)", f"${metrics['test_mae_usd']:.2f}", f"MAPE: {metrics['test_mape_usd']:.2f}%")
    c4.metric("Test RMSE / 음수 예측", f"${metrics['test_rmse_usd']:.2f}", f"음수 예측: {metrics['neg_preds']}건")

    st.markdown("---")
    col1, col2 = st.columns(2)

    sample_eval = eval_df.sample(2000, random_state=42)
    with col1:
        fig_pred = px.scatter(
            sample_eval, x="Actual_USD", y="Pred_USD", opacity=0.35,
            title="테스트셋 실제 가격 vs 예측 가격 ($)",
            labels={"Actual_USD": "실제 가격 ($)", "Pred_USD": "예측 가격 ($)"},
            color_discrete_sequence=["#1f77b4"]
        )
        fig_pred.add_trace(
            go.Scatter(x=[0, 19000], y=[0, 19000], mode="lines", name="이상적 예측선 (y=x)", line=dict(color="red", dash="dash"))
        )
        st.plotly_chart(fig_pred, use_container_width=True)

    with col2:
        cat_coef = coef_df[coef_df["Feature"] != "log_carat"].copy()
        cat_coef["Group"] = cat_coef["Feature"].apply(
            lambda x: "Cut (기준: Fair)" if "cut" in x else ("Color (기준: J)" if "color" in x else "Clarity (기준: I1)")
        )
        fig_coef = px.bar(
            cat_coef, x="Multiplier", y="Feature", color="Group", orientation="h",
            title="등급별 가격 상승 배율 exp(β) (기준 등급 = 1.00배)",
            labels={"Multiplier": "가격 상승 배율 (배)", "Feature": "더미 변수"}
        )
        fig_coef.update_yaxes(autorange="reversed")
        fig_coef.add_vline(x=1.0, line_dash="dot", line_color="black")
        st.plotly_chart(fig_coef, use_container_width=True)

    st.subheader("학습된 전체 회귀 계수 상세표")
    st.markdown(f"**절편 (Intercept, $\\beta_0$):** `{metrics['intercept']:.4f}` | **`log_carat` 탄력성 계수:** `{coef_df.loc[0, 'Coefficient']:.4f}` (무게 2배 시 가격 약 $2^{{1.8846}} \\approx 3.69$배 상승)")
    st.dataframe(
        coef_df.style.format({"Coefficient": "{:.4f}", "Multiplier": "{:.4f}배"}),
        use_container_width=True
    )

# ---------------------------------------------------------
# 페이지 4: 실시간 다이아몬드 가격 예측기
# ---------------------------------------------------------
elif page == "4. 실시간 다이아몬드 가격 예측기":
    st.title("🔮 실시간 다이아몬드 가격 예측 시뮬레이터")
    st.markdown("학습된 로그-로그 선형 회귀 모델(`4C 원-핫 인코딩`)을 사용하여 원하는 스펙의 다이아몬드 적정 시장 가격을 즉시 계산합니다.")

    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("다이아몬드 4C 스펙 입력")
        input_carat = st.slider("무게 (Carat)", min_value=0.20, max_value=5.00, value=1.00, step=0.01)
        input_cut = st.select_slider("커팅 등급 (Cut: 낮음 → 높음)", options=info["cut_order"], value="Ideal")
        input_color = st.select_slider("색상 등급 (Color: 낮음 J → 높음 D)", options=info["color_order"], value="G")
        input_clarity = st.select_slider("투명도 등급 (Clarity: 낮음 I1 → 높음 IF)", options=info["clarity_order"], value="VS2")

    # 입력 벡터 구성
    input_dict = {col: 0.0 for col in feature_cols}
    input_dict["log_carat"] = np.log(input_carat)
    if f"cut_{input_cut}" in input_dict:
        input_dict[f"cut_{input_cut}"] = 1.0
    if f"color_{input_color}" in input_dict:
        input_dict[f"color_{input_color}"] = 1.0
    if f"clarity_{input_clarity}" in input_dict:
        input_dict[f"clarity_{input_clarity}"] = 1.0

    input_df = pd.DataFrame([input_dict])[feature_cols]
    pred_log_val = float(model.predict(input_df)[0])
    pred_usd_val = np.exp(pred_log_val) * metrics["smearing"]

    # 로그 잔차 표준편차(RMSE_log) 기반 약 68% / 95% 신뢰 구간 범위 추정
    rmse_log = metrics["test_rmse_log"]
    low_68 = np.exp(pred_log_val - rmse_log) * metrics["smearing"]
    high_68 = np.exp(pred_log_val + rmse_log) * metrics["smearing"]

    with col2:
        st.subheader("모델 예측 결과")
        st.metric(
            label=f"{input_carat:.2f} ct | {input_cut} | {input_color} | {input_clarity}",
            value=f"${pred_usd_val:,.0f}",
            delta=f"캐럿당 단가: ${pred_usd_val / input_carat:,.0f} / ct"
        )
        st.write(f"- **예상 적정 시세 범위 (±1σ 구간):** `${low_68:,.0f}` ~ `${high_68:,.0f}`")
        st.write(f"- **예측 로그 가격 (`log_price`):** `{pred_log_val:.4f}` (Smearing 보정계수 `{metrics['smearing']:.5f}` 적용)")

        # 유사 조건 실제 데이터 비교
        similar_df = df_clean[
            (df_clean["carat"].between(input_carat - 0.05, input_carat + 0.05)) &
            (df_clean["cut"] == input_cut) &
            (df_clean["color"] == input_color) &
            (df_clean["clarity"] == input_clarity)
        ]
        if len(similar_df) > 0:
            st.success(
                f"📌 데이터셋 내 동일 등급·유사 무게(±0.05ct) 실제 매물 **{len(similar_df)}건**의 "
                f"평균 가격은 **${similar_df['price'].mean():,.0f}** (중앙값 **${similar_df['price'].median():,.0f}**)입니다."
            )
        else:
            st.warning("📌 데이터셋 내에 완전히 일치하는 등급·무게의 실제 매물이 없어 회귀 모델의 일반화 추정치로 산출되었습니다.")
