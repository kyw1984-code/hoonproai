import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="훈프로 쿠팡 광고 분석기", layout="wide")
st.title("📊 쇼크트리 훈프로 쿠팡 광고 성과 분석기")
st.markdown("쿠팡 보고서(CSV 또는 XLSX)를 업로드하면 훈프로의 정밀 운영 전략이 자동으로 생성됩니다.")

# --- 2. 사이드바: 수익성 계산 설정 ---
st.sidebar.header("💰 마진 계산 설정")
unit_price = st.sidebar.number_input("상품 판매가 (원)", min_value=0, value=0, step=100)
unit_cost = st.sidebar.number_input("최종원가(매입가 등) (원)", min_value=0, value=0, step=100)

# 로켓그로스 입출고비 및 수수료 설정
delivery_fee = st.sidebar.number_input("로켓그로스 입출고비 (원)", min_value=0, value=3650, step=10)
coupang_fee_rate = st.sidebar.number_input("쿠팡 수수료(vat포함) (%)", min_value=0.0, max_value=100.0, value=11.55, step=0.1)

# 수수료 금액 계산 (판매가 * 수수료율)
total_fee_amount = unit_price * (coupang_fee_rate / 100)

# 최종 마진 계산: 상품 판매가 - 최종원가 - 로켓그로스 입출고비 - 쿠팡 수수료
net_unit_margin = unit_price - unit_cost - delivery_fee - total_fee_amount

st.sidebar.divider()
st.sidebar.write(f"**📦 입출고비 합계:** {delivery_fee:,.0f}원")
st.sidebar.write(f"**📊 예상 수수료 ({coupang_fee_rate}%):** {total_fee_amount:,.0f}원")
st.sidebar.write(f"**💡 개당 예상 마진:** :green[{net_unit_margin:,.0f}원]") 

# 마진율 표시
if unit_price > 0:
    margin_rate = (net_unit_margin / unit_price) * 100
    st.sidebar.write(f"**📈 예상 마진율:** {margin_rate:.1f}%")

# 3. 파일 업로드
uploaded_file = st.file_uploader("보고서 파일을 선택하세요 (CSV 또는 XLSX)", type=['csv', 'xlsx'])

