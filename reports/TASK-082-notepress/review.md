# notepress 验收审查

结论：在无 `NOTEPRESS_LLM_API_KEY`、不访问外网的条件下，演示模式从选题到导出发布包可以跑通。pytest 32 项通过，真实流程自测 16 个检查点通过，按 README 启动的服务在 `127.0.0.1:8000` 上 `/health` 与首页均返回 200。没有 P0。没有需要改代码的 P1。规格数字与 README 一致。许可证四字段齐全，上游 commit 未向外网复核。

## 本地跑通记录

环境：Python 3.11.9（命令 `python --version`）。虚拟环境放在 `E:\muse-bridge\work\TASK-082-notepress\venv`，没有写进仓库。临时库、日志、自测目录通过 `TMP`/`TEMP` 指到 `E:\muse-bridge\work\TASK-082-notepress`。本机 `NOTEPRESS_LLM_API_KEY` 未设置。本机有 `HTTP_PROXY=http://127.0.0.1:7890`；访问本机服务时使用 `trust_env=False`。系统字体：`C:\Windows\Fonts\msyh.ttc`（19704352 字节）、`C:\Windows\Fonts\msyhbd.ttc`（16883552 字节）。

### 安装依赖

```
E:\muse-bridge\work\TASK-082-notepress\venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-082-notepress\requirements.txt -r E:\muse-bridge\in\TASK-082-notepress\requirements-dev.txt
```

结果：退出码 0。已安装 `fastapi-0.156.8`、`uvicorn-0.54.0`、`python-multipart-0.0.32`、`httpx-0.28.1`、`pillow-13.0.0`、`pytest-9.1.1`。

### 自动化测试

```
E:\muse-bridge\work\TASK-082-notepress\venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```

工作目录：`E:\muse-bridge\in\TASK-082-notepress`。已去掉 `NOTEPRESS_LLM_API_KEY`。

```
................................                                         [100%]
32 passed, 1 warning in 15.30s
```

警告原文（不导致失败）：

```
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

出处：`E:\muse-bridge\work\TASK-082-notepress\venv\Lib\site-packages\fastapi\testclient.py:1`。32 这个数字与 README.md:66 的「25+7」一致：`tests/test_app.py` 25 个 `def test_`，`tests/test_acceptance.py` 7 个 `def test_`。

其中 `tests/test_acceptance.py:98` `test_demo_mode_does_not_call_httpx_post` 已通过，演示模式扩题和写稿没有调用 `httpx.post`。

### 真实流程自测

```
E:\muse-bridge\work\TASK-082-notepress\venv\Scripts\python.exe E:\muse-bridge\in\TASK-082-notepress\tests\live_selftest.py
```

无 API key。耗时 2.08 秒，退出码 0。输出：

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

16 与 README.md:67 一致。脚本在 `finally` 里 `proc.terminate()`（tests/live_selftest.py:115）。

### 按 README 起服务

```
NOTEPRESS_HOST=127.0.0.1
PORT=8000
NOTEPRESS_LLM_API_KEY 未设置
NOTEPRESS_DB / NOTEPRESS_MEDIA / NOTEPRESS_BANNED_WORDS 指向 E:\muse-bridge\work\TASK-082-notepress\smoke-run
E:\muse-bridge\work\TASK-082-notepress\venv\Scripts\python.exe E:\muse-bridge\in\TASK-082-notepress\app.py
```

服务日志：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:57788 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:57788 - "GET / HTTP/1.1" 200 OK
```

`GET /health`：200，`{"status":"ok","app_id":"notepress"}`。响应头含 `x-content-type-options: nosniff`、`x-frame-options: DENY`、`referrer-policy: same-origin`。

`GET /`：200，`text/html; charset=utf-8`，正文长度 25259，含 `notepress` 与 `笔记工坊`。

停服务：对启动进程 `terminate()`，返回码 1（Windows 上进程被终止时常见）。随后 `tasklist /FI "PID eq 30952"` 无匹配进程（日志里的服务 PID）。再请求 `http://127.0.0.1:8000/health` 得到 404 `{"detail":"Not Found"}`，`server: uvicorn`，响应体里没有 `app_id`。那是端口上的另一个程序，不是本次 notepress。本次拉起的 notepress 已退出。没有使用 taskkill。

浏览器点击流程未做：本会话没有浏览器工具。接口流程由 live_selftest 和上述 HTTP 检查覆盖。

### 补充探针（无外网）

命令：`E:\muse-bridge\work\TASK-082-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-082-notepress\probe.py`

- 实际字体：`FONT_REGULAR C:/Windows/Fonts/msyh.ttc`，`FONT_BOLD C:/Windows/Fonts/msyhbd.ttc`
- 演示稿：3 个标题，长度 13/11/12，均不超过 20；正文 284 字；`demo True`；5 个标签
- 三种语气正文长度：checklist 301、experience 251、pitfall 239，均不超过 1000
- 不存在的用户名登录：401 `用户名或密码不对`
- 选题 100 字：200；101 字：400 `选题超过上限 100 字（当前 101 字）`
- 21 字标签：400 `标签超过上限 20 字（当前 21 字）`
- 固定样例渲染两次，PNG 字节相同（40834 字节），尺寸 `(1080, 1440)`，标题区非背景像素 29067
- `PUT` 正文里 `published_url: null` 返回 200，读回的值是字符串 `None`（见分级清单 P2-3）

