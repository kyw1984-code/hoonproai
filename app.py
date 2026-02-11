import os
import sys
import time
import subprocess
import glob
import pandas as pd
import streamlit as st

# --- [1] 필수 라이브러리 자동 설치 및 환경 세팅 ---
def prepare_environment():
    # 파이썬 3.12+에서 제거된 distutils 대응을 위해 setuptools 필수 포함
    required = {'undetected-chromedriver', 'pandas', 'openpyxl', 'setuptools'}
    try:
        import pkg_resources
        installed = {pkg.key for pkg in pkg_resources.working_set}
    except ImportError:
        installed = set()
    
    missing = required - installed
    if missing:
        st.info(f"🛠️ 첫 실행에 필요한 라이브러리를 설치 중입니다: {missing}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        st.success("✅ 설치 완료! 잠시만 기다려주세요.")

prepare_environment()

# 설치 후 라이브러리 임포트
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- [2] Selenium 자동화: 로그인 및 보고서 다운로드 ---
def run_auto_download(user_id, user_pw):
    options = uc.ChromeOptions()
    current_dir = os.getcwd() # 현재 파이썬 파일이 있는 폴더
    
    # 다운로드 설정: 현재 폴더로 파일이 들어오도록 세팅
    prefs = {
        "download.default_directory": current_dir,
        "download.prompt_for_download": False,
        "directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)
    
    driver = uc.Chrome(options=options)
    try:
        # 1. 쿠팡 윙 로그인
        driver.get("https://wing.coupang.com/login")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(user_id)
        driver.find_element(By.ID, "password").send_keys(user_pw)
        driver.find_element(By.ID, "login-btn").click()

        # 2. 2단계 인증 대기
        st.warning("⚠️ 브라우저에서 2단계 인증을 완료해 주세요. 완료 시 자동으로 진행됩니다.")
        WebDriverWait(driver, 300).until(EC.url_contains("dashboard"))
        
        # 3. 광고 보고서 페이지로 직접 이동
        driver.get("https://ad.coupang.com/m/reports/download")
        time.sleep(5)
        
        # 4. '어제' 버튼 클릭 및 생성
        yesterday_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '어제')]"))
        )
        yesterday_btn.click()
        time.sleep(1)
        driver.find_element(By.XPATH, "//button[contains(., '보고서 생성')]").click()
        
        # 5. 다운로드 버튼 클릭
        print("보고서 생성 대기 중...")
        dl_btn = WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "다운로드"))
        )
        dl_btn.click()
        time.sleep(5) # 파일 저장 완료 대기
        return True
    except Exception as e:
        st.error(f"❌ 자동화 실행 중 오류 발생: {e}")
        return False
    finally:
        driver.quit()

# --- [3] 메인 UI 구성 (기존 김프로님 코드 통합) ---
st.set_page_config(page_title="훈프로 쿠팡 광고 분석기", layout="wide")
st.title("📊 쇼크트리 훈프로 쿠팡 광고 성과 분석기")
st.markdown("쿠팡 WING 연동을 통해 훈프로의 정밀 운영 전략을 자동으로 확인하세요.")

# 사이드바: 자동 연동 및 마진 설정
st.sidebar.header("🔐 쿠팡 연동")
c_id = st.sidebar.text_input("쿠팡 아이디")
c_pw = st.sidebar.text_input("쿠팡 비밀번호", type="password")

if st.sidebar.button("🚀 자동 데이터 추출 시작"):
    if c_id and c_pw:
        with st.spinner("쿠팡 데이터를 가져오는 중..."):
            if run_auto_download(c_id, c_pw):
                st.sidebar.success("추출 성공! 데이터를 분석합니다.")
                st.rerun()
    else:
        st.sidebar.error("ID/PW를 입력해주세요.")

st.sidebar.divider()
st.sidebar.header("💰 마진 계산 설정")
unit_price = st.sidebar.number_input("상품 판매가 (원)", min_value=0, value=0, step=100)
unit_cost = st.sidebar.number_input("최종원가(매입가 등) (원)", min_value=0, value=0, step=100)
delivery_fee = st.sidebar.number_input("로켓그로스 입출고비 (원)", min_value=0, value=3650, step=10)
coupang_fee_rate = st.sidebar.number_input("쿠팡 수수료(vat포함) (%)", min_value=0.0, max_value=100.0, value=11.55, step=0.1)

# 마진 계산 로직
total_fee_amount = unit_price * (coupang_fee_rate / 100)
net_unit_margin = unit_price - unit_cost - delivery_fee - total_fee_amount

st.sidebar.write(f"**💡 개당 예상 마진:** :green[{net_unit_margin:,.0f}원]") 

# --- [4] 데이터 로드 및 분석 로직 ---
# 현재 폴더에서 '광고일괄보고서'로 시작하는 최신 파일 찾기
target_files = glob.glob("광고일괄보고서*.csv") + glob.glob("광고일괄보고서*.xlsx")
latest_file = max(target_files, key=os.path.getctime) if target_files else None

# 파일 업로더도 유지 (수동 업로드 대비)
uploaded_file = st.file_uploader("또는 보고서 파일을 직접 선택하세요", type=['csv', 'xlsx'])
final_file = uploaded_file if uploaded_file else latest_file

if final_file:
    try:
        # 파일 읽기 (자동 추출/업로드 구분)
        fname = final_file.name if hasattr(final_file, 'name') else final_file
        if fname.endswith('.csv'):
            try: df = pd.read_csv(final_file, encoding='utf-8-sig')
            except: df = pd.read_csv(final_file, encoding='cp949')
        else:
            df = pd.read_excel(final_file, engine='openpyxl')

        # --- 데이터 전처리 및 시각화 (김프로님의 기존 분석 로직) ---
        df.columns = [str(c).strip() for c in df.columns]
        qty_targets = ['총 판매수량(14일)', '총 판매수량(1일)', '총 판매수량', '전환 판매수량', '판매수량']
        col_qty = next((c for c in qty_targets if c in df.columns), None)

        if '광고 노출 지면' in df.columns and col_qty:
            for col in ['노출수', '클릭수', '광고비', col_qty]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').replace('-', '0'), errors='coerce').fillna(0)

            # 지면별 요약
            summary = df.groupby('광고 노출 지면').agg({'노출수':'sum', '클릭수':'sum', '광고비':'sum', col_qty:'sum'}).reset_index()
            summary.columns = ['지면', '노출수', '클릭수', '광고비', '판매수량']
            
            # (이하 기존 지표 계산 및 대시보드 출력 코드 동일하게 적용...)
            st.success(f"✅ 분석 파일: {os.path.basename(fname)}")
            st.dataframe(summary) # 예시로 요약표 출력
            
            # [김프로님의 상세 분석 제안 로직들을 여기에 유지하시면 됩니다]
            
    except Exception as e:
        st.error(f"데이터 분석 중 오류 발생: {e}")
else:
    st.info("사이드바에서 자동 추출을 시작하거나 보고서 파일을 업로드해 주세요.")

# 푸터
st.divider()
st.markdown("<div style='text-align: center;'><a href='https://hoonpro.liveklass.com/' target='_blank'>🏠 쇼크트리 훈프로 홈페이지 바로가기</a></div>", unsafe_allow_html=True)