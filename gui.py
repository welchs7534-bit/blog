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

# ── 색상 팔레트 ──────────────────────────────
C = {
    "bg":         "#f0f2f5",
    "card":       "#ffffff",
    "header_bg":  "#1e1e2e",
    "header_sub": "#a0a0c0",
    "accent":     "#7c6ff7",
    "accent_h":   "#6459e0",
    "success":    "#00b894",
    "success_h":  "#00a381",
    "danger":     "#d63031",
    "text":       "#2d3436",
    "text2":      "#636e72",
    "border":     "#dfe6e9",
    "log_bg":     "#1a1b26",
    "log_fg":     "#c0caf5",
    "log_ok":     "#9ece6a",
    "log_err":    "#f7768e",
    "log_info":   "#7dcfff",
    "log_warn":   "#e0af68",
}

FONT_TITLE  = ("맑은 고딕", 18, "bold")
FONT_SUB    = ("맑은 고딕",  9)
FONT_LABEL  = ("맑은 고딕", 10, "bold")
FONT_BODY   = ("맑은 고딕", 10)
FONT_BTN    = ("맑은 고딕", 11, "bold")
FONT_LOG    = ("Consolas",   9)


def load_settings():
    s = {"GROQ_API_KEY":"","UNSPLASH_ACCESS_KEY":"",
         "TISTORY_ID":"","TISTORY_PW":"","TISTORY_BLOG_NAME":""}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                if k.strip() in s:
                    s[k.strip()] = v.strip()
    return s


def save_settings(s):
    lines = [f"{k}={v}" for k, v in s.items()]
    ENV_FILE.write_text("\n".join(lines), encoding="utf-8")


# ── 커스텀 위젯 헬퍼 ─────────────────────────

def card(parent, **kw):
    f = tk.Frame(parent, bg=C["card"], bd=0, highlightthickness=1,
                 highlightbackground=C["border"], **kw)
    return f


def label(parent, text, font=FONT_BODY, fg=None, bg=None, **kw):
    return tk.Label(parent, text=text, font=font,
                    fg=fg or C["text"], bg=bg or C["card"], **kw)


def hover_btn(parent, text, cmd, bg, hover, fg="white", font=FONT_BTN, **kw):
    b = tk.Button(parent, text=text, command=cmd, font=font,
                  bg=bg, fg=fg, activebackground=hover, activeforeground=fg,
                  relief="flat", bd=0, cursor="hand2", **kw)
    b.bind("<Enter>", lambda e: b.config(bg=hover))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


class RoundEntry(tk.Frame):
    """Entry with colored left border accent."""
    def __init__(self, parent, show="", **kw):
        super().__init__(parent, bg=C["card"], bd=0,
                         highlightthickness=1, highlightbackground=C["border"])
        self._accent = tk.Frame(self, bg=C["accent"], width=4)
        self._accent.pack(side="left", fill="y")
        self._var = tk.StringVar()
        self._entry = tk.Entry(self, textvariable=self._var, show=show,
                               font=FONT_BODY, bd=0, relief="flat",
                               bg=C["card"], fg=C["text"],
                               insertbackground=C["text"], **kw)
        self._entry.pack(side="left", fill="both", expand=True,
                         padx=(8, 8), pady=6)
        self.bind("<FocusIn>",  lambda e: self.config(highlightbackground=C["accent"]))
        self.bind("<FocusOut>", lambda e: self.config(highlightbackground=C["border"]))
        self._entry.bind("<FocusIn>",  lambda e: self.config(highlightbackground=C["accent"]))
        self._entry.bind("<FocusOut>", lambda e: self.config(highlightbackground=C["border"]))

    def get(self): return self._var.get()
    def set(self, v): self._var.set(v)


class BlogApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("블로그 자동 포스팅")
        self.geometry("660x680")
        self.resizable(False, False)
        self.configure(bg=C["bg"])
        try:
            self.iconbitmap(BASE_DIR / "icon.ico")
        except Exception:
            pass
        self._build_ui()
        self._load_settings()

    # ── UI 구성 ──────────────────────────────

    def _build_ui(self):
        self._build_header()
        self._build_tabs()

    def _build_header(self):
        h = tk.Frame(self, bg=C["header_bg"], height=80)
        h.pack(fill="x")
        h.pack_propagate(False)

        inner = tk.Frame(h, bg=C["header_bg"])
        inner.place(relx=.5, rely=.5, anchor="center")

        tk.Label(inner, text="블로그 자동 포스팅",
                 font=("맑은 고딕", 17, "bold"),
                 fg="white", bg=C["header_bg"]).pack()
        tk.Label(inner, text="뉴스 URL 하나로 티스토리 자동 발행",
                 font=FONT_SUB, fg=C["header_sub"],
                 bg=C["header_bg"]).pack()

        # 탭 버튼 바
        tab_bar = tk.Frame(self, bg=C["header_bg"], height=40)
        tab_bar.pack(fill="x")
        tab_bar.pack_propagate(False)

        self._tab_btns = {}
        for name, idx in [("  포스팅  ", 0), ("  설정  ", 1)]:
            b = tk.Button(tab_bar, text=name, font=("맑은 고딕", 10),
                          bd=0, relief="flat", cursor="hand2",
                          fg="white", bg=C["header_bg"],
                          activeforeground="white",
                          activebackground=C["accent"],
                          command=lambda i=idx: self._switch_tab(i))
            b.pack(side="left", ipady=8, ipadx=6)
            self._tab_btns[idx] = b
        self._switch_tab(0)

    def _build_tabs(self):
        self._pages = {}
        container = tk.Frame(self, bg=C["bg"])
        container.pack(fill="both", expand=True)

        for i, builder in enumerate([self._page_post, self._page_settings]):
            f = tk.Frame(container, bg=C["bg"])
            f.place(relwidth=1, relheight=1)
            builder(f)
            self._pages[i] = f

    def _switch_tab(self, idx):
        for i, f in self._pages.items():
            f.lift() if i == idx else f.lower()
        for i, b in self._tab_btns.items():
            b.config(bg=C["accent"] if i == idx else C["header_bg"])

    # ── 포스팅 탭 ────────────────────────────

    def _page_post(self, parent):
        wrap = tk.Frame(parent, bg=C["bg"])
        wrap.pack(fill="both", expand=True, padx=20, pady=16)

        # URL 입력 카드
        c1 = card(wrap)
        c1.pack(fill="x", pady=(0, 12))
        inner = tk.Frame(c1, bg=C["card"])
        inner.pack(fill="x", padx=16, pady=14)

        label(inner, "뉴스 URL", FONT_LABEL).pack(anchor="w")
        label(inner, "네이버·다음 등 뉴스 기사 주소를 붙여넣으세요",
              FONT_SUB, fg=C["text2"]).pack(anchor="w", pady=(2, 8))

        self._url_entry = RoundEntry(inner)
        self._url_entry.pack(fill="x")

        # 시작 버튼
        self._start_btn = hover_btn(
            wrap, "  포스팅 시작  ", self._start,
            C["success"], C["success_h"],
            pady=12
        )
        self._start_btn.pack(fill="x", pady=(0, 12))

        # 진행 상황 카드
        c2 = card(wrap)
        c2.pack(fill="both", expand=True)
        top = tk.Frame(c2, bg=C["card"])
        top.pack(fill="x", padx=16, pady=(12, 6))
        label(top, "진행 상황", FONT_LABEL).pack(side="left")
        hover_btn(top, "지우기", self._clear_log,
                  C["border"], C["text2"], fg=C["text2"],
                  font=("맑은 고딕", 8), pady=2, padx=6).pack(side="right")

        self._log = scrolledtext.ScrolledText(
            c2, font=FONT_LOG, state="disabled",
            bg=C["log_bg"], fg=C["log_fg"],
            selectbackground=C["accent"],
            relief="flat", bd=0, padx=10, pady=8,
            insertbackground=C["log_fg"]
        )
        self._log.pack(fill="both", expand=True, padx=1, pady=(0, 1))

        # 로그 색상 태그
        for tag, col in [("ok", C["log_ok"]), ("err", C["log_err"]),
                         ("info", C["log_info"]), ("warn", C["log_warn"])]:
            self._log.tag_config(tag, foreground=col)

    # ── 설정 탭 ──────────────────────────────

    def _page_settings(self, parent):
        wrap = tk.Frame(parent, bg=C["bg"])
        wrap.pack(fill="both", expand=True, padx=20, pady=16)

        sections = [
            ("AI 설정", [
                ("Groq API 키", "GROQ_API_KEY", False,
                 "console.groq.com 에서 무료 발급"),
                ("Unsplash Access Key", "UNSPLASH_ACCESS_KEY", False,
                 "unsplash.com/developers 에서 무료 발급"),
            ]),
            ("티스토리 계정", [
                ("이메일 (카카오 계정)", "TISTORY_ID", False, ""),
                ("비밀번호",            "TISTORY_PW", True,  ""),
                ("블로그 주소",         "TISTORY_BLOG_NAME", False,
                 "예: myblog  →  myblog.tistory.com"),
            ]),
        ]

        self._sv = {}
        for section_title, fields in sections:
            # 섹션 헤더
            tk.Label(wrap, text=section_title, font=("맑은 고딕", 10, "bold"),
                     fg=C["accent"], bg=C["bg"]).pack(anchor="w", pady=(8, 4))

            c = card(wrap)
            c.pack(fill="x", pady=(0, 6))
            inner = tk.Frame(c, bg=C["card"])
            inner.pack(fill="x", padx=16, pady=12)

            for i, (lbl, key, pw, hint) in enumerate(fields):
                if i > 0:
                    tk.Frame(inner, bg=C["border"], height=1).pack(fill="x", pady=8)
                row = tk.Frame(inner, bg=C["card"])
                row.pack(fill="x")
                label(row, lbl, FONT_LABEL, bg=C["card"]).pack(anchor="w")
                if hint:
                    label(row, hint, FONT_SUB, fg=C["text2"],
                          bg=C["card"]).pack(anchor="w", pady=(1, 4))
                e = RoundEntry(row, show="*" if pw else "")
                e.pack(fill="x", pady=(2, 0))
                self._sv[key] = e

        hover_btn(
            wrap, "  설정 저장  ", self._save_settings,
            C["accent"], C["accent_h"], pady=11
        ).pack(fill="x", pady=(12, 0))

    # ── 로직 ─────────────────────────────────

    def _load_settings(self):
        s = load_settings()
        for k, e in self._sv.items():
            e.set(s.get(k, ""))

    def _save_settings(self):
        s = {k: e.get().strip() for k, e in self._sv.items()}
        save_settings(s)
        messagebox.showinfo("저장 완료", "설정이 저장되었습니다.")

    def _log_write(self, msg, tag=None):
        self._log.configure(state="normal")
        self._log.insert("end", msg + "\n", tag or "")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _clear_log(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    def _start(self):
        url = self._url_entry.get().strip()
        if not url:
            messagebox.showwarning("알림", "뉴스 URL을 입력해주세요.")
            return
        s = load_settings()
        if not s["GROQ_API_KEY"] or not s["TISTORY_ID"]:
            messagebox.showwarning("알림", "설정 탭에서 API 키와 티스토리 정보를 먼저 입력해주세요.")
            self._switch_tab(1)
            return
        self._start_btn.config(state="disabled", text="  포스팅 중...  ",
                               bg="#b2bec3", activebackground="#b2bec3")
        self._clear_log()
        threading.Thread(target=self._run, args=(url,), daemon=True).start()

    def _run(self, url):
        def log(msg, tag=None):
            self.after(0, self._log_write, msg, tag)

        try:
            if str(BASE_DIR) not in sys.path:
                sys.path.insert(0, str(BASE_DIR))
            os.chdir(BASE_DIR)
            from dotenv import load_dotenv
            load_dotenv(ENV_FILE, override=True)

            log("━" * 44, "info")
            log("[1/4]  뉴스 내용 수집 중...", "info")
            from crawler.news_crawler import crawl_news
            news = crawl_news(url)
            log(f"  제목: {news['title']}", "ok")

            log("\n[2/4]  AI가 글을 재작성 중...", "info")
            from ai_writer.content_generator import generate_post
            post = generate_post(news)
            log(f"  새 제목: {post['title']}", "ok")
            log(f"  태그: {', '.join(post['tags'][:5])}", "ok")

            log("\n[3/4]  이미지 검색 중...", "info")
            from uploader.image_fetcher import fetch_image
            kw = post["tags"][0] if post["tags"] else news["title"][:20]
            img = fetch_image(kw)
            if img:
                log(f"  이미지: {img['photographer']} on Unsplash", "ok")
            else:
                log("  이미지를 찾지 못했습니다.", "warn")

            log("\n[4/4]  티스토리에 포스팅 중...", "info")
            log("  브라우저가 자동으로 열립니다...", "warn")
            from uploader.tistory_uploader import upload_post
            upload_post(post, img, wait_after=False)

            log(f"\n  완료: {post['title']}", "ok")
            log("━" * 44, "info")
            self.after(0, lambda: messagebox.showinfo(
                "완료", f"포스팅이 완료되었습니다!\n\n{post['title']}"))

        except Exception as e:
            log(f"\n오류: {e}", "err")
            self.after(0, lambda: messagebox.showerror("오류", str(e)))
        finally:
            self.after(0, lambda: self._start_btn.config(
                state="normal", text="  포스팅 시작  ",
                bg=C["success"], activebackground=C["success_h"]))


if __name__ == "__main__":
    app = BlogApp()
    app.mainloop()
