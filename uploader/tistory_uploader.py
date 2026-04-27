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


def upload_post(post_data, image_data=None):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    wait = WebDriverWait(driver, 20)

    try:
        _login(driver, wait)
        _write_post(driver, wait, post_data, image_data)
        print(f"포스팅 완료: {post_data['title']}")
    finally:
        time.sleep(2)
        driver.quit()


def _login(driver, wait):
    driver.get("https://www.tistory.com/auth/login")
    time.sleep(2)

    id_input = wait.until(EC.presence_of_element_located((By.ID, "loginId")))
    id_input.send_keys(TISTORY_ID)

    pw_input = driver.find_element(By.ID, "loginPw")
    pw_input.send_keys(TISTORY_PW)

    driver.find_element(By.CLASS_NAME, "btn_login").click()
    time.sleep(3)


def _write_post(driver, wait, post_data, image_data):
    write_url = f"https://{TISTORY_BLOG_NAME}.tistory.com/manage/newpost"
    driver.get(write_url)
    time.sleep(3)

    # 제목 입력
    title_input = wait.until(EC.presence_of_element_located((By.ID, "post-title-inp")))
    title_input.clear()
    title_input.send_keys(post_data["title"])
    time.sleep(1)

    # 기본 모드로 전환 후 본문 입력
    driver.switch_to.frame(driver.find_element(By.ID, "editor-tistory_ifr"))
    body = driver.find_element(By.ID, "tinymce")
    body.clear()

    # 이미지 출처 문구 추가
    content = post_data["body"]
    if image_data:
        content += f'\n\n<p>📷 사진: <a href="{image_data["photographer_link"]}">{image_data["photographer"]}</a> on Unsplash</p>'

    body.send_keys(content)
    driver.switch_to.default_content()
    time.sleep(1)

    # 태그 입력
    if post_data.get("tags"):
        tag_input = driver.find_element(By.CLASS_NAME, "tf-tag")
        for tag in post_data["tags"]:
            tag_input.send_keys(tag)
            tag_input.send_keys(",")
        time.sleep(1)

    # 발행 버튼 클릭
    publish_btn = driver.find_element(By.CLASS_NAME, "btn-publish")
    publish_btn.click()
    time.sleep(2)

    confirm_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btn-publishing")))
    confirm_btn.click()
    time.sleep(3)
