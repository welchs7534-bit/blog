import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import os
import sys
from pathlib import Path


def get_base_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent


BASE_DIR = get_base_dir()
ENV_FILE = BASE_DIR / ".env"


def load_settings():
    settings = {
        "GROQ_API_KEY": "",
        "UNSPLASH_ACCESS_KEY": "",
        "TISTORY_ID": "",
        "TISTORY_PW": "",
        "TISTORY_BLOG_NAME": "",
    }
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                if k.strip() in settings:
                    settings[k.strip()] = v.strip()
    return settings


def save_settings(settings):
    lines = []
    for k, v in settings.items():
        lines.append(f"{k}={v}")
    ENV_FILE.write_text("\n".join(lines), encoding="utf-8")


class BlogApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("블로그 자동 포스팅 프로그램")
        self.geometry("620x600")
        self.resizable(False, False)
        self.configure(bg="#f5f5f5")

        # 아이콘 없으면 그냥 넘김
        try:
            self.iconbitmap(BASE_DIR / "icon.ico")
        except Exception:
            pass

        self._build_ui()
        self._load_settings_to_ui()

    def _build_ui(self):
        # 헤더
        header = tk.Frame(self, bg="#2c3e50", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header, text="블로그 자동 포스팅 프로그램",
            font=("맑은 고딕", 15, "bold"), fg="white", bg="#2c3e50"
        ).pack(expand=True)

        # 탭
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self._build_post_tab()
        self._build_settings_tab()

    def _build_post_tab(self):
        frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(frame, text="  포스팅  ")

        # URL 입력
        tk.Label(frame, text="뉴스 URL 입력", font=("맑은 고딕", 11, "bold")).pack(anchor="w")
        tk.Label(frame, text="네이버 뉴스, 다음 뉴스 등 기사 URL을 붙여넣으세요.",
                 font=("맑은 고딕", 9), fg="#666").pack(anchor="w")

        url_frame = tk.Frame(frame)
        url_frame.pack(fill="x", pady=(5, 10))
        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(url_frame, textvariable=self.url_var,
                                   font=("맑은 고딕", 10), relief="solid", bd=1)
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=6)

        # 시작 버튼
        self.start_btn = tk.Button(
            frame, text="포스팅 시작", font=("맑은 고딕", 11, "bold"),
            bg="#2ecc71", fg="white", relief="flat", cursor="hand2",
            padx=20, pady=8, command=self._start_posting
        )
        self.start_btn.pack(fill="x", pady=(0, 10))

        # 진행 로그
        tk.Label(frame, text="진행 상황", font=("맑은 고딕", 10, "bold")).pack(anchor="w")
        self.log_area = scrolledtext.ScrolledText(
            frame, height=18, font=("Consolas", 9),
            state="disabled", bg="#1e1e1e", fg="#d4d4d4",
            relief="flat", bd=0
        )
        self.log_area.pack(fill="both", expand=True)

    def _build_settings_tab(self):
        frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(frame, text="  설정  ")

        fields = [
            ("Groq API 키", "GROQ_API_KEY", False,
             "console.groq.com 에서 발급 (무료)"),
            ("Unsplash Access Key", "UNSPLASH_ACCESS_KEY", False,
             "unsplash.com/developers 에서 발급 (무료)"),
            ("티스토리 이메일", "TISTORY_ID", False,
             "카카오 계정 이메일"),
            ("티스토리 비밀번호", "TISTORY_PW", True,
             "카카오 계정 비밀번호"),
            ("블로그 주소", "TISTORY_BLOG_NAME", False,
             "예: newchallenge7534  (xxx.tistory.com 에서 xxx 부분)"),
        ]

        self.setting_vars = {}
        for label, key, is_pw, hint in fields:
            tk.Label(frame, text=label, font=("맑은 고딕", 10, "bold")).pack(anchor="w", pady=(8, 0))
            tk.Label(frame, text=hint, font=("맑은 고딕", 8), fg="#888").pack(anchor="w")
            var = tk.StringVar()
            show = "*" if is_pw else ""
            entry = tk.Entry(frame, textvariable=var, show=show,
                             font=("맑은 고딕", 10), relief="solid", bd=1)
            entry.pack(fill="x", ipady=5, pady=(2, 0))
            self.setting_vars[key] = var

        tk.Button(
            frame, text="설정 저장", font=("맑은 고딕", 11, "bold"),
            bg="#3498db", fg="white", relief="flat", cursor="hand2",
            padx=20, pady=8, command=self._save_settings
        ).pack(fill="x", pady=(15, 0))

    def _load_settings_to_ui(self):
        s = load_settings()
        for key, var in self.setting_vars.items():
            var.set(s.get(key, ""))

    def _save_settings(self):
        s = {k: v.get().strip() for k, v in self.setting_vars.items()}
        save_settings(s)
        messagebox.showinfo("저장 완료", "설정이 저장되었습니다.")

    def _log(self, msg):
        self.log_area.configure(state="normal")
        self.log_area.insert("end", msg + "\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")

    def _clear_log(self):
        self.log_area.configure(state="normal")
        self.log_area.delete("1.0", "end")
        self.log_area.configure(state="disabled")

    def _start_posting(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("알림", "뉴스 URL을 입력해주세요.")
            return

        s = load_settings()
        if not s["GROQ_API_KEY"] or not s["TISTORY_ID"]:
            messagebox.showwarning("알림", "설정 탭에서 API 키와 티스토리 정보를 먼저 입력해주세요.")
            self.notebook.select(1)
            return

        self.start_btn.configure(state="disabled", text="포스팅 중...", bg="#95a5a6")
        self._clear_log()
        threading.Thread(target=self._run_posting, args=(url,), daemon=True).start()

    def _run_posting(self, url):
        try:
            # sys.path에 현재 디렉토리 추가
            if str(BASE_DIR) not in sys.path:
                sys.path.insert(0, str(BASE_DIR))

            os.chdir(BASE_DIR)

            # 환경변수 로드
            from dotenv import load_dotenv
            load_dotenv(ENV_FILE, override=True)

            self._log("[1/4] 뉴스 내용 수집 중...")
            from crawler.news_crawler import crawl_news
            news_data = crawl_news(url)
            self._log(f"  제목: {news_data['title']}")

            self._log("\n[2/4] AI가 글을 재작성 중...")
            from ai_writer.content_generator import generate_post
            post_data = generate_post(news_data)
            self._log(f"  새 제목: {post_data['title']}")
            self._log(f"  태그: {', '.join(post_data['tags'][:5])}")

            self._log("\n[3/4] 이미지 검색 중...")
            from uploader.image_fetcher import fetch_image
            keyword = post_data["tags"][0] if post_data["tags"] else news_data["title"][:20]
            image_data = fetch_image(keyword)
            if image_data:
                self._log(f"  이미지: {image_data['photographer']} on Unsplash")
            else:
                self._log("  이미지를 찾지 못했습니다.")

            self._log("\n[4/4] 티스토리에 포스팅 중...")
            self._log("  브라우저가 자동으로 열립니다...")
            from uploader.tistory_uploader import upload_post
            upload_post(post_data, image_data, wait_after=False)

            self._log(f"\n포스팅 완료: {post_data['title']}")
            self._log("=" * 45)
            self.after(0, lambda: messagebox.showinfo("완료", f"포스팅이 완료되었습니다!\n\n{post_data['title']}"))

        except Exception as e:
            self._log(f"\n오류 발생: {e}")
            self.after(0, lambda: messagebox.showerror("오류", str(e)))

        finally:
            self.after(0, lambda: self.start_btn.configure(
                state="normal", text="포스팅 시작", bg="#2ecc71"
            ))


if __name__ == "__main__":
    app = BlogApp()
    app.mainloop()
