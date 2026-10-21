# notepress 修复报告

结论：review.md 的分级清单里没有 P0，没有 P1。没有修改待审仓库的源码。P2 按任务边界不修；其中 P2-10 即使想修也不能改测试文件。

## 未改条目

### P0

无条目。

### P1

无条目。

### P2（列出但不改）

- P2-1 演示模式超限正文仍返回 200。位置 app.py:351-352。未改。原因：不是跑不起来，也不是安全、已存数据或权限问题；创建草稿时 app.py:685-689 仍会 400，超限正文进不了数据库。
- P2-2 部分超长标题被静默丢弃。位置 app.py:368-370。未改。原因：同上，且「全部超长则 502」已被 tests/test_app.py:193 锁住。放宽或收紧都会碰到测试边界，本次不改行为。
- P2-3 模型标签未校验单条 20 字。位置 app.py:376-377。未改。原因：保存路径 app.py:845-849 已拒绝，不属于 P0/P1。
- P2-4 选题框 maxlength 120 与上限 100 不一致。位置 static/index.html:111、app.py:768-769。未改。原因：接口已正确返回 400，属于界面与常量不一致，不是 P0/P1。
- P2-5 无效 topic_id 导致 500。位置 app.py:867-873。未改。原因：实测响应正文为 `Internal Server Error`，不泄露 SQL；异常路径会回滚，没有半成品数据。健壮性缺陷，等级 P2。
- P2-6 封面路径拼接未取 basename。位置 app.py:521。未改。原因：上传只写入 `{id}.png|jpg`（app.py:985-994），现有接口到不了绝对路径。防御性缺口，不升 P1。
- P2-7 示例稿「第一步」命中违禁词「第一」。位置 app.py:301、data/banned_words.json:1。未改。原因：子串匹配被 tests/test_app.py:270-271 依赖，不能改匹配规则。
- P2-8 「示例模式」与「演示模式」用词不同。位置 static/index.html:295、README.md:12。未改。原因：文案，不是 P0/P1。
- P2-9 NOTES 漏写 python-multipart。位置 NOTES.md:22、requirements.txt:3。未改。原因：文档笔误，安装清单本身是对的，不是 P0/P1。
- P2-10 测试中的假 key `sk-test-not-real`。位置 tests/test_app.py:173、tests/test_app.py:194、tests/test_app.py:208。修不动。原因：禁止修改测试文件。改 app.py 也去不掉测试里的字符串。
- P2-11 TestClient 的 httpx2 弃用警告。未改。原因：测试已通过，不是依赖冲突；禁止改 requirements 里的版本号。

## 全量测试（清单确认后重跑）

未改源码。重跑命令与审查阶段相同，basetemp 换了一个目录，避免和上一轮临时文件搅在一起。

```
E:\muse-bridge\work\TASK-075-notepress\venv\Scripts\python.exe -B -X utf8 -m pytest tests -q -p no:cacheprovider --basetemp=E:\muse-bridge\work\TASK-075-notepress\pytest-tmp-final
```

输出：

```
................................                                         [100%]
============================== warnings summary ===============================
..\..\work\TASK-075-notepress\venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-075-notepress\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
32 passed, 1 warning in 15.52s
```

exit 0。没有失败项。那一条警告是 Starlette 对 TestClient 的弃用提示，断言没有失败。

## git status

待审仓库里没有源码改动。review.md、run.md、fix-report.md 写在 `E:\muse-bridge\out\TASK-075-notepress\`，不在这个 git 仓库里，所以 status 为空。空输出表示没有仓库改动，不是改动丢失。

```
git status --porcelain
```

标准输出为空，exit 0。
