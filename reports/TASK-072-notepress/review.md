# notepress 验收

结论：无 API key、不访问外网时，演示模式可以从选题走到导出。pytest 32 项通过，真实服务自测 16 项通过，`127.0.0.1:8000` 的 `/health` 与首页正常，进程已退出。没有 P0，没有 P1。本次不改仓库源码。

仓库最大文件 `app.py` 41006 字节（`Get-ChildItem`），低于 2MB。目录枚举没有 ttf/otf/woff/woff2，也没有渲染缓存。本机成卡用到 `C:/Windows/Fonts/msyh.ttc` 与 `msyhbd.ttc`。

## 本地跑通记录

解释器 `Python 3.11.9`。虚拟环境在 `E:\muse-bridge\work\TASK-072-notepress\venv`，没有装进仓库。依赖按 `requirements.txt`、`requirements-dev.txt` 安装，退出码都是 0。装上的版本包括 `fastapi-0.156.8`、`uvicorn-0.54.0`、`python-multipart-0.0.32`、`httpx-0.28.1`、`pillow-13.0.0`、`pytest-9.1.1`，传递依赖有 `starlette-1.9.0`。

pytest（仓库根目录，`NOTEPRESS_LLM_API_KEY` 置空）：

```
python -B -m pytest tests -q -p no:cacheprovider
................................                                         [100%]
32 passed, 1 warning in 15.00s
```

警告原文来自已安装的 `fastapi\testclient.py:1`：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 不是本仓库代码。

真实流程（`python -B tests\live_selftest.py`，默认端口 8155，无密钥）：16 行均为 `PASS`，末行 `ALL PASS · 16 个检查点`，退出码 0。覆盖登录、演示扩题、演示写稿、草稿、违禁词、成卡、导出、回填链接。

首页与健康检查（`PORT=8000`，`NOTEPRESS_HOST=127.0.0.1`，数据库和媒体目录在工作目录）：

