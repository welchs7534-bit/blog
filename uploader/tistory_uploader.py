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


def upload_post(post_data, image_data=None, wait_after=True):
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
        if wait_after:
            input("\n브라우저 확인 후 엔터를 누르면 종료됩니다...")
        else:
            time.sleep(3)
    finally:
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

    # 제목 입력 - input 또는 contenteditable 모두 처리
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys

    title_el = None
    for sel in ["#post-title-inp", ".tit-post", "[placeholder*='제목']"]:
        try:
            title_el = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, sel))
            )
            break
        except Exception:
            continue

    if title_el:
        title_el.click()
        time.sleep(0.5)
        # 전체 선택 후 지우기
        title_el.send_keys(Keys.CONTROL + "a")
        title_el.send_keys(Keys.DELETE)
        time.sleep(0.3)
        title_el.send_keys(clean(post_data["title"]))
        time.sleep(0.5)
    print("  제목 입력 완료")

    # 본문 HTML 변환 (가독성 최적화)
    import re as _re

    def to_html(text):
        # 단락 분리 (빈 줄 기준)
        paragraphs = _re.split(r'\n{2,}', text.strip())
        html = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            # 번호 소제목: <strong>1. 제목</strong> → <h3> 태그
            para = _re.sub(
                r'<strong>(\d+\..+?)</strong>',
                r'<h3 style="font-size:18px; font-weight:bold; margin-top:30px; margin-bottom:8px; color:#1a1a1a;">\1</h3>',
                para
            )
            # 단락 내 줄바꿈 → <br>
            para = para.replace('\n', '<br>')
            # h3 포함 단락은 p 태그 없이
            if para.startswith('<h3'):
                html.append(para)
            else:
                html.append(
                    f'<p style="line-height:1.9; margin-bottom:18px; font-size:15px;">{para}</p>'
                )
        return '\n'.join(html)

    content = clean(post_data["body"])
    content_html = to_html(content)

    if image_data:
        img_html = (
            f'<p style="margin:25px 0; text-align:center;">'
            f'<img src="{image_data["url"]}" style="max-width:100%; border-radius:8px;" '
            f'alt="{clean(image_data["photographer"])}"/></p>'
            f'<p style="font-size:12px; color:#999; text-align:center; margin-bottom:20px;">'
            f'사진: {clean(image_data["photographer"])} on Unsplash</p>'
        )
        content_html = content_html + "\n" + img_html

    # 본문 입력 - TinyMCE setContent API 사용
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys

    # 메인 문서에서 tinyMCE API 호출
    inserted = driver.execute_script("""
        if(typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
            tinyMCE.activeEditor.setContent(arguments[0]);
            tinyMCE.activeEditor.save();
            return 'tinyMCE.setContent 성공';
        }
        if(typeof tinymce !== 'undefined' && tinymce.activeEditor) {
            tinymce.activeEditor.setContent(arguments[0]);
            tinymce.activeEditor.save();
            return 'tinymce.setContent 성공';
        }
        return 'tinyMCE 없음';
    """, content_html)

    if "없음" in str(inserted):
        # iframe 안에서 시도
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            try:
                driver.switch_to.frame(iframe)
                result = driver.execute_script("""
                    if(typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                        tinyMCE.activeEditor.setContent(arguments[0]);
                        return 'iframe tinyMCE 성공';
                    }
                    var el = document.getElementById('tinymce');
                    if(el) {
                        el.focus();
                        document.execCommand('selectAll', false, null);
                        document.execCommand('insertText', false, arguments[1]);
                        return 'iframe execCommand 성공';
                    }
                    return null;
                """, content_html, content)
                driver.switch_to.default_content()
                if result:
                    inserted = result
                    break
            except Exception:
                try:
                    driver.switch_to.default_content()
                except Exception:
                    pass

    time.sleep(1)
    print(f"  본문 입력 완료: {inserted}")

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

    # 완료 버튼 클릭 (JavaScript로 텍스트 기반 클릭)
    clicked = driver.execute_script("""
        var btns = document.querySelectorAll('button');
        for(var i=0; i<btns.length; i++){
            var t = btns[i].innerText.trim();
            if(t === '완료' || t === '발행' || t === '저장') {
                btns[i].click();
                return btns[i].innerText.trim();
            }
        }
        return null;
    """)
    print(f"  완료 버튼 클릭: {clicked}")
    time.sleep(4)

    time.sleep(2)

    # "공개" 라디오 버튼 클릭 (label 텍스트가 정확히 "공개"인 것)
    driver.execute_script("""
        var labels = document.querySelectorAll('label');
        for(var i=0; i<labels.length; i++){
            if(labels[i].innerText.trim() === '공개') {
                labels[i].click();
                return;
            }
        }
        // label 안의 input[type=radio] 직접 클릭
        var radios = document.querySelectorAll('input[type=radio]');
        if(radios.length > 0) radios[0].click();
    """)
    time.sleep(1)
    print("  공개 설정 완료")

    # 버튼 텍스트 확인 후 클릭 (비공개 저장 → 발행 으로 바뀌었는지)
    clicked2 = driver.execute_script("""
        var btns = document.querySelectorAll('button');
        var all = [];
        for(var i=0; i<btns.length; i++){
            var t = btns[i].innerText.trim();
            if(btns[i].offsetParent !== null && t) all.push(t);
        }
        // 비공개 저장이 아닌 저장/발행 버튼 클릭
        for(var i=0; i<btns.length; i++){
            var t = btns[i].innerText.trim();
            if(btns[i].offsetParent !== null &&
               (t === '발행' || t === '저장' || t === '공개 저장' || t === '공개 발행') &&
               t !== '비공개 저장') {
                btns[i].click();
                return '클릭: ' + t;
            }
        }
        // 그래도 없으면 비공개 저장이라도 클릭
        for(var i=0; i<btns.length; i++){
            var t = btns[i].innerText.trim();
            if(btns[i].offsetParent !== null && t.includes('저장')) {
                btns[i].click();
                return '클릭(폴백): ' + t;
            }
        }
        return 'NOTFOUND: ' + all.join('|');
    """)
    print(f"  발행 버튼: {clicked2}")
    time.sleep(4)
