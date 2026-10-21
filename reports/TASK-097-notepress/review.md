# TASK-097 notepress 审查

结论：在无 API key、不访问大模型的条件下，演示模式从选题到导出能跑通。pytest 32 项通过，live_selftest 16 个检查点通过，`127.0.0.1:8000` 的首页和 `/health` 正常，服务已停。规格（标题 20、正文 1000、标签最多 10 个且每个 20 字、封面 1080×1440）与 README 一致。要修的运行阻断项没有。有 1 项可修的 P1（上传封面在极端宽高比下会按比例放大整图）和 1 项修不动的 P1（测试里的假 key，禁止改测试）。

## 本地跑通记录

环境：本机 Python 3.11.9。虚拟环境在 `E:\muse-bridge\work\TASK-097-notepress\venv`，没有写进仓库。依赖按 README 的钉死版本装上：fastapi 0.156.8、uvicorn 0.54.0、python-multipart 0.0.32、httpx 0.28.1、pillow 13.0.0、pytest 9.1.1。全程未设置 `NOTEPRESS_LLM_API_KEY`。

命令与结果（完整命令在 `run.md`）：

- `python -m pytest tests -q -p no:cacheprovider --tb=short`  
  `32 passed, 1 warning in 14.45s`  
  警告原文：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 测试没有失败。
- `python tests\live_selftest.py 8155`  
  `ALL PASS · 16 个检查点`（health、登录、演示扩题、演示写稿、草稿、违禁词「第一」、成卡 PNG、zip 里 `01.png` 与 `文案.txt`、回填链接）。
- 起 `python app.py`，日志：`Uvicorn running on http://127.0.0.1:8000`。  
  `GET /health` → `200 {"status":"ok","app_id":"notepress"}`。  
  `GET /` → `200 text/html`，26530 字节，正文含 `notepress` 和 `笔记工坊`。  
  无密钥流程：`/api/me` 的 `llm_configured` 为 false；扩题 `demo true`、6 条；写稿标题「用AI写周报，这样做超简单」（13 字）、正文 281 字；成卡 `(1080, 1440)`；导出 zip 含 `01.png` `02.png` `03.png` `文案.txt`。未登录 `GET /api/drafts` → 401。  
  进程 terminate 后退出码 1（Windows）。随后连接 `127.0.0.1:8000` 和 `8155` 均在 2 秒内无人接受（`TimeoutError`）。

无密钥证据：pytest 夹具删除了 `NOTEPRESS_LLM_API_KEY`；`tests/test_acceptance.py:98` 把 `httpx.post` 换成会抛错的桩，该项包含在 32 passed 里。live 与 8000 实测的扩题/写稿都返回 `demo: true`。源码读密钥只在 `app.py:236` 和 `app.py:242`，两处都是 `os.environ.get("NOTEPRESS_LLM_API_KEY", ...)`。

仓库体积：最大文件 `app.py` 41750 字节。扩展名里没有 ttf/otf/woff/woff2。本机字体探针：`C:/Windows/Fonts/msyh.ttc`（19704352 字节）和 `msyhbd.ttc`（16883552 字节）存在，渲染实际用到它们（探针打印 `FONT C:/Windows/Fonts/msyh.ttc C:/Windows/Fonts/msyhbd.ttc`）。

确定性样例：`tests/test_acceptance.py:18` 固定标题「用AI写周报教程」、正文「第一段内容。…」、标签 `AI工具`/`周报`；`test_render_fixed_sample_size_and_no_overflow`（同文件 122 行）断言 PNG 存在、大小在 500 到 2000000 字节之间、尺寸 `(1080, 1440)`、外缘无溢出墨点，有字体时标题区墨点 > 80。该用例在 32 passed 中。另用标题 20 个「国」、正文 1000 个「国」、4 个 20 字标签渲染 5 张卡：内容卡外缘 8 像素非背景点数为 0，墨点 bbox 的 x 在 84..996。封面卡外缘有墨点，来自 `app.py:554` 的通栏色条和 `app.py:555` 的装饰圆，不是文字画出卡片。

会话时长：探针读到 `created_at=2026-10-22T01:36:45`、`expires_at=2026-10-23T01:36:45`，与 `app.py:37` 的 24 小时一致。

## README 与实际不符处

核对后一致、不单列缺陷的：标题 20 / 正文 1000（`README.md:11`，`app.py:32-33`，`app.py:694-698`）；标签最多 10 个、每个 20 字（`README.md:14`，`app.py:35-36`，`app.py:854-858`）；封面只做 3:4 的 1080×1440、不做 9:16（`README.md:13-14`，`app.py:38`）；三套语气和三套模板；字体回退顺序 `README.md:94-100` 与 `app.py:397-405` 一致，找不到字体时 `app.py:434` 使用 `ImageFont.load_default()`；默认账号、只提示改密、监听 `127.0.0.1:8000`；测试数量 25+7=32，live 16 个检查点（`README.md:70-71`），与本次运行一致。10 个种子选题 × 3 种语气的演示稿标题都不超过 20、正文最长 295。

不符：

