# notepress 验收

结论：演示模式在无 API key、不访问外网的条件下可以跑通。pytest 32 项通过，真实服务自测 16 个检查点通过，`127.0.0.1:8000` 的 `/` 与 `/health` 返回正常，检查后已关掉进程。仓库源码与 README 的平台规格一致。P0 为空。唯一触及专项字面要求的问题是测试文件里的占位密钥字符串，禁止改测试，本次不改源码。

## 本地跑通记录

环境：本机 `Python 3.11.9`。虚拟环境在 `E:\muse-bridge\work\TASK-089-notepress\venv`，没有在仓库里建 `.venv`。`NOTEPRESS_LLM_API_KEY` 未设置。临时目录指向 `E:\muse-bridge\work\TASK-089-notepress`。

装依赖（exit 0）：

```
python -m venv E:\muse-bridge\work\TASK-089-notepress\venv
E:\muse-bridge\work\TASK-089-notepress\venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
```

装上 fastapi==0.156.8、uvicorn==0.54.0、python-multipart==0.0.32、httpx==0.28.1、pillow==13.0.0、pytest==9.1.1。

全量测试（cwd = 仓库根，exit 0）：

```
E:\muse-bridge\work\TASK-089-notepress\venv\Scripts\python.exe -m pytest tests\ -q -p no:cacheprovider
```

```
................................                                         [100%]
32 passed, 1 warning in 15.58s
```

警告原文是 StarletteDeprecationWarning：`Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 测试没有失败。`DECISIONS.md:37` 已写明不为这条警告改依赖版本。

真实流程自测（exit 0，脚本默认端口 8155，自己起进程并在结束时终止）：

```
E:\muse-bridge\work\TASK-089-notepress\venv\Scripts\python.exe tests\live_selftest.py
```

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

按 README 再起一次服务。数据库和媒体放到工作目录，监听 `127.0.0.1:8000`，无密钥。

```
Uvicorn running on http://127.0.0.1:8000
GET /health -> 200 {"status":"ok","app_id":"notepress"}
GET / -> 200 text/html; charset=utf-8 ，长度 25227，含 notepress 与「笔记工坊」
x-content-type-options: nosniff
x-frame-options: DENY
```

同一进程上无密钥走完：登录 200，`/api/me` 为 `llm_configured: false`，扩题 `demo: true`，写稿 `demo: true`，存草稿，渲染 3 张卡，封面卡为 PNG（59289 字节）。然后 terminate。进程退出码 1，是终止带来的；终止前访问日志全部是 200。复查 `GET /health` 被拒绝，原文含 `WinError 10061`。`netstat` 里 `127.0.0.1:8000` 只剩 `TIME_WAIT`，没有 `LISTEN`。

补充探针（未改仓库）：

- 11 个不同标签返回 400：`标签超过上限 10 个（当前 11 个）`。21 字标签 400。101 字选题 400。51 字方向词 400。
- 三套演示语气在选题 100 字时正文最长 375，500 字时 checklist 正文 775，都小于 1000。
- 无令牌建草稿 401。`/docs`、`/redoc`、`openapi.json` 均为 404。
- 上传文件名 `..\..\evil.png` 落盘为 `covers/1.png`。仓库根下没有 `evil.png`。
- 本机实际字体 `C:/Windows/Fonts/msyh.ttc` 与 `C:/Windows/Fonts/msyhbd.ttc`。
- 20 字标题加 4 条长标签的文字包围盒在 1080×1440 内。模板封面边缘非背景像素只有强调色 `(255, 36, 66)`（顶栏铺满），内容卡外缘墨点为 0。

## README 与实际不符处

平台规格、端口、演示模式、字体回退、测试数量，与代码一致，本次命令结果也一致。下面只列对得上文件行号的差异。

1. `README.md:26`、`README.md:85` 写密钥只放环境变量、不要写进仓库。`tests/test_app.py:173`、`tests/test_app.py:194`、`tests/test_app.py:208` 提交了字符串 `sk-test-not-real`。源码 `app.py:236`、`app.py:242` 只从 `NOTEPRESS_LLM_API_KEY` 读取。全仓库检索，这段占位串只出现在测试里。它不能当真实密钥用，但和「不要写进任何文件」以及专项「测试里不得出现假 key」字面冲突。
2. `README.md:5` 写功能清单「均已实测」，其中 `README.md:9` 包含「接了 AI 接口时由 AI 扩题」。本仓库能重复的证据是演示模式和 `tests/test_app.py:172` 起的 `llm_chat` 打桩。真实大模型 HTTP 本次未调用（无密钥，且任务禁止抓取外网）。这一条是证据不足，实现本身有 `app.py:332` 起的分支。
3. `README.md:76` 的环境变量表没有写这些已实现的上限：选题 100 字（`app.py:34`、`app.py:777`）、方向词 50 字（`app.py:801`）、新密码至少 6 位（`app.py:740`）、封面 10MB（`app.py:986`）。这是文档遗漏，接口行为与「超限报错」的口径一致。
4. `static/index.html:111` 选题框 `maxlength="120"`，后端 `app.py:34` 是 100。README 没写 120，所以这是前端和后端不一致，不是 README 写错一个数字。101 字提交时接口返回 400，并带当前字数。

下列 README 条款与代码、本次运行一致，不记缺陷：

- 标题 20、正文 1000、不静默截断：`app.py:32`、`app.py:33`、`app.py:694`。21 字标题和 1001 字正文由已通过的 `test_title_body_limits_with_lengths` 覆盖。
- 标签最多 10 个、每个最多 20 字，封面最多画 4 个：`app.py:35`、`app.py:36`、`app.py:566`。11 个不同标签本次返回 400。
- 只做 3:4、1080×1440，不做 9:16：`app.py:38`。全仓库源码没有 9:16 分支。本次卡片尺寸为 1080×1440。
- 无密钥走演示模式且 `demo` 为 true：`app.py:351`、`app.py:333`。`/api/me` 返回 `llm_configured: false`。`test_demo_mode_does_not_call_httpx_post` 已通过。
- 默认 `127.0.0.1:8000`：`app.py:1089`、`app.py:1090`。日志为 `Uvicorn running on http://127.0.0.1:8000`。
- 令牌 24 小时、改密只提示：`app.py:37`、`app.py:176`、`app.py:197`。未做 24 小时实等。业务接口在 `must_change` 为 true 时仍返回 200，与 `README.md:9`、`DECISIONS.md:3` 一致。
- 字体顺序：`README.md:94` 至 `README.md:103` 与 `app.py:397` 至 `app.py:434` 一致。找不到字体时用 `ImageFont.load_default()`。本机走到微软雅黑。
- 测试数量：`README.md:70` 的 25+7=32，与 `32 passed` 一致。`README.md:71` 的 16 个检查点与自测输出一致。
- 违禁词只提示不拦截：已通过的 `test_banned_words_flagged_save_not_blocked`。
- 不做自动发布、点赞、爬虫、多账号、视频：`README.md:20`。业务源码里没有这些实现。

