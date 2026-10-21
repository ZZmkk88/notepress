"""验收补充：演示模式、成卡不溢出、导出、违禁词、无外网。

不配置任何 API key。已有 tests/test_app.py 的断言不动，本文件只新增用例。
"""

import io
import json
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import app as app_module

SAMPLE_TITLE = "用AI写周报教程"
SAMPLE_BODY = "第一段内容。\n\n第二段内容，讲讲步骤。"
SAMPLE_TAGS = ["AI工具", "周报"]


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db = tmp_path / "acc.db"
    media = tmp_path / "media"
    words = tmp_path / "banned.json"
    words.write_text(
        json.dumps({"words": ["第一", "免费领取", "稳赚"]}, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(app_module, "DB_PATH", db)
    monkeypatch.setattr(app_module, "MEDIA_DIR", media)
    monkeypatch.setattr(app_module, "BANNED_WORDS_FILE", words)
    monkeypatch.delenv("NOTEPRESS_LLM_API_KEY", raising=False)
    app_module.init_db()
    with TestClient(app_module.app) as c:
        yield c


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _login(client):
    r = client.post("/api/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _outer_ink(im, margin=8, y_min=400):
    """卡片外缘（避开顶部色条和装饰圆）上的非背景像素。文字被裁切时会落在这里。"""
    px = im.load()
    w, h = im.size
    bg = px[12, 80]
    n = 0
    for y in range(y_min, h):
        for x in range(w):
            if (x < margin or x >= w - margin or y >= h - margin) and px[x, y] != bg:
                n += 1
    return n


def _ink_box(im, x0, y0, x1, y1):
    px = im.load()
    bg = px[12, 80]
    n = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            if px[x, y] != bg:
                n += 1
    return n


def _open_card(client, token, did, n):
    r = client.get(f"/api/drafts/{did}/cards/{n}", headers=_auth(token))
    assert r.status_code == 200, r.text
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"
    path = app_module.MEDIA_DIR / "cards" / str(did) / f"card_{n}.png"
    assert path.is_file()
    assert 500 < path.stat().st_size < 2_000_000
    im = Image.open(io.BytesIO(r.content)).convert("RGB")
    assert im.size == (1080, 1440)
    assert im.size[0] * 4 == im.size[1] * 3
    assert _outer_ink(im) == 0
    return im


def test_expand_topics_in_demo_mode(client):
    token = _login(client)
    r = client.post("/api/topics/expand", headers=_auth(token), json={"direction": "写邮件"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["demo"] is True
    assert len(body["candidates"]) >= 5
    assert all("写邮件" in c for c in body["candidates"])


def test_demo_mode_does_not_call_httpx_post(client, monkeypatch):
    calls = []

    def _forbidden(*args, **kwargs):
        calls.append(1)
        raise AssertionError("演示模式不应调用 httpx.post")

    monkeypatch.setattr(app_module.httpx, "post", _forbidden)
    token = _login(client)
    me = client.get("/api/me", headers=_auth(token))
    assert me.json()["llm_configured"] is False
    expand = client.post(
        "/api/topics/expand", headers=_auth(token), json={"direction": "写邮件"}
    )
    assert expand.status_code == 200 and expand.json()["demo"] is True
    gen = client.post(
        "/api/generate",
        headers=_auth(token),
        json={"topic": "用AI写周报", "tone": "checklist"},
    )
    assert gen.status_code == 200 and gen.json()["demo"] is True
    assert calls == []


def test_render_fixed_sample_size_and_no_overflow(client):
    """固定输入：文件存在、3:4、文字不进外缘。"""
    token = _login(client)
    r = client.post(
        "/api/drafts",
        headers=_auth(token),
        json={
            "title": SAMPLE_TITLE,
            "body": SAMPLE_BODY,
            "tags": SAMPLE_TAGS,
            "template": "berry",
        },
    )
    assert r.status_code == 200, r.text
    did = r.json()["id"]
    rendered = client.post(
        f"/api/drafts/{did}/render", headers=_auth(token), json={"template": "berry"}
    )
    assert rendered.status_code == 200, rendered.text
    assert rendered.json()["count"] >= 2
    cover = None
    for n in range(1, rendered.json()["count"] + 1):
        im = _open_card(client, token, did, n)
        if n == 1:
            cover = im
    assert cover is not None
    if app_module.find_font(False):
        # 标题区左侧，避开右上角装饰圆，确认字真的画上去了
        assert _ink_box(cover, 84, 300, 640, 520) > 80


def test_long_tags_stay_inside_card(client):
    """产品允许每个标签 20 字、封面最多画 4 个。这些字必须留在画布内。"""
    token = _login(client)
    tags = ["标" * 20, "签" * 20, "题" * 20, "目" * 20]
    r = client.post(
        "/api/drafts",
        headers=_auth(token),
        json={"title": "题" * 20, "body": "正" * 300, "tags": tags, "template": "berry"},
    )
    assert r.status_code == 200, r.text
    did = r.json()["id"]
    rendered = client.post(
        f"/api/drafts/{did}/render", headers=_auth(token), json={"template": "berry"}
    )
    assert rendered.status_code == 200, rendered.text
    assert rendered.json()["count"] >= 2
    for n in range(1, rendered.json()["count"] + 1):
        _open_card(client, token, did, n)


def test_export_zip(client):
    token = _login(client)
    r = client.post(
        "/api/drafts",
        headers=_auth(token),
        json={"title": SAMPLE_TITLE, "body": SAMPLE_BODY, "tags": SAMPLE_TAGS},
    )
    did = r.json()["id"]
    r = client.post(f"/api/drafts/{did}/export", headers=_auth(token))
    assert r.status_code == 200, r.text
    assert "zip" in r.headers.get("content-type", "")
    z = zipfile.ZipFile(io.BytesIO(r.content))
    names = z.namelist()
    assert "文案.txt" in names
    assert "01.png" in names
    text = z.read("文案.txt").decode("utf-8")
    assert SAMPLE_TITLE in text
    assert "#AI工具" in text
    cover = z.read("01.png")
    assert cover[:8] == b"\x89PNG\r\n\x1a\n"
    im = Image.open(io.BytesIO(cover))
    assert im.size == (1080, 1440)


def test_banned_words_flagged_save_not_blocked(client):
    """违禁词自查标出命中。README 口径是只提示，不拦截保存。"""
    token = _login(client)
    r = client.post(
        "/api/check",
        headers=_auth(token),
        json={"title": "全国第一", "body": "这能稳赚，还能免费领取"},
    )
    assert r.status_code == 200, r.text
    hits = {h["word"] for h in r.json()["hits"]}
    assert hits == {"第一", "稳赚", "免费领取"}
    saved = client.post(
        "/api/drafts",
        headers=_auth(token),
        json={"title": "全国第一", "body": "这能稳赚"},
    )
    assert saved.status_code == 200, saved.text


def test_missing_font_still_renders(client, monkeypatch):
    monkeypatch.setattr(app_module, "find_font", lambda bold=False: None)
    app_module._font_cache.clear()
    token = _login(client)
    r = client.post(
        "/api/drafts",
        headers=_auth(token),
        json={"title": SAMPLE_TITLE, "body": SAMPLE_BODY, "tags": SAMPLE_TAGS},
    )
    did = r.json()["id"]
    rendered = client.post(f"/api/drafts/{did}/render", headers=_auth(token), json={})
    assert rendered.status_code == 200, rendered.text
    assert rendered.json()["count"] >= 2
    for n in range(1, rendered.json()["count"] + 1):
        _open_card(client, token, did, n)


def test_update_null_fields_not_stored_as_none_string(client):
    """回归：草稿更新时传 JSON null，不得存成 "None" 字面量（082-P2-3）。"""
    token = _login(client)
    r = client.post(
        "/api/drafts",
        headers=_auth(token),
        json={"title": "空值测试", "body": "正文", "tags": []},
    )
    assert r.status_code == 200, r.text
    did = r.json()["id"]
    r = client.put(
        f"/api/drafts/{did}",
        headers=_auth(token),
        json={"published_url": None, "published_at": None, "status": "published"},
    )
    assert r.status_code == 200, r.text
    d = client.get(f"/api/drafts/{did}", headers=_auth(token)).json()
    assert d["published_url"] in (None, ""), d["published_url"]
    assert d["published_at"] in (None, ""), d["published_at"]
    assert '"None"' not in json.dumps(d, ensure_ascii=False)


def test_extreme_aspect_cover_renders(client):
    """回归：2000×10 极端宽高比封面不把中间图放大到数亿像素（097-P1-1）。

    旧公式 scale=max(1080/2000, 1440/10)=144 会算出 288000×1440（约 4.15 亿像素）
    的中间图；ImageOps.fit 先裁后缩，内存可控。
    """
    import time
    token = _login(client)
    r = client.post(
        "/api/drafts",
        headers=_auth(token),
        json={"title": "宽高比测试", "body": "正文", "tags": []},
    )
    assert r.status_code == 200, r.text
    did = r.json()["id"]
    buf = io.BytesIO()
    Image.new("RGB", (2000, 10), "navy").save(buf, "PNG")
    up = client.post(
        f"/api/drafts/{did}/cover",
        files={"file": ("wide.png", buf.getvalue(), "image/png")},
        headers=_auth(token),
    )
    assert up.status_code == 200, up.text
    t0 = time.time()
    rendered = client.post(f"/api/drafts/{did}/render", headers=_auth(token), json={})
    dt = time.time() - t0
    assert rendered.status_code == 200, rendered.text
    assert rendered.json()["count"] >= 1
    # 注：不用 _open_card——它的外缘溢墨断言只适用于模板封面（浅底），
    # 上传照片封面整张都是图。这里只断言下载成功、尺寸 1080×1440、耗时合理。
    r = client.get(f"/api/drafts/{did}/cards/1", headers=_auth(token))
    assert r.status_code == 200, r.text
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"
    im = Image.open(io.BytesIO(r.content)).convert("RGB")
    assert im.size == (1080, 1440)
    assert dt < 30, f"渲染耗时 {dt:.1f}s 过长"
