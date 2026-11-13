import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==========================================
# 1. 페이지 기본 설정
# ==========================================
st.set_page_config(
    page_title="성수동 커피 상권 분석 및 5개년 수요예측 대시보드",
    page_icon="☕",
    layout="wide",
)

st.title("☕ 성수동 커피 상권 분석 및 5개년(2026~2030) 수요예측 대시보드")
st.markdown(
    "서울시 생활인구 시계열 데이터(2023.01~2026.10)와 상권 밀집도 지표를 결합한"
    " 인터랙티브 분석 리포트입니다."
)


# ==========================================
# 2. 데이터 로드 및 전처리
# ==========================================
@st.cache_data
def load_data():
  # 로컬 경로에 있는 '생활인구_성수_월간집계.csv' 파일 로드
  df = pd.read_csv("생활인구_성수_월간집계.csv")
  df["date"] = pd.to_datetime(df["ym"].astype(str), format="%Y%m")
  df["청년비중(%)"] = (df["청년(20-39)_평균"] / df["총생활인구수_평균"]) * 100
  df["중년비중(%)"] = (df["중년(40-59)_평균"] / df["총생활인구수_평균"]) * 100
  return df


try:
  df = load_data()
except FileNotFoundError:
  st.error(
      "⚠️ '생활인구_성수_월간집계.csv' 파일을 찾을 수 없습니다. app.py와 같은"
      " 폴더에 파일을 위치시켜 주세요."
  )
  st.stop()

# 상권 카페 밀집도 데이터 (행정동별 추정치)
cafe_density_df = pd.DataFrame({
    "행정동명": ["성수1가1동", "성수1가2동", "성수2가1동", "성수2가3동"],
    "추정카페수": [130, 280, 110, 180],
    "상권유형": [
        "역세권·상업복합",
        "서울숲·카페거리",
        "로컬·준공업골목",
        "IT·오피스밀집",
    ],
})

# 5개년 수요예측 시나리오 데이터 (2026=100 기준)
forecast_df = pd.DataFrame({
    "연도": ["2026", "2027", "2028", "2029", "2030"],
    "성장 시나리오 (Growth)": [100.0, 118.5, 140.2, 165.8, 196.0],
    "중립 시나리오 (Neutral)": [100.0, 107.0, 114.5, 122.6, 131.2],
    "포화 시나리오 (Saturated)": [100.0, 103.0, 104.5, 103.0, 99.0],
})

# ==========================================
# 3. 사이드바 필터
# ==========================================
st.sidebar.header("🔍 분석 조건 필터")
selected_dongs = st.sidebar.multiselect(
    "분석할 행정동 선택",
    options=df["행정동명"].unique(),
    default=df["행정동명"].unique(),
)

filtered_df = df[df["행정동명"].isin(selected_dongs)]

# ==========================================
# 4. 상단 KPI 요약 카드
# ==========================================
avg_total_pop = (
    filtered_df.groupby("ym")["총생활인구수_평균"].sum().mean()
    if not filtered_df.empty
    else 0
)
youth_ratio = (
    filtered_df["청년(20-39)_평균"].sum()
    / filtered_df["총생활인구수_평균"].sum()
    * 100
    if not filtered_df.empty
    else 0
)
middle_ratio = (
    filtered_df["중년(40-59)_평균"].sum()
    / filtered_df["총생활인구수_평균"].sum()
    * 100
    if not filtered_df.empty
    else 0
)
total_cafes = cafe_density_df[cafe_density_df["행정동명"].isin(selected_dongs)][
    "추정카페수"
].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("선택 상권 월평균 생활인구", f"{avg_total_pop:,.0f} 명")
col2.metric("핵심 소비층(20~59세) 비중", f"{youth_ratio + middle_ratio:.1f} %")
col3.metric("추정 영업 카페 수", f"{total_cafes:,} 개")
col4.metric("2030년 수요 지수 (중립 기준)", "131.2", "+31.2% vs 2026")

st.divider()

# ==========================================
# 5. 탭 구성 (시계열/연령분석 vs 밀집도/수요예측)
# ==========================================
tab1, tab2 = st.tabs(
    ["📊 1. 생활인구 및 연령 프로파일", "📈 2. 상권 밀집도 및 5개년 수요예측"]
)

