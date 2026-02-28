import streamlit as st
import pandas as pd

# -----------------------------------------------------------
# 1. 전역 페이지 설정 (맨 위에 필수)
# -----------------------------------------------------------
st.set_page_config(page_title="훈프로 통합 솔루션", layout="wide")

# -----------------------------------------------------------
# 2. 페이지 이동을 위한 상태 관리 초기화
# -----------------------------------------------------------
# 'current_page'라는 변수로 현재 보고 있는 페이지를 관리합니다.
if 'current_page' not in st.session_state:
    st.session_state.current_page = "🏠 홈"

# 페이지 이동 함수
def switch_page(page_name):
    st.session_state.current_page = page_name
    st.rerun()

# -----------------------------------------------------------
# 3. 기능 함수 정의
# -----------------------------------------------------------

def run_analyzer():
    st.title("📊 쇼크트리 훈프로 쿠팡 광고 성과 분석기")
    st.markdown("쿠팡 보고서(CSV 또는 XLSX)를 업로드하면 훈프로의 정밀 운영 전략이 자동으로 생성됩니다.")
    st.markdown("---")

    # --- 사이드바: 수익성 계산 설정 ---
    st.sidebar.header("💰 마진 계산 설정")
    unit_price = st.sidebar.number_input("상품 판매가 (원)", min_value=0, value=0, step=100)
    unit_cost = st.sidebar.number_input("최종원가(매입가 등) (원)", min_value=0, value=0, step=100)

    # 로켓그로스 입출고비 및 수수료 설정
    delivery_fee = st.sidebar.number_input("로켓그로스 입출고비 (원)", min_value=0, value=3650, step=10)
    coupang_fee_rate = st.sidebar.number_input("쿠팡 수수료(vat포함) (%)", min_value=0.0, max_value=100.0, value=11.55, step=0.1)

    # 수수료 금액 계산 (판매가 * 수수료율)
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
                try:
                    df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
                except:
                    df = pd.read_csv(uploaded_file, encoding='cp949')
            else:
                df = pd.read_excel(uploaded_file, engine='openpyxl')

            df.columns = [str(c).strip() for c in df.columns]
            qty_targets = ['총 판매수량(14일)', '총 판매수량(1일)', '총 판매수량', '전환 판매수량', '판매수량']
            col_qty = next((c for c in qty_targets if c in df.columns), None)

            if '광고 노출 지면' in df.columns and col_qty:
                for col in ['노출수', '클릭수', '광고비', col_qty]:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').replace('-', '0'), errors='coerce').fillna(0)

                target_cols = {'노출수': 'sum', '클릭수': 'sum', '광고비': 'sum', col_qty: 'sum'}
                summary = df.groupby('광고 노출 지면').agg(target_cols).reset_index()
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
                
                total_data = {
                    '지면': '🏢 전체 합계',
                    '노출수': tot['노출수'], '클릭수': tot['클릭수'], '광고비': tot['광고비'],
                    '판매수량': tot['판매수량'], '실제매출액': total_real_revenue,
                    '클릭률(CTR)': tot['클릭수'] / tot['노출수'] if tot['노출수'] > 0 else 0,
                    '구매전환율(CVR)': tot['판매수량'] / tot['클릭수'] if tot['클릭수'] > 0 else 0,
                    'CPC': int(tot['광고비'] / tot['클릭수']) if tot['클릭수'] > 0 else 0,
                    '실제ROAS': total_real_roas,
                    '실질순이익': total_profit
                }
                total_row = pd.DataFrame([total_data])
                display_df = pd.concat([summary, total_row], ignore_index=True)

                st.subheader("📌 핵심 성과 지표")
                m1, m2, m3, m4 = st.columns(4)
                profit_color = "#FF4B4B" if total_profit >= 0 else "#1C83E1"

                metrics = [
                    ("최종 실질 순이익", f"{total_profit:,.0f}원", profit_color),
                    ("총 광고비", f"{tot['광고비']:,.0f}원", "#31333F"),
                    ("실제 ROAS", f"{total_real_roas:.2%}", "#31333F"),
                    ("총 판매수량", f"{tot['판매수량']:,.0f}개", "#31333F")
                ]
                
                for col, (label, value, color) in zip([m1, m2, m3, m4], metrics):
                    col.markdown(f"""<div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; min-height: 100px;">
                        <p style="margin:0; font-size:14px; color:#555;">{label}</p>
                        <h2 style="margin:0; color:{color}; font-size: 24px;">{value}</h2>
                    </div>""", unsafe_allow_html=True)

                st.write("")

                def color_profit(val):
                    if isinstance(val, (int, float)):
                        color = 'red' if val >= 0 else 'blue'
                        return f'color: {color}; font-weight: bold;'
                    return ''

                st.subheader("📍 지면별 상세 분석")
                st.dataframe(display_df.style.format({
                    '노출수': '{:,.0f}', '클릭수': '{:,.0f}', '광고비': '{:,.0f}원', 
                    '판매수량': '{:,.0f}', '실제매출액': '{:,.0f}원', 'CPC': '{:,.0f}원',
                    '클릭률(CTR)': '{:.2%}', '구매전환율(CVR)': '{:.2%}', '실제ROAS': '{:.2%}',
                    '실질순이익': '{:,.0f}원'
                }).applymap(color_profit, subset=['실질순이익']), use_container_width=True)

                # 옵션별 성과
                target_prod_col = '광고집행 상품명'
                if target_prod_col in df.columns:
                    st.divider()
                    st.subheader(f"🛍️ 옵션별 성과 분석 ({target_prod_col} 기준)")
                    df[target_prod_col] = df[target_prod_col].fillna('상품명 미확인')
                    prod_agg = df.groupby(target_prod_col).agg({
                        '광고비': 'sum', col_qty: 'sum', '노출수': 'sum', '클릭수': 'sum'
                    }).reset_index()
                    prod_agg.columns = ['상품명', '광고비', '판매수량', '노출수', '클릭수']
                    prod_agg['실제매출액'] = prod_agg['판매수량'] * unit_price
                    prod_agg['실제ROAS'] = (prod_agg['실제매출액'] / prod_agg['광고비']).fillna(0)
                    prod_agg['실질순이익'] = (prod_agg['판매수량'] * net_unit_margin) - prod_agg['광고비']
                    prod_agg['구매전환율(CVR)'] = (prod_agg['판매수량'] / prod_agg['클릭수']).fillna(0)

                    st.markdown("##### 🏆 잘 팔리는 효자 옵션 (판매수량 순)")
                    winning_products = prod_agg[prod_agg['판매수량'] > 0].sort_values(by='판매수량', ascending=False)
                    if not winning_products.empty:
                        winning_products = winning_products.reset_index(drop=True)
                        winning_products.index = winning_products.index + 1
                        st.dataframe(winning_products.style.format({
                            '광고비': '{:,.0f}원', '판매수량': '{:,.0f}개', '실제매출액': '{:,.0f}원',
                            '실제ROAS': '{:.2%}', '실질순이익': '{:,.0f}원', '구매전환율(CVR)': '{:.2%}'
                        }).applymap(color_profit, subset=['실질순이익']), use_container_width=True)
                    else:
                        st.info("판매가 발생한 상품 옵션이 없습니다.")

                    st.write("")
                    st.markdown("##### 💸 돈만 나가는 옵션 (판매 0건, 광고비 지출 순)")
                    losing_products = prod_agg[(prod_agg['판매수량'] == 0) & (prod_agg['광고비'] > 0)].sort_values(by='광고비', ascending=False)
                    if not losing_products.empty:
                        losing_products = losing_products.reset_index(drop=True)
                        losing_products.index = losing_products.index + 1
                        st.error(f"⚠️ 총 **{len(losing_products)}개**의 옵션이 판매 없이 광고비만 소진 중입니다.")
                        st.dataframe(losing_products[['상품명', '광고비', '노출수', '클릭수']].style.format({
                            '광고비': '{:,.0f}원', '노출수': '{:,.0f}', '클릭수': '{:,.0f}'
                        }), use_container_width=True)

                # 키워드 성과
                if '키워드' in df.columns:
                    df['키워드'] = df['키워드'].fillna('미식별')
                    kw_agg_all = df.groupby('키워드').agg({
                        '광고비': 'sum', col_qty: 'sum', '노출수': 'sum', '클릭수': 'sum'
                    }).reset_index()
                    kw_agg_all.columns = ['키워드', '광고비', '판매수량', '노출수', '클릭수']
                    kw_agg_all['실제매출액'] = kw_agg_all['판매수량'] * unit_price
                    kw_agg_all['실제ROAS'] = (kw_agg_all['실제매출액'] / kw_agg_all['광고비']).fillna(0)
                    kw_agg_all['실질순이익'] = (kw_agg_all['판매수량'] * net_unit_margin) - kw_agg_all['광고비']
                    
                    st.divider()
                    st.subheader("💰 판매 발생 키워드 (전체)")
                    good_kws = kw_agg_all[(kw_agg_all['판매수량'] > 0) & (kw_agg_all['키워드'] != '-')].sort_values(by='광고비', ascending=False)
                    if not good_kws.empty:
                        good_kws = good_kws.reset_index(drop=True)
                        good_kws.index = good_kws.index + 1
                        st.success(f"✅ 현재 총 **{len(good_kws)}개**의 키워드에서 판매가 발생했습니다.")
                        st.dataframe(good_kws.style.format({
                            '광고비': '{:,.0f}원', '판매수량': '{:,.0f}개', '실제매출액': '{:,.0f}원', 
                            '실제ROAS': '{:.2%}', '실질순이익': '{:,.0f}원', '노출수': '{:,.0f}', '클릭수': '{:,.0f}'
                        }).applymap(color_profit, subset=['실질순이익']), use_container_width=True)
                    else:
                        st.info("판매가 발생한 키워드가 아직 없습니다.")

                    st.divider()
                    st.subheader("✂️ 돈먹는 키워드 (제외 대상 제안)")
                    bad_mask = (kw_agg_all['광고비'] > 0) & (kw_agg_all['판매수량'] == 0) & (kw_agg_all['키워드'] != '-')
                    bad_kws = kw_agg_all[bad_mask].sort_values(by='광고비', ascending=False)
                    if not bad_kws.empty:
                        total_waste_spend = bad_kws['광고비'].sum()
                        st.error(f"⚠️ 현재 총 **{len(bad_kws)}개**의 키워드가 매출 없이 **{total_waste_spend:,.0f}원**의 광고비를 소진했습니다.")
                        bad_names = bad_kws['키워드'].astype(str).tolist()
                        st.text_area("📋 아래 키워드를 복사 후 '제외 키워드'에 등록하세요:", value=", ".join(bad_names), height=120)
                        st.dataframe(bad_kws[['키워드', '광고비', '판매수량', '노출수', '클릭수']].style.format({
                            '광고비': '{:,.0f}원', '판매수량': '{:,.0f}개', '노출수': '{:,.0f}', '클릭수': '{:,.0f}'
                        }), use_container_width=True)

                st.divider()
                st.subheader("💡 훈프로의 정밀 운영 제안")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info("🖼️ **클릭률(CTR) 분석**")
                    ctr_val = total_data['클릭률(CTR)']
                    st.write(f"- **현재 CTR: {ctr_val:.2%}**")
                    if ctr_val < 0.01: st.write("- 썸네일 개선이 시급합니다.")
                    else: st.write("- 시각적 매력이 충분합니다.")
                with col2:
                    st.warning("🛒 **구매전환율(CVR) 분석**")
                    cvr_val = total_data['구매전환율(CVR)']
                    st.write(f"- **현재 CVR: {cvr_val:.2%}**")
                    if cvr_val < 0.05: st.write("- 상세페이지 혜택 강조 필요.")
                    else: st.write("- 상세페이지 설득력 우수.")
                with col3:
                    st.error("💰 **ROAS 가이드**")
                    st.write(f"- **ROAS: {total_real_roas:.2%}**")
                    if total_real_roas < 2.5: st.write("- 🔴 심각한 적자, 대대적 수정 필요.")
                    elif total_real_roas < 4.0: st.write("- 🟡 손익분기 근접, 효율화 필요.")
                    else: st.write("- 🟢 안정적 수익 구간.")

        except Exception as e:
            st.error(f"데이터 처리 중 오류 발생: {e}")

