import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

load_dotenv()
TISTORY_ID = os.getenv("TISTORY_ID")
TISTORY_PW = os.getenv("TISTORY_PW")
TISTORY_BLOG_NAME = os.getenv("TISTORY_BLOG_NAME")


def _get_chromedriver_path():
    path = ChromeDriverManager().install()
    import os
    driver_dir = os.path.dirname(path)
    exe_path = os.path.join(driver_dir, "chromedriver.exe")
    if os.path.exists(exe_path):
        return exe_path
    return path


def upload_post(post_data, image_data=None):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(
        service=Service(_get_chromedriver_path()),
        options=options
    )
    wait = WebDriverWait(driver, 20)

    try:
        _login(driver, wait)
        print(f"로그인 후 현재 URL: {driver.current_url}")
        _write_post(driver, wait, post_data, image_data)
        print(f"포스팅 완료: {post_data['title']}")
    finally:
        time.sleep(2)
        driver.quit()


def _login(driver, wait):
    driver.get("https://www.tistory.com/auth/login")
    time.sleep(3)
    print(f"  현재 URL: {driver.current_url}")

    # 카카오계정으로 로그인 버튼 클릭
    print("  카카오 로그인 버튼 클릭 중...")
    time.sleep(2)

    # 페이지의 모든 클릭 가능한 요소 중 첫 번째 버튼/링크 클릭
    kakao_btn = None
    for selector in [
        (By.CSS_SELECTOR, "a.btn_login_kakao"),
        (By.CSS_SELECTOR, "a[href*='kakao']"),
        (By.CSS_SELECTOR, "button[class*='kakao']"),
        (By.XPATH, "//a[contains(@class,'link_kakao') or contains(@class,'kakao')]"),
        (By.CSS_SELECTOR, ".wrap_login a"),
        (By.CSS_SELECTOR, "a.btn_kakao"),
        (By.TAG_NAME, "a"),
    ]:
        try:
            kakao_btn = driver.find_element(*selector)
            if kakao_btn.is_displayed():
                break
        except Exception:
            continue

    if kakao_btn:
        kakao_btn.click()
    time.sleep(4)
    print(f"  카카오 페이지 URL: {driver.current_url}")

    # 카카오 로그인 페이지 - 이메일 입력
    print("  이메일 입력 중...")
    id_input = WebDriverWait(driver, 30).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "input[name='loginId'], input[type='email'], input[autocomplete='username']")
    ))
    id_input.clear()
    id_input.send_keys(TISTORY_ID)
    time.sleep(0.5)

    # 비밀번호 입력
    print("  비밀번호 입력 중...")
    pw_input = driver.find_element(
        By.CSS_SELECTOR, "input[name='password'], input[type='password']"
    )
    pw_input.clear()
    pw_input.send_keys(TISTORY_PW)
    time.sleep(0.5)

    # 로그인 버튼 클릭
    login_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
    login_btn.click()
    time.sleep(5)
    print(f"  로그인 완료 URL: {driver.current_url}")

    # 티스토리 제3자 동의 페이지 처리
    if "agreement" in driver.current_url or "consent" in driver.current_url:
        print("  동의 페이지 처리 중...")
        try:
            agree_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(),'동의') or contains(text(),'확인') or contains(text(),'agree')]")
            ))
            agree_btn.click()
            time.sleep(3)
        except Exception:
            # 모든 체크박스 체크 후 확인 버튼 클릭
            checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            for cb in checkboxes:
                if not cb.is_selected():
                    cb.click()
            time.sleep(1)
            for btn_text in ["동의", "확인", "agree", "submit"]:
                try:
                    btn = driver.find_element(By.XPATH, f"//button[contains(text(),'{btn_text}')]")
                    btn.click()
                    break
                except Exception:
                    continue
            time.sleep(3)
        print(f"  동의 후 URL: {driver.current_url}")


def _write_post(driver, wait, post_data, image_data):
    write_url = f"https://{TISTORY_BLOG_NAME}.tistory.com/manage/newpost"
    driver.get(write_url)
    time.sleep(4)

    # 이전 임시저장 팝업 처리 (취소 = 새 글 작성)
    try:
        alert = driver.switch_to.alert
        alert.dismiss()
        time.sleep(1)
    except Exception:
        pass

    print(f"  글쓰기 페이지 URL: {driver.current_url}")

    # BMP 범위 밖 문자 제거 함수
    def clean(text):
        return "".join(c for c in text if ord(c) <= 0xFFFF)

    # 제목 입력 - JavaScript로 직접 설정
    driver.execute_script("""
        var el = document.querySelector('#post-title-inp');
        if(el) {
            el.focus();
            el.value = arguments[0];
            el.dispatchEvent(new Event('input', {bubbles:true}));
            el.dispatchEvent(new Event('change', {bubbles:true}));
        }
    """, clean(post_data["title"]))
    time.sleep(1)
    print("  제목 입력 완료")

    # 본문 내용 준비
    content = clean(post_data["body"])
    if image_data:
        content += f'\n\n사진: {clean(image_data["photographer"])} on Unsplash'
    content_html = content.replace("\n", "<br>")

    # 본문 입력 - 새 티스토리 에디터 (contenteditable div)
    driver.execute_script("""
        // 새 에디터 (contenteditable)
        var editors = document.querySelectorAll('[contenteditable=true]');
        for(var i=0; i<editors.length; i++){
            var el = editors[i];
            if(el.className && (el.className.includes('ProseMirror') ||
               el.className.includes('editor') || el.className.includes('content'))) {
                el.focus();
                el.innerHTML = arguments[0];
                el.dispatchEvent(new Event('input', {bubbles:true}));
                break;
            }
        }
        // TinyMCE 폴백
        if(typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
            tinyMCE.activeEditor.setContent(arguments[0]);
        }
    """, content_html)
    time.sleep(1)
    print("  본문 입력 완료")

    # 태그 입력
    if post_data.get("tags"):
        for sel in [".tf-tag", "input.tag", "input[placeholder*='태그']", ".area_tag input"]:
            try:
                tag_input = driver.find_element(By.CSS_SELECTOR, sel)
                for tag in post_data["tags"]:
                    tag_input.send_keys(clean(tag))
                    tag_input.send_keys(",")
                print("  태그 입력 완료")
                break
            except Exception:
                continue
        time.sleep(1)

    # 발행(완료) 버튼 클릭
    for sel, by in [
        (".btn_complete", By.CSS_SELECTOR),
        (".btn-publish", By.CSS_SELECTOR),
        (".btn_publish", By.CSS_SELECTOR),
        ("//button[contains(text(),'완료')]", By.XPATH),
        ("//button[contains(text(),'발행')]", By.XPATH),
    ]:
        try:
            btn = driver.find_element(by, sel)
            btn.click()
            print("  발행 버튼 클릭")
            break
        except Exception:
            continue
    time.sleep(2)

    # 발행 확인 팝업이 뜨면 확인 클릭
    try:
        for sel, by in [
            (".btn-publishing", By.CSS_SELECTOR),
            ("//button[contains(text(),'공개')]", By.XPATH),
            ("//button[contains(text(),'발행')]", By.XPATH),
        ]:
            try:
                confirm_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((by, sel)))
                confirm_btn.click()
                print("  발행 확인 완료")
                break
            except Exception:
                continue
    except Exception:
        pass
    time.sleep(3)
