# notepress 验收报告

结论：无 API key、不访问外网的条件下，演示模式全流程可跑通。pytest 32 项通过，真实服务自测 16 项通过，`127.0.0.1:8000` 的 `/health` 与首页返回正常。仓库没有超过 2MB 的文件，也没有字体文件。成卡使用系统微软雅黑，固定样例会检查文件、尺寸和是否溢出。标题 20 字、正文 1000 字、标签 10×20、封面 3:4 在保存和渲染路径上与 README 一致。超长自由选题的演示写稿会返回超过 1000 字的正文，记为 P2。许可证与 UPSTREAM 的署名自洽；上游 commit 未联网核实。没有 P0，没有 P1，本次不改源码。

## 本地跑通记录

环境：Python 3.11.9，虚拟环境 `E:\muse-bridge\work\TASK-066-notepress\venv`。依赖按 `requirements.txt` 与 `requirements-dev.txt` 安装成功（fastapi 0.156.8、uvicorn 0.54.0、python-multipart 0.0.32、httpx 0.28.1、pillow 13.0.0、pytest 9.1.1）。全程未设置 `NOTEPRESS_LLM_API_KEY`。命令全文和输出在 `run.md`。

自动化测试（退出码 0）：

```
python -m pytest tests -q -p no:cacheprovider
32 passed, 1 warning in 11.80s
```

警告原文：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 来自 FastAPI 的 TestClient 导入，不导致失败。`tests/test_app.py` 有 25 个 `test_`（第 52–353 行），`tests/test_acceptance.py` 有 7 个（第 88–216 行），合计 32，与 README.md:66 一致。其中 `test_demo_mode_does_not_call_httpx_post`（test_acceptance.py:98）断言演示模式不调用 `httpx.post`，已通过。

真实流程（退出码 0，端口 8155，脚本结束时自行关掉进程）：

```
python tests\live_selftest.py 8155
ALL PASS · 16 个检查点
```

与 README.md:67 的 16 个检查点一致。路径是选题扩写 → 写稿 → 草稿 → 成卡 → 导出 → 回填链接，响应里 `demo` 为 true。

README 默认端口（随后已关掉）：

```
HEALTH_STATUS 200
HEALTH_BODY {"status":"ok","app_id":"notepress"}
HOME_STATUS 200
HOME_HAS_NOTEPRESS True
HOME_HAS_TITLE True
```

首页标题片段：`notepress · 笔记工坊`。监听 `127.0.0.1:8000`。

无密钥结论：源码只从环境变量读密钥（app.py:236、app.py:242）。上述三次运行的记录都是 `NOTEPRESS_LLM_API_KEY set: False`。演示模板能走完写稿和成卡。带真实密钥调用大模型的路径本次没有执行（无密钥，且不对外抓页面）。

渲染：固定样例在 test_acceptance.py:122 `test_render_fixed_sample_size_and_no_overflow`，输入为标题「用AI写周报教程」、固定正文和标签（test_acceptance.py:17-19）。断言 PNG 文件存在、体积在 500 字节到 2MB 之间、尺寸 1080×1440、`宽*4==高*3`、外缘 8 像素无非背景墨点（test_acceptance.py:74-85）。有系统字体时还断言标题区有墨（test_acceptance.py:148-150）。另一次边界探针：标题 20 字、正文 1000 字、10 个 20 字标签，渲染 5 张，每张 `(1080, 1440)`，`outer_ink 0`。本机字体解析为 `C:/Windows/Fonts/msyh.ttc` 与 `msyhbd.ttc`（系统字体，不在仓库内）。

仓库体积：最大文件 `app.py` 39526 字节。遍历结果里没有 ttf、otf、woff、woff2、ttc。`.gitignore` 已忽略 `*.db`、`media/`、`*.zip`。

## README 与实际不符处

下列每条都对照过当前文件。与 README 一致、且已被上面的命令证实的部分（32 项测试、16 个检查点、3:4 的 1080×1440、三套模板、标签上限、保存时的 20/1000 字校验、字体查找顺序、默认账号和只提示改密）不重复列入。

1. 界面文案写成「示例模式」，README 写「演示模式」。README.md:12、README.md:26；static/index.html:295（「示例模式：未配置 AI 接口…」）、static/index.html:337。接口字段仍是 `demo`（app.py:329）。修法：把这两处界面文案改成「演示模式」。

