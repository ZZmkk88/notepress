"""notepress · 小红书图文内容工作台

选题 → AI 写稿 → 排版成图 → 草稿管理 → 导出发布包（人工发布）。
单文件 FastAPI + SQLite + Pillow 成卡；前端为 static/index.html 单页。
"""

import hashlib
import io
import json
import os
import re
import secrets
import sqlite3
import zipfile
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path

import httpx
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from PIL import Image, ImageDraw, ImageFont, ImageOps

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("NOTEPRESS_DB", str(BASE_DIR / "notepress.db")))
MEDIA_DIR = Path(os.environ.get("NOTEPRESS_MEDIA", str(BASE_DIR / "media")))
BANNED_WORDS_FILE = Path(
    os.environ.get("NOTEPRESS_BANNED_WORDS", str(BASE_DIR / "data" / "banned_words.json"))
)
STATIC_INDEX = BASE_DIR / "static" / "index.html"

TITLE_LIMIT = 20          # 小红书标题硬上限（平台规矩）
BODY_LIMIT = 1000         # 小红书正文硬上限（平台规矩）
TOPIC_LIMIT = 100
TAG_LIMIT = 20
MAX_TAGS = 10
TOKEN_TTL_HOURS = 24
CARD_W, CARD_H = 1080, 1440   # 3:4 竖版卡片

TONES = {
    "checklist": "干货清单",
    "experience": "亲身体验",
    "pitfall": "避坑故事",
}

SEED_TOPICS = [
    "不会写周报？让 AI 先帮你打个草稿",
    "用 AI 把会议录音变成整齐的纪要",
    "Excel 公式记不住，让 AI 帮你写",
    "给娃编睡前故事：主角就是 TA 自己",
    "简历不会写？AI 帮你把经历说漂亮",
    "把说明书喂给 AI，售后问题随问随答",
    "用 AI 把冰箱剩菜变成一周菜谱",
    "英语不好也能回邮件：AI 润色三档语气",
    "帮爸妈把药盒说明拍成大字版",
    "旅行攻略别再抄了，AI 按你的节奏排",
]

DEMO_TAGS = ["AI工具", "普通人用AI", "效率提升", "职场干货", "AI教程", "生活小妙招"]

# ---------------------------------------------------------------- 数据库


class _ClosingConn:
    """with 结束时 commit/rollback 并 close，避免连接泄漏。"""

    def __init__(self, conn):
        self._conn = conn

    def __enter__(self):
        return self._conn

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                self._conn.commit()
            else:
                self._conn.rollback()
        finally:
            self._conn.close()
        return False


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return _ClosingConn(conn)


def now_str():
    return datetime.now().isoformat(timespec="seconds")


def init_db():
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    (MEDIA_DIR / "cards").mkdir(exist_ok=True)
    (MEDIA_DIR / "covers").mkdir(exist_ok=True)
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                must_change INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                direction TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT 'manual',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER REFERENCES topics(id) ON DELETE SET NULL,
                title TEXT NOT NULL DEFAULT '',
                body TEXT NOT NULL DEFAULT '',
                tags TEXT NOT NULL DEFAULT '[]',
                tone TEXT NOT NULL DEFAULT 'checklist',
                template TEXT NOT NULL DEFAULT 'berry',
                status TEXT NOT NULL DEFAULT 'draft',
                cover_mode TEXT NOT NULL DEFAULT 'card',
                cover_file TEXT NOT NULL DEFAULT '',
                published_url TEXT NOT NULL DEFAULT '',
                published_at TEXT NOT NULL DEFAULT '',
                exported_at TEXT NOT NULL DEFAULT '',
                checked_at TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        # 老库补列：checked_at 是进度条"违禁词自查"步的推导依据（后加的字段）
        cols = [r[1] for r in conn.execute("PRAGMA table_info(drafts)").fetchall()]
        if cols and "checked_at" not in cols:
            conn.execute("ALTER TABLE drafts ADD COLUMN checked_at TEXT NOT NULL DEFAULT ''")
        row = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
        if row["c"] == 0:
            conn.execute(
                "INSERT INTO users (username, password_hash, must_change, created_at) VALUES (?, ?, 1, ?)",
                ("admin", hash_password("admin123"), now_str()),
            )
        row = conn.execute("SELECT COUNT(*) AS c FROM topics").fetchone()
        if row["c"] == 0:
            for t in SEED_TOPICS:
                conn.execute(
                    "INSERT INTO topics (title, direction, source, created_at) VALUES (?, '', 'seed', ?)",
                    (t, now_str()),
                )


# ---------------------------------------------------------------- 密码与会话


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000)
    return f"{salt}${digest.hex()}"


# 启动时备一份固定假哈希：用户名不存在时也走一次等时长的校验，
# 避免每次现生成新盐带来的时序差异（侧信道小事，顺手做掉）
_DUMMY_HASH = hash_password("notepress-login-dummy")


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, expected = stored.split("$", 1)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000)
    return secrets.compare_digest(digest.hex(), expected)