1. `README.md:82` 至 `README.md:84` 把 `NOTEPRESS_DB`、`NOTEPRESS_MEDIA`、`NOTEPRESS_BANNED_WORDS` 的默认值写成 `./notepress.db`、`./media`、`./data/banned_words.json`。`app.py:25-29` 的默认值是 `Path(__file__).resolve().parent` 下的同名路径，不看进程的当前目录。在仓库根目录按快速开始启动时两者重合；换目录执行 `python 某路径\app.py` 时，库文件落在 `app.py` 旁边。
2. `README.md:9` 只说可以记选题、按方向词扩题，没有字数上限。`app.py:34` 的 `TOPIC_LIMIT = 100`，`app.py:777-778` 超过即 400。实测「题」×101 返回 `选题超过上限 100 字（当前 101 字）`，「题」×100 返回 200。方向词上限在 `app.py:801-802`，实测 51 字返回 `方向词超过上限 50 字（当前 51 字）`。同一事项上，`static/index.html:111` 的选题输入框 `maxlength="120"`，101 到 120 字能提交，再被后端拒绝。
3. `README.md:26` 把演示模式限定为「不设置 `NOTEPRESS_LLM_API_KEY`」。`app.py:346-347` 在已经配置密钥但扩题调用抛错时，也会返回演示候选且 `demo: true`。写稿路径不是这样：`app.py:365` 起的异常会变成 502 或继续向外抛。无密钥时的主路径与 README 一致，本条是失败回退超出文档。
4. `README.md:48` 只写打开 `http://127.0.0.1:8000`。`app.py:666-668` 另有 `GET /health`。这是文档没写，不是行为相反。实测该接口返回 200。

## 许可证与署名核查

`UPSTREAM.md:8-11` 与 `UPSTREAM.md:15-18` 两个参考都有 `source_url`、`source_commit`、`license`、`attribution` 四字段。`LICENSE:3` 的 `Copyright 2025 xpzouying` 与参考一 attribution 相同；`LICENSE:4` 的 `Copyright (c) 2023 dreammis` 与参考二相同；`LICENSE:5` 另有本仓 `Copyright (c) 2026 ZZmkk88`。`README.md:4`、`UPSTREAM.md:3`、`NOTES.md:3` 都写代码是独立实现/独立重写。仓库里没有 Go 源码，也没有自动发布脚本，和「不复制上游实现、只参考字段模型」的说法相符。

未联网核对两个 `source_commit` 是否真实存在（本任务禁止抓取外部页面），因此不断言这两个提交号有效或无效。

参考一的 license 字段是 Apache-2.0，本仓 `LICENSE` 正文是 MIT。独立重写时，MIT 正文覆盖的是本仓代码；上游版权行按专项要求留在 `LICENSE` 抬头。没有看到需要改写的事实错误，本次不改 `LICENSE` 和 `UPSTREAM.md`。

默认口令 `admin` / `admin123`（`README.md:24`，`app.py:145`）是公开的单用户登录口令，不是大模型密钥。`DECISIONS.md:3-4` 规定首次改密只提示、不强制，本次不加强制改密。

假 key 不在 `app.py`。`tests/test_app.py:173`、`tests/test_app.py:194`、`tests/test_app.py:208` 有字面量 `sk-test-not-real`，只用来让 `llm_configured()` 为真，同时 `llm_chat` 被桩替换，不会出网。`DECISIONS.md:35-36` 把这件事写成永久关闭，理由是不许改测试。这仍然违反本次专项「测试里不得出现假 key」。

## 分级修复清单

### P0

无。上面三条运行记录都是通过，没有阻断启动或全量失败的测试。

### P1

1. `app.py:533-537` 上传封面时用 `scale = max(卡片/源图)` 把整图放大再裁剪。2000×10 的源图按该公式得到中间图 288001×1441，约 4.15 亿像素（只计算，未分配）。修法：改成 `ImageOps.fit`，在源图上裁出 3:4 再直接缩放到 1080×1440。
2. `tests/test_app.py:173`、`tests/test_app.py:194`、`tests/test_app.py:208` 写死假 key `sk-test-not-real`。修法：删掉该字面量，用 monkeypatch 把 `llm_configured` 设为真。本次不改测试文件，所以这条修不动。

### P2

1. `README.md:82-84` 与 `app.py:25-29` 的默认路径一个相对 cwd、一个相对 `app.py` 所在目录。修法：把 README 表格改成「默认放在 app.py 同目录」。
2. `app.py:777-778`、`app.py:801-802` 有选题 100 字、方向词 50 字上限，`README.md:9` 没写；`static/index.html:111` 仍允许 120 字。修法：README 补上两处上限，输入框 `maxlength` 改成 100，方向词输入补 50。
3. `app.py:346-347` 扩题失败时静默退回演示稿。修法：与写稿一样返回 502，不要把失败伪装成 `demo: true`。
4. `app.py:386` 对模型返回的标签 `tags[:MAX_TAGS]` 静默丢掉第 11 个以后的；用户提交路径在 `app.py:857-858` 是 400。修法：条数超过 10 时与单条超长一样返回 502。
5. `DECISIONS.md:36-37` 已记录的 httpx2 弃用警告。修法：不改。测试是绿的，不是依赖冲突，本次也不许改已钉死的版本号。
6. `README.md:48` 没写 `app.py:666-668` 的 `/health`。修法：快速开始补一句健康检查路径。

## 专项验收

1. 无密钥全流程：见「本地跑通记录」。源码与演示路径不访问外网；假 key 只出现在测试，见 P1-2。
2. 体积与字体：最大文件 41750 字节；仓库无字体文件；README 字体名和降级与 `app.py:397-434` 一致；本机走微软雅黑。
3. 渲染可复现：`tests/test_acceptance.py:122` 在 32 passed 里，断言文件、尺寸和文字不进外缘。
4. 规格：标题、正文、标签、3:4 封面与 README 一致，证据见上一节开头。不符的是选题/方向词上限和默认路径，不改变这四项平台规格。
5. 溯源：四字段和版权行都在；commit 未联网核实；不改 LICENSE。

P1-1 已按清单改在 `app.py`，验证写在 `fix-report.md`。上面的行号是改前行号。
