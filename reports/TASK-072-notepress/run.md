# TASK-072-notepress 执行记录

开工时间：2026-10-21。工作目录 `E:\muse-bridge\in\TASK-072-notepress`。先读仓库再装依赖、跑测试、起服务。

## 环境

- 解释器：`python --version` → `Python 3.11.9`
- 虚拟环境：`E:\muse-bridge\work\TASK-072-notepress\venv`（不写进仓库）
- 仓库最大文件 `app.py` 41006 字节。目录枚举无 ttf/otf/woff/woff2。

## 安装依赖

命令（工作目录虚拟环境，未写入仓库）：

```
E:\muse-bridge\work\TASK-072-notepress\venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-072-notepress\requirements.txt
```

结果摘录：`Successfully installed ... fastapi-0.156.8 ... httpx-0.28.1 ... pillow-13.0.0 ... python-multipart-0.0.32 ... uvicorn-0.54.0`（退出码 0）。传递依赖里有 `starlette-1.9.0`。

```
E:\muse-bridge\work\TASK-072-notepress\venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-072-notepress\requirements-dev.txt
```

结果摘录：`Successfully installed ... pytest-9.1.1`（退出码 0）。

补充：曾用仓库外的 `pytest.main(["tests", ...])` 收集，当时 `sys.path` 不含仓库根，`tests/test_acceptance.py:15` 报 `ModuleNotFoundError: No module named 'app'`。那不是 README 命令。下面这条才是 README 的跑法，32 项通过。不记为项目缺陷。

## pytest

命令（先 `cd /d E:\muse-bridge\in\TASK-072-notepress`，`NOTEPRESS_LLM_API_KEY` 置空，`TEMP`/`TMP` 指到工作目录）：

```
E:\muse-bridge\work\TASK-072-notepress\venv\Scripts\python.exe -B -m pytest tests -q -p no:cacheprovider
```

输出摘录：

```
................................                                         [100%]
32 passed, 1 warning in 15.00s
```

警告原文：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 来自已安装的 `fastapi\testclient.py:1`，不是本仓库代码。32 项全部通过。

## 真实流程自测

命令（仓库根目录，`NOTEPRESS_LLM_API_KEY` 置空，`TEMP`/`TMP` 指向 `E:\muse-bridge\work\TASK-072-notepress`）：

```
E:\muse-bridge\work\TASK-072-notepress\venv\Scripts\python.exe -B tests\live_selftest.py
```

默认端口 8155。输出摘录（退出码 0）：

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
```

## 首页与健康检查

命令：`venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-072-notepress\smoke_server.py`  
环境：`NOTEPRESS_HOST=127.0.0.1`，`PORT=8000`，`NOTEPRESS_LLM_API_KEY` 已去掉，数据库和媒体目录在工作目录。退出码 0。

```
HEALTH 200 {"status":"ok","app_id":"notepress"}
HOME 200 len 25259
HOME_HAS_TITLE True
HOME_HAS_APP True
HEALTH_HDR nosniff DENY
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:56070 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:56070 - "GET / HTTP/1.1" 200 OK
```

进程在脚本 finally 里 `terminate()`。随后探测端口：`PORT_CLOSED 8000 TimeoutError`，`PORT_CLOSED 8155 TimeoutError`。服务已关掉。

## 边界探针

命令：`venv\Scripts\python.exe -B E:\muse-bridge\work\TASK-072-notepress\probe.py`（无密钥，库文件在工作目录）。摘录：

```
FONT C:/Windows/Fonts/msyh.ttc C:/Windows/Fonts/msyhbd.ttc
LONG_TOPIC 200 demo True body_len 1078 titles [17, 15, 16]
LONG_SAVE 400 {"detail":"正文超过上限 1000 字（当前 1078 字）"}
TOPIC100_BODY 378 titles [17, 15, 16]
TAG21 400 标签超过上限 20 字（当前 21 字）
TAG11 400 标签超过上限 10 个（当前 11 个）
AFTER_DELETE 404 dir_exists False
UPDATE_TITLE 200 card_still False
CARD_AFTER_EDIT 404
EXPORT 200 png_changed True text_has_new True text_has_old False
STATUS_ONLY_SAME_BYTES True
NOAUTH_CARD 401
NOAUTH_DRAFTS 401
COVER_MED_LEN 1891369
COVER_MED 200
COVER_HUGE 400 {"detail":"图片超过上限 10MB（当前 10.0MB）"}
PARTIAL_TITLE 200 titles 只剩「短标题」，tags 含 30 字标签
BAD_TOPIC_FK_EXC IntegrityError FOREIGN KEY constraint failed
BANDS 封面外缘 (432, 28, 0)；内容卡外缘全 0
```

`BANDS` 三个数依次是外缘 8 像素里、背景色以外的像素：y<30、30≤y<400、y≥400。封面非零像素来自顶栏和装饰圆；y≥400 为 0。内容卡外缘为 0。

## 收尾重跑

源码未改。再次执行：

```
python -B -m pytest tests -q -p no:cacheprovider
```

```
................................                                         [100%]
32 passed, 1 warning in 15.24s
```

同一脚本里的 `git status --porcelain` 无输出（退出码 0）。仓库工作区没有已跟踪文件的改动。