2. 演示写稿在超长自由选题下不按 1000 字报错。README.md:11 要求标题 20 字、正文 1000 字硬校验，超限报错不截断。保存和更新走 app.py:661-665，会 400。已配置密钥时，正文超限在 app.py:374-375 返回 502。未配置密钥时 `ai_generate`（app.py:350-352）直接返回 `demo_generate`（app.py:280-329），`generate`（app.py:792-797）不再量正文长度。正文模板把完整选题拼进去，标题却用截到 10 字的 `_short_topic`（app.py:262-264）。实测：`POST /api/generate`，选题 800 个「题」，返回 200，`body_len 1078`，`demo true`。种子选题三种语气的正文是 222–298 字，标题候选 11–17 字，这一条不影响预置选题。写稿页自由输入框没有 maxlength（static/index.html:137）。修法：在返回演示稿前若正文超过 1000 字则 400，原文不截断。

3. README 要求密钥不要写进提交文件，测试里有假 key。README.md:26、README.md:81；tests/test_app.py:173、test_app.py:194、test_app.py:208 为 `monkeypatch.setenv("NOTEPRESS_LLM_API_KEY", "sk-test-not-real")`。这三处都把 `llm_chat` 换成了本地桩，字符串不会发到网络。app.py 中没有写死的密钥。修法：测试里不要放 `sk-` 形态的假密钥。本次禁止改测试文件，不能动。

4. 模型返回的标题只有一部分超限时会被丢掉，不会整单报错。README.md:11 与 DECISIONS.md:17-18（D-8：AI 结果超限则拒绝并提示重试）。app.py:368-370 先滤掉超过 20 字的标题，一条不剩才 502。现有测试 `test_generate_llm_overlong_title_rejected`（test_app.py:193）只覆盖「全部超限」。修法：只要有一条标题超过 20 字就返回 502，不静默丢弃。

5. NOTES 把运行时依赖写成四个包。NOTES.md:22 写 FastAPI、uvicorn、httpx、Pillow。requirements.txt:3 还有 `python-multipart==0.0.32`，封面上传依赖它。修法：NOTES 改为五个运行时包，补上 python-multipart。

6. NOTES 的字体查找顺序和 README、代码不一致。NOTES.md:34 写成「Windows 微软雅黑 → macOS 苹方 → Linux Noto」。README.md:90-95 与 app.py:388-395 的顺序是 Noto Sans CJK、文泉驿正黑、微软雅黑、苹方、华文黑体，再前面还有 `NOTEPRESS_FONT_PATH`（app.py:404-409）。本机因 Linux 路径不存在，实际用到微软雅黑，和 README 的回退说明一致。修法：把 NOTES.md:34 改成与 `_FONT_CANDIDATES` 相同的顺序。

7. 选题输入框允许 120 字，接口上限是 100。static/index.html:111 `maxlength="120"`；app.py:34 `TOPIC_LIMIT = 100`；app.py:744-745 超过 100 返回 400。实测 100 字成功、101 字返回「选题超过上限 100 字（当前 101 字）」。README 没有写选题字数。修法：输入框 maxlength 改为 100。

8. 界面准备了「AI 扩题」来源标签，接口从不写入该来源。static/index.html:319 在 `source === "ai"` 时显示「· AI 扩题」。创建选题的 SQL 把 source 写成 `'manual'`（app.py:748），种子是 `'seed'`（app.py:151）。修法：扩题入库时写入 `ai`，或删掉这条不会出现的分支。

## 许可证与署名核查

LICENSE 是 MIT（LICENSE:1）。版权行三条：`Copyright 2025 xpzouying`（LICENSE:3）、`Copyright (c) 2023 dreammis`（LICENSE:4）、`Copyright (c) 2026 ZZmkk88`（LICENSE:5）。

UPSTREAM.md 写明代码为独立重写，并给出两个参考，四字段齐全：

| 参考 | source_url | source_commit | license | attribution |
|---|---|---|---|---|
| 小红书发布工具 | UPSTREAM.md:8 `https://github.com/xpzouying/xiaohongshu-mcp` | UPSTREAM.md:9 `7797fd375aba02dcd33afe143f6bee13e5870859` | UPSTREAM.md:10 Apache-2.0 | UPSTREAM.md:11 `Copyright 2025 xpzouying` |
| 多平台发布工具 | UPSTREAM.md:15 `https://github.com/dreammis/social-auto-upload` | UPSTREAM.md:16 `28bb5bc20206c26d088311633540127402e4de56` | UPSTREAM.md:17 MIT | UPSTREAM.md:18 `Copyright (c) 2023 dreammis` |

