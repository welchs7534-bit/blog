import os
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """너는 인기 한국어 블로그 포스팅 전문 작가야.
반드시 아래 형식으로만 답해야 해. 다른 말은 절대 붙이지 마.
한자, 일본어, 중국어 문자를 절대 사용하지 마. 오직 순수한 한국어(한글, 영어, 숫자, 기본 문장부호)만 사용해.

[제목]: 여기에 제목
[본문]: 여기에 본문
[태그]: 태그1, 태그2, 태그3, 태그4, 태그5"""


def generate_post(news_data):
    title = news_data["title"]
    content = news_data["content"]

    prompt = f"""아래 뉴스를 인기 블로그 스타일로 새롭게 재작성해줘.

원본 제목: {title}
원본 내용: {content[:2000]}

[제목 작성 규칙]
- 긴급성이 느껴지는 표현 사용 ("당장", "지금 바로", "반드시" 등)
- 핵심 키워드를 괄호 안에 넣기 예: "당장 이것부터 끊어야 합니다!(콜레스테롤 낮추는 법)"
- 독자가 클릭하고 싶게 만들기
- 느낌표 또는 의문문 활용

[본문 작성 규칙]
- 원문 그대로 복사 절대 금지, 완전히 새로 작성
- 한자, 중국어, 일본어 문자 절대 사용 금지
- 1000자 이상 작성
- 다음 구조로 작성:
  1) 도입부: 독자의 공감을 끌어내는 2~3문장
  2) 번호 소제목 3~4개 사용 (예: **1. 소제목**)
  3) 각 소제목 아래 2~4문장 설명
  4) 핵심 정보는 **굵은 글씨**로 강조
  5) 마무리: 실용적인 조언이나 정리 2~3문장
- 친근하고 대화하는 듯한 말투
- 짧고 읽기 쉬운 문장 사용

반드시 이 형식으로만 답해:
[제목]: 새로운 제목
[본문]: 본문 내용
[태그]: 태그1, 태그2, 태그3, 태그4, 태그5"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )
    result = _parse_response(response.choices[0].message.content)

    # 한자/중국어/일본어 문자 제거
    def remove_cjk(text):
        return re.sub(r'[一-鿿぀-ゟ゠-ヿ]', '', text)

    result["title"] = remove_cjk(result["title"])
    result["body"] = remove_cjk(result["body"])

    # **굵은 글씨** → HTML <strong> 변환
    result["body"] = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', result["body"])

    return result


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

    if not result["title"] and not result["body"]:
        lines = text.strip().split("\n")
        result["title"] = lines[0][:60] if lines else "제목 없음"
        result["body"] = text
        result["tags"] = []

    return result
