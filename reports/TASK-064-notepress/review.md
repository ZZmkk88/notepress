# notepress 验收审查

结论：无 API key、HTTP(S) 代理指向 `127.0.0.1:9` 时，自动化测试 25 项通过（11.10s），真实流程自测 16 项通过，`127.0.0.1:8000` 的 `/health` 与首页均为 200，服务已关。没有 P0。确认 3 个 P1，下面按清单直接修。字体文档、长选题演示稿超限、测试缺溢出断言、测试里的假 key、LICENSE 未写上游版权行，列为 P2，本轮不改。

## 本地跑通记录

环境：Python 3.11.9。虚拟环境 `E:\muse-bridge\work\TASK-064-notepress\venv`。依赖按 `requirements.txt` 与 `requirements-dev.txt` 安装成功，版本为 fastapi 0.156.8、uvicorn 0.54.0、python-multipart 0.0.32、httpx 0.28.1、pillow 13.0.0、pytest 9.1.1。

pytest 命令（工作目录为仓库，`--basetemp` 在 work 目录，`NOTEPRESS_LLM_API_KEY` 为空，代理为 `http://127.0.0.1:9`）：

```
E:\muse-bridge\work\TASK-064-notepress\venv\Scripts\python.exe -m pytest tests\test_app.py -q --basetemp=E:\muse-bridge\work\TASK-064-notepress\pytest-tmp
```

输出片段：

```
.........................                                                [100%]
25 passed, 1 warning in 11.10s
```

警告是 `fastapi/testclient.py` 的 `StarletteDeprecationWarning`（建议安装 httpx2）。25 项仍全部通过。

真实流程（`tests\live_selftest.py` 自己起服务，端口 8155，同样无密钥、无效代理）：

```
ALL PASS · 16 个检查点
```

含登录、演示模式扩题与写稿、草稿、违禁词、成卡 PNG、导出 zip、状态回填。脚本结束时关掉子进程。

