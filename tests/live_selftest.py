"""真实流程自测：另起真 uvicorn 进程，演示模式走完 选题→写稿→草稿→成卡→导出 全流程。

用法：python tests/live_selftest.py [端口]
不依赖任何真实 LLM 密钥（演示模式）。自测脚本里的 httpx 必须 trust_env=False，
否则会被云端代理环境变量带偏（团队备忘）。
"""

import io
import os
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8155
BASE = f"http://127.0.0.1:{PORT}"

passed = 0


def check(name, cond, extra=""):
    global passed
    if cond:
        passed += 1
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {extra}")
        raise SystemExit(1)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="notepress-selftest-"))
    env = dict(os.environ)
    env["NOTEPRESS_DB"] = str(tmp / "np.db")
    env["NOTEPRESS_MEDIA"] = str(tmp / "media")
    env["NOTEPRESS_BANNED_WORDS"] = str(ROOT / "data" / "banned_words.json")
    env.pop("NOTEPRESS_LLM_API_KEY", None)
    env["PORT"] = str(PORT)
    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "app.py")],
        cwd=ROOT, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        client = httpx.Client(base_url=BASE, timeout=15, trust_env=False)
        for _ in range(50):
            try:
                if client.get("/health").status_code == 200:
                    break
            except Exception:
                time.sleep(0.3)
        else:
            raise SystemExit("服务没起来")
        check("health 200", True)

        r = client.post("/api/login", json={"username": "admin", "password": "admin123"})
        check("登录成功", r.status_code == 200)
        token = r.json()["token"]
        check("首次登录提示改密", r.json()["must_change"] is True)
        h = {"Authorization": f"Bearer {token}"}

        topics = client.get("/api/topics", headers=h).json()["topics"]
        check("种子选题已预置", len(topics) >= 8, f"got {len(topics)}")

        r = client.post("/api/topics/expand", headers=h, json={"direction": "写邮件"})
        check("AI 扩题（演示模式）", r.status_code == 200 and r.json()["demo"] is True
              and len(r.json()["candidates"]) >= 5)

        r = client.post("/api/generate", headers=h,
                        json={"topic": "用AI写邮件", "tone": "experience"})
        check("生成稿件（演示模式标注示例稿）", r.status_code == 200 and r.json()["demo"] is True)
        gen = r.json()
        check("标题合规 ≤20 字", all(len(t) <= 20 for t in gen["titles"]))
        check("正文合规 ≤1000 字", 0 < len(gen["body"]) <= 1000)

        r = client.post("/api/drafts", headers=h, json={
            "title": gen["titles"][0], "body": gen["body"], "tags": gen["tags"],
            "tone": "experience"})
        check("存入草稿箱", r.status_code == 200)
        did = r.json()["id"]

        r = client.post("/api/check", headers=h,
                        json={"title": "全国第一好用", "body": gen["body"]})
        check("违禁词自查命中「第一」",
              any(x["word"] == "第一" for x in r.json()["hits"]))

        r = client.post(f"/api/drafts/{did}/render", headers=h, json={"template": "mint"})
        check("生成卡片 ≥2 张", r.status_code == 200 and r.json()["count"] >= 2,
              r.text[:200])
        r = client.get(f"/api/drafts/{did}/cards/1", headers=h)
        check("封面卡是 PNG", r.status_code == 200 and r.content[:4] == b"\x89PNG")

        r = client.post(f"/api/drafts/{did}/export", headers=h)
        check("导出发布包", r.status_code == 200)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        names = z.namelist()
        check("发布包含编号图片+文案", "文案.txt" in names
              and any(n == "01.png" for n in names))
        text = z.read("文案.txt").decode("utf-8")
        check("文案内容对得上", gen["titles"][0] in text and "#AI工具" in text)

        r = client.put(f"/api/drafts/{did}", headers=h,
                       json={"status": "published",
                             "published_url": "https://www.xiaohongshu.com/explore/demo",
                             "published_at": "2026-10-21 20:30:00"})
        check("状态流转到已发布并回填链接", r.status_code == 200)

        print(f"\nALL PASS · {passed} 个检查点")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