```
HEALTH 200 {"status":"ok","app_id":"notepress"}
HOME 200 len 25259
HOME_HAS_TITLE True
HOME_HAS_APP True
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

首页文本含「笔记工坊」和 `notepress`。响应头有 `nosniff` 与 `X-Frame-Options: DENY`。脚本 `terminate()` 之后，8000 和 8155 的连接结果都是 `PORT_CLOSED TimeoutError`。

命令全文和探针原文在 `run.md`。

## README 与实际不符处

下列每条都对过当前文件。与 README 一致且已被上面的命令证实的部分不重复开条：32 项测试、16 个检查点、默认账号 `admin`/`admin123`（README.md:24，app.py:145）、令牌 24 小时（README.md:8，app.py:37）、`127.0.0.1:8000`（README.md:28、README.md:48，app.py:1075-1077）、标题 20 / 正文 1000 / 标签 10 个且每个 20 字 / 封面 1080×1440（README.md:11-15，app.py:32-38，app.py:35-36，app.py:685-689，app.py:839-849）、字体查找顺序（README.md:90-95，app.py:388-409）、只提示改密（README.md:24，DECISIONS.md:3-4，app.py 不拦截业务接口）。

1. 界面写「示例模式」，README 写「演示模式」。README.md:12、README.md:26；static/index.html:295（「示例模式：未配置 AI 接口…」）、static/index.html:337、static/index.html:385（「这是示例稿…」）。接口字段仍是 `demo`（app.py:329）。修法：这三处界面文案改成「演示模式」。

2. 演示写稿在超长自由选题下不按 1000 字报错。README.md:11 要求标题 20 字、正文 1000 字硬校验，超限报错不截断。保存和更新走 app.py:685-689，会 400。已配置密钥时，正文超限在 app.py:374-375 返回 502。未配置密钥时 `ai_generate`（app.py:350-352）直接返回 `demo_generate`（app.py:280-329），不再量正文长度。正文模板拼进完整选题，标题却用截到 10 字的 `_short_topic`（app.py:262-264）。探针：`POST /api/generate`，选题 800 个「题」，返回 200，`body_len 1078`，`demo true`；再保存得到 `400 正文超过上限 1000 字（当前 1078 字）`。选题库上限 100 字时，checklist 正文 378 字，标题候选 17/15/16 字，不越界。写稿页自由输入框没有 maxlength（static/index.html:137）。修法：返回演示稿前若正文超过 1000 字则 400，原文不截断。

3. README 要求密钥不要写进提交文件，测试里有假 key。README.md:26、README.md:81；tests/test_app.py:173、test_app.py:194、test_app.py:208 为 `monkeypatch.setenv("NOTEPRESS_LLM_API_KEY", "sk-test-not-real")`。这三处都把 `llm_chat` 换成了本地桩。`app.py` 只从环境变量读密钥（app.py:235-236，app.py:242），没有写死的 key。修法：测试里不要放 `sk-` 形态的假密钥。禁止改测试，不能动。

4. 模型返回的标题只有一部分超限时会被丢掉，不会整单报错。README.md:11 与 DECISIONS.md:17-18（D-8：AI 结果超限则拒绝并提示重试）。app.py:368-370 先滤掉超过 20 字的标题，一条不剩才 502。现有测试 `test_generate_llm_overlong_title_rejected`（test_app.py:193）只覆盖「全部超限」。探针把一条超长标题和一条「短标题」交给打过桩的 `llm_chat`，返回 200，`titles` 只剩「短标题」。同一次响应里的标签是「标签」重复 15 次（30 字），app.py:376-377 只按个数截到 10 个，不查每个标签的 20 字上限。修法：只要有一条标题或一个标签超过上限就 502，不静默丢弃、不原样返回超长标签。

5. 测试一节只写安装 `requirements-dev.txt`。README.md:55-57。该文件只有 `pytest==9.1.1`（requirements-dev.txt:1），没有 `-r requirements.txt`。测试要导入 FastAPI（test_app.py:15）。本次是先装了 `requirements.txt` 再跑，所以通过。只按测试一节在空环境里装，收集会缺运行时包。修法：`requirements-dev.txt` 增加 `-r requirements.txt`，或在 README 测试步骤写明先装运行时依赖。不改已有版本号。

6. NOTES 把运行时依赖写成四个包。NOTES.md:22 写 FastAPI、uvicorn、httpx、Pillow。requirements.txt:3 还有 `python-multipart==0.0.32`，封面上传依赖它。修法：NOTES 改为五个运行时包。

7. NOTES 的字体顺序和 README、代码不一致。NOTES.md:34 写成「Windows 微软雅黑 → macOS 苹方 → Linux Noto」。README.md:90-95 与 app.py:388-395 的顺序是 Noto Sans CJK、文泉驿正黑、微软雅黑、苹方、华文黑体，前面还有 `NOTEPRESS_FONT_PATH`（app.py:404-409）。本机 Linux 路径不存在，实际用到微软雅黑，和 README 的回退说明一致。修法：把 NOTES.md:34 改成与 `_FONT_CANDIDATES` 相同的顺序。

8. 选题输入框允许 120 字，接口上限是 100。static/index.html:111 `maxlength="120"`；app.py:34 `TOPIC_LIMIT = 100`；app.py:768-769 超过 100 返回 400。探针：100 字成功、101 字返回 400。README 没有写选题字数，这条是前后端不一致。修法：输入框 maxlength 改为 100。

9. 界面准备了「AI 扩题」来源标签，接口从不写入该来源。static/index.html:319 在 `source === "ai"` 时显示「· AI 扩题」。创建选题的 SQL 把 source 写成 `'manual'`（app.py:772），种子是 `'seed'`（app.py:151）。修法：扩题入库时写入 `ai`，或删掉这条不会出现的分支。

## 许可证与署名核查

LICENSE 是 MIT（LICENSE:1）。版权行三条：`Copyright 2025 xpzouying`（LICENSE:3）、`Copyright (c) 2023 dreammis`（LICENSE:4）、`Copyright (c) 2026 ZZmkk88`（LICENSE:5）。

UPSTREAM.md 写明代码为独立重写，两条参考的四字段都在：

| 参考 | source_url | source_commit | license | attribution |
|---|---|---|---|---|
| 小红书发布工具 | UPSTREAM.md:8 `https://github.com/xpzouying/xiaohongshu-mcp` | UPSTREAM.md:9 `7797fd375aba02dcd33afe143f6bee13e5870859` | UPSTREAM.md:10 Apache-2.0 | UPSTREAM.md:11 `Copyright 2025 xpzouying` |
| 多平台发布工具 | UPSTREAM.md:15 `https://github.com/dreammis/social-auto-upload` | UPSTREAM.md:16 `28bb5bc20206c26d088311633540127402e4de56` | UPSTREAM.md:17 MIT | UPSTREAM.md:18 `Copyright (c) 2023 dreammis` |

attribution 与 LICENSE 里对应的两行一致。README.md:4 与 UPSTREAM.md:3 都声明独立实现。`Get-ChildItem -Recurse -File` 只看到本仓的 `app.py`、`static/index.html`、测试、违禁词表和说明文件，没有上游源码树。`ZZmkk88` 只出现在 LICENSE，UPSTREAM 只记录上游，二者不冲突。

参考一是 Apache-2.0，本仓库 LICENSE 正文仍是 MIT，只保留了版权行，没有 Apache 许可证全文。在「独立重写、未见复制代码」的前提下，这样符合本任务「参考了开源项目则 LICENSE 保留上游版权行」的要求。若实际上复制了 Apache 代码，许可证就不完整。本次看不到复制，不据此改 LICENSE。