## README 与实际不符处

下列规格已对照代码和通过的测试，**一致，不列入不符**：

- 标题 20、正文 1000：README.md:11；app.py:32-33；app.py:686-689
- 标签最多 10 个、每个 20 字：README.md:14；app.py:35-36；app.py:845-849
- 封面 3:4、1080×1440、不做 9:16、封面最多画前 4 个标签：README.md:13-15；app.py:38；app.py:557
- 令牌 24 小时、默认 `127.0.0.1:8000`：README.md:8、README.md:28；app.py:37、app.py:1075-1076
- 测试 25+7=32、自测 16 个检查点：README.md:66-67；本次命令输出
- 字体查找顺序：README.md:90-95 与 app.py:388-396 相同
- 环境变量表：README.md:74-84 与 app.py:25-29、236、240-241、404、1075-1076 对应

不符与文档缺口：

1. README.md:12、README.md:26 写「演示模式」。界面文案是「示例模式」：static/index.html:295、static/index.html:337、static/index.html:385。接口字段仍是 `demo: true`（app.py:329、app.py:334）。
2. README.md:15 写封面标签「单行放不下会换行」。app.py:568-570 在换行后还用 `fit_line`（app.py:456）加省略号。DECISIONS.md:20 写了「先截断、再换行」。README 少了截断这一步。
3. README.md:55 的测试段只写 `pip install -r requirements-dev.txt`。requirements-dev.txt:1 只有 `pytest==9.1.1`。tests/test_app.py:15-16 要 import `fastapi` 和 `PIL`，requirements.txt:1-5 才有这些包。只抄测试段会在收集测试时 ImportError。按 README 从上往下先做快速开始（README.md:35）再测，可以跑通，本次就是这样。
4. NOTES.md:22 写运行时包「只有 FastAPI/uvicorn/httpx/Pillow 四个」。requirements.txt:1-5 还有 `python-multipart==0.0.32`。这是 NOTES，不是 README。
5. NOTES.md:34 把回退链写成「Windows 微软雅黑 → macOS 苹方 → Linux Noto」。代码与 README 的查找顺序是 Noto、文泉驿、微软雅黑、苹方、华文黑体（README.md:91-95，app.py:388-396）。在本机 Linux 路径不存在，实际用到的是微软雅黑（探针 `FONT_REGULAR`）。

static/index.html:111 选题输入 `maxlength="120"`，后端上限是 100（app.py:34、app.py:768-769）。README 没有写选题字数，所以不算 README 失实，记在 P2-2。

## 许可证与署名核查

| 位置 | 内容 |
|---|---|
| LICENSE:1 | `MIT License` |
| LICENSE:3-5 | `Copyright 2025 xpzouying`；`Copyright (c) 2023 dreammis`；`Copyright (c) 2026 ZZmkk88` |
| UPSTREAM.md:8-11 | source_url `https://github.com/xpzouying/xiaohongshu-mcp`；source_commit `7797fd375aba02dcd33afe143f6bee13e5870859`；license `Apache-2.0`；attribution `Copyright 2025 xpzouying` |
| UPSTREAM.md:15-18 | source_url `https://github.com/dreammis/social-auto-upload`；source_commit `28bb5bc20206c26d088311633540127402e4de56`；license `MIT`；attribution `Copyright (c) 2023 dreammis` |
| README.md:4 | 「代码为独立实现」 |
| UPSTREAM.md:3 | 「代码为独立重写」 |

内部自洽：两份参考都有 source_url / source_commit / license / attribution。LICENSE 里的前两行版权与 UPSTREAM 的 attribution 字面相同。README 与 UPSTREAM 都声明代码是独立写的，不是把上游仓库改个许可证再发布。

未改 LICENSE / UPSTREAM。依据：

- 版权行与 UPSTREAM 的 attribution 对得上，没有查出写错的名字或年份。
- 参考一的许可证是 Apache-2.0，本仓许可证正文是 MIT，仓库里没有 Apache-2.0 文本。在「独立重写、只保留署名」的前提下，这和任务要求的「有参考就保留上游版权行」一致。本次没有看到把上游发布器或爬虫代码抄进 app.py 的痕迹（app.py 是 FastAPI 选题/写稿/成卡）。不能据此证明没有抄表达，只说明静态阅读下声明和代码形态相符。
- source_commit 是否真是这两个仓库的提交：**未核实**。任务禁止抓取外部页面，没有访问 GitHub。

`Copyright (c) 2026 ZZmkk88` 是本仓多出来的版权行，UPSTREAM 没有把 ZZmkk88 列成上游项目。这是作者署名，不是缺字段。