def create_session(conn, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires = (datetime.now() + timedelta(hours=TOKEN_TTL_HOURS)).isoformat(timespec="seconds")
    conn.execute(
        "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, user_id, now_str(), expires),
    )
    return token


def get_current_user(request: Request):
    auth = request.headers.get("Authorization", "")
    token = auth.removeprefix("Bearer ") if auth.startswith("Bearer ") else ""
    if not token:
        raise HTTPException(401, "未登录")
    with get_db() as conn:
        row = conn.execute(
            "SELECT u.id, u.username, u.must_change, s.expires_at FROM sessions s "
            "JOIN users u ON u.id = s.user_id WHERE s.token = ?",
            (token,),
        ).fetchone()
    if row is None:
        raise HTTPException(401, "登录已失效，请重新登录")
    if row["expires_at"] <= now_str():
        raise HTTPException(401, "登录已过期，请重新登录")
    return {"id": row["id"], "username": row["username"],
            "must_change": bool(row["must_change"]), "token": token}


# ---------------------------------------------------------------- 违禁词


def load_banned_words():
    try:
        data = json.loads(BANNED_WORDS_FILE.read_text(encoding="utf-8"))
        words = data.get("words", [])
        return [str(w) for w in words if str(w).strip()]
    except Exception:
        return []


def save_banned_words(words):
    BANNED_WORDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {"comment": "常见违禁/极限词，自查只做提示不拦截发布；可在设置页或直接改本文件增删。",
               "words": words}
    BANNED_WORDS_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")


def check_banned(title: str, body: str):
    hits = []
    for w in load_banned_words():
        in_title = title.count(w)
        in_body = body.count(w)
        if in_title or in_body:
            hits.append({"word": w, "in_title": in_title, "in_body": in_body})
    return hits


# ---------------------------------------------------------------- LLM 层


def llm_configured() -> bool:
    return bool(os.environ.get("NOTEPRESS_LLM_API_KEY", "").strip())


def llm_chat(messages, temperature=0.8) -> str:
    base = os.environ.get("NOTEPRESS_LLM_BASE_URL", "https://api.deepseek.com/v1").rstrip("/")
    model = os.environ.get("NOTEPRESS_LLM_MODEL", "deepseek-chat")
    key = os.environ.get("NOTEPRESS_LLM_API_KEY", "")
    resp = httpx.post(
        f"{base}/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": model, "messages": messages, "temperature": temperature},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _parse_json(text: str):
    m = re.search(r"\{.*\}|\[.*\]", text, re.S)
    if not m:
        raise ValueError("no json in llm output")
    return json.loads(m.group(0))


# ---- 演示模式（未配密钥时用内置模板生成示例稿，保证全流程可跑、测试可打桩）

def _short_topic(topic: str) -> str:
    core = topic.strip().rstrip("。！？!?")
    return core if len(core) <= 10 else core[:10]


def demo_expand(direction: str):
    # 方向词接口上限 50 字，演示模板不再截到 12 字，用完整方向词
    d = direction.strip()
    patterns = [
        f"用AI搞定{d}，小白完整教程",
        f"{d}别再手动做了，试试AI",
        f"普通人学AI：从{d}开始",
        f"{d}提速的3个AI用法",
        f"我用AI做{d}，结果惊了",
        f"{d}新手避坑指南",
    ]
    return patterns


def demo_generate(topic: str, tone: str):
    s = _short_topic(topic)
    pool = [
        f"{s}，这样做超简单",
        f"{s}保姆级教程",
        f"亲测！{s}真的香",
        f"{s}，小白也能学会",
        f"别再手动了，{s}",
        f"{s}全流程分享",
    ]
    titles = []
    for t in pool:
        if len(t) <= TITLE_LIMIT and t not in titles:
            titles.append(t)
        if len(titles) == 3:
            break
    bodies = {
        "checklist": (
            f"今天分享一个普通人也能上手的 AI 用法：{topic}。\n\n"
            "先说结论：不用学代码，不用背命令，把需求说清楚就行。\n\n"
            "【准备】\n1. 一个能用的 AI 对话工具\n2. 把你的原始材料（文字、表格或照片）准备好\n3. 一句话说清你想要的结果\n\n"
            "【步骤】\n先把材料发给 AI，并告诉它你的身份和场景。\n"
            "第二步，让它先给一版结果，不要急着用。\n"
            "第三步，指出不满意的地方，让它按你的要求改。\n"
            "第四步，把最终版存下来，下次同类任务直接套这个说法。\n\n"
            "【小提示】\n描述越具体，结果越靠谱；涉及隐私的内容记得先打码。\n\n"
            "你平时最想让 AI 帮你干哪件事？评论区告诉我，下期安排。"
        ),
        "experience": (
            f"上周我试着用 AI 做了这件事：{topic}，说说我的真实感受。\n\n"
            "以前这类事我都是手动慢慢磨，费时还容易出错。这次把材料丢给 AI，"
            "先让它给一版，我再逐句挑毛病让它改，前后不到十分钟就搞定了。\n\n"
            "最惊喜的是，它给的版本里有两个我自己想不到的说法；"
            "最需要提醒的是，初版千万别直接用，细节一定要自己核对一遍。\n\n"
            "我的用法很简单：说清场景、给足材料、逐轮修改。"
            "普通人用 AI，不用追求多高级，把手头一件小事做快做顺，就是赚到。\n\n"
            "你们用 AI 做过最省事的一件事是什么？"
        ),
        "pitfall": (
            f"关于{topic}，我先替你们踩了三个坑，看完再上手。\n\n"
            "坑一：一上来就问得很笼统。AI 给的回答放之四海皆准，等于没帮上忙。"
            "正确做法是把场景、材料、想要的格式一次说清。\n\n"
            "坑二：初版直接拿去用。AI 偶尔会一本正经地编细节，数字和名字一定要自己核对。\n\n"
            "坑三：把隐私原样发出去。身份证号、公司内部数据、客户信息，发之前先打码或替换。\n\n"
            "避开这三个坑，AI 就是个好帮手；避不开，再强的工具也白搭。\n\n"
            "你还踩过什么坑？评论区补充，我整理成下期。"
        ),
    }
    body = bodies.get(tone, bodies["checklist"])
    return {"titles": titles, "body": body, "tags": DEMO_TAGS[:5], "demo": True}


def ai_expand(direction: str):
    if not llm_configured():
        return {"candidates": demo_expand(direction), "demo": True}
    prompt = (
        "你是小红书选题策划，赛道是「AI 工具平民玩法」（教普通人用 AI 干日常事）。"
        f"围绕方向词「{direction}」给出 6 个适合新号的图文选题标题，每个不超过 40 字，"
        "只输出 JSON 数组，不要解释。"
    )
    try:
        out = _parse_json(llm_chat([{"role": "user", "content": prompt}], temperature=0.9))
        cands = [str(x).strip() for x in out if str(x).strip()][:6]
        if not cands:
            raise ValueError("empty")
        return {"candidates": cands, "demo": False}
    except HTTPException:
        raise
    except Exception:
        # 上游失败不再伪装成演示模式：明确报错 502
        raise HTTPException(502, "AI 扩题失败，请重试")


def ai_generate(topic: str, tone: str):
    if not llm_configured():
        out = demo_generate(topic, tone)
        if len(out["body"]) > BODY_LIMIT:
            raise HTTPException(400, f"演示稿正文 {len(out['body'])} 字，超过 {BODY_LIMIT} 字上限")
        return out
    tone_label = TONES.get(tone, "干货清单")
    prompt = (
        "你是小红书图文文案写手，赛道「AI 工具平民玩法」，语气亲切接地气。\n"
        f"选题：{topic}\n风格：{tone_label}\n"
        "硬性要求：给出 3 个标题候选，每个标题不超过 20 字；正文不超过 950 字，"
        "分段清晰、适合排成图文卡片；给出 5-8 个话题标签（不带#号）。"
        "不要使用广告法极限词（如第一、最佳、100%等）。"
        '只输出 JSON：{"titles":["..."],"body":"...","tags":["..."]}，不要解释。'
    )
    try:
        raw = llm_chat([{"role": "user", "content": prompt}], temperature=0.9)
    except HTTPException:
        raise
    except Exception:
        # 上游调用失败与扩题统一：明确报错 502，不让异常裸奔
        raise HTTPException(502, "AI 写稿失败，请重试")
    try:
        out = _parse_json(raw)
    except Exception:
        raise HTTPException(502, "AI 返回格式不对，请重试")
    titles = [str(t).strip() for t in out.get("titles", []) if str(t).strip()]
    over = next((t for t in titles if len(t) > TITLE_LIMIT), None)
    if over:
        raise HTTPException(502, f"AI 返回的标题超过 20 字（{over[:12]}…），请重试")
    titles = titles[:3]
    if not titles:
        raise HTTPException(502, "AI 返回的标题都超过 20 字，请重试")
    body = str(out.get("body", "")).strip()
    if not body:
        raise HTTPException(502, "AI 没有返回正文，请重试")
    if len(body) > BODY_LIMIT:
        raise HTTPException(502, f"AI 返回的正文 {len(body)} 字，超过 {BODY_LIMIT} 字上限，请重试")
    if len(titles) < 3:
        raise HTTPException(502, f"AI 返回的标题只有 {len(titles)} 个，不足 3 个，请重试")
    tags = [str(t).strip().lstrip("#") for t in out.get("tags", []) if str(t).strip()]
    over_tag = next((t for t in tags if len(t) > TAG_LIMIT), None)
    if over_tag:
        raise HTTPException(502, f"AI 返回的标签超过 {TAG_LIMIT} 字（{over_tag[:12]}…），请重试")
    if len(tags) > MAX_TAGS:
        raise HTTPException(502, f"AI 返回的标签 {len(tags)} 个，超过 {MAX_TAGS} 个上限，请重试")
    return {"titles": titles, "body": body, "tags": tags, "demo": False}

# ---------------------------------------------------------------- 图文成卡

TEMPLATES = {
    "berry": {"bg": (255, 249, 245), "accent": (255, 36, 66), "text": (51, 51, 51), "sub": (140, 130, 124)},
    "mint": {"bg": (242, 250, 245), "accent": (31, 157, 116), "text": (34, 51, 43), "sub": (110, 130, 118)},
    "ink": {"bg": (30, 42, 56), "accent": (255, 200, 87), "text": (245, 241, 232), "sub": (168, 178, 190)},
}

_FONT_CANDIDATES = [
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
     "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
    ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
     "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),
    ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc"),
    ("/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/PingFang.ttc"),
    ("/System/Library/Fonts/STHeiti Medium.ttc", "/System/Library/Fonts/STHeiti Medium.ttc"),
]
_font_cache = {}


def find_font(bold=False):
    key = "b" if bold else "r"
    if key in _font_cache:
        return _font_cache[key]
    env = os.environ.get("NOTEPRESS_FONT_PATH", "")
    paths = []
    if env:
        paths.append(env)
    for regular, boldp in _FONT_CANDIDATES:
        paths.append(boldp if bold else regular)
    for p in paths:
        if p and Path(p).exists():
            _font_cache[key] = p
            return p
    _font_cache[key] = None
    return None


def get_font(size, bold=False):
    # 粗体文件缺失或打不开时，回退到同一次查找里的常规字体，
    # 而不是直接退到位图默认字体（后者没有中文）
    paths = []
    if bold:
        paths.append(find_font(True))
    paths.append(find_font(False))
    for path in paths:
        if path:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200D\u2190-\u21FF\u2300-\u23FF]"
)


def sanitize_for_card(text: str) -> str:
    """卡片字体没有彩色 emoji 字形，渲染前去掉，避免出现豆腐块。"""
    return _EMOJI_RE.sub("", text)


def wrap_text(draw, text, font, max_width):
    lines = []
    for para in text.split("\n"):
        if not para:
            lines.append("")
            continue
        cur = ""
        for ch in para:
            trial = cur + ch
            if draw.textlength(trial, font=font) <= max_width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = ch
        lines.append(cur)
    return lines


def fit_line(draw, text, font, max_width):
    if draw.textlength(text, font=font) <= max_width:
        return text
    ell = "…"
    if draw.textlength(ell, font=font) > max_width:
        return ""
    best = ""
    lo, hi = 0, len(text)
    while lo <= hi:
        mid = (lo + hi) // 2
        cand = text[:mid] + ell
        if draw.textlength(cand, font=font) <= max_width:
            best = cand
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def clear_card_files(draft_id):
    """内容或封面变了就丢掉旧卡，避免预览和导出还拿着上一版。"""
    d = MEDIA_DIR / "cards" / str(draft_id)
    if not d.exists():
        return
    for old in d.glob("card_*.png"):
        old.unlink()
    try:
        d.rmdir()
    except OSError:
        pass


def clear_cover_files(draft_id, cover_file=""):
    names = [f"{draft_id}.png", f"{draft_id}.jpg"]
    extra = Path(str(cover_file or "")).name
    if extra and extra not in names and extra not in (".", ".."):
        names.append(extra)
    for name in names:
        p = MEDIA_DIR / "covers" / name
        if p.is_file():
            p.unlink()


def _cards_dir(draft_id):
    d = MEDIA_DIR / "cards" / str(draft_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def render_cards(draft) -> list:
    """把草稿渲染成卡片 PNG，返回文件名列表（card_1.png ...）。"""
    tpl = TEMPLATES.get(draft["template"], TEMPLATES["berry"])
    draft_id = draft["id"]
    out_dir = _cards_dir(draft_id)
    for old in out_dir.glob("card_*.png"):
        old.unlink()
    title = sanitize_for_card(draft["title"] or "未命名笔记")
    body = sanitize_for_card(draft["body"] or "")
    tags = json.loads(draft["tags"] or "[]")

    files = []
    # ---- 封面卡
    cover_path = out_dir / "card_1.png"
    made_cover = False
    if draft["cover_mode"] == "upload" and draft["cover_file"]:
        src = MEDIA_DIR / "covers" / Path(draft["cover_file"]).name
        if src.exists():
            img = Image.open(src).convert("RGB")
            # 先在源图上裁出 3:4 再缩放到卡片，避免极端宽高比把整图放大到数亿像素。
            img = ImageOps.fit(img, (CARD_W, CARD_H))
            band = img.crop((0, CARD_H - 420, CARD_W, CARD_H))
            dark = Image.new("RGB", (CARD_W, 420), (0, 0, 0))
            img.paste(Image.blend(band, dark, 0.55), (0, CARD_H - 420))
            d = ImageDraw.Draw(img)
            f_title = get_font(64, bold=True)
            lines = wrap_text(d, title, f_title, CARD_W - 160)[:3]
            ty = CARD_H - 400
            for ln in lines:
                d.text((80, ty), ln, font=f_title, fill=(255, 255, 255))
                ty += 88
            img.save(cover_path)
            files.append("card_1.png")
            made_cover = True
    if not made_cover:
        img = Image.new("RGB", (CARD_W, CARD_H), tpl["bg"])
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, CARD_W, 26], fill=tpl["accent"])
        d.ellipse([CARD_W - 420, -220, CARD_W + 160, 360], outline=tpl["accent"], width=3)
        f_kick = get_font(40)
        d.text((84, 150), "AI 工具平民玩法", font=f_kick, fill=tpl["accent"])
        f_title = get_font(96, bold=True)
        lines = wrap_text(d, title, f_title, CARD_W - 168)[:6]
        ty = 300
        for ln in lines:
            d.text((84, ty), ln, font=f_title, fill=tpl["text"])
            ty += 138
        f_sub = get_font(42)
        safe_tags = []
        for t in tags[:4]:
            s = sanitize_for_card(str(t)).strip()
            if s:
                safe_tags.append(s)
        tag_line = "  ".join("#" + t for t in safe_tags)
        max_w = CARD_W - 168
        if tag_line:
            if d.textlength(tag_line, font=f_sub) <= max_w:
                # 单行放得下：位置与旧版一致
                d.text((84, CARD_H - 240), tag_line, font=f_sub, fill=tpl["sub"])
            else:
                # 先截断、再换行：整块底对齐在页脚上方，文字不画出卡片外
                tag_lines = [fit_line(d, ln, f_sub, max_w)
                             for ln in wrap_text(d, tag_line, f_sub, max_w)]
                tag_lines = [ln for ln in tag_lines if ln]
                line_h = 56
                ty = (CARD_H - 150) - 16 - line_h * len(tag_lines)
                for ln in tag_lines:
                    d.text((84, ty), ln, font=f_sub, fill=tpl["sub"])
                    ty += line_h
        d.text((84, CARD_H - 150), "notepress 笔记工坊", font=f_sub, fill=tpl["sub"])
        img.save(cover_path)
        files.append("card_1.png")

    # ---- 内容卡（分页）
    probe = Image.new("RGB", (CARD_W, CARD_H), tpl["bg"])
    pd = ImageDraw.Draw(probe)
    f_body = get_font(46)
    body_lines = wrap_text(pd, body, f_body, CARD_W - 168) if body else []
    line_h = 78
    top = 190
    bottom = CARD_H - 130
    per_page = max(1, (bottom - top) // line_h)
    pages = [body_lines[i:i + per_page] for i in range(0, len(body_lines), per_page)] or [[]]
    total = len(pages) + 1  # 含封面
    for idx, page_lines in enumerate(pages):
        n = idx + 2
        img = Image.new("RGB", (CARD_W, CARD_H), tpl["bg"])
        d = ImageDraw.Draw(img)
        f_head = get_font(40, bold=True)
        head = wrap_text(d, title, f_head, CARD_W - 168)[:1]
        if head:
            d.text((84, 84), head[0], font=f_head, fill=tpl["text"])
        d.line([84, 150, CARD_W - 84, 150], fill=tpl["accent"], width=4)
        y = top
        for ln in page_lines:
            d.text((84, y), ln, font=f_body, fill=tpl["text"])
            y += line_h
        f_page = get_font(36)
        d.text((84, CARD_H - 110), f"{n} / {total}", font=f_page, fill=tpl["sub"])
        p = out_dir / f"card_{n}.png"
        img.save(p)
        files.append(f"card_{n}.png")
    return files


def list_card_files(draft_id):
    d = MEDIA_DIR / "cards" / str(draft_id)
    if not d.exists():
        return []
    return sorted((p.name for p in d.glob("card_*.png")),
                  key=lambda s: int(s.split("_")[1].split(".")[0]))


# ---------------------------------------------------------------- 应用与中间件


class SecurityHeadersMiddleware:
    """纯 ASGI 安全响应头，不缓冲响应体。"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def send_wrap(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-content-type-options", b"nosniff"))
                headers.append((b"x-frame-options", b"DENY"))
                headers.append((b"referrer-policy", b"same-origin"))
                message["headers"] = headers
            await send(message)

        return await self.app(scope, receive, send_wrap)


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(title="notepress", docs_url=None, redoc_url=None, openapi_url=None,
              lifespan=lifespan)
app.add_middleware(SecurityHeadersMiddleware)


@app.get("/health")
def health():
    return {"status": "ok", "app_id": "notepress"}


@app.get("/")
def index():
    return FileResponse(STATIC_INDEX)


async def body_json(request: Request):
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def draft_row_to_dict(row):
    d = dict(row)
    try:
        d["tags"] = json.loads(d.get("tags") or "[]")
    except Exception:
        d["tags"] = []
    d["cards"] = list_card_files(d["id"])
    return d


def validate_title_body(title, body):
    if len(title) > TITLE_LIMIT:
        raise HTTPException(400, f"标题超过上限 {TITLE_LIMIT} 字（当前 {len(title)} 字）")
    if len(body) > BODY_LIMIT:
        raise HTTPException(400, f"正文超过上限 {BODY_LIMIT} 字（当前 {len(body)} 字）")


# ---------------------------------------------------------------- 账号


@app.post("/api/login")
async def login(request: Request):
    data = await body_json(request)
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if row is None or not verify_password(password, row["password_hash"]):
            if row is None:
                # 用户名不存在也照常走一次哈希校验，避免时序差异
                verify_password(password, _DUMMY_HASH)
            raise HTTPException(401, "用户名或密码不对")
        conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (now_str(),))
        token = create_session(conn, row["id"])
        must_change = bool(row["must_change"])
    return {"token": token, "username": username, "must_change": must_change}


@app.get("/api/me")
def me(user=Depends(get_current_user)):
    return {"username": user["username"], "must_change": user["must_change"],
            "llm_configured": llm_configured()}


@app.post("/api/logout")
def logout(user=Depends(get_current_user)):
    with get_db() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (user["token"],))
    return {"ok": True}


@app.post("/api/change-password")
async def change_password(request: Request, user=Depends(get_current_user)):
    data = await body_json(request)
    old = str(data.get("old_password", ""))
    new = str(data.get("new_password", ""))
    if len(new) < 6:
        raise HTTPException(400, "新密码至少 6 位")
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
        if not verify_password(old, row["password_hash"]):
            raise HTTPException(400, "原密码不对")
        if verify_password(new, row["password_hash"]):
            raise HTTPException(400, "新密码不能和原密码相同")
        conn.execute(
            "UPDATE users SET password_hash = ?, must_change = 0 WHERE id = ?",
            (hash_password(new), user["id"]),
        )
        # 口径第 2 条：改密同事务吊销其他会话，保留本次；取不到当前令牌则不删
        if user.get("token"):
            conn.execute(
                "DELETE FROM sessions WHERE user_id = ? AND token != ?",
                (user["id"], user["token"]),
            )
    return {"ok": True}

# ---------------------------------------------------------------- 选题


@app.get("/api/topics")
def list_topics(user=Depends(get_current_user)):
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM topics ORDER BY id DESC").fetchall()
    return {"topics": [dict(r) for r in rows]}


@app.post("/api/topics")
async def create_topic(request: Request, user=Depends(get_current_user)):
    data = await body_json(request)
    title = str(data.get("title", "")).strip()
    direction = str(data.get("direction", "")).strip()
    if not title:
        raise HTTPException(400, "选题不能为空")
    if len(title) > TOPIC_LIMIT:
        raise HTTPException(400, f"选题超过上限 {TOPIC_LIMIT} 字（当前 {len(title)} 字）")
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO topics (title, direction, source, created_at) VALUES (?, ?, 'manual', ?)",
            (title, direction, now_str()),
        )
        tid = cur.lastrowid
    return {"id": tid}


@app.delete("/api/topics/{topic_id}")
def delete_topic(topic_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        conn.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
    return {"ok": True}


@app.post("/api/topics/expand")
async def expand_topics(request: Request, user=Depends(get_current_user)):
    data = await body_json(request)
    direction = str(data.get("direction", "")).strip()
    if not direction:
        raise HTTPException(400, "先给一个方向词")
    if len(direction) > 50:
        raise HTTPException(400, f"方向词超过上限 50 字（当前 {len(direction)} 字）")
    return ai_expand(direction)


# ---------------------------------------------------------------- 写稿


@app.post("/api/generate")
async def generate(request: Request, user=Depends(get_current_user)):
    data = await body_json(request)
    topic = str(data.get("topic", "")).strip()
    tone = str(data.get("tone", "checklist"))
    if tone not in TONES:
        tone = "checklist"
    if not topic:
        topic_id = data.get("topic_id")
        if topic_id:
            with get_db() as conn:
                row = conn.execute("SELECT title FROM topics WHERE id = ?", (topic_id,)).fetchone()
            if row:
                topic = row["title"]
    if not topic:
        raise HTTPException(400, "先选一个选题")
    result = ai_generate(topic, tone)
    result["topic"] = topic
    result["tone"] = tone
    result["banned_hits"] = check_banned(
        result["titles"][0] if result["titles"] else "", result["body"])
    return result


# ---------------------------------------------------------------- 草稿


@app.get("/api/drafts")
def list_drafts(status: str = "", user=Depends(get_current_user)):
    with get_db() as conn:
        if status in ("draft", "ready", "published"):
            rows = conn.execute(
                "SELECT * FROM drafts WHERE status = ? ORDER BY updated_at DESC", (status,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM drafts ORDER BY updated_at DESC").fetchall()
    return {"drafts": [draft_row_to_dict(r) for r in rows]}


def _clean_tags(raw):
    tags = []
    if isinstance(raw, list):
        for t in raw:
            s = str(t).strip().lstrip("#")
            if s and s not in tags:
                if len(s) > TAG_LIMIT:
                    raise HTTPException(400, f"标签超过上限 {TAG_LIMIT} 字（当前 {len(s)} 字）")
                tags.append(s)
    if len(tags) > MAX_TAGS:
        raise HTTPException(400, f"标签超过上限 {MAX_TAGS} 个（当前 {len(tags)} 个）")
    return tags


@app.post("/api/drafts")
async def create_draft(request: Request, user=Depends(get_current_user)):
    data = await body_json(request)
    title = str(data.get("title", "")).strip()
    body = str(data.get("body", ""))
    validate_title_body(title, body)
    tags = _clean_tags(data.get("tags", []))
    tone = str(data.get("tone", "checklist"))
    if tone not in TONES:
        tone = "checklist"
    template = str(data.get("template", "berry"))
    if template not in TEMPLATES:
        template = "berry"
    topic_id = data.get("topic_id") or None
    if topic_id is not None:
        with get_db() as conn:
            trow = conn.execute("SELECT id FROM topics WHERE id = ?", (topic_id,)).fetchone()
        if trow is None:
            raise HTTPException(400, "选题不存在")
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO drafts (topic_id, title, body, tags, tone, template, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (topic_id, title, body, json.dumps(tags, ensure_ascii=False), tone, template,
             now_str(), now_str()),
        )
        did = cur.lastrowid
    return {"id": did}


@app.get("/api/drafts/{draft_id}")
def get_draft(draft_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "草稿不存在")
    return draft_row_to_dict(row)


@app.put("/api/drafts/{draft_id}")
async def update_draft(draft_id: int, request: Request, user=Depends(get_current_user)):
    data = await body_json(request)
    with get_db() as conn:
        row = conn.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "草稿不存在")
        cur = dict(row)
        # JSON null 按空字符串处理（不再 str(None) 存成 "None" 字面量），
        # 键缺席时保留原值
        def _pick(key, cur_val):
            if key not in data:
                return cur_val
            v = data[key]
            return "" if v is None else str(v)
        title = _pick("title", cur["title"]).strip()
        body = _pick("body", cur["body"])
        validate_title_body(title, body)
        old_tags = json.loads(cur["tags"] or "[]")
        tags = _clean_tags(data["tags"]) if "tags" in data else old_tags
        status = str(data.get("status", cur["status"]))
        if status not in ("draft", "ready", "published"):
            raise HTTPException(400, "状态不对")
        template = str(data.get("template", cur["template"]))
        if template not in TEMPLATES:
            raise HTTPException(400, "模板不对")
        content_changed = (
            title != cur["title"] or body != cur["body"]
            or tags != old_tags or template != cur["template"]
        )
        # 标题/正文改动后，自查结论对新内容不再成立：清掉 checked_at，
        # 进度条的「违禁词自查」步退回未完成，提醒重查（与改稿清卡片同理）
        text_changed = title != cur["title"] or body != cur["body"]
        new_checked_at = "" if text_changed else cur.get("checked_at", "")
        conn.execute(
            "UPDATE drafts SET title=?, body=?, tags=?, status=?, template=?, "
            "published_url=?, published_at=?, checked_at=?, updated_at=? WHERE id=?",
            (title, body, json.dumps(tags, ensure_ascii=False), status, template,
             _pick("published_url", cur["published_url"]),
             _pick("published_at", cur["published_at"]),
             new_checked_at,
             now_str(), draft_id),
        )
    if content_changed:
        clear_card_files(draft_id)
    return {"ok": True}


@app.delete("/api/drafts/{draft_id}")
def delete_draft(draft_id: int, user=Depends(get_current_user)):
    cover = ""
    with get_db() as conn:
        row = conn.execute("SELECT cover_file FROM drafts WHERE id = ?", (draft_id,)).fetchone()
        if row is not None:
            cover = row["cover_file"] or ""
        conn.execute("DELETE FROM drafts WHERE id = ?", (draft_id,))
    clear_card_files(draft_id)
    clear_cover_files(draft_id, cover)
    return {"ok": True}


# ---------------------------------------------------------------- 成卡与封面


@app.post("/api/drafts/{draft_id}/render")
async def render_draft(draft_id: int, request: Request, user=Depends(get_current_user)):
    data = await body_json(request)
    with get_db() as conn:
        row = conn.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "草稿不存在")
        draft = dict(row)
        template = str(data.get("template", draft["template"]))
        if template in TEMPLATES and template != draft["template"]:
            conn.execute("UPDATE drafts SET template=?, updated_at=? WHERE id=?",
                         (template, now_str(), draft_id))
            draft["template"] = template
    files = render_cards(draft)
    return {"cards": [f"/api/drafts/{draft_id}/cards/{i + 1}" for i in range(len(files))],
            "count": len(files)}


@app.get("/api/drafts/{draft_id}/cards/{n}")
def get_card(draft_id: int, n: int, user=Depends(get_current_user)):
    with get_db() as conn:
        row = conn.execute("SELECT id FROM drafts WHERE id = ?", (draft_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "草稿不存在")
    p = MEDIA_DIR / "cards" / str(draft_id) / f"card_{n}.png"
    if not p.exists():
        raise HTTPException(404, "卡片不存在，先生成卡片")
    return FileResponse(p, media_type="image/png")


@app.post("/api/drafts/{draft_id}/cover")
async def upload_cover(draft_id: int, file: UploadFile = File(...),
                       user=Depends(get_current_user)):
    limit = 10 * 1024 * 1024
    size = file.size
    if size is not None and size > limit:
        raise HTTPException(400, f"图片超过上限 10MB（当前 {size} 字节）")
    raw = await file.read(limit + 1)
    if len(raw) > limit:
        raise HTTPException(400, f"图片超过上限 10MB（当前 {len(raw)} 字节）")
    try:
        img = Image.open(io.BytesIO(raw))
        img.verify()
        fmt = (img.format or "PNG").lower()
    except Exception:
        raise HTTPException(400, "这不是一张能打开的图片")
    ext = "jpg" if fmt in ("jpeg", "jpg") else "png"
    name = f"{draft_id}.{ext}"
    with get_db() as conn:
        row = conn.execute("SELECT id FROM drafts WHERE id = ?", (draft_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "草稿不存在")
    # 换封面改扩展名时先删旧文件，避免 1.png / 1.jpg 同时残留
    clear_cover_files(draft_id)
    (MEDIA_DIR / "covers" / name).write_bytes(raw)
    with get_db() as conn:
        conn.execute("UPDATE drafts SET cover_mode='upload', cover_file=?, updated_at=? WHERE id=?",
                     (name, now_str(), draft_id))
    clear_card_files(draft_id)
    return {"ok": True, "cover_file": name}


# ---------------------------------------------------------------- 违禁词


@app.get("/api/banned-words")
def get_banned(user=Depends(get_current_user)):
    return {"words": load_banned_words()}


@app.post("/api/banned-words")
async def add_banned(request: Request, user=Depends(get_current_user)):
    data = await body_json(request)
    word = str(data.get("word", "")).strip()
    if not word:
        raise HTTPException(400, "词不能为空")
    if len(word) > 20:
        raise HTTPException(400, f"违禁词超过上限 20 字（当前 {len(word)} 字）")
    words = load_banned_words()
    if word not in words:
        words.append(word)
        save_banned_words(words)
    return {"words": words}


@app.delete("/api/banned-words/{word}")
def delete_banned(word: str, user=Depends(get_current_user)):
    words = [w for w in load_banned_words() if w != word]
    save_banned_words(words)
    return {"words": words}


@app.post("/api/check")
async def check_text(request: Request, user=Depends(get_current_user)):
    data = await body_json(request)
    title = str(data.get("title", ""))
    body = str(data.get("body", ""))
    draft_id = data.get("draft_id")
    if draft_id:
        # 编辑器里对已存草稿自查时带上 draft_id：记下自查时间，
        # 进度条的「违禁词自查」步靠 checked_at 推导（查过没有也算查过）。
        # 工作室里还没存草稿时不带，不记录。
        with get_db() as conn:
            conn.execute("UPDATE drafts SET checked_at=? WHERE id=?", (now_str(), draft_id))
    return {"hits": check_banned(title, body),
            "title_len": len(title), "body_len": len(body),
            "title_limit": TITLE_LIMIT, "body_limit": BODY_LIMIT}


# ---------------------------------------------------------------- 发布包导出


@app.post("/api/drafts/{draft_id}/export")
def export_draft(draft_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "草稿不存在")
        draft = dict(row)
    files = render_cards(draft)
    tags = json.loads(draft["tags"] or "[]")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for i, name in enumerate(files, 1):
            z.write(MEDIA_DIR / "cards" / str(draft_id) / name, f"{i:02d}.png")
        text = (
            f"标题：{draft['title']}\n\n{draft['body']}\n\n"
            + " ".join("#" + t for t in tags)
            + "\n"
        )
        z.writestr("文案.txt", text)
    with get_db() as conn:
        conn.execute("UPDATE drafts SET exported_at=?, updated_at=? WHERE id=?",
                     (now_str(), now_str(), draft_id))
    buf.seek(0)
    return Response(
        content=buf.read(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="notepress-{draft_id}.zip"'},
    )


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("NOTEPRESS_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
