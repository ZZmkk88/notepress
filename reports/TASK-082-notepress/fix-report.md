# notepress 修复记录

结论：review.md 的分级清单里没有 P0，也没有 P1。按「只修 P0 和 P1，最多 5 项」未改仓库源码。全量测试仍是 32 passed。

## P0

问题编号：P0（无条目）

文件:行号：无

改法：没有跑不起来或阻断项。pip 安装成功，pytest 32 项通过，live_selftest 16 个检查点通过，`python app.py` 的 `/health` 与 `/` 返回 200。

验证：见文末全量测试。

## P1

问题编号：P1（无条目）

文件:行号：无

改法：没有发现要改代码的安全、数据或权限缺陷。默认口令不强制修改是 DECISIONS.md:3（D-1）和 README.md:24 的既定行为，不改。

验证：见文末全量测试。

## 未修的 P2（规则不允许顺手修）

问题编号：P2-1

文件:行号：static/index.html:295、static/index.html:337、static/index.html:385

改法：未改。用词与 README 不一致，不阻断、不涉及安全或数据损坏。

验证：未改，无单独回归。全量测试仍通过。

问题编号：P2-2

文件:行号：static/index.html:111；对照 app.py:34、app.py:768

改法：未改。前端允许输入 120 字，后端拒绝 101 字及以上。保存会被 400 拦住，不会静默截断。

验证：探针 `TOPIC_101 400 选题超过上限 100 字（当前 101 字）`。未改代码。

问题编号：P2-3

文件:行号：app.py:895-896、app.py:914-915

改法：未改。JSON `null` 会被 `str()` 写成字面量 `None`。官方页面提交的是字符串，不走这条路径。

验证：探针 `NULL_URL_PUT 200`，随后 `URL_AFTER_NULL 'None'`。未改代码，所以这个结果仍然如此。

问题编号：P2-4

文件:行号：app.py:408-425

改法：未改。本机粗体字体存在（探针 `FONT_BOLD C:/Windows/Fonts/msyhbd.ttc`），渲染正常。

验证：探针标题区非背景像素 29067；验收测试 `test_render_fixed_sample_size_and_no_overflow` 在全量结果里通过。

问题编号：P2-5

文件:行号：app.py:521；对照 app.py:490

改法：未改。上传接口只写入 `{id}.png` 或 `{id}.jpg`（app.py:986），接口不能把 `cover_file` 写成 `../`。

验证：未改代码。

问题编号：P2-6

文件:行号：app.py:268；对照 app.py:792

改法：未改。演示扩题截到 12 字，接口允许 50 字。短方向词的测试是绿的。

验证：全量测试里 `test_expand_demo_mode` 通过。未改代码。

问题编号：P2-7

文件:行号：app.py:376-377；对照 app.py:845

改法：未改。超长标签在保存时拒绝。本次没有密钥，没有调用真实模型。

验证：探针 `TAG_21 400 标签超过上限 20 字（当前 21 字）`。未改代码。

问题编号：P2-8

文件:行号：tests/test_app.py:173、tests/test_app.py:194、tests/test_app.py:208

改法：修不动。字符串是 `sk-test-not-real`，用来把 `llm_configured()` 打成已配置，同时桩掉 `llm_chat`。任务禁止改测试文件，也禁止改断言。改应用去忽略这个环境变量会让这三项失败。

验证：这三项包含在全量 32 passed 里。没有把该字符串发到网络（`llm_chat` 被替换）。

问题编号：P2-9

文件:行号：NOTES.md:22、NOTES.md:34

改法：未改。文档与 requirements.txt:1-5、README.md:90-95 不一致，不影响运行。

验证：未改代码。

问题编号：P2-10

文件:行号：README.md:55

改法：未改。测试段没写先装 requirements.txt。本次两个 requirements 都装了，测试能跑。

验证：全量测试 32 passed。

问题编号：P2-11

文件:行号：依赖站点包 `fastapi/testclient.py:1`，不是本仓源码

改法：修不动。警告不失败。任务禁止在非冲突时改 requirements 里的版本号。

验证：见下方警告原文。退出码 0。

## 全量测试（审查结束后重跑）

命令：

```
E:\muse-bridge\work\TASK-082-notepress\venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```

工作目录：`E:\muse-bridge\in\TASK-082-notepress`。已去掉 `NOTEPRESS_LLM_API_KEY`。`TMP`/`TEMP` 为 `E:\muse-bridge\work\TASK-082-notepress`。

真实输出：

```
................................                                         [100%]
============================== warnings summary ===============================
..\..\work\TASK-082-notepress\venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-082-notepress\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
32 passed, 1 warning in 15.27s
```

退出码 0。耗时 16.16 秒（含进程启动）。没有失败项。

审查前一次同样命令的结果是 `32 passed, 1 warning in 15.30s`。两次都是 32 项通过。

## git status

命令：

```
git -C E:\muse-bridge\in\TASK-082-notepress status --porcelain
```

输出：（空，退出码 0）

```
```

空输出是因为没有改仓库源码：清单里没有 P0/P1。审查报告在 `E:\muse-bridge\out\TASK-082-notepress\`，不在仓库工作区。不存在「改过又被还原」的文件。没有执行 `git checkout`、`git restore`、`git stash`、`git clean`。