仓库内没有写死的真实 API key。app.py:236 只从环境变量 `NOTEPRESS_LLM_API_KEY` 读取。测试里有占位字符串 `sk-test-not-real`：tests/test_app.py:173、tests/test_app.py:194、tests/test_app.py:208。这三处同时 `monkeypatch` 掉了 `llm_chat`，字符串不会发到网络。它仍然是写在仓库里的假 key，和「源码与测试里不得出现假 key」不一致。测试文件禁止修改，所以不改。默认口令 `admin123` 写在 app.py:145，README.md:24 有说明，是登录口令，不是模型密钥。

## 专项验收证据

1. 无密钥跑通：审计脚本打印 `KEY_SET False`。pytest 32 passed，含演示模式不调用 `httpx.post`。live_selftest 16 个检查点全过，覆盖选题扩写、写稿、草稿、成卡、导出。真实密钥路径本次没有调用（没有密钥，也没有访问外网），不把它写成已验证。
2. 体积：仓库 14 个文件（不含 `.git`）合计 108754 字节。最大是 app.py 41006 字节。无单文件超过 2MB。无 ttf/otf/woff/woff2。出处：`audit_env.py` 输出。字体说明在 README.md:86-99：微软雅黑、苹方、华文黑体、Noto Sans CJK、文泉驿正黑；都找不到时用 `ImageFont.load_default()`（app.py:425，README.md:99）。本机实际加载微软雅黑。`tests/test_acceptance.py:216` 缺字体仍输出 1080×1440，该测试已通过。
3. 确定性样例：tests/test_acceptance.py:17-19 固定标题「用AI写周报教程」、正文「第一段内容。\n\n第二段内容，讲讲步骤。」、标签 `AI工具`/`周报`。tests/test_acceptance.py:122 起断言文件存在、大小在 500 到 2000000 字节之间、尺寸 1080×1440、外缘墨点为 0，有字体时标题区墨点大于 80。该测试已通过。探针两次渲染字节相同，标题区墨点 29067，说明画的是系统字体里的字，不是空卡。
4. 规格：见上一节「一致」列表。实现与 README 的字数、标签数、封面比例一致。
5. 溯源：见上一节。四字段齐全。commit 未核实。

## 分级修复清单

### P0

无。安装、32 项测试、16 个检查点、首页和健康检查都已跑通。

### P1

无。未发现未授权访问、密钥泄漏、越权改数据或默认配置下的权限绕过。登录接口都要 Bearer（app.py:184）。卡片下载先查草稿（app.py:959-966）。封面保存名是 `{草稿id}.png/jpg`（app.py:986），不使用上传文件名。默认只听 `127.0.0.1`（app.py:1075）。演示模式不读密钥、不调用 `httpx.post`。

默认口令 `admin/admin123` 且不强制改密是 README.md:24 和 DECISIONS.md:3（D-1）的既定行为，不作为缺陷修。

### P2

1. static/index.html:295、static/index.html:337、static/index.html:385 与 README.md:12 用词不一致。修法：这三处「示例模式」改成「演示模式」。
2. static/index.html:111 `maxlength="120"`，app.py:34 与 app.py:768 上限是 100。修法：输入框 `maxlength` 改为 100。
3. app.py:914-915 对 JSON `null` 做 `str()`，`published_url` 会存成字面量 `None`（探针已复现）。`published_at` 同样。app.py:895-896 在键存在且值为 `null` 时，标题和正文也会变成 `"None"`。修法：值为 `null` 时标题/正文/链接按空字符串处理，缺键时仍保留原值。
4. app.py:408-425 粗体文件不存在时直接 `load_default()`，不会改用已经找到的常规字体。本机 `msyhbd.ttc` 存在，当前渲染正常。修法：粗体缺失时回退到同一次查找里的常规字体文件。
5. app.py:521 用 `MEDIA_DIR / "covers" / draft["cover_file"]` 拼路径。删除路径 app.py:490 已取 basename。修法：渲染前对 `cover_file` 取 `Path.name`，拒绝空名和 `..`。
6. app.py:268 演示扩题只用方向词前 12 字，app.py:792 允许 50 字。修法：演示模板使用与接口相同的上限，或在 README 写明演示模式只取前 12 字。
7. app.py:376-377 模型返回的标签只截断个数，不检查 20 字。保存时 app.py:845 才拒绝。修法：生成结果里超长标签按 502 拒绝或在返回前丢掉并在响应里说明。
8. tests/test_app.py:173、194、208 写了 `sk-test-not-real`。修法：不改。测试文件禁止修改，改应用逻辑会让这三项打桩测试失去「已配置密钥」分支。
9. NOTES.md:22、NOTES.md:34 与依赖列表、字体查找顺序不一致。修法：改成五个运行时包，字体顺序与 README.md:90-95 相同。
10. README.md:55 测试段未写先装 requirements.txt。修法：在该段加一句先安装 requirements.txt。
11. 测试收集时的 `StarletteDeprecationWarning`（fastapi/testclient.py 提示安装 httpx2）。修法：不改。requirements 版本号在测试全绿时不动。

本次只允许修 P0 和 P1，最多 5 项。上面没有 P0/P1，所以不改仓库源码。
