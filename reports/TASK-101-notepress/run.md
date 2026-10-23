# TASK-101-notepress 执行记录

开工：2026-10-23。工作目录 `E:\muse-bridge\in\TASK-101-notepress`。先审查再修 P0/P1（最多 5 项）。临时文件目录 `E:\muse-bridge\work\TASK-101-notepress`。

除 pytest 自报耗时外，其余命令未另计墙钟。

## 环境与仓库清点

```
python --version
Python 3.11.9
```

```
git rev-parse --short HEAD
cecf9b6
```

```
git log -5 --format=%h%x09%an%x09%s
cecf9b6	ZZmkk88	fix(TASK-097): 上传封面改用 ImageOps.fit 防极端宽高比 DoS（2000×10 旧公式会算出约 4.15 亿像素中间图）；配回归测试 test_extreme_aspect_cover_renders
```

浅克隆，只看到这一条提交。

```
git status --porcelain
```

开工时标准输出为空。

系统字体存在：`C:\Windows\Fonts\msyh.ttc`、`C:\Windows\Fonts\msyhbd.ttc`。清点脚本 `E:\muse-bridge\work\TASK-101-notepress\inventory.py` 末行：

```
OVER2MB []
FONTFILES []
```

最大源文件 `app.py` 42866 字节。运行时 `find_font` 返回 `C:/Windows/Fonts/msyh.ttc` 与 `C:/Windows/Fonts/msyhbd.ttc`。

## 装依赖

虚拟环境：`E:\muse-bridge\work\TASK-101-notepress\venv`（不放进仓库）。

```
E:\muse-bridge\work\TASK-101-notepress\venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-101-notepress\requirements.txt -r E:\muse-bridge\in\TASK-101-notepress\requirements-dev.txt
```

退出码 0。已装 fastapi==0.156.8、uvicorn==0.54.0、python-multipart==0.0.32、httpx==0.28.1、pillow==13.0.0、pytest==9.1.1。

## 全量测试（审查时）

未设置 `NOTEPRESS_LLM_API_KEY`。`TMP`/`TEMP` 指向 `E:\muse-bridge\work\TASK-101-notepress\tmp`。

```
python -m pytest tests\ -q -p no:cacheprovider
..................................                                       [100%]
34 passed, 1 warning in 18.90s
```

警告：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.`

脚本打印 `KEY_SET False`。退出码 0。

## 真服务自测

```
python tests\live_selftest.py 8155
  PASS health 200
  PASS 登录成功
  PASS 首次登录提示改密
  PASS 种子选题已预置
  PASS AI 扩题（演示模式）
  PASS 生成稿件（演示模式标注示例稿）
  PASS 标题合规 ≤20 字
  PASS 正文合规 ≤1000 字
  PASS 存入草稿箱
  PASS 违禁词自查命中「第一」
  PASS 生成卡片 ≥2 张
  PASS 封面卡是 PNG
  PASS 导出发布包
  PASS 发布包含编号图片+文案
  PASS 文案内容对得上
  PASS 状态流转到已发布并回填链接

ALL PASS · 16 个检查点
```

退出码 0。`KEY_SET False`。

## 按 README 起服务

默认端口 8000（数据库与媒体改到工作目录，避免在仓库留下 db）：

```
ERROR:    [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000): 通常每个套接字地址(协议/网络地址/端口)只允许使用一次。
```

本进程没有完成绑定。占着 8000 的不是本仓库。未结束该进程。

改 `PORT=8765` 后：

```
INFO:     Uvicorn running on http://127.0.0.1:8765 (Press CTRL+C to quit)
INFO:     127.0.0.1:64071 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:64071 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:64071 - "POST /api/login HTTP/1.1" 200 OK
INFO:     127.0.0.1:64071 - "GET /api/me HTTP/1.1" 200 OK
INFO:     127.0.0.1:64071 - "POST /api/generate HTTP/1.1" 200 OK
```

```
HEALTH_BODY {"status":"ok","app_id":"notepress"}
HOME_STATUS 200
HOME_LEN 25242
HOME_HAS_NOTEPRESS True
HOME_HAS_TITLE True
LOGIN_MUST_CHANGE True
ME 200 {"username":"admin","must_change":true,"llm_configured":false}
GEN 200 demo True title0 用AI写周报，这样做超简单 body_len 281
```

安全头：`x-content-type-options: nosniff`，`x-frame-options: DENY`，`referrer-policy: same-origin`。

随后 `terminate`。`Get-Process -Id 5724` 结果为 `ObjectNotFound`（找不到该 PID），服务已关。

## 探针（未改仓库）

11 个不同标签：`400 {"detail":"标签超过上限 10 个（当前 11 个）"}`。10 个标签：200。21 字标签：400。JPEG 封面渲染 `(1080, 1440)`，删除草稿后封面与卡片目录为空。100 字选题三条演示正文长度 375 / 327 / 315。未登录导出、渲染、卡片、违禁词：401。`/docs` 与 `/media/covers/1.png`：404。

## 收尾重跑

```
python -m pytest tests\ -q -p no:cacheprovider
..................................                                       [100%]
34 passed, 1 warning in 18.77s
```

退出码 0。`KEY_SET False`。警告原文与审查时相同。

```
git status --porcelain
```

标准输出为空，退出码 0。仓库无改动。