def run_namer():
    st.title("🏷️ 쇼크트리 훈프로 쿠팡 상품명 제조기")
    st.markdown("입력값이 수정되면 상품명이 **실시간으로 자동 변경**됩니다.")
    st.divider()

    st.subheader("1. 상품 정보 입력")
    col1, col2 = st.columns(2)
    with col1:
        brand = st.text_input("브랜드 (없으면 공란)", placeholder="예: 나이키, 훈프로")
        target = st.selectbox("타겟 (성별/대상)", ["", "남자", "여성", "남녀공용", "아동", "유아", "키즈", "성인"])
        season = st.multiselect("시즌 (여러개 선택 가능)", ["봄", "여름", "가을", "겨울", "간절기", "사계절"], default=[])
    with col2:
        main_keyword = st.text_input("제품명 1 (핵심 키워드) *필수", placeholder="예: 반팔티, 원피스")
        appeal_point = st.text_input("소구점 (특징/재질/핏)", placeholder="예: 오버핏, 린넨, 구김없는")
        sub_keyword = st.text_input("제품명 2 (세부 키워드)", placeholder="예: 라운드티, 롱원피스")
        set_info = st.text_input("구성 (몇종/세트)", placeholder="예: 3종 세트, 1+1")

    season_str = " ".join(season)

    def clean_join(parts):
        return " ".join([p.strip() for p in parts if p.strip()])

    final_title = clean_join([brand, target, season_str, main_keyword, appeal_point, sub_keyword, set_info])

    st.divider()
    st.subheader("2. 생성된 상품명 확인")

    if main_keyword:
        st.markdown("##### ✅ 최종 상품명")
        st.caption("공식: 브랜드 + 타겟 + 시즌 + 제품명1 + 소구점 + 제품명2 + 구성")
        st.code(final_title, language="text")
        
        text_len = len(final_title)
        st.caption(f"📏 글자수: {text_len}자 (공백 포함)")

        st.markdown("---")
        st.subheader("🔍 훈프로의 상품명 진단")
        if text_len > 50:
            st.warning(f"⚠️ **길이 주의 ({text_len}자):** 50자 초과. 뒷부분 잘림 주의.")
        else:
            st.success(f"✅ **길이 적합 ({text_len}자):** 모바일 가독성 좋음.")

        words = final_title.split()
        duplicates = set([x for x in words if words.count(x) > 1])
        if duplicates:
            st.error(f"🚫 **중복 단어 발견:** '{', '.join(duplicates)}'")
        else:
            st.success("✅ **중복 없음:** 깔끔한 키워드 조합.")
    else:
        st.info("👆 위 칸에 '제품명 1'을 입력하고 엔터를 치세요.")

