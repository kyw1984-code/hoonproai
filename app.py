import os
import sys
import time
import subprocess
import glob
import pandas as pd
import streamlit as st

# --- [1] 필수 라이브러리 자동 설치 (파이썬 3.12+ 호환성 보완) ---
def prepare_env():
    # undetected-chromedriver 실행에 필요한 setuptools 포함
    required = {'undetected-chromedriver', 'pandas', 'openpyxl', 'setuptools'}
    try:
        import pkg_resources
        installed = {pkg.key for pkg in pkg_resources.working_set}
    except ImportError:
        installed = set()
    
    missing = required - installed
    if missing:
        st.info(f"🛠️ 첫 실행을 위한 라이브러리 설치 중... {missing}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        st.success("✅ 설치 완료! 프로그램을 시작합니다.")

prepare_env()

# 설치 후 임포트
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- [2] Selenium 로그인 및 다운로드 로직 ---
def run_selenium_automation(user_id, user_pw):
    options = uc.ChromeOptions()
    current_folder = os.getcwd()
    
    # 다운로드 파일을 현재 폴더로 저장하도록 설정
    prefs = {
        "download.default_directory": current_folder,
        "download.prompt_for_download": False,
        "directory_upgrade": True
    }
    options.add_experimental_option("prefs", prefs)
    
    driver = uc.Chrome(options=options)
    try:
        # 1. 로그인
        driver.get("https://wing.coupang.com/login")
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(user_id)
        driver.find_element(By.ID, "password").send_keys(user_pw)
        driver.find_element(By.ID, "login-btn").click()

        # 2. 2단계 인증 대기
        st.warning("⚠️ 브라우저 창에서 휴대폰 인증을 완료해 주세요! (인증 후 자동 진행)")
        WebDriverWait(driver, 300).until(EC.url_contains("dashboard"))
        
        # 3. 광고 보고서 페이지 이동
        driver.get("https://ad.coupang.com/m/reports/download")
        time.sleep(5)
        
        # 4. '어제' 버튼 클릭 및 생성
        yesterday_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '어제')]"))
        )
        yesterday_btn.click()
        driver.find_element(By.XPATH, "//button[contains(., '보고서 생성')]").click()
        
        # 5. 다운로드
        dl_btn = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.LINK_TEXT, "다운로드")))
        dl_btn.click()
        time.sleep(5) # 파일 저장 시간 확보
        return True
    except Exception as e:
        st.error(f"실행 오류: {e}")
        return False
    finally:
        driver.quit()

# --- [3] 메인 UI 구성 ---
st.set_page_config(page_title="훈프로 쿠팡 광고 분석기", layout="wide")
st.title("📊 쇼크트리 훈프로 쿠팡 광고 성과 분석기")

# 사이드바
st.sidebar.header("🔐 쿠팡 계정 연동")
c_id = st.sidebar.text_input("아이디")
c_pw = st.sidebar.text_input("비밀번호", type="password")

if st.sidebar.button("🚀 자동 데이터 추출"):
    if c_id and c_pw:
        with st.spinner("쿠팡에서 보고서를 가져오는 중..."):
            if run_selenium_automation(c_id, c_pw):
                st.sidebar.success("추출 완료! 화면을 새로고침 하세요.")
                st.rerun()
    else:
        st.sidebar.error("ID와 PW를 입력하세요.")

# --- 기존 마진 계산 로직 (김프로님 코드) ---
st.sidebar.divider()
st.sidebar.header("💰 마진 계산 설정")
unit_price = st.sidebar.number_input("상품 판매가 (원)", min_value=0, value=0)
unit_cost = st.sidebar.number_input("최종원가 (원)", min_value=0, value=0)
delivery_fee = st.sidebar.number_input("로켓그로스 입출고비 (원)", min_value=0, value=3650)
coupang_fee_rate = st.sidebar.number_input("쿠팡 수수료 (%)", min_value=0.0, value=11.55)

total_fee_amount = unit_price * (coupang_fee_rate / 100)
net_unit_margin = unit_price - unit_cost - delivery_fee - total_fee_amount
st.sidebar.write(f"**💡 개당 예상 마진:** :green[{net_unit_margin:,.0f}원]")

# --- [4] 데이터 분석 및 출력 ---
# 현재 폴더에서 '광고일괄보고서' 파일 찾기
target_files = glob.glob("광고일괄보고서*.csv") + glob.glob("광고일괄보고서*.xlsx")
latest_file = max(target_files, key=os.path.getctime) if target_files else None

if latest_file:
    st.success(f"현재 분석 파일: {os.path.basename(latest_file)}")
    # 여기에 김프로님의 기존 데이터 프레임 전처리 및 시각화 코드를 연결하세요.
    # df = pd.read_csv(latest_file, ...)
else:
    st.info("사이드바에서 자동 추출을 진행하거나 보고서 파일을 업로드해 주세요.")

st.divider()
st.markdown("<center><a href='https://hoonpro.liveklass.com/'>🏠 홈페이지 바로가기</a></center>", unsafe_allow_html=True)