import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading, os, sys
from pathlib import Path


def get_base_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent

BASE_DIR = get_base_dir()
ENV_FILE = BASE_DIR / ".env"

BG       = "#070b18"
BG2      = "#0d1226"
ACCENT   = "#1a8fff"
ACCENT_H = "#0e6dd4"
TEXT     = "#ffffff"
TEXT2    = "#6a7fa8"
LINE     = "#1e2d4a"
LINE_ACT = "#1a8fff"
SUCCESS  = "#00c896"
WARN     = "#e0af68"
ERR      = "#f7768e"
INFO     = "#7dcfff"

F_LOGO  = ("맑은 고딕", 20, "bold")
F_SUB   = ("맑은 고딕",  9)
F_LABEL = ("맑은 고딕",  8)
F_INPUT = ("맑은 고딕", 12)
F_BTN   = ("맑은 고딕", 11, "bold")
F_LOG   = ("Consolas",   9)


def load_settings():
    s = {"GROQ_API_KEY":"","UNSPLASH_ACCESS_KEY":"",
         "TISTORY_ID":"","TISTORY_PW":"","TISTORY_BLOG_NAME":""}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k,v = line.split("=",1)
                if k.strip() in s: s[k.strip()] = v.strip()
    return s

def save_settings(s):
    ENV_FILE.write_text("\n".join(f"{k}={v}" for k,v in s.items()), encoding="utf-8")


class UnderlineEntry(tk.Frame):
    """밑줄 스타일 입력창"""
    def __init__(self, parent, label="", show="", bg=BG2, **kw):
        super().__init__(parent, bg=bg)
        self._bg = bg
        tk.Label(self, text=label, font=F_LABEL, fg=ACCENT, bg=bg).pack(anchor="w")
        self._var = tk.StringVar()
        self._e = tk.Entry(self, textvariable=self._var, show=show,
                           font=F_INPUT, bd=0, relief="flat",
                           bg=bg, fg=TEXT, insertbackground=TEXT,
                           highlightthickness=0, **kw)
        self._e.pack(fill="x", pady=(4, 4))
        self._line = tk.Frame(self, bg=LINE, height=2)
        self._line.pack(fill="x")
        self._e.bind("<FocusIn>",  lambda e: self._line.config(bg=LINE_ACT))
        self._e.bind("<FocusOut>", lambda e: self._line.config(bg=LINE))

    def get(self): return self._var.get()
    def set(self, v): self._var.set(v)
    def focus(self): self._e.focus()


class GlowButton(tk.Canvas):
    """파란 글로우 버튼"""
    def __init__(self, parent, text, cmd, width=380, height=46,
                 color=ACCENT, hover=ACCENT_H, **kw):
        super().__init__(parent, width=width, height=height,
                         bd=0, highlightthickness=0, bg=BG2, **kw)
        self._text = text
        self._cmd  = cmd
        self._c    = color
        self._h    = hover
        self._draw(color)
        self.bind("<Enter>",          lambda e: self._draw(hover))
        self.bind("<Leave>",          lambda e: self._draw(color))
        self.bind("<ButtonRelease-1>", lambda e: cmd())
        self.config(cursor="hand2")

    def _draw(self, color):
        self.delete("all")
        r = 8
        w, h = int(self["width"]), int(self["height"])
        self.create_rounded_rect(0, 0, w, h, r, fill=color, outline="")
        self.create_text(w//2, h//2, text=self._text,
                         font=F_BTN, fill=TEXT)

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kw):
        pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
               x2,y2-r, x2,y2, x2-r,y2, x1+r,y2,
               x1,y2, x1,y2-r, x1,y1+r, x1,y1]
        return self.create_polygon(pts, smooth=True, **kw)

    def set_state(self, text, color=None):
        self._text = text
        self._draw(color or self._c)


class BlogApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("블로그 자동 포스팅")
        self.geometry("760x640")
        self.resizable(False, False)
        self.configure(bg=BG)
        try: self.iconbitmap(BASE_DIR/"icon.ico")
        except: pass

        self._pages = {}
        self._build()
        self._load()

    # ─── 빌드 ────────────────────────────────

    def _build(self):
        self._draw_bg()
        self._build_center()

    def _draw_bg(self):
        """오로라 느낌 배경"""
        c = tk.Canvas(self, width=760, height=640,
                      bd=0, highlightthickness=0, bg=BG)
        c.place(x=0, y=0)
        # 왼쪽 상단 오로라 포인트 (청록)
        for i, alpha in enumerate(range(80, 0, -8)):
            r = 180 + i*18
            x, y = -20, -20
            col = f"#{0:02x}{max(0,20-i):02x}{max(0,40-i*2):02x}"
            try:
                c.create_oval(x-r, y-r, x+r, y+r,
                              fill=col, outline="")
            except: pass
        # 오른쪽 하단 포인트 (파랑)
        for i in range(6):
            r = 160 + i*20
            col = f"#{0:02x}{0:02x}{max(0,35-i*4):02x}"
            try:
                c.create_oval(700-r, 600-r, 700+r, 600+r,
                              fill=col, outline="")
            except: pass
        c.lower()

    def _build_center(self):
        outer = tk.Frame(self, bg=BG)
        outer.place(relx=.5, rely=.5, anchor="center")

        # 반투명 카드 효과 (약간 밝은 배경)
        card = tk.Frame(outer, bg=BG2, bd=0,
                        highlightthickness=1,
                        highlightbackground="#1a2a4a")
        card.pack(padx=0, pady=0)
        inner = tk.Frame(card, bg=BG2)
        inner.pack(padx=50, pady=40)

        # 로고
        tk.Label(inner, text="블로그 자동 포스팅",
                 font=F_LOGO, fg=TEXT, bg=BG2).pack()
        tk.Label(inner, text="AI가 뉴스를 읽고 티스토리에 자동으로 발행합니다",
                 font=F_SUB, fg=TEXT2, bg=BG2).pack(pady=(4, 28))

        # 탭 버튼
        tab_row = tk.Frame(inner, bg=BG2)
        tab_row.pack(fill="x", pady=(0, 24))
        self._tab_btns = {}
        for lbl, idx in [("포스팅", 0), ("설정", 1)]:
            b = tk.Button(tab_row, text=lbl, font=("맑은 고딕", 10),
                          bd=0, relief="flat", cursor="hand2",
                          fg=TEXT2, bg=BG2,
                          activeforeground=TEXT,
                          activebackground=BG2,
                          padx=18, pady=6,
                          command=lambda i=idx: self._tab(i))
            b.pack(side="left")
            self._tab_btns[idx] = b

        # 페이지 컨테이너
        self._cont = tk.Frame(inner, bg=BG2, width=460)
        self._cont.pack(fill="both")
        self._cont.pack_propagate(False)

        self._make_post(self._cont)
        self._make_settings(self._cont)
        self._tab(0)

    def _make_post(self, parent):
        f = tk.Frame(parent, bg=BG2)
        self._pages[0] = f

        self._url_e = UnderlineEntry(f, label="뉴스 URL", bg=BG2)
        self._url_e.pack(fill="x", pady=(0, 28))

        self._btn = GlowButton(f, "포스팅 시작", self._start, width=460)
        self._btn.pack(pady=(0, 20))

        # 로그
        log_frame = tk.Frame(f, bg=BG2, highlightthickness=1,
                             highlightbackground=LINE)
        log_frame.pack(fill="both")
        top = tk.Frame(log_frame, bg=BG2)
        top.pack(fill="x", padx=8, pady=(6,4))
        tk.Label(top, text="진행 상황", font=("맑은 고딕", 8, "bold"),
                 fg=TEXT2, bg=BG2).pack(side="left")
        tk.Button(top, text="지우기", font=("맑은 고딕", 7),
                  bd=0, relief="flat", cursor="hand2",
                  fg=TEXT2, bg=BG2, command=self._clear).pack(side="right")

        self._log = scrolledtext.ScrolledText(
            log_frame, height=10, font=F_LOG,
            state="disabled", bg="#0a0e1c", fg=INFO,
            relief="flat", bd=0, padx=10, pady=6)
        self._log.pack(fill="both", padx=1, pady=(0,1))
        for tag, col in [("ok",SUCCESS),("err",ERR),
                         ("warn",WARN),("info",INFO)]:
            self._log.tag_config(tag, foreground=col)

    def _make_settings(self, parent):
        f = tk.Frame(parent, bg=BG2)
        self._pages[1] = f

        fields = [
            ("GROQ API 키",      "GROQ_API_KEY",        False),
            ("Unsplash Key",     "UNSPLASH_ACCESS_KEY", False),
            ("티스토리 이메일",  "TISTORY_ID",          False),
            ("티스토리 비밀번호","TISTORY_PW",           True),
            ("블로그 주소",      "TISTORY_BLOG_NAME",   False),
        ]
        self._sv = {}
        for lbl, key, pw in fields:
            e = UnderlineEntry(f, label=lbl, show="*" if pw else "", bg=BG2)
            e.pack(fill="x", pady=(0, 16))
            self._sv[key] = e

        GlowButton(f, "설정 저장", self._save, width=460,
                   color=SUCCESS, hover="#00a87e").pack(pady=(4,0))

    # ─── 탭 전환 ─────────────────────────────

    def _tab(self, idx):
        for i, p in self._pages.items():
            if i == idx: p.pack(fill="both")
            else:        p.pack_forget()
        for i, b in self._tab_btns.items():
            if i == idx:
                b.config(fg=ACCENT,
                         font=("맑은 고딕", 10, "bold"))
            else:
                b.config(fg=TEXT2,
                         font=("맑은 고딕", 10))
        # 탭 아래 강조선
        try: self._tab_line.destroy()
        except: pass
        b = self._tab_btns[idx]
        self._tab_line = tk.Frame(b.master, bg=ACCENT, height=2)
        self._tab_line.place(in_=b, relx=0, rely=1,
                             relwidth=1, anchor="nw")

    # ─── 설정 ────────────────────────────────

    def _load(self):
        s = load_settings()
        for k, e in self._sv.items():
            e.set(s.get(k,""))

    def _save(self):
        s = {k: e.get().strip() for k, e in self._sv.items()}
        save_settings(s)
        messagebox.showinfo("저장", "설정이 저장되었습니다.")

    # ─── 로그 ────────────────────────────────

    def _log_w(self, msg, tag=None):
        self._log.configure(state="normal")
        self._log.insert("end", msg+"\n", tag or "info")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _clear(self):
        self._log.configure(state="normal")
        self._log.delete("1.0","end")
        self._log.configure(state="disabled")

    # ─── 포스팅 ──────────────────────────────

    def _start(self):
        url = self._url_e.get().strip()
        if not url:
            messagebox.showwarning("알림","뉴스 URL을 입력해주세요.")
            return
        s = load_settings()
        if not s["GROQ_API_KEY"] or not s["TISTORY_ID"]:
            messagebox.showwarning("알림","설정 탭에서 API 키와 티스토리 정보를 입력해주세요.")
            self._tab(1); return
        self._btn.set_state("처리 중...", "#334466")
        self._btn.config(cursor="")
        self._clear()
        threading.Thread(target=self._run, args=(url,), daemon=True).start()

    def _run(self, url):
        log = lambda m, t=None: self.after(0, self._log_w, m, t)
        try:
            if str(BASE_DIR) not in sys.path:
                sys.path.insert(0, str(BASE_DIR))
            os.chdir(BASE_DIR)
            from dotenv import load_dotenv
            load_dotenv(ENV_FILE, override=True)

            log("━"*40)
            log("[1/4]  뉴스 수집 중...", "info")
            from crawler.news_crawler import crawl_news
            news = crawl_news(url)
            log(f"  ✓ {news['title']}", "ok")

            log("[2/4]  AI 재작성 중...", "info")
            from ai_writer.content_generator import generate_post
            post = generate_post(news)
            log(f"  ✓ 제목: {post['title']}", "ok")

            log("[3/4]  이미지 검색 중...", "info")
            from uploader.image_fetcher import fetch_image
            kw = post["tags"][0] if post["tags"] else news["title"][:20]
            img = fetch_image(kw)
            log(f"  ✓ {img['photographer']} on Unsplash" if img
                else "  이미지 없음", "ok" if img else "warn")

            log("[4/4]  티스토리 발행 중...", "info")
            from uploader.tistory_uploader import upload_post
            upload_post(post, img, wait_after=False)

            log(f"\n  완료: {post['title']}", "ok")
            log("━"*40)
            self.after(0, lambda: messagebox.showinfo(
                "완료", f"포스팅 완료!\n\n{post['title']}"))

        except Exception as e:
            log(f"  오류: {e}", "err")
            self.after(0, lambda: messagebox.showerror("오류", str(e)))
        finally:
            self.after(0, lambda: (
                self._btn.set_state("포스팅 시작", ACCENT),
                self._btn.config(cursor="hand2")))


if __name__ == "__main__":
    app = BlogApp()
    app.mainloop()
