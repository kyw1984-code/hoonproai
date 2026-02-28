import streamlit as st

# 페이지 설정
st.set_page_config(page_title="훈프로 쿠팡 상품명 생성기", layout="centered")

st.title("🏷️ 쇼크트리 훈프로 쿠팡 상품명 제조기")
st.markdown("쿠팡 SEO 로직에 맞춰 상품명을 자동으로 조합하고 최적화합니다.")
st.divider()

# --- 입력 섹션 ---
st.subheader("1. 상품 정보 입력")

col1, col2 = st.columns(2)
with col1:
    brand = st.text_input("브랜드 (없으면 공란)", placeholder="예: 나이키, 훈프로")
    target = st.selectbox("타겟 (성별/대상)", ["", "남성", "여성", "남녀공용", "아동", "유아", "키즈", "성인"])
    season = st.multiselect("시즌 (여러개 선택 가능)", ["봄", "여름", "가을", "겨울", "간절기", "사계절"], default=[])

with col2:
    main_keyword = st.text_input("제품명 1 (핵심 키워드) *필수", placeholder="예: 반팔티, 원피스")
    sub_keyword = st.text_input("제품명 2 (세부 키워드)", placeholder="예: 라운드티, 롱원피스")
    appeal_point = st.text_input("소구점 (특징/재질/핏)", placeholder="예: 오버핏, 린넨, 구김없는")
    set_info = st.text_input("구성 (몇종/세트)", placeholder="예: 3종 세트, 1+1")

# 시즌 리스트를 문자열로 변환
season_str = " ".join(season)

# --- 생성 로직 ---
def clean_join(parts):
    # 빈 값 제거하고 공백으로 연결
    return " ".join([p.strip() for p in parts if p.strip()])

# 1. 사용자 요청 공식
# 공식: 브랜드 + 타겟 + 시즌 + 제품명 1 + 소구점 + 제품명 2 + 몇종세트
user_title = clean_join([brand, target, season_str, main_keyword, appeal_point, sub_keyword, set_info])

# 2. 훈프로 추천 SEO 공식 (쿠팡 최적화)
# 의견: 브랜드 직후에 핵심 키워드(제품명1)가 오는 것이 검색 노출에 유리합니다.
# 소구점(형용사)은 제품명 앞으로 보내 자연스럽게 수식하는 것이 가독성에 좋습니다.
# 공식: [브랜드] + 소구점 + 타겟/시즌 + 제품명 1 + 제품명 2 + 구성
seo_title = clean_join([brand, appeal_point, target, season_str, main_keyword, sub_keyword, set_info])

# 3. 가독성 중심 공식 (모바일 최적화)
# 공식: [브랜드] 제품명 1 + 제품명 2 + (타겟/시즌/소구점) + 구성
readable_title = clean_join([brand, main_keyword, sub_keyword, target, season_str, appeal_point, set_info])


# --- 결과 출력 섹션 ---
st.divider()
st.subheader("2. 생성된 상품명 확인")

if main_keyword:
    # 탭으로 구분하여 보여주기
    tab1, tab2, tab3 = st.tabs(["사용자 맞춤형", "🏆 쿠팡 SEO 추천", "📱 가독성 추천"])

    with tab1:
        st.caption("요청하신 공식대로 조합된 상품명입니다.")
        st.success("공식: 브랜드 + 타겟 + 시즌 + 제품명1 + 소구점 + 제품명2 + 구성")
        st.text_input("결과 (복사 가능)", value=user_title, key="t1")
        st.caption(f"글자수: {len(user_title)}자 (공백 포함)")

    with tab2:
        st.caption("💡 훈프로 추천! 검색 알고리즘이 좋아하는 순서입니다.")
        st.info("공식: 브랜드 + 소구점 + 타겟/시즌 + 제품명1(핵심) + 제품명2 + 구성")
        st.markdown("**추천 이유:** 브랜드 뒤에 핵심 키워드가 빨리 나올수록 정확도가 올라갑니다.")
        st.text_input("결과 (복사 가능)", value=seo_title, key="t2")
        st.caption(f"글자수: {len(seo_title)}자 (공백 포함)")

    with tab3:
        st.caption("고객이 모바일에서 한눈에 상품을 파악하기 좋은 순서입니다.")
        st.warning("공식: 브랜드 + 제품명1 + 제품명2 + (수식어들) + 구성")
        st.text_input("결과 (복사 가능)", value=readable_title, key="t3")
        st.caption(f"글자수: {len(readable_title)}자 (공백 포함)")

    # --- 유효성 검사 및 팁 ---
    st.divider()
    st.subheader("🔍 훈프로의 상품명 진단")
    
    # 1. 글자수 체크
    if len(seo_title) > 50:
        st.warning("⚠️ **길이 주의:** 상품명이 50자를 넘으면 모바일 목록에서 뒷부분이 잘릴 수 있습니다. 핵심 키워드를 앞쪽으로 배치하세요.")
    else:
        st.success("✅ **길이 적합:** 50자 이내로 모바일 가독성이 좋습니다.")

    # 2. 중복 단어 체크
    words = seo_title.split()
    duplicates = set([x for x in words if words.count(x) > 1])
    if duplicates:
        st.error(f"🚫 **중복 단어 발견:** '{', '.join(duplicates)}' 단어가 중복되었습니다. 쿠팡은 동일 단어 반복을 어뷰징으로 간주할 수 있으니 하나를 삭제하세요.")
    else:
        st.success("✅ **중복 없음:** 깔끔한 키워드 조합입니다.")

    # 3. 특수문자 팁
    if set_info and not any(c in set_info for c in ['[', ']', '(', ')']):
        st.info("💡 **팁:** 구성(세트) 정보에는 대괄호 `[ ]`를 사용하면 눈에 더 잘 띕니다. (예: [3종 세트])")

else:
    st.info("👆 위 칸에 '제품명 1'을 입력하면 상품명이 자동으로 생성됩니다.")

# 푸터
st.markdown("---")
st.markdown("<div style='text-align: center; color: #888;'>Developed by HoonPro Think Partner</div>", unsafe_allow_html=True)
