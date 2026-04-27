from crawler.news_crawler import crawl_news
from ai_writer.content_generator import generate_post
from uploader.image_fetcher import fetch_image
from uploader.tistory_uploader import upload_post


def main():
    print("=" * 50)
    print("  블로그 자동 포스팅 프로그램")
    print("=" * 50)

    url = input("\n뉴스 URL을 입력하세요: ").strip()
    if not url:
        print("URL을 입력해주세요.")
        return

    print("\n[1/4] 뉴스 내용 수집 중...")
    news_data = crawl_news(url)
    print(f"제목: {news_data['title']}")

    print("\n[2/4] AI가 글을 재작성 중...")
    post_data = generate_post(news_data)
    print(f"새 제목: {post_data['title']}")
    print(f"태그: {', '.join(post_data['tags'])}")

    print("\n[3/4] 이미지 검색 중...")
    keyword = post_data["tags"][0] if post_data["tags"] else news_data["title"][:20]
    image_data = fetch_image(keyword)
    if image_data:
        print(f"이미지 찾음: {image_data['photographer']} on Unsplash")
    else:
        print("이미지를 찾지 못했습니다. 이미지 없이 포스팅합니다.")

    print("\n[4/4] 티스토리에 포스팅 중...")
    print("잠시 후 브라우저가 자동으로 열립니다...")
    upload_post(post_data, image_data)

    print("\n✅ 포스팅이 완료되었습니다!")
    print("=" * 50)


if __name__ == "__main__":
    main()
