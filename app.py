import streamlit as st
import pandas as pd

# -----------------------------------------------------------
# 1. 페이지 설정 및 네비게이션 상태 관리
# -----------------------------------------------------------
st.set_page_config(page_title="쇼크트리 훈프로 통합 솔루션", layout="wide")

if 'page' not in st.session_state:
    st.session_state.page = "🏠 홈"

def chg_page(page_name):
    st.session_state.page = page_name

# -----------------------------------------------------------
# 2. [기능 1] 쿠팡 광고 성과 분석기 (훈프로 오리지널 로직)
# -----------------------------------------------------------
def run_analyzer():
    st.title("📊 쇼크트리 훈프로 쿠팡 광고 성과 분석기")
    st.markdown("쿠팡 보고서(CSV 또는 XLSX)를 업로드하면 훈프로의 정밀 운영 전략이 자동으로 생성됩니다.")

    # --- 사이드바: 수익성 계산 설정 ---
    st.sidebar.header("💰 마진 계산 설정")
    unit_price = st.sidebar.number_input("상품 판매가 (원)", min_value=0, value=0, step=100)
    unit_cost = st.sidebar.number_input("최종원가(매입가 등) (원)", min_value=0, value=0, step=100)

    delivery_fee = st.sidebar.number_input("로켓그로스 입출고비 (원)", min_value=0, value=3650, step=10)
    coupang_fee_rate = st.sidebar.number_input("쿠팡 수수료(vat포함) (%)", min_value=0.0, max_value=100.0, value=11.55, step=0.1)

    total_fee_amount = unit_price * (coupang_fee_rate / 100)
    net_unit_margin = unit_price - unit_cost - delivery_fee - total_fee_amount

    st.sidebar.divider()
    st.sidebar.write(f"**📦 입출고비 합계:** {delivery_fee:,.0f}원")
    st.sidebar.write(f"**📊 예상 수수료 ({coupang_fee_rate}%):** {total_fee_amount:,.0f}원")
    st.sidebar.write(f"**💡 개당 예상 마진:** :green[{net_unit_margin:,.0f}원]") 

    if unit_price > 0:
        margin_rate = (net_unit_margin / unit_price) * 100
        st.sidebar.write(f"**📈 예상 마진율:** {margin_rate:.1f}%")

    uploaded_file = st.file_uploader("보고서 파일을 선택하세요 (CSV 또는 XLSX)", type=['csv', 'xlsx'])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                try: df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
                except: df = pd.read_csv(uploaded_file, encoding='cp949')
            else:
                df = pd.read_excel(uploaded_file, engine='openpyxl')

            df.columns = [str(c).strip() for c in df.columns]
            qty_targets = ['총 판매수량(14일)', '총 판매수량(1일)', '총 판매수량', '전환 판매수량', '판매수량']
            col_qty = next((c for c in qty_targets if c in df.columns), None)

            if '광고 노출 지면' in df.columns and col_qty:
                for col in ['노출수', '클릭수', '광고비', col_qty]:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').replace('-', '0'), errors='coerce').fillna(0)

                # 지면별 요약
                summary = df.groupby('광고 노출 지면').agg({'노출수': 'sum', '클릭수': 'sum', '광고비': 'sum', col_qty: 'sum'}).reset_index()
                summary.columns = ['지면', '노출수', '클릭수', '광고비', '판매수량']
                
                summary['실제매출액'] = summary['판매수량'] * unit_price
                summary['실제ROAS'] = (summary['실제매출액'] / summary['광고비']).fillna(0)
                summary['클릭률(CTR)'] = (summary['클릭수'] / summary['노출수']).fillna(0)
                summary['구매전환율(CVR)'] = (summary['판매수량'] / summary['클릭수']).fillna(0)
                summary['CPC'] = (summary['광고비'] / summary['클릭수']).fillna(0).astype(int)
                summary['실질순이익'] = (summary['판매수량'] * net_unit_margin) - summary['광고비']

                tot = summary.sum(numeric_only=True)
                total_real_revenue = tot['판매수량'] * unit_price
                total_real_roas = total_real_revenue / tot['광고비'] if tot['광고비'] > 0 else 0
                total_profit = (tot['판매수량'] * net_unit_margin) - tot['광고비']
                
                # 전체 데이터 객체 (제안 섹션용)
                total_data = {
                    '클릭률(CTR)': tot['클릭수'] / tot['노출수'] if tot['노출수'] > 0 else 0,
                    '구매전환율(CVR)': tot['판매수량'] / tot['클릭수'] if tot['클릭수'] > 0 else 0
                }
                
                # 핵심 지표 대시보드
                st.subheader("📌 핵심 성과 지표")
                m1, m2, m3, m4 = st.columns(4)
                p_color = "#FF4B4B" if total_profit >= 0 else "#1C83E1"
                
                cols = [m1, m2, m3, m4]
                vals = [("최종 실질 순이익", f"{total_profit:,.0f}원", p_color), 
                        ("총 광고비", f"{tot['광고비']:,.0f}원", "#31333F"), 
                        ("실제 ROAS", f"{total_real_roas:.2%}", "#31333F"), 
                        ("총 판매수량", f"{tot['판매수량']:,.0f}개", "#31333F")]
                
                for c, (l, v, clr) in zip(cols, vals):
                    c.markdown(f"<div style='background-color:#f0f2f6;padding:15px;border-radius:10px;text-align:center;'> <p style='margin:0;font-size:14px;'>{l}</p><h2 style='margin:0;color:{clr};'>{v}</h2></div>", unsafe_allow_html=True)

                # 상세 표
                def color_p(val): return f'color: {"red" if val >= 0 else "blue"}; font-weight: bold;'
                st.write(""); st.subheader("📍 지면별 상세 분석")
                st.dataframe(summary.style.format({'노출수': '{:,.0f}', '클릭수': '{:,.0f}', '광고비': '{:,.0f}원', '판매수량': '{:,.0f}', '실제매출액': '{:,.0f}원', 'CPC': '{:,.0f}원', '클릭률(CTR)': '{:.2%}', '구매전환율(CVR)': '{:.2%}', '실제ROAS': '{:.2%}', '실질순이익': '{:,.0f}원'}).applymap(color_p, subset=['실질순이익']), use_container_width=True)

                # 옵션별 분석
                if '광고집행 상품명' in df.columns:
                    st.divider(); st.subheader("🛍️ 옵션별 성과 분석")
                    df['광고집행 상품명'] = df['광고집행 상품명'].fillna('미확인')
                    prod_agg = df.groupby('광고집행 상품명').agg({'광고비': 'sum', col_qty: 'sum', '노출수': 'sum', '클릭수': 'sum'}).reset_index()
                    prod_agg.columns = ['상품명', '광고비', '판매수량', '노출수', '클릭수']
                    prod_agg['실질순이익'] = (prod_agg['판매수량'] * net_unit_margin) - prod_agg['광고비']
                    
                    st.markdown("##### 🏆 효자 옵션 (판매순)")
                    st.dataframe(prod_agg[prod_agg['판매수량']>0].sort_values('판매수량', ascending=False).style.format({'광고비': '{:,.0f}원', '판매수량': '{:,.0f}개', '실질순이익': '{:,.0f}원'}), use_container_width=True)
                    
                    st.markdown("##### 💸 돈만 쓰는 옵션 (판매0)")
                    st.dataframe(prod_agg[(prod_agg['판매수량']==0) & (prod_agg['광고비']>0)].sort_values('광고비', ascending=False), use_container_width=True)

                # 키워드 분석
                if '키워드' in df.columns:
                    st.divider(); st.subheader("✂️ 제외 키워드 제안")
                    kw_df = df.groupby('키워드').agg({'광고비': 'sum', col_qty: 'sum'}).reset_index()
                    bad_kws = kw_df[(kw_df[col_qty]==0) & (kw_df['광고비']>0)].sort_values('광고비', ascending=False)
                    st.text_area("복사해서 제외 등록하세요:", ", ".join(bad_kws['키워드'].astype(str).tolist()))

                # 훈프로 정밀 운영 제안 섹션
                st.divider()
                st.subheader("💡 훈프로의 정밀 운영 제안")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.info("🖼️ **클릭률(CTR) 분석 (썸네일)**")
                    ctr_val = total_data['클릭률(CTR)']
                    st.write(f"- **현재 CTR: {ctr_val:.2%}**")
                    if ctr_val < 0.01:
                        st.write("- **상태**: 고객의 눈길을 전혀 끌지 못하고 있습니다.")
                        st.write("- **액션**: 썸네일 배경 제거, 텍스트 강조, 혹은 주력 이미지 교체가 시급합니다.")
                    else:
                        st.write("- **상태**: 시각적 매력이 충분합니다. 클릭률을 유지하며 공격적인 노출을 시도하세요.")

                with col2:
                    st.warning("🛒 **구매전환율(CVR) 분석 (상세페이지)**")
                    cvr_val = total_data['구매전환율(CVR)']
                    st.write(f"- **현재 CVR: {cvr_val:.2%}**")
                    if cvr_val < 0.05:
                        st.write("- **상태**: 유입은 되나 설득력이 부족해 구매로 이어지지 않습니다.")
                        st.write("- **액션**: 상단에 '무료배송', '이벤트' 등 혜택을 강조하고 구매평 관리에 집중하세요.")
                    else:
                        st.write("- **상태**: 상세페이지 전환 능력이 탁월합니다. 유입 단가(CPC) 관리에 힘쓰세요.")

                with col3:
                    st.error("💰 **목표수익률 최적화 가이드**")
                    st.write(f"- **현재 실제 ROAS: {total_real_roas:.2%}**")
                    
                    if total_real_roas < 2.0:
                        st.write("🔴 **[200% 미만] 절대 손실 구간**")
                        st.write("- **액션**: 광고를 새로만드시거나 대대적인 수정이 시급합니다. 목표수익률을 최소 200%p 이상 상향하세요.")
                    elif 2.0 <= total_real_roas < 3.0:
                        st.write("🟠 **[200%~300%] 적자 지속 구간**")
                        st.write("- **액션**: 역마진이 심각합니다. 목표수익률 상향과 고비용 키워드 차단이 필요합니다.")
                    elif 3.0 <= total_real_roas < 4.0:
                        st.write("🟡 **[300%~400%] 손익분기점 안착 구간**")
                        st.write("- **액션**: 수익이 나기 시작합니다. 효율 낮은 키워드를 솎아내며 목표수익률을 50%p 상향하세요.")
                    elif 4.0 <= total_real_roas < 5.0:
                        st.write("🟢 **[400%~500%] 안정적 수익 구간**")
                        st.write("- **전략**: 황금 밸런스입니다. 현재를 유지하며 매출 확대를 위해 목표수익률을 미세 조정하세요.")
                    elif 5.0 <= total_real_roas < 6.0:
                        st.write("🔵 **[500%~600%] 시장 점유 확장 단계**")
                        st.write("- **전략**: 수익이 넉넉합니다. 목표수익률을 하향 조정한 후 노출량을 극대화하세요.")
                    else:
                        st.write("🚀 **[600% 이상] 시장 지배 구간**")
                        st.write("- **전략**: 과감한 하향 조정을 통해 매출 규모 자체를 키우세요.")

        except Exception as e:
            st.error(f"데이터 처리 중 오류 발생: {e}")