if uploaded_file is not None:
    try:
        # 파일 확장자에 따른 읽기 방식
        if uploaded_file.name.endswith('.csv'):
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
            except:
                df = pd.read_csv(uploaded_file, encoding='cp949')
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')

        # 데이터 전처리: 컬럼명 공백 제거
        df.columns = [str(c).strip() for c in df.columns]

        # 판매수량 컬럼 통합 검색
        qty_targets = ['총 판매수량(14일)', '총 판매수량(1일)', '총 판매수량', '전환 판매수량', '판매수량']
        col_qty = next((c for c in qty_targets if c in df.columns), None)

        if '광고 노출 지면' in df.columns and col_qty:
            # 수치 데이터 내 '-' 문자 제거 및 숫자 변환
            for col in ['노출수', '클릭수', '광고비', col_qty]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').replace('-', '0'), errors='coerce').fillna(0)

            # 4. 데이터 요약 분석
            target_cols = {'노출수': 'sum', '클릭수': 'sum', '광고비': 'sum', col_qty: 'sum'}
            summary = df.groupby('광고 노출 지면').agg(target_cols).reset_index()
            summary.columns = ['지면', '노출수', '클릭수', '광고비', '판매수량']

            # 실제 매출액 및 실제 ROAS 계산
            summary['실제매출액'] = summary['판매수량'] * unit_price
            summary['실제ROAS'] = (summary['실제매출액'] / summary['광고비']).fillna(0)
            summary['클릭률(CTR)'] = (summary['클릭수'] / summary['노출수']).fillna(0)
            summary['구매전환율(CVR)'] = (summary['판매수량'] / summary['클릭수']).fillna(0)
            summary['CPC'] = (summary['광고비'] / summary['클릭수']).fillna(0).astype(int)
            summary['실질순이익'] = (summary['판매수량'] * net_unit_margin) - summary['광고비']

            # 전체 합계 계산
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

            # 5. 성과 요약 대시보드
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

            # 6. 상세 분석 표 스타일링
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

            # --- [수정된 기능] 옵션별 성과 분석 ('광고집행 상품명' 기준) ---
            target_prod_col = '광고집행 상품명'
            if target_prod_col in df.columns:
                st.divider()
                st.subheader(f"🛍️ 옵션별 성과 분석")
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
                winning_products = prod_agg[prod_agg['판매수량'] > 0].sort_values(by='판매수량', ascending=False).reset_index(drop=True)
                winning_products.index = winning_products.index + 1
                if not winning_products.empty:
                    st.dataframe(winning_products.style.format({
                        '광고비': '{:,.0f}원', '판매수량': '{:,.0f}개', '실제매출액': '{:,.0f}원',
                        '실제ROAS': '{:.2%}', '실질순이익': '{:,.0f}원', '구매전환율(CVR)': '{:.2%}'
                    }).applymap(color_profit, subset=['실질순이익']), use_container_width=True)
                else:
                    st.info("판매가 발생한 상품 옵션이 없습니다.")

                st.write("")
                st.markdown("##### 💸 돈만 나가는 옵션 (판매 0건, 광고비 지출 순)")
                losing_products = prod_agg[(prod_agg['판매수량'] == 0) & (prod_agg['광고비'] > 0)].sort_values(by='광고비', ascending=False).reset_index(drop=True)
                losing_products.index = losing_products.index + 1
                if not losing_products.empty:
                    st.error(f"⚠️ 총 **{len(losing_products)}개**의 옵션이 판매 없이 광고비만 소진 중입니다.")
                    st.dataframe(losing_products[['상품명', '광고비', '노출수', '클릭수']].style.format({
                        '광고비': '{:,.0f}원', '노출수': '{:,.0f}', '클릭수': '{:,.0f}'
                    }), use_container_width=True)

            # --- 7. 판매 발생 키워드 (전체) ---
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
                good_kws = kw_agg_all[(kw_agg_all['판매수량'] > 0) & (kw_agg_all['키워드'] != '-')].sort_values(by='광고비', ascending=False).reset_index(drop=True)
                good_kws.index = good_kws.index + 1
                if not good_kws.empty:
                    st.success(f"✅ 현재 총 **{len(good_kws)}개**의 키워드에서 판매가 발생했습니다. (광고비 높은 순 정렬)")
                    st.dataframe(good_kws.style.format({
                        '광고비': '{:,.0f}원', '판매수량': '{:,.0f}개', '실제매출액': '{:,.0f}원', 
                        '실제ROAS': '{:.2%}', '실질순이익': '{:,.0f}원', '노출수': '{:,.0f}', '클릭수': '{:,.0f}'
                    }).applymap(color_profit, subset=['실질순이익']), use_container_width=True)

                st.divider()
                st.subheader("✂️ 돈먹는 키워드 (제외 대상 제안)")
                bad_kws = kw_agg_all[(kw_agg_all['광고비'] > 0) & (kw_agg_all['판매수량'] == 0) & (kw_agg_all['키워드'] != '-')].sort_values(by='광고비', ascending=False)
                if not bad_kws.empty:
                    st.error(f"⚠️ 현재 총 **{len(bad_kws)}개**의 키워드가 매출 없이 **{bad_kws['광고비'].sum():,.0f}원**의 광고비를 소진했습니다.")
                    st.text_area("📋 제외 키워드 목록:", value=", ".join(bad_kws['키워드'].astype(str).tolist()), height=120)

            # --- 8. 훈프로의 정밀 운영 제안 ---
            st.divider()
            st.subheader("💡 훈프로의 정밀 운영 제안")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info("🖼️ **클릭률(CTR) 분석**")
                ctr_val = total_data['클릭률(CTR)']
                st.write(f"- **현재 CTR: {ctr_val:.2%}**")
                if ctr_val < 0.01: st.write("- **액션**: 썸네일 교체 시급")
                else: st.write("- **상태**: 시각적 매력 충분")
            with col2:
                st.warning("🛒 **구매전환율(CVR) 분석**")
                cvr_val = total_data['구매전환율(CVR)']
                st.write(f"- **현재 CVR: {cvr_val:.2%}**")
                if cvr_val < 0.05: st.write("- **액션**: 상세페이지/리뷰 보완")
                else: st.write("- **상태**: 상세페이지 전환 능력 탁월")
            with col3:
                st.error("💰 **목표수익률 최적화 가이드**")
                st.write(f"- **현재 실제 ROAS: {total_real_roas:.2%}**")
                if total_real_roas < 2.0: st.write("🔴 **[200% 미만] 절대 손실 구간**")
                elif total_real_roas < 2.5: st.write("🟠 **[200%~250%] 심각한 적자 구간**")
                elif total_real_roas < 3.0: st.write("🟠 **[250%~300%] 적자 지속 구간**")
                elif total_real_roas < 3.5: st.write("🟡 **[300%~350%] 초기 수익(BEP) 구간**")
                elif total_real_roas < 4.0: st.write("🟡 **[350%~400%] 손익분기점 안착 구간**")
                elif total_real_roas < 4.5: st.write("🟢 **[400%~450%] 안정적 수익 구간**")
                elif total_real_roas < 5.0: st.write("🟢 **[450%~500%] 고수익 유지 구간**")
                elif total_real_roas < 5.5: st.write("🔵 **[500%~550%] 고효율 공격 단계**")
                elif total_real_roas < 6.0: st.write("🔵 **[550%~600%] 시장 점유 확장 단계**")
                else: st.write("🚀 **[600% 이상] 시장 지배 구간**")

    except Exception as e:
        st.error(f"데이터 처리 중 오류 발생: {e}")

# 푸터
st.divider()
st.markdown("<div style='text-align: center;'><a href='https://hoonpro.liveklass.com/' target='_blank'>🏠 쇼크트리 훈프로 홈페이지 바로가기</a></div>", unsafe_allow_html=True)