def run_home():
    st.title("🚀 쇼크트리 훈프로 통합 솔루션")
    st.markdown("### 쿠팡 셀러를 위한 필수 도구 모음입니다.")
    st.divider()

    c1, c2 = st.columns(2)
    
    with c1:
        st.info("📊 **쿠팡 광고 성과 분석기**")
        st.markdown("광고 보고서를 분석하여 수익성과 운영 전략을 제시합니다.")
        # 버튼 클릭 시 switch_page 함수 호출
        if st.button("광고 분석기 실행하기", use_container_width=True):
            switch_page("📊 광고 성과 분석기")

    with c2:
        st.success("🏷️ **쿠팡 상품명 제조기**")
        st.markdown("쿠팡 SEO에 최적화된 상품명을 자동으로 생성합니다.")
        # 버튼 클릭 시 switch_page 함수 호출
        if st.button("상품명 제조기 실행하기", use_container_width=True):
            switch_page("🏷️ 상품명 제조기")

    st.markdown("---")
    st.markdown("#### 💡 사용 방법")
    st.markdown("1. 원하는 도구의 버튼을 클릭하세요.")
    st.markdown("2. 언제든 왼쪽 **사이드바 메뉴**를 통해 홈으로 돌아오거나 다른 도구로 이동할 수 있습니다.")

# -----------------------------------------------------------
# 4. 메인 실행 로직 (사이드바 + 페이지 라우팅)
# -----------------------------------------------------------

# 사이드바 메뉴 (Key를 'current_page'로 설정하여 세션 상태와 연동)
# 이렇게 하면 메인 화면 버튼에서 상태를 바꿔도 사이드바가 자동으로 업데이트됩니다.
st.sidebar.title("📌 메뉴 선택")
menu_selection = st.sidebar.radio(
    "이동할 페이지를 선택하세요", 
    ["🏠 홈", "📊 광고 성과 분석기", "🏷️ 상품명 제조기"],
    key='current_page' 
)

# 선택된 페이지에 따라 함수 실행
if menu_selection == "🏠 홈":
    run_home()
elif menu_selection == "📊 광고 성과 분석기":
    run_analyzer()
elif menu_selection == "🏷️ 상품명 제조기":
    run_namer()

# 푸터 (공통)
st.markdown("---")
st.markdown("<div style='text-align: center; color: #888;'>Developed by HoonPro Think Partner</div>", unsafe_allow_html=True)