attribution 与 LICENSE 里对应的两行一致。README.md:4 与 UPSTREAM.md:3 都声明独立实现。仓库里只有本仓的 `app.py`、`static/index.html`、测试和违禁词表，没有上游源码树。Apache-2.0 的版权行留在 MIT 许可证里，符合本任务「参考了开源项目则 LICENSE 保留上游版权行」的要求；本仓自身条款仍是 MIT。`ZZmkk88` 只出现在 LICENSE，UPSTREAM 只记录上游，二者不冲突。

`source_commit` 两枚哈希本次未核实：任务禁止抓取外部页面，没有对照 GitHub。不据此改 LICENSE 或 UPSTREAM。

## 分级修复清单

### P0

无。安装、32 项测试、16 项真实流程、8000 端口首页和健康检查都已跑通。

### P1

无。登录有会话校验；草稿、成卡、导出、违禁词写接口都要求登录（例如 app.py:731、app.py:776、app.py:902）。卡片不挂静态目录，读取要带令牌（app.py:920-925）。默认只监听 `127.0.0.1`（app.py:1031）。密钥不进源码。封面上传不使用客户端原始文件名（app.py:940-946）。SQL 使用参数绑定。默认口令 `admin123` 和「只提示改密」是 README.md:24 与 DECISIONS.md:3-5（D-1）的既定行为，测试依赖它，不作为缺陷修改。

### P2

1. static/index.html:295、static/index.html:337：界面「示例模式」改为「演示模式」。
2. app.py:329 与 app.py:792：演示写稿返回前检查正文长度，超过 1000 字则 400，不截断。
3. tests/test_app.py:173、test_app.py:194、test_app.py:208：去掉假密钥字符串。禁止改测试，本次不修。
4. app.py:368：模型标题只要有一条超过 20 字就 502，不再滤掉后继续返回。
5. NOTES.md:22：运行时依赖改为五个，补上 python-multipart。
6. NOTES.md:34：字体顺序改成与 app.py:388-395 相同。
7. static/index.html:111：选题 maxlength 从 120 改为 100，与 app.py:34 一致。
8. app.py:748 或 static/index.html:319：扩题入库写入 `ai`，或删除不会命中的「AI 扩题」标签。
9. app.py:931：封面在 `file.read()` 之后才判断 10MB。改为分块读取，超过立即 400，避免先把整个请求体放进内存。
10. app.py:892：删除草稿只删数据库行。同时删除该草稿的卡片目录和封面文件。

## 专项验收

1. 无密钥跑通：见「本地跑通记录」。32 项与 16 项均在无 key 下通过，并有「不调用 httpx.post」的断言。假 key 只存在于测试桩，见不符处第 3 条，不阻断演示流程。
2. 体积与字体：最大文件 39526 字节；仓库无字体文件。README.md:86-99 写明微软雅黑、苹方、华文黑体、Noto Sans CJK、文泉驿，以及都找不到时用 `ImageFont.load_default()`。代码回退在 app.py:388-425。本机实测命中 `msyh.ttc` / `msyhbd.ttc`。缺字体用例 `test_missing_font_still_renders`（test_acceptance.py:216）已通过，仍输出 1080×1440。
3. 渲染可复现：固定输入与文件、尺寸、外缘断言见 test_acceptance.py:17-19 与 test_acceptance.py:122-150。长标签用例 test_acceptance.py:153 同样检查外缘。本次边界探针在满字数输入下 `outer_ink 0`。
4. 规格：保存路径标题 20（app.py:32、app.py:662）、正文 1000（app.py:33、app.py:664）、标签最多 10 个且每个 20 字（app.py:35-36、app.py:821-825）。封面 1080×1440（app.py:38），没有 9:16 分支。实测满上限草稿可渲染且不溢出；21 字标签和 11 个标签返回 400。不符点是不符处第 2 条和第 4 条。
5. 溯源：见「许可证与署名核查」。四字段齐全，上游版权行保留，commit 未核实。