# -----------------------------------------------------------
# 3. [기능 2] 쿠팡 상품명 제조기
# -----------------------------------------------------------
def run_namer():
    st.title("🏷️ 쇼크트리 훈프로 쿠팡 상품명 제조기")
    st.markdown("가이드에 최적화된 상품명을 실시간 조합합니다.")
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        brand = st.text_input("브랜드명", "훈프로")
        target = st.selectbox("타겟", ["", "남자", "여성", "공용"])
        season = st.multiselect("시즌", ["봄", "여름", "가을", "겨울", "사계절"])
    with col2:
        main_p = st.text_input("핵심 키워드 (필수) *", "")
        sub_p = st.text_input("보조 소구점", "")
        unit = st.text_input("구성 (세트/수량)", "1개")

    if main_p:
        name = f"{brand} {target} {' '.join(season)} {main_p} {sub_p} {unit}".replace("  ", " ").strip()
        st.subheader("✅ 최적화 상품명")
        st.code(name)
        st.caption(f"글자수: {len(name)}자")

# -----------------------------------------------------------
# 4. [기능 3] 홈 화면
# -----------------------------------------------------------
def run_home():
    st.title("🚀 쇼크트리 훈프로 통합 솔루션")
    st.markdown("### 쿠팡 셀러를 위한 데이터 기반 성장 도구")
    st.divider()
    
    c1, c2 = st.columns(2)
    with c1:
        st.info("📊 **광고 성과 분석기**")
        st.write("ROAS 50% 단위 세분화 분석 및 키워드 제외 제안")
        if st.button("분석기 바로가기", use_container_width=True): chg_page("📊 광고 분석기")
    with c2:
        st.success("🏷️ **상품명 제조기**")
        st.write("클릭을 부르는 최적의 상품명 조합기")
        if st.button("제조기 바로가기", use_container_width=True): chg_page("🏷️ 상품명 제조기")

# -----------------------------------------------------------
# 5. 메인 실행 제어 (네비게이션)
# -----------------------------------------------------------
menu = ["🏠 홈", "📊 광고 분석기", "🏷️ 상품명 제조기"]
st.sidebar.title("🛠️ 메뉴")
sel = st.sidebar.radio("이동할 페이지 선택", menu, index=menu.index(st.session_state.page))

if sel != st.session_state.page:
    chg_page(sel)
    st.rerun()

if st.session_state.page == "🏠 홈": run_home()
elif st.session_state.page == "📊 광고 분석기": run_analyzer()
elif st.session_state.page == "🏷️ 상품명 제조기": run_namer()

# 푸터 (공통)
st.divider()
st.markdown("<div style='text-align: center;'><a href='https://hoonpro.liveklass.com/' target='_blank'>🏠 쇼크트리 훈프로 홈페이지 바로가기</a></div>", unsafe_allow_html=True)