`source_commit` 两枚哈希未核实：任务禁止抓取外部页面，没有对照 GitHub。不改 LICENSE，不改 UPSTREAM。

## 分级修复清单

### P0

无。安装、32 项测试、16 项真实流程、8000 端口首页和健康检查都已跑通。

### P1

无。登录后业务接口要带令牌（未登录时 `/api/drafts` 与卡片下载均为 401）。卡片不挂静态目录（app.py:957-966）。默认只监听 `127.0.0.1`（app.py:1075）。密钥不进源码。封面不用客户端原始文件名（app.py:985-986）。SQL 使用参数绑定。删除草稿会删卡片目录和封面（app.py:923-933）；探针在删除后 `GET` 卡片为 404，目录不存在。编辑标题会删旧卡，导出重新渲染，文案里是新标题、没有旧标题。只改状态时卡片字节不变。约 1.9MB 的 PNG 封面返回 200；超过 10MB 返回 400。默认口令 `admin123` 和「只提示改密」是 README.md:24 与 DECISIONS.md:3-5（D-1）的既定行为，不作为缺陷修改。

### P2

1. static/index.html:295、static/index.html:337、static/index.html:385：界面「示例模式」改为「演示模式」。
2. app.py:329 与 app.py:350-352：演示写稿返回前检查正文长度，超过 1000 字则 400，不截断。
3. tests/test_app.py:173、test_app.py:194、test_app.py:208：去掉假密钥字符串。禁止改测试，不修。
4. app.py:368 与 app.py:376-377：模型给出的标题或标签只要超限就 502，不再滤掉标题或放行超长标签。
5. NOTES.md:22：运行时依赖改为五个，补上 python-multipart。
6. NOTES.md:34：字体顺序改成与 app.py:388-395 相同。
7. static/index.html:111：选题 maxlength 从 120 改为 100，与 app.py:34 一致。
8. app.py:772 或 static/index.html:319：扩题入库写入 `ai`，或删除不会命中的「AI 扩题」标签。
9. README.md:55 与 requirements-dev.txt:1：测试依赖写上运行时包。不改已有版本号。
10. app.py:866-871：`topic_id` 在选题表里不存在时返回 400。探针得到 `IntegrityError FOREIGN KEY constraint failed`（TestClient 默认把服务端异常抛出）。事务在 `get_db` 里回滚，没有半截草稿。

已定决策，不作为缺陷：DECISIONS.md:3-5 规定默认密码只提示改密、不强制。代码与此一致。

## 专项验收

1. 无密钥跑通：pytest 与 live_selftest 均在未设置 `NOTEPRESS_LLM_API_KEY` 时通过。`test_demo_mode_does_not_call_httpx_post`（test_acceptance.py:98）断言演示模式不调用 `httpx.post`。密钥只从环境变量读取（app.py:236，app.py:242）。源码没有写死真实 key。测试里有假 key `sk-test-not-real`，见不符处第 3 条。真实大模型接口本次没有调用。`admin123` 是 README 写明的本地默认口令，不是 API key。

2. 体积与字体：最大文件 `app.py` 41006 字节。无字体文件，无提交的渲染缓存。README.md:86-99 写明微软雅黑、苹方、华文黑体、Noto Sans CJK、文泉驿，以及都找不到时用 `ImageFont.load_default()`。代码回退在 app.py:388-425。本机实测命中 `msyh.ttc` / `msyhbd.ttc`。缺字体用例 `test_missing_font_still_renders`（test_acceptance.py:216）已通过，仍输出 1080×1440。

3. 渲染可复现：固定输入在 test_acceptance.py:17-19，断言在 test_acceptance.py:122-150（文件存在、500 字节到 2MB、尺寸 1080×1440、3:4、外缘 8 像素无额外墨点）。长标签用例 test_acceptance.py:153 同样检查外缘。另一次满上限探针（标题 20 字、正文 1000 字、4 个 20 字标签）渲染 5 张卡：内容卡外缘非背景像素为 0；封面外缘在 y<30 有 432 像素、30≤y<400 有 28 像素、y≥400 为 0。前两段对应 app.py:545 的通栏色条和 app.py:546 的装饰圆，不是文字。

4. 规格：保存路径标题 20（app.py:32、app.py:686）、正文 1000（app.py:33、app.py:688）、标签最多 10 个且每个 20 字（app.py:35-36、app.py:845-849）。封面 1080×1440（app.py:38），没有 9:16 分支。探针：21 字标签和 11 个标签返回 400；100 字选题的演示正文 378 字。不符点是不符处第 2 条和第 4 条，发生在生成接口，保存接口会拒绝。

5. 溯源：见「许可证与署名核查」。四字段齐全，上游版权行保留，commit 未核实。
