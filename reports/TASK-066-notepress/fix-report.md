# notepress 修复记录

结论：review.md 的分级清单里没有 P0，也没有 P1。按「只修 P0 和 P1、最多 5 项」的约束，没有改仓库源码。P2 共 10 条，本次不修。

## P0

无条目。没有改文件。

## P1

无条目。没有改文件。

默认口令、只提示改密、演示模式不拦截保存，是 README 与 DECISIONS.md D-1 的既定行为，测试也锁定了这些断言，不当作缺陷去改。

## 未修的 P2（清单内，超出本次允许的修复级别）

1. P2-1 界面「示例模式」：static/index.html:295、index.html:337。未改。原因：文案不一致，不阻断运行，也不是安全或数据损坏。
2. P2-2 超长选题的演示正文可超过 1000 字：app.py:329、app.py:792。未改。原因：种子选题实测正文 222–298 字；保存接口仍会 400。要约 700 字以上的自由选题才会在写稿接口返回超限正文。
3. P2-3 测试中的假 key：tests/test_app.py:173、test_app.py:194、test_app.py:208。未改。原因：禁止修改测试文件。该字符串只用于把 `llm_configured` 置真，同用例已替换 `llm_chat`，不会发到网络。
4. P2-4 部分超限标题被滤掉：app.py:368。未改。原因：返回给调用方的标题仍然都不超过 20 字；全部超限时已经 502。现有测试只断言全部超限这一种情况。
5. P2-5 NOTES 漏写 python-multipart：NOTES.md:22。未改。原因：文档笔误，安装清单本身是对的。
6. P2-6 NOTES 字体顺序：NOTES.md:34。未改。原因：README 与 app.py:388-395 一致，本机已解析到微软雅黑。
7. P2-7 选题框 maxlength 120：static/index.html:111。未改。原因：接口会拒绝 101 字以上，数据不会写进库。
8. P2-8 `source=ai` 从未写入：app.py:748、static/index.html:319。未改。原因：只影响列表上的来源标签，扩题和入库功能可用。
9. P2-9 封面先读入再限 10MB：app.py:931。未改。原因：默认只监听本机，且要登录；现有测试用的是小图。
10. P2-10 删草稿不删媒体文件：app.py:892。未改。原因：文件不经静态目录对外提供，读取卡片仍要登录。

## 全量测试（审查结束后重跑）

未改代码之后执行。工作目录为仓库根，无 `NOTEPRESS_LLM_API_KEY`，临时目录在 `E:\muse-bridge\work\TASK-066-notepress\tmp`。

命令：

```
E:\muse-bridge\work\TASK-066-notepress\venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```

退出码 0。结果行：

```
32 passed, 1 warning in 10.38s
```

警告原文（非失败）：

```
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

没有失败项。没有为了变绿而改测试或断言。

## git status

命令与原样输出（退出码 0，标准输出 0 行）：

```
git status --porcelain
```

标准输出到此结束，没有文件名。仓库工作区是干净的：本次没有修改源码。审查报告写在仓库外的 `E:\muse-bridge\out\TASK-066-notepress\`（review.md、run.md、fix-report.md）。
