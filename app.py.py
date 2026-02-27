import streamlit as st
import requests
import urllib.parse
import json

# 페이지 설정
st.set_page_config(page_title="쿠팡 키워드 소싱기", page_icon="🌳", layout="centered")

def get_coupang_autocomplete(keyword):
    # 쿠팡 자동완성 API (callback을 비워 순수 JSON으로 받음)
    url = f"https://www.coupang.com/np/search/autoComplete?callback=&keyword={urllib.parse.quote(keyword)}"
    
    # 🌟 차단 방지를 위한 브라우저 헤더 완벽 위장 (가장 중요)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.coupang.com/",
        "X-Requested-With": "XMLHttpRequest"
    }

    try:
        # timeout을 설정하여 무한 대기 방지
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status() 
        
        # 텍스트 형태의 응답을 JSON으로 파싱
        data = json.loads(response.text)
        keywords = []
        
        # 자동완성 데이터 추출 로직
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and 'keyword' in item:
                    keywords.append(item['keyword'])
                    
        return keywords
    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다. (IP가 일시적으로 차단되었을 수 있습니다) \n\n 에러: {e}")
        return []

# UI 구성
st.title("🌳 쿠팡 자동완성 키워드 추출기")
st.markdown("사용자가 쿠팡 검색창에 입력 시 노출되는 **실시간 연관 검색어**를 수집합니다.")

search_keyword = st.text_input("메인 키워드를 입력하세요:", placeholder="예: 무선 마우스")

if st.button("키워드 추출하기", type="primary"):
    if search_keyword.strip():
        with st.spinner('쿠팡에서 키워드 데이터를 수집 중입니다...'):
            results = get_coupang_autocomplete(search_keyword)
            
            if results:
                st.success(f"성공적으로 {len(results)}개의 연관 키워드를 찾았습니다!")
                
                # 가독성을 위해 리스트로 출력
                st.write("### 📌 추천 키워드 리스트")
                for i, kw in enumerate(results, 1):
                    st.write(f"{i}. **{kw}**")
            else:
                st.warning("추출된 키워드가 없거나 쿠팡 서버에서 응답을 거부했습니다.")
    else:
        st.warning("키워드를 먼저 입력해주세요.")