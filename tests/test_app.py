"""notepress 自动化测试。

每个用例用独立的临时数据库/媒体目录/违禁词文件互不干扰；
LLM 一律打桩或走演示模式，不打真实接口、不需要任何密钥。
"""

import io
import json
import os
import sys
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app as app_module


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    media = tmp_path / "media"
    words = tmp_path / "banned.json"
    words.write_text(json.dumps({"words": ["第一", "免费领取", "稳赚"]}, ensure_ascii=False),
                     encoding="utf-8")
    monkeypatch.setattr(app_module, "DB_PATH", db)
    monkeypatch.setattr(app_module, "MEDIA_DIR", media)
    monkeypatch.setattr(app_module, "BANNED_WORDS_FILE", words)
    monkeypatch.delenv("NOTEPRESS_LLM_API_KEY", raising=False)
    app_module.init_db()
    with TestClient(app_module.app) as c:
        yield c


def login(client, password="admin123"):
    r = client.post("/api/login", json={"username": "admin", "password": password})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------- 账号


def test_login_ok_and_me(client):
    r = client.post("/api/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200
    assert r.json()["must_change"] is True
    token = r.json()["token"]
    me = client.get("/api/me", headers=auth(token))
    assert me.status_code == 200
    assert me.json()["username"] == "admin"
    assert me.json()["llm_configured"] is False  # 测试环境不配密钥


def test_login_wrong_password(client):
    r = client.post("/api/login", json={"username": "admin", "password": "nope"})
    assert r.status_code == 401


def test_unauthorized_401(client):
    assert client.get("/api/topics").status_code == 401
    assert client.get("/api/drafts").status_code == 401


def test_docs_closed(client):
    for p in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(p).status_code == 404, p


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["app_id"] == "notepress"


def test_hint_only_password_change(client):
    """口径第 1 条：未改密时只是提示，业务接口照常可用。"""
    token = login(client)
    assert client.get("/api/topics", headers=auth(token)).status_code == 200
    assert client.post("/api/drafts", headers=auth(token),
                       json={"title": "提示下也能做单", "body": "正文"}).status_code == 200


def test_change_password_revokes_other_sessions(client):
    """口径第 2 条：改密吊销其他会话、保留本次，并配回归断言。"""
    t1 = login(client)
    t2 = login(client)
    r = client.post("/api/change-password", headers=auth(t1),
                    json={"old_password": "admin123", "new_password": "newpass1"})
    assert r.status_code == 200
    assert client.get("/api/me", headers=auth(t2)).status_code == 401  # 其他会话被吊销
    assert client.get("/api/me", headers=auth(t1)).status_code == 200  # 本次保留
    assert client.get("/api/me", headers=auth(t1)).json()["must_change"] is False
    t3 = login(client, "newpass1")
    assert client.get("/api/me", headers=auth(t3)).status_code == 200


def test_change_password_same_and_wrong(client):
    token = login(client)
    r = client.post("/api/change-password", headers=auth(token),
                    json={"old_password": "admin123", "new_password": "admin123"})
    assert r.status_code == 400 and "相同" in r.json()["detail"]
    r = client.post("/api/change-password", headers=auth(token),
                    json={"old_password": "wrong", "new_password": "whatever1"})
    assert r.status_code == 400


def test_logout_revokes_current_only(client):
    t1 = login(client)
    t2 = login(client)
    assert client.post("/api/logout", headers=auth(t1)).status_code == 200
    assert client.get("/api/me", headers=auth(t1)).status_code == 401
    assert client.get("/api/me", headers=auth(t2)).status_code == 200


# ---------------------------------------------------------------- 选题


def test_seed_topics_present(client):
    token = login(client)
    topics = client.get("/api/topics", headers=auth(token)).json()["topics"]
    assert len(topics) >= 8
    assert all(t["source"] == "seed" for t in topics)


def test_topic_crud_and_limit(client):
    token = login(client)
    r = client.post("/api/topics", headers=auth(token), json={"title": "我的新选题"})
    assert r.status_code == 200
    tid = r.json()["id"]
    titles = [t["title"] for t in client.get("/api/topics", headers=auth(token)).json()["topics"]]
    assert "我的新选题" in titles
    r = client.post("/api/topics", headers=auth(token), json={"title": "长" * 101})
    assert r.status_code == 400
    assert "100" in r.json()["detail"] and "101" in r.json()["detail"]
    assert client.delete(f"/api/topics/{tid}", headers=auth(token)).status_code == 200


def test_expand_demo_mode(client):
    token = login(client)
    r = client.post("/api/topics/expand", headers=auth(token), json={"direction": "带娃"})
    assert r.status_code == 200
    body = r.json()
    assert body["demo"] is True
    assert len(body["candidates"]) >= 5
    assert all("带娃" in c for c in body["candidates"])


# ---------------------------------------------------------------- 写稿


def test_generate_demo_mode(client):
    token = login(client)
    r = client.post("/api/generate", headers=auth(token),
                    json={"topic": "用AI写周报", "tone": "checklist"})
    assert r.status_code == 200
    d = r.json()
    assert d["demo"] is True
    assert 1 <= len(d["titles"]) <= 3
    assert all(len(t) <= 20 for t in d["titles"])
    assert 0 < len(d["body"]) <= 1000
    assert len(d["tags"]) >= 3


def test_generate_with_stubbed_llm(client, monkeypatch):
    monkeypatch.setenv("NOTEPRESS_LLM_API_KEY", "sk-test-not-real")

    def fake_chat(messages, temperature=0.8):
        return json.dumps({
            "titles": ["AI写周报真香", "周报交给AI写", "3分钟搞定周报"],
            "body": "正文一段。\n\n第二段。",
            "tags": ["AI工具", "周报"],
        }, ensure_ascii=False)

    monkeypatch.setattr(app_module, "llm_chat", fake_chat)
    token = login(client)
    r = client.post("/api/generate", headers=auth(token),
                    json={"topic": "用AI写周报", "tone": "experience"})
    assert r.status_code == 200
    d = r.json()
    assert d["demo"] is False
    assert d["titles"][0] == "AI写周报真香"
    assert d["tags"] == ["AI工具", "周报"]


def test_generate_llm_overlong_title_rejected(client, monkeypatch):
    monkeypatch.setenv("NOTEPRESS_LLM_API_KEY", "sk-test-not-real")

    def fake_chat(messages, temperature=0.8):
        return json.dumps({"titles": ["这是一个超过二十个字的非常非常长的标题候选啊"],
                           "body": "正文", "tags": []}, ensure_ascii=False)

    monkeypatch.setattr(app_module, "llm_chat", fake_chat)
    token = login(client)
    r = client.post("/api/generate", headers=auth(token),
                    json={"topic": "选题", "tone": "checklist"})
    assert r.status_code == 502


def test_generate_llm_overlong_body_rejected(client, monkeypatch):
    monkeypatch.setenv("NOTEPRESS_LLM_API_KEY", "sk-test-not-real")

    def fake_chat(messages, temperature=0.8):
        return json.dumps({"titles": ["正常标题"], "body": "字" * 1001, "tags": []},
                          ensure_ascii=False)

    monkeypatch.setattr(app_module, "llm_chat", fake_chat)
    token = login(client)
    r = client.post("/api/generate", headers=auth(token),
                    json={"topic": "选题", "tone": "checklist"})
    assert r.status_code == 502 and "1000" in r.json()["detail"]


# ---------------------------------------------------------------- 草稿与校验


def test_draft_crud_and_status_flow(client):
    token = login(client)
    r = client.post("/api/drafts", headers=auth(token),
                    json={"title": "第一篇", "body": "正文内容", "tags": ["AI工具"]})
    assert r.status_code == 200
    did = r.json()["id"]
    d = client.get(f"/api/drafts/{did}", headers=auth(token)).json()
    assert d["status"] == "draft" and d["tags"] == ["AI工具"]
    r = client.put(f"/api/drafts/{did}", headers=auth(token), json={"status": "ready"})
    assert r.status_code == 200
    r = client.put(f"/api/drafts/{did}", headers=auth(token),
                   json={"status": "published", "published_url": "https://example.com/n/1",
                         "published_at": "2026-10-21 20:00:00"})
    assert r.status_code == 200
    d = client.get(f"/api/drafts/{did}", headers=auth(token)).json()
    assert d["status"] == "published" and d["published_url"].endswith("/n/1")
    lst = client.get("/api/drafts?status=published", headers=auth(token)).json()["drafts"]
    assert [x["id"] for x in lst] == [did]
    assert client.delete(f"/api/drafts/{did}", headers=auth(token)).status_code == 200
    assert client.get(f"/api/drafts/{did}", headers=auth(token)).status_code == 404


def test_title_body_limits_with_lengths(client):
    """口径第 10 条：超限 400，报错带上限与当前字数，不静默截断。"""
    token = login(client)
    r = client.post("/api/drafts", headers=auth(token),
                    json={"title": "题" * 21, "body": "正文"})
    assert r.status_code == 400
    assert "20" in r.json()["detail"] and "21" in r.json()["detail"]
    r = client.post("/api/drafts", headers=auth(token),
                    json={"title": "正常", "body": "字" * 1001})
    assert r.status_code == 400
    assert "1000" in r.json()["detail"] and "1001" in r.json()["detail"]
    # 恰好卡在上限是允许的
    r = client.post("/api/drafts", headers=auth(token),
                    json={"title": "题" * 20, "body": "字" * 1000})
    assert r.status_code == 200


# ---------------------------------------------------------------- 违禁词


def test_banned_words_check_and_crud(client):
    token = login(client)
    r = client.post("/api/check", headers=auth(token),
                    json={"title": "全国第一的工具", "body": "用了能稳赚，还能免费领取"})
    hits = {h["word"] for h in r.json()["hits"]}
    assert hits == {"第一", "稳赚", "免费领取"}
    r = client.post("/api/banned-words", headers=auth(token), json={"word": "绝绝子"})
    assert "绝绝子" in r.json()["words"]
    r = client.post("/api/check", headers=auth(token), json={"title": "绝绝子", "body": ""})
    assert {h["word"] for h in r.json()["hits"]} == {"绝绝子"}
    r = client.delete("/api/banned-words/绝绝子", headers=auth(token))
    assert "绝绝子" not in r.json()["words"]


# ---------------------------------------------------------------- 成卡与导出


def _make_draft(client, token, body="第一段内容。\n\n第二段内容，讲讲步骤。"):
    r = client.post("/api/drafts", headers=auth(token),
                    json={"title": "AI写周报教程", "body": body, "tags": ["AI工具", "周报"]})
    assert r.status_code == 200
    return r.json()["id"]


def test_render_cards_size_and_pagination(client):
    token = login(client)
    did = _make_draft(client, token, body="\n\n".join(f"第{i}段，内容填充。" * 8 for i in range(6)))
    r = client.post(f"/api/drafts/{did}/render", headers=auth(token), json={})
    assert r.status_code == 200
    assert r.json()["count"] >= 3  # 封面 + 至少 2 页内容
    d = client.get(f"/api/drafts/{did}", headers=auth(token)).json()
    assert len(d["cards"]) == r.json()["count"]
    r = client.get(f"/api/drafts/{did}/cards/1", headers=auth(token))
    assert r.status_code == 200
    img = Image.open(io.BytesIO(r.content))
    assert img.size == (1080, 1440)


def test_render_each_template(client):
    token = login(client)
    did = _make_draft(client, token)
    for tpl in ("berry", "mint", "ink"):
        r = client.post(f"/api/drafts/{did}/render", headers=auth(token), json={"template": tpl})
        assert r.status_code == 200 and r.json()["count"] >= 2


def test_cover_upload_and_render(client):
    token = login(client)
    did = _make_draft(client, token)
    buf = io.BytesIO()
    Image.new("RGB", (800, 600), (200, 80, 90)).save(buf, "PNG")
    r = client.post(f"/api/drafts/{did}/cover", headers=auth(token),
                    files={"file": ("cover.png", buf.getvalue(), "image/png")})
    assert r.status_code == 200
    d = client.get(f"/api/drafts/{did}", headers=auth(token)).json()
    assert d["cover_mode"] == "upload"
    r = client.post(f"/api/drafts/{did}/render", headers=auth(token), json={})
    assert r.status_code == 200
    img = Image.open(io.BytesIO(client.get(f"/api/drafts/{did}/cards/1",
                                            headers=auth(token)).content))
    assert img.size == (1080, 1440)


def test_cover_upload_rejects_non_image(client):
    token = login(client)
    did = _make_draft(client, token)
    r = client.post(f"/api/drafts/{did}/cover", headers=auth(token),
                    files={"file": ("x.txt", b"not an image", "text/plain")})
    assert r.status_code == 400


def test_export_package(client):
    token = login(client)
    did = _make_draft(client, token)
    r = client.post(f"/api/drafts/{did}/export", headers=auth(token))
    assert r.status_code == 200
    z = zipfile.ZipFile(io.BytesIO(r.content))
    names = z.namelist()
    assert "文案.txt" in names
    pngs = [n for n in names if n.endswith(".png")]
    assert pngs == sorted(pngs) and len(pngs) >= 2 and pngs[0] == "01.png"
    text = z.read("文案.txt").decode("utf-8")
    assert "AI写周报教程" in text and "#AI工具" in text
    d = client.get(f"/api/drafts/{did}", headers=auth(token)).json()
    assert d["exported_at"] != ""


def test_index_page_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "notepress" in r.text and "笔记工坊" in r.text
