import streamlit as st

# 페이지 설정
st.set_page_config(page_title="훈프로 쿠팡 상품명 생성기", layout="centered")

st.title("🏷️ 쇼크트리 훈프로 쿠팡 상품명 제조기")
st.markdown("입력값이 수정되면 상품명이 **실시간으로 자동 변경**됩니다.")
st.divider()

# --- 입력 섹션 ---
st.subheader("1. 상품 정보 입력")

col1, col2 = st.columns(2)
with col1:
    brand = st.text_input("브랜드 (없으면 공란)", placeholder="예: 나이키, 훈프로")
    # [변경됨] "남성" -> "남자"
    target = st.selectbox("타겟 (성별/대상)", ["", "남자", "여성", "남녀공용", "아동", "유아", "키즈", "성인"])
    season = st.multiselect("시즌 (여러개 선택 가능)", ["봄", "여름", "가을", "겨울", "간절기", "사계절"], default=[])

with col2:
    # [순서 유지] 제품명1 -> 소구점 -> 제품명2 -> 구성
    main_keyword = st.text_input("제품명 1 (핵심 키워드) *필수", placeholder="예: 반팔티, 원피스")
    appeal_point = st.text_input("소구점 (특징/재질/핏)", placeholder="예: 오버핏, 린넨, 구김없는")
    sub_keyword = st.text_input("제품명 2 (세부 키워드)", placeholder="예: 라운드티, 롱원피스")
    set_info = st.text_input("구성 (몇종/세트)", placeholder="예: 3종 세트, 1+1")

# 시즌 리스트를 문자열로 변환
season_str = " ".join(season)

# --- 생성 로직 (실시간 반영) ---
def clean_join(parts):
    # 빈 값 제거하고 공백으로 연결
    return " ".join([p.strip() for p in parts if p.strip()])

# 공식 적용 (입력 즉시 계산됨)
# 공식: 브랜드 + 타겟 + 시즌 + 제품명 1 + 소구점 + 제품명 2 + 구성
final_title = clean_join([brand, target, season_str, main_keyword, appeal_point, sub_keyword, set_info])

# --- 결과 출력 섹션 ---
st.divider()
st.subheader("2. 생성된 상품명 확인")

# 핵심 키워드가 입력되는 순간부터 결과를 보여줍니다.
if main_keyword:
    st.markdown("##### ✅ 최종 상품명")
    st.caption("공식: 브랜드 + 타겟 + 시즌 + 제품명1 + 소구점 + 제품명2 + 구성")
    
    # 결과 출력 (입력값 변경 시 즉시 업데이트)
    st.text_input("결과", value=final_title, key="result_final")
    
    # 글자수 확인
    text_len = len(final_title)
    st.caption(f"📏 글자수: {text_len}자 (공백 포함)")

    # --- 유효성 검사 ---
    st.markdown("---")
    st.subheader("🔍 훈프로의 상품명 진단")
    
    # 1. 글자수 체크
    if text_len > 50:
        st.warning(f"⚠️ **길이 주의 ({text_len}자):** 50자를 넘으면 모바일 목록에서 뒷부분이 잘릴 수 있습니다.")
    else:
        st.success(f"✅ **길이 적합 ({text_len}자):** 모바일 가독성이 좋은 길이입니다.")

    # 2. 중복 단어 체크
    words = final_title.split()
    duplicates = set([x for x in words if words.count(x) > 1])
    if duplicates:
        st.error(f"🚫 **중복 단어 발견:** '{', '.join(duplicates)}' 단어가 중복되었습니다. 쿠팡 어뷰징 방지를 위해 하나를 삭제해주세요.")
    else:
        st.success("✅ **중복 없음:** 깔끔한 키워드 조합입니다.")
    
    # [삭제됨] 팁(Tip) 섹션

else:
    st.info("👆 위 칸에 '제품명 1'을 입력하면 상품명이 자동으로 생성됩니다.")

# 푸터
st.markdown("---")
st.markdown("<div style='text-align: center; color: #888;'>Developed by HoonPro Think Partner</div>", unsafe_allow_html=True)
