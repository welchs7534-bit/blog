import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")


def generate_post(news_data):
    title = news_data["title"]
    content = news_data["content"]

    prompt = f"""
아래 뉴스 기사를 블로그 포스팅용으로 새롭게 작성해줘.

[원본 제목]
{title}

[원본 내용]
{content[:3000]}

[작성 조건]
- 원문을 그대로 복사하지 말고 완전히 새롭게 재작성할 것
- 친근하고 읽기 쉬운 말투로 작성
- 800자 이상 작성
- 블로그 포스팅 형식으로 단락 구분
- 제목은 SEO에 유리하게 새로 만들기
- 마지막에 핵심 키워드 5개를 쉼표로 구분해서 [태그: 키워드1, 키워드2, ...]형식으로 추가

결과물 형식:
[제목]: 새로운 제목
[본문]: 본문 내용
[태그]: 태그1, 태그2, 태그3, 태그4, 태그5
"""

    response = model.generate_content(prompt)
    return _parse_response(response.text)


def _parse_response(text):
    result = {"title": "", "body": "", "tags": []}

    lines = text.strip().split("\n")
    current_section = None
    body_lines = []

    for line in lines:
        if line.startswith("[제목]:"):
            result["title"] = line.replace("[제목]:", "").strip()
            current_section = "title"
        elif line.startswith("[본문]:"):
            current_section = "body"
            body_lines.append(line.replace("[본문]:", "").strip())
        elif line.startswith("[태그]:"):
            tags_str = line.replace("[태그]:", "").strip()
            result["tags"] = [t.strip() for t in tags_str.split(",")]
            current_section = "tags"
        elif current_section == "body":
            body_lines.append(line)

    result["body"] = "\n".join(body_lines).strip()
    return result