## 许可证与署名核查

自洽，本次不改 `LICENSE` 和 `UPSTREAM.md`。

- `UPSTREAM.md:8` 至 `UPSTREAM.md:11`：`source_url`、`source_commit`、`license`（Apache-2.0）、`attribution`（Copyright 2025 xpzouying）四字段都在。
- `UPSTREAM.md:14` 至 `UPSTREAM.md:18`：同样四字段，MIT，Copyright (c) 2023 dreammis。
- `LICENSE:3` 至 `LICENSE:5` 保留上述两行上游版权，并有本仓 `Copyright (c) 2026 ZZmkk88`。
- 本地 `.git/config` 的 origin 是 `https://github.com/ZZmkk88/notepress.git`，与 `LICENSE:5` 的署名一致。
- `README.md:3`、`UPSTREAM.md:3` 都写代码为独立实现/独立重写。`app.py` 是 FastAPI 写稿成卡，仓库里没有上游发布工具、扫码登录或爬虫代码。
- `source_commit` 两枚都是 40 位十六进制。任务禁止抓取外部页面，这两枚提交是否真实存在标为未核实。没有确凿事实错误，所以不改许可证文件。
- 在「只借鉴思路、LICENSE 保留上游版权行」这个前提下，MIT 全文加上这两行版权，与 UPSTREAM 的四个字段互相一致。

## 分级修复清单

### P0

无。依赖能装上，32 项测试通过，16 个自测点通过，8000 端口首页和健康检查正常。

### P1

1. `tests/test_app.py:173`、`tests/test_app.py:194`、`tests/test_app.py:208` 写死占位串 `sk-test-not-real`，用来让 `llm_configured()` 变成 true。这不是可用密钥，也没有提交真实 key。专项要求测试里不得出现假 key，`README.md:85` 要求不要写进任何文件。修法：测试里改成不含密钥形态的占位值，断言仍只依赖「环境变量非空」。本次不修：任务禁止改测试文件，`DECISIONS.md:35` 至 `DECISIONS.md:37` 也把这项标成永久关闭。`app.py` 没有写死 key，没有可改的源码点。

没有第二项 P1。默认口令 `admin` / `admin123` 写在 `app.py:145` 和 `README.md:24`，改密只提示，这是 `DECISIONS.md:3` 的既定决策，默认只监听 `127.0.0.1`。不把强制改密加回来。

### P2

1. `static/index.html:111` 的 `maxlength="120"` 与 `app.py:34` 的 100 字不一致。修法：前端改成 100。
2. `static/index.html:137` 自由选题没有长度限制，`app.py:816` 的生成接口也不限制 topic。超长选题会把演示正文顶过 1000 字然后 400（`app.py:353`）。500 字选题本次仍能生成。修法：生成接口使用与选题库相同的 100 字上限。
3. `static/index.html:118` 方向词没有 maxlength，上限在 `app.py:801` 为 50。修法：输入框加上 50。
4. `static/index.html:52` 的超限样式是 `.count.over`，`static/index.html:160` 的字数 span 没有 `count` 类，超限不会变红。服务端仍会 400。修法：给字数 span 加上该类。
5. `app.py:365` 在已配置密钥时，大模型网络错误会变成未捕获的 500；`app.py:346` 的扩题失败则退回演示稿。演示模式不进入这两条路径。修法：生成接口捕获传输错误并返回 502，避免和演示成功混在一起。
6. `README.md:76` 未列出选题 100 字、方向词 50 字、密码 6 位、封面 10MB。修法：补进 README 的限制说明。
7. pytest 的 httpx2 弃用警告。修法：保持 `requirements.txt` 与 `requirements-dev.txt` 的版本不动（`DECISIONS.md:37`）。

本次只允许修 P0 和 P1。P1 落在测试文件里，不能改。因此不修改仓库源码。
