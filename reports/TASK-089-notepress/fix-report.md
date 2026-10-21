# 修复记录

清单里没有 P0。P1 只有一条，落在测试文件上，任务禁止改测试，所以没有改仓库源码。P2 不在本次修改范围。

## P1-1 测试里的占位密钥字符串

- 问题编号：P1-1
- 文件：`tests/test_app.py:173`、`tests/test_app.py:194`、`tests/test_app.py:208`
- 改法：未改。
- 原因：这三行是 `monkeypatch.setenv("NOTEPRESS_LLM_API_KEY", "sk-test-not-real")`，用来让写稿走「已配置密钥」分支，真正的 `llm_chat` 被桩替换。字符串不能当真实密钥。源码 `app.py:236` 与 `app.py:242` 只读环境变量，没有写死 key，没有可改的源码位置。本任务禁止改测试文件，`DECISIONS.md:35` 至 `DECISIONS.md:37` 也写明此项关闭。
- 验证：不存在对应的源码补丁。全量测试见下方，32 项通过。

## P0

无。

## P2

`review.md` 里 P2-1 至 P2-7 本次不改。

## 全量测试

未改仓库源码之后重跑。cwd = `E:\muse-bridge\in\TASK-089-notepress`，环境中无 `NOTEPRESS_LLM_API_KEY`。

命令：

```
E:\muse-bridge\work\TASK-089-notepress\venv\Scripts\python.exe -m pytest tests\ -q -p no:cacheprovider
```

输出：

```
................................                                         [100%]
============================== warnings summary ===============================
..\..\work\TASK-089-notepress\venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-089-notepress\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
32 passed, 1 warning in 16.12s
```

exit 0。没有失败项。那条警告是测试客户端依赖的弃用提示，`DECISIONS.md:37` 要求不为此改版本号。

## git status

仓库路径 `E:\muse-bridge\in\TASK-089-notepress`。本次没有改仓库源码，空输出是预期：改动没有丢，因为本来就没有写进工作区。

命令：

```
git status --porcelain
```

输出：（空，exit 0）

```
```
