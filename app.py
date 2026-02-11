import streamlit as st
import pandas as pd
import os
import sys
import time
import subprocess
import glob

# --- [1] 필수 라이브러리 자동 설치 로직 ---
def install_dependencies():
    required = {'undetected-chromedriver', 'pandas', 'openpyxl', 'setuptools'}
    try:
        import pkg_resources
        installed = {pkg.key for pkg in pkg_resources.working_set}
    except ImportError:
        installed = set()
    missing = required - installed
    if missing:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])

install_dependencies()

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- [2] Selenium 로그인 및 다운로드 함수 ---
def get_coupang_report_auto(user_id, user_pw):
    options = uc.ChromeOptions()
    # 다운로드 경로를 현재 폴더로 지정
    download_path = os.getcwd()
    prefs = {"download.default_directory": download_path}
    options.add_experimental_option("prefs", prefs)
    
    driver = uc.Chrome(options=options)
    try:
        driver.get("https://wing.coupang.com/login")
        # 로그인 수행
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(user_id)
        driver.find_element(By.ID, "password").send_keys(user_pw)
        driver.find_element(By.ID, "login-btn").click()

        st.info("💡 브라우저에서 2단계 인증을 완료해 주세요...")
        WebDriverWait(driver, 300).until(EC.url_contains("dashboard"))
        
        # 광고 보고서 페이지 이동 및 다운로드 (어제 기준 예시)
        driver.get("https://ad.coupang.com/m/reports/download")
        time.sleep(5)
        
        # '어제' 버튼 클릭 및 생성 (XPath는 쿠팡 업데이트에 따라 확인 필요)
        yesterday_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '어제')]"))
        )
        yesterday_btn.click()
        driver.find_element(By.XPATH, "//button[contains(., '보고서 생성')]").click()
        
        # 다운로드 버튼 대기 및 클릭
        dl_btn = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.LINK_TEXT, "다운로드")))
        dl_btn.click()
        time.sleep(5) # 파일 저장 시간
        return True
    except Exception as e:
        st.error(f"자동화 오류: {e}")
        return False
    finally:
        driver.quit()

# --- [3] 기존 Streamlit UI 설정 ---
st.set_page_config(page_title="훈프로 쿠팡 광고 분석기", layout="wide")
st.title("📊 쇼크트리 훈프로 쿠팡 광고 성과 분석기")

# --- 사이드바: 자동 로그인 세션 ---
st.sidebar.header("🔐 쿠팡 자동 연동")
expander = st.sidebar.expander("자동으로 보고서 가져오기")
with expander:
    c_id = st.text_input("쿠팡 아이디")
    c_pw = st.text_input("쿠팡 비밀번호", type="password")
    if st.button("데이터 자동 추출 시작"):
        if c_id and c_pw:
            with st.spinner("쿠팡에서 데이터를 가져오는 중..."):
                success = get_coupang_report_auto(c_id, c_pw)
                if success:
                    st.success("데이터 추출 완료! 아래에서 파일을 확인하세요.")
        else:
            st.warning("아이디와 비밀번호를 입력해주세요.")

st.sidebar.divider()
# ... (기존 마진 계산 로직 시작) ...
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

# --- [4] 파일 로드 로직 (업로드 + 자동추출 파일 대응) ---
st.subheader("📁 데이터 로드")
# 자동 추출된 파일이 있는지 확인
auto_files = glob.glob("광고일괄보고서*.csv") + glob.glob("광고일괄보고서*.xlsx")
default_file = auto_files[-1] if auto_files else None

uploaded_file = st.file_uploader("보고서 파일을 선택하세요 (자동 추출 시 자동 선택됨)", type=['csv', 'xlsx'])

# 업로드된 파일이 없으면 자동 추출된 최신 파일을 사용
final_file = uploaded_file if uploaded_file else default_file

if final_file:
    # ... (이후 김프로님의 기존 데이터 처리 및 분석 로직 그대로 유지) ...
    try:
        # 파일 읽기 부분 (final_file 변수 사용)
        if hasattr(final_file, 'name'): # 업로드 파일인 경우
             fname = final_file.name
        else: # 자동 추출된 로컬 파일 경로인 경우
             fname = final_file
             
        if fname.endswith('.csv'):
            try: df = pd.read_csv(final_file, encoding='utf-8-sig')
            except: df = pd.read_csv(final_file, encoding='cp949')
        else:
            df = pd.read_excel(final_file, engine='openpyxl')
            
        # (기존의 df 전처리 및 대시보드 출력 코드 시작)
        st.success(f"현재 분석 중인 파일: {fname}")
        
        # ... [이후 김프로님의 기존 코드와 동일] ...
        # (df 컬럼 공백 제거, summary 계산, 메트릭 출력, 지면별 상세 분석 등)
        
    except Exception as e:
        st.error(f"데이터 처리 중 오류 발생: {e}")

# (기존 푸터 로직)
st.divider()
st.markdown("<div style='text-align: center;'><a href='https://hoonpro.liveklass.com/' target='_blank'>🏠 쇼크트리 훈프로 홈페이지 바로가기</a></div>", unsafe_allow_html=True)