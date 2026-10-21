# TASK-097-notepress 执行记录

开工：2026-10-22，工作目录 E:\muse-bridge\in\TASK-097-notepress。先审查再修 P0/P1。

## 环境探测

命令：`python --version`

```
Python 3.11.9
```

命令：`python E:\muse-bridge\work\TASK-097-notepress\sizes.py`

最大单文件 41750 字节（app.py），低于 2MB。扩展名统计无 ttf/otf/woff/woff2。仓库内可见源码文件 43 个（含 .git）。最大源码文件 app.py=41750，index.html=26530。

命令：`python E:\muse-bridge\work\TASK-097-notepress\fonts.py`

```
EXISTS C:/Windows/Fonts/msyh.ttc 19704352
EXISTS C:/Windows/Fonts/msyhbd.ttc 16883552
MISSING C:/Windows/Fonts/msyh.ttf
EXISTS C:/Windows/Fonts/simhei.ttf 9745792
EXISTS C:/Windows/Fonts/simsun.ttc 18316748
MISSING Linux Noto / 文泉驿 / macOS 苹方 / 华文黑体（本机是 Windows，预期缺失）
```

虚拟环境放在仓库外：`E:\muse-bridge\work\TASK-097-notepress\venv`（避免往仓库写 .venv）。

命令：`python -m venv E:\muse-bridge\work\TASK-097-notepress\venv`

退出码 0。

## 安装运行依赖

命令：`E:\muse-bridge\work\TASK-097-notepress\venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-097-notepress\requirements.txt`

退出码 0。装上 fastapi==0.156.8、uvicorn==0.54.0、python-multipart==0.0.32、httpx==0.28.1、pillow==13.0.0（及 starlette、pydantic 等传递依赖）。末行：`Successfully installed ... fastapi-0.156.8 ... pillow-13.0.0 ... uvicorn-0.54.0`

## 安装测试依赖

命令：`E:\muse-bridge\work\TASK-097-notepress\venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-097-notepress\requirements-dev.txt`

退出码 0。`Successfully installed ... pytest-9.1.1`

## 全量 pytest（无 API key）

命令：`E:\muse-bridge\work\TASK-097-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-097-notepress\run_pytest.py`

该脚本设置 TEMP/TMP 到 `E:\muse-bridge\work\TASK-097-notepress\tmp`，去掉 `NOTEPRESS_LLM_API_KEY`，在仓库目录执行 `python -m pytest tests -q -p no:cacheprovider --tb=short`。

输出：

```
................................                                         [100%]
============================== warnings summary ===============================
..\..\work\TASK-097-notepress\venv\Lib\site-packages\fastapi\testclient.py:1
  StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
32 passed, 1 warning in 14.45s
NOTEPRESS_LLM_API_KEY_SET False
```

退出码 0。

## 真实流程自测 live_selftest（无 API key，端口 8155）

命令：`E:\muse-bridge\work\TASK-097-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-097-notepress\run_live.py`

脚本把 TEMP/TMP 指到工作目录，去掉 `NOTEPRESS_LLM_API_KEY`，再执行 `python tests\live_selftest.py 8155`。

输出：

```
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
NOTEPRESS_LLM_API_KEY_SET False
```

退出码 0。

## 按 README 起服务（127.0.0.1:8000）并走完演示流程

命令：`E:\muse-bridge\work\TASK-097-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-097-notepress\run_server.py`

数据库和媒体目录改到 `E:\muse-bridge\work\TASK-097-notepress\server-8000`，未设置 `NOTEPRESS_LLM_API_KEY`。脚本结束后对子进程调用 terminate。

输出片段：

```
PID 28740
KEY_SET False
HEALTH 200 {"status":"ok","app_id":"notepress"}
INDEX 200 text/html; charset=utf-8 bytes 26530
INDEX_HAS_NOTEPRESS True
INDEX_HAS_GONGFANG True
SECURITY {'x-content-type-options': 'nosniff', 'x-frame-options': 'DENY', 'referrer-policy': 'same-origin'}
LOGIN 200 must_change True token_len 43
ME 200 {'username': 'admin', 'must_change': True, 'llm_configured': False}
EXPAND 200 demo True n 6
GENERATE 200 demo True title0 用AI写周报，这样做超简单 title_lens [13, 11, 12] body_len 281 tags ['AI工具', '普通人用AI', '效率提升', '职场干货', 'AI教程']
DRAFT 200 {"id":1}
RENDER 200 count 3
CARD 200 image/png size (1080, 1440) bytes 60229
EXPORT 200 application/zip ['01.png', '02.png', '03.png', '文案.txt']
NOAUTH 401
STOPPED 1
```

uvicorn 日志有 `Uvicorn running on http://127.0.0.1:8000`。另有一条 `127.0.0.1:49816 GET /`，不是本脚本的 httpx 客户端（脚本侧是 59402），只记录。

随后 `check_port.py`：`PORT_8000_CLOSED TimeoutError`，`PORT_8155_CLOSED TimeoutError`。2 秒内没有进程接受连接。`STOPPED 1` 是 Windows 上 terminate 的退出码。

## 边界探针（修复前）

命令：`E:\muse-bridge\work\TASK-097-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-097-notepress\probe.py`

封面旧算法的中间图像素（只代入 app.py 的算式，没有真的分配）：

```
src 800x600 scale 2.4000 tmp 1921x1441 pixels 2768161
src 2000x10 scale 144.0000 tmp 288001x1441 pixels 415009441
src 10x2000 scale 108.0000 tmp 1081x216001 pixels 233497081
src 8000x50 scale 28.8000 tmp 230401x1441 pixels 332007841
```

其它片段：

```
FONT C:/Windows/Fonts/msyh.ttc C:/Windows/Fonts/msyhbd.ttc
10 个种子选题 × 3 种语气全部 200；标题长度都是 [17, 15, 16]；正文最长 295；over20 False
EXTREME_RENDER 200 count 5（标题 20 个「国」、正文 1000 个「国」、4 个 20 字标签）
  CARD 1 bbox (0, 0, 1079, 1344) edge8 8972
  CARD 2..5 bbox x=84..996 y=95..1373 edge8 0
UPLOAD1 200 cover_file 2.png（原始文件名 ../../..\secret.png）
UPLOAD2 200 然后 DELETE 200，COVER_FILES_AFTER []
NOAUTH 401
DOCS 404 404
TITLE21 400 标题超过上限 20 字（当前 21 字）
TOPIC101 400 选题超过上限 100 字（当前 101 字）
DIR51 400 方向词超过上限 50 字（当前 51 字）
TAG21 400 标签超过上限 20 字（当前 21 字）
SESSION_SPAN ('2026-10-22T01:36:45', '2026-10-23T01:36:45')
```

封面卡 edge8=8972 来自通栏色条 `app.py` 里 `rectangle([0, 0, CARD_W, 26])` 和右上角装饰圆，内容卡外缘 8 像素无非背景点。

`probe_tags.py`：`UNIQUE11 400 {"detail":"标签超过上限 10 个（当前 11 个）"}`；`UNIQUE10 200`。

## 修复 P1-1 后的验证

对应测试命令：`E:\muse-bridge\work\TASK-097-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-097-notepress\run_focus.py`

```
5 passed, 1 warning in 3.77s
```

极端封面命令：`...\venv\Scripts\python.exe E:\muse-bridge\work\TASK-097-notepress\verify_cover.py`

```
WIDE RENDER 200 ... 0.070s
WIDE CARD 200 (1080, 1440)
TALL RENDER 200 ... 0.057s
TALL CARD 200 (1080, 1440)
NORMAL CARD 200 (1080, 1440)
NORMAL CENTER (200, 80, 90)
```

全量重跑：同一 `run_pytest.py`。

```
32 passed, 1 warning in 14.79s
NOTEPRESS_LLM_API_KEY_SET False
```

退出码 0。警告仍是 httpx2 弃用，没有失败用例。

命令：`git status --porcelain`

```
 M app.py
```