按 README 用 `python app.py` 再起一次，端口 8000，数据库和媒体目录改到 work 目录，避免写进仓库：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
HEALTH 200 {"status":"ok","app_id":"notepress"}
INDEX 200 len 25259
INDEX_HAS_NOTEPRESS True
INDEX_HAS_TITLE True
```

首页标题为「notepress · 笔记工坊」。主动 terminate 后 uvicorn 退出码 1。`netstat` 只剩 `127.0.0.1:8000` 的 `TIME_WAIT`，没有 LISTENING。仓库里没有 `*.db` 和 `media`。

修复前额外探测（`work\TASK-064-notepress\probe.py`，无密钥）：

- 字体命中 `C:/Windows/Fonts/msyh.ttc` 与 `msyhbd.ttc`，`llm_configured` 为 False。
- 标题 20 字、正文 1000 字、10 个标签渲染 5 张卡，尺寸 `(1080, 1440)`。57 次文字绘制的包围盒为 minx 84、miny 94、maxx 994、maxy 1374，`OVERFLOW_COUNT 0`。标题区域有 108928 个非背景像素，中文被画出来了。
- 改标题后导出：`STALE_PNG_SAME True`，`EXPORT_HAS_NEW_TITLE True`，`EXPORT_HAS_OLD_TITLE False`。
- 删除草稿后目录仍在，`GET /api/drafts/1/cards/1` 返回 200，正文 46516 字节。
- 11 个标签返回 400：`标签超过上限 10 个（当前 11 个）`。

`probe_topic.py`：演示稿在选题 100 字时正文 378 字；选题 800 字时 checklist 正文 1078 字，仍由 `demo_generate` 直接返回，不报错。

## README 与实际不符处

相符、本次有输出佐证的部分：默认账号 `admin` / `admin123`（README.md:23，app.py:145）；令牌 24 小时（README.md:8，app.py:37）；监听 `127.0.0.1:8000`（README.md:43、README.md:67-68，app.py:1020-1022，启动日志）；标题 20 / 正文 1000 / 卡片 1080×1440 即 3:4（README.md:11-13，app.py:32-38）；演示模式无密钥可走完流程（README.md:12，live_selftest 16 项）；自动化 25 项、自测 16 项（README.md:59-61，实测数量一致）；仓库不打包字体（README.md:81，目录枚举无字体文件）。

不符：

1. 字体查找顺序与 README 不一致。README.md:79-81 写的顺序是环境变量 → Windows 微软雅黑 → macOS 苹方 → Linux Noto Sans CJK / 文泉驿。app.py:388-409 的 `_FONT_CANDIDATES` 顺序是 Noto CJK、文泉驿、微软雅黑（`msyh.ttc` / `msyhbd.ttc`）、苹方、华文黑体 `STHeiti Medium.ttc`。README 没有写 STHeiti。本机只有微软雅黑存在，所以实际用到的仍是微软雅黑。
2. 缺字体时的降级没写全。README.md:80-81 只写了 Linux 安装 `fonts-noto-cjk`。app.py:418-425 在所有候选都不存在时使用 `ImageFont.load_default()`。README 没有写 Windows 缺少微软雅黑、macOS 缺少苹方时的下一步，也没有写最终会落到 Pillow 默认位图字体（中文基本画不出来）。专项要求的「各平台缺失时的降级方案」因此不完整。Linux 上 `fonts-noto-cjk` 是否正好落在 app.py:389 的路径，本机不是 Linux，未核实。
3. 「超限明确报错不截断」没有盖住全部写稿路径。README.md:11。草稿创建与更新在 app.py:650-654 返回 400，并带上限和当前字数。AI 正文超限在 app.py:374-375 返回 502。AI 标题在 app.py:368 被静默丢掉，只有全部超过 20 字才在 app.py:369-370 返回 502。演示模式在 app.py:350-352 直接返回 `demo_generate`，不检查正文长度。`probe_topic.py`：选题 800 个「题」时，checklist 正文 1078 字，函数仍正常返回。
4. README 禁止把密钥写进提交的文件。README.md:72。`tests/test_app.py:173`、`tests/test_app.py:194`、`tests/test_app.py:208` 写死 `NOTEPRESS_LLM_API_KEY=sk-test-not-real`。这是假 key。测试把 `llm_chat` 打桩，这次 pytest 在无效代理下仍通过，说明该字符串没有发出去。专项第 1 条仍然不允许它出现在测试里。
5. 话题标签数量 README 没有声明。README.md:10-11 只说「话题标签」。app.py:35-36 规定单标签 20 字、最多 10 个，app.py:813-814 超限返回 400。实测 11 个标签得到「标签超过上限 10 个（当前 11 个）」。专项第 4 条要求标签数量以 README 为准，文档侧没有这个数。
6. 相邻文档 NOTES.md:22 写「依赖只有 FastAPI/uvicorn/httpx/Pillow 四个运行时包」。requirements.txt:1-5 还有 `python-multipart==0.0.32`。README 本身只要求 `pip install -r requirements.txt`，这句与文件一致。

代码内部不一致（README 未写选题字数，故不计入上表，列入 P2）：`static/index.html:111` 选题输入 `maxlength="120"`，app.py:34 与 app.py:733-734 的上限是 100。

## 许可证与署名核查

LICENSE:1-3 为 MIT，版权行只有 `Copyright (c) 2026 ZZmkk88`。全文是常见 MIT 模板，到 LICENSE:21 结束。

UPSTREAM.md 声明代码为独立重写，两条参考都有四字段：

- UPSTREAM.md:8-11 `source_url` https://github.com/xpzouying/xiaohongshu-mcp ，`source_commit` `7797fd375aba02dcd33afe143f6bee13e5870859`，`license` Apache-2.0，`attribution` Copyright 2025 xpzouying
- UPSTREAM.md:15-18 `source_url` https://github.com/dreammis/social-auto-upload ，`source_commit` `28bb5bc20206c26d088311633540127402e4de56`，`license` MIT，`attribution` Copyright (c) 2023 dreammis

README.md:4 与 UPSTREAM.md:3 的「设计参考、代码独立实现」说法一致。在 `app.py`、`static/index.html`、`tests/` 中检索，没有 xpzouying、dreammis、selenium、playwright 或自动发布实现。`tests/live_selftest.py:109` 只有一条示例笔记链接。源码形态与「独立实现」相符。

两处缺口：

- LICENSE 没有保留上游版权行。专项要求只要参考了开源项目，LICENSE 就保留上游版权行。当前文件没有 `xpzouying` 与 `dreammis`。
- `source_commit` 本次禁止访问外网，未对照 GitHub 复核，记为未核实。

不改 LICENSE / UPSTREAM。仓库里看不到被复制的上游源码；在未核实提交号的情况下把上游版权写进 LICENSE，会把「参考了思路」写成「软件包含上游代码」。

## 专项验收证据

1. 无密钥跑通：pytest 与 live_selftest 均在未设置 `NOTEPRESS_LLM_API_KEY`、代理指向 `127.0.0.1:9` 时通过。密钥只从环境变量读取（app.py:236，app.py:242）。源码没有写死真实 key。测试里有假 key `sk-test-not-real`（见不符第 4 条）。真实大模型接口本次没有调用。
2. 体积与字体：最大源文件 `app.py` 38913 字节。无 ttf/otf/woff/woff2，无渲染缓存。成卡使用系统字体，本机为微软雅黑。README 写了字体名，但顺序和缺字体降级不完整（不符第 1、2 条）。
3. 渲染可复现：测试 `tests/test_app.py:290-301` 断言张数和尺寸 `(1080, 1440)`，不断言文字是否溢出，也没有固定输入对固定输出的期望文件。探测样例（标题 20 字、正文 1000 字）包围盒在画布内，这是审查时加跑的脚本，不是仓库测试。专项第 3 条的测试断言未满足。
4. 规格：README 声明的 20 字、1000 字、3:4（1080×1440）与常量一致，草稿保存路径有硬校验。演示模式长选题可返回超过 1000 字的正文；AI 超长标题会被悄悄丢掉；标签上限 README 未写。见不符第 3、5 条。
5. 溯源：UPSTREAM 四字段在文件里齐全；提交号未核实；LICENSE 未保留上游版权行。见上一节。

## 分级修复清单

行号是修复前的位置。修完后的行号写在 fix-report.md。

### P0

无。安装、25 项测试、16 项真实流程、8000 端口首页和健康检查都已跑通。

### P1

1. 编辑后导出的图片仍是旧卡，文案已是新内容。文件：`app.py:992-994`（已有卡片就不再渲染），`app.py:852-878`（更新标题、正文、标签、模板不删旧图），`app.py:935-938`（更换封面不删旧图）。修法：导出前按当前草稿重新渲染；标题、正文、标签、模板或封面变化时删除该草稿的 `card_*.png`。
2. 删除草稿后卡片仍可下载。文件：`app.py:881-885`（只删数据库行），`app.py:909-914`（只判断文件在不在）。证据：删除后 `GET /api/drafts/1/cards/1` 仍 200，46516 字节。修法：删除时去掉卡片文件和封面文件；下载接口先确认草稿还在，不在则 404。
3. 封面上传先把整个文件读进内存，再判断是否超过 10MB。文件：`app.py:920-922`。`UploadFile.read()` 在不带长度时读完全部（依赖 starlette `datastructures.py:476-479`）；multipart 的文件部件不受 1MB 字段上限约束（`formparsers.py:185-192`）。修法：先看 `file.size`，超过 10MB 直接 400；读取时最多读 10MB+1 字节，超出即拒绝。

### P2

1. 字体顺序和缺字体降级与 README 不一致。文件：README.md:79-81，app.py:388-425。修法：让 `_FONT_CANDIDATES` 顺序与 README 一致，或改 README 为实际顺序，并写明各系统缺字体以及最终位图字体的降级。本轮不改。
2. 演示模式在选题很长时返回超过 1000 字的正文。文件：app.py:350-352，app.py:280-329。选题 800 字时 checklist 正文 1078 字。修法：返回前若正文超过 1000 字则 400，错误里写上限和当前字数。保存草稿的路径已经会拒绝，故不升为 P1。
3. AI 超长标题被静默过滤。文件：app.py:368-370。修法：任一标题超过 20 字就按 README 返回错误，保留已返回的原文长度，不丢弃。
4. 测试没有断言文字不溢出，也没有确定性期望输出。文件：`tests/test_app.py:290-301`。修法：对固定标题和正文断言产物存在、尺寸为 1080×1440、文字包围盒在画布内。禁止改测试，修不动。
5. 测试提交了假 key。文件：`tests/test_app.py:173`、`:194`、`:208`。修法：去掉字面量，改由打桩函数直接走已配置分支，同时不把密钥字符串写入仓库。禁止改测试，修不动。
6. LICENSE 未保留上游版权行。文件：LICENSE:3，对照 UPSTREAM.md:11 与 UPSTREAM.md:18。修法需先核实确实复制了上游代码再补版权行。本次未见复制，且禁止在未核实情况下改 LICENSE 的事实声明，不改。
7. 选题字数前后端不一致。文件：`static/index.html:111` 为 120，app.py:34 为 100。修法：输入框 `maxlength` 改为 100。
8. README 未声明标签上限。文件：README.md:10-11，对照 app.py:35-36。修法：在 README 写明最多 10 个、每个 20 字。
9. NOTES 把运行时依赖写成四个包。文件：NOTES.md:22，对照 requirements.txt:3。修法：补上 python-multipart。
10. UPSTREAM 的 `source_commit` 未在本环境对照上游复核。文件：UPSTREAM.md:9、UPSTREAM.md:16。修法：在能访问 GitHub 时核对这两枚提交是否仍是对应许可证文本的 HEAD。本次禁止抓取外网，未改。

已定决策，不作为缺陷：DECISIONS.md:3-4 规定默认密码只提示改密、不强制。代码与此一致，不改回强制改密。
