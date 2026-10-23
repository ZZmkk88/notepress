# 修复报告

结论：审查清单里 P0 为 0、P1 为 0。没有改仓库源码。P2 共 7 条，按本轮额度只记录、不修。

## 未动手的条目

- P0：无。
- P1：无。
- P2-1 `README.md:71` 测试计数。不修。原因：额度只修 P0/P1，且明确不要为 P2 改文案。
- P2-2 `README.md:18` 状态流转措辞。不修。原因同上。收紧 `app.py:939-941` 会让 `tests/live_selftest.py:107-111` 失败，测试文件也不能改。
- P2-3 `tests/test_app.py:173`、`tests/test_app.py:194`、`tests/test_app.py:208` 的假 key `sk-test-not-real`。不修。原因：禁止改测试文件。字符串只作为环境变量交给被打桩的 `llm_chat`，本次运行 `KEY_SET False` 的全量测试与自测都没有出网。
- P2-4 `app.py:401` AI 标签条数静默切片。不修。原因：额度只修 P0/P1。演示模式不走这条路径。
- P2-5 TestClient 的 httpx2 弃用警告。不修。原因：不是失败；禁止为它改 `requirements.txt` 版本号。
- P2-6 `app.py:267-269` 演示标题硬切 10 字。不修。原因：额度只修 P0/P1。标题长度仍 ≤ 20，全量测试通过。
- P2-7 `README.md:111-119` 目录遗漏。不修。原因：额度只修 P0/P1，不改文案。

没有「改了哪个文件」的条目。下面是收尾重跑，不是修完某一条之后的回归。

## 收尾全量测试

命令（工作目录脚本，未设置 `NOTEPRESS_LLM_API_KEY`）：

```
E:\muse-bridge\work\TASK-101-notepress\venv\Scripts\python.exe -m pytest tests\ -q -p no:cacheprovider
```

工作目录 `E:\muse-bridge\in\TASK-101-notepress`。脚本打印 `KEY_SET False`。

输出：

```
..................................                                       [100%]
============================== warnings summary ===============================
..\..\work\TASK-101-notepress\venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-101-notepress\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
34 passed, 1 warning in 18.77s
```

退出码 0。没有失败项。警告与审查时相同，见 P2-5，不把它当成用例失败。

## git status --porcelain

在仓库 `E:\muse-bridge\in\TASK-101-notepress` 执行：

```
git status --porcelain
```

标准输出为空，退出码 0。

```
```

本轮没有改过仓库文件，空输出是预期，不是改动丢失。报告在 `E:\muse-bridge\out\TASK-101-notepress\`，不在仓库里。