with tab1:
  c1, c2 = st.columns([6, 4])

  with c1:
    st.subheader("월별 생활인구 추이 (2023.01 ~ 2026.10)")
    fig_trend = px.line(
        filtered_df,
        x="date",
        y="총생활인구수_평균",
        color="행정동명",
        markers=True,
        labels={
            "date": "기준월",
            "총생활인구수_평균": "월평균 생활인구(명)",
            "행정동명": "행정동",
        },
    )
    fig_trend.update_layout(hovermode="x unified")
    st.plotly_chart(fig_trend, use_container_width=True)

  with c2:
    st.subheader("행정동별 연령대 구성 비교")
    age_summary = (
        filtered_df.groupby("행정동명")[[
            "청소년(0-19)_평균",
            "청년(20-39)_평균",
            "중년(40-59)_평균",
            "장년(60+)_평균",
        ]]
        .mean()
        .reset_index()
    )
    age_melted = age_summary.melt(
        id_vars="행정동명", var_name="연령대", value_name="평균인구"
    )
    fig_age = px.bar(
        age_melted,
        x="행정동명",
        y="평균인구",
        color="연령대",
        barmode="stack",
        labels={"행정동명": "행정동", "평균인구": "평균 체류인구(명)"},
    )
    st.plotly_chart(fig_age, use_container_width=True)

with tab2:
  c3, c4 = st.columns([6, 4])

  with c3:
    st.subheader("향후 5개년(2026~2030) 커피 수요예측 시나리오")
    fig_forecast = go.Figure()
    colors = {
        "성장 시나리오 (Growth)": "#2E86AB",
        "중립 시나리오 (Neutral)": "#F6AE2D",
        "포화 시나리오 (Saturated)": "#F26419",
    }
    for col in [
        "성장 시나리오 (Growth)",
        "중립 시나리오 (Neutral)",
        "포화 시나리오 (Saturated)",
    ]:
      fig_forecast.add_trace(
          go.Scatter(
              x=forecast_df["연도"],
              y=forecast_df[col],
              mode="lines+markers+text",
              name=col,
              text=forecast_df[col].round(1),
              textposition="top center",
              line=dict(width=3, color=colors[col]),
          )
      )
    fig_forecast.update_layout(
        yaxis_title="수요 지수 (2026년 = 100)",
        xaxis_title="예측 연도",
        hovermode="x unified",
    )
    st.plotly_chart(fig_forecast, use_container_width=True)

  with c4:
    st.subheader("행정동별 카페 경쟁 강도 (생활인구 만 명당 카페 수)")
    latest_pop = (
        df[df["ym"].astype(str).str.startswith("2026")]
        .groupby("행정동명")["총생활인구수_평균"]
        .mean()
        .reset_index()
    )
    merged_density = pd.merge(latest_pop, cafe_density_df, on="행정동명")
    merged_density["만명당_카페수"] = (
        merged_density["추정카페수"]
        / (merged_density["총생활인구수_평균"] / 10000)
    ).round(1)

    fig_density = px.bar(
        merged_density.sort_values("만명당_카페수", ascending=True),
        x="만명당_카페수",
        y="행정동명",
        orientation="h",
        color="만명당_카페수",
        text="만명당_카페수",
        color_continuous_scale="YlOrRd",
        labels={"만명당_카페수": "생활인구 만 명당 카페 수(개)", "행정동명": ""},
    )
    st.plotly_chart(fig_density, use_container_width=True)

  st.subheader("📋 상권 전략 요약 매트릭스")
  st.dataframe(
      merged_density[[
          "행정동명",
          "상권유형",
          "총생활인구수_평균",
          "추정카페수",
          "만명당_카페수",
      ]].rename(
          columns={
              "총생활인구수_평균": "2026 월평균 생활인구(명)",
              "추정카페수": "추정 카페 수(개)",
              "만명당_카페수": "밀도 지수(만 명당 카페 수)",
          }
      ),
      use_container_width=True,
      hide_index=True,
  )