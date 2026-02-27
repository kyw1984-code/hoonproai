import streamlit as st
import requests
import pandas as pd
import time

# 페이지 기본 설정
st.set_page_config(
    page_title="쿠팡 연관 검색어 추출기",
    page_icon="🛒",
    layout="wide"
)

st.title("🛒 쿠팡 자동완성 검색어 추출기")
st.markdown("쿠팡 검색창에 뜨는 **자동완성 키워드**를 실시간으로 가져옵니다.")

# -------------------------------------------------------------------------
# 함수: 쿠팡 자동완성 키워드 가져오기
# -------------------------------------------------------------------------
def get_coupang_keywords(keyword):
    # 쿠팡 자동완성 API URL
    url = "https://completer.coupang.com/complete/GetResult"
    
    # 봇 차단을 방지하기 위한 헤더 설정 (일반 브라우저인 척 위장)
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.coupang.com/",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    params = {
        "keyword": keyword,
        "resultSize": 20  # 가져올 최대 개수
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        
        if response.status_code == 200:
            # JSON 응답 파싱
            data = response.json()
            # 데이터 구조: {'keyword': '...', 'result': [{'keyword': '...', ...}, ...]}
            
            # 검색 결과 리스트 추출
            if "result" in data:
                keywords = [item["keyword"] for item in data["result"]]
                return keywords
            else:
                return []
        else:
            st.error(f"데이터를 가져오는데 실패했습니다. 상태 코드: {response.status_code}")
            return []
            
    except Exception as e:
        st.error(f"에러 발생: {e}")
        return []

# -------------------------------------------------------------------------
# 메인 UI
# -------------------------------------------------------------------------
with st.form("search_form"):
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input("검색어를 입력하세요 (예: 노트북, 마스크)", placeholder="키워드 입력")
    with col2:
        submitted = st.form_submit_button("키워드 추출 🚀")

if submitted and user_input:
    with st.spinner(f"'{user_input}' 연관 검색어 수집 중..."):
        # 너무 빠른 반복 요청 방지를 위한 딜레이 (선택 사항)
        time.sleep(0.5) 
        
        result_list = get_coupang_keywords(user_input)
        
        if result_list:
            st.success(f"총 {len(result_list)}개의 키워드를 찾았습니다!")
            
            # 결과 표시 (데이터프레임 & 리스트)
            df = pd.DataFrame(result_list, columns=["연관 키워드"])
            
            # 화면 분할
            res_col1, res_col2 = st.columns(2)
            
            with res_col1:
                st.markdown("### 📋 리스트 보기")
                st.dataframe(df, use_container_width=True)
            
            with res_col2:
                st.markdown("### 📥 복사하기 쉬운 텍스트")
                text_output = "\n".join(result_list)
                st.text_area("결과 복사", value=text_output, height=400)
                
                # CSV 다운로드 버튼
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="CSV로 다운로드",
                    data=csv,
                    file_name=f"coupang_{user_input}_keywords.csv",
                    mime="text/csv",
                )
        else:
            st.warning("연관 검색어가 없거나 가져오지 못했습니다.")

elif submitted and not user_input:
    st.warning("검색어를 입력해주세요.")