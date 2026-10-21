# TASK-088-notepress 执行记录

开工：2026-10-22。工作目录 E:\muse-bridge\in\TASK-088-notepress。先审查再修 P0/P1。

## 1. 环境

命令：`python --version`

```
Python 3.11.9
```

系统字体：`Test-Path C:\Windows\Fonts\msyh.ttc` → True；`Test-Path C:\Windows\Fonts\msyhbd.ttc` → True。

虚拟环境（放在工作目录，不进仓库）：`python -m venv E:\muse-bridge\work\TASK-088-notepress\venv`
确认：`Test-Path E:\muse-bridge\work\TASK-088-notepress\venv\Scripts\python.exe` → True

## 2. 仓库体积与字体文件

命令：`E:\muse-bridge\work\TASK-088-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-088-notepress\scan_files.py`

```
FILE_COUNT 43
OVER_2MB []
FONTS []
41006	app.py
26567	static\index.html
14343	tests\test_app.py
7659	tests\test_acceptance.py
5734	README.md
4745	tests\live_selftest.py
```

最大单文件 app.py 41006 字节，低于 2MB。无 ttf/otf/woff/woff2。

## 3. 安装依赖

命令：

```
E:\muse-bridge\work\TASK-088-notepress\venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-088-notepress\requirements.txt -r E:\muse-bridge\in\TASK-088-notepress\requirements-dev.txt
```

结果：exit 0。装上 fastapi==0.156.8、uvicorn==0.54.0、python-multipart==0.0.32、httpx==0.28.1、pillow==13.0.0、pytest==9.1.1。末行含 `Successfully installed ... fastapi-0.156.8 ... pillow-13.0.0 ... pytest-9.1.1`。未升级 pip。

## 4. 全量 pytest（无 API key）

命令：`E:\muse-bridge\work\TASK-088-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-088-notepress\run_pytest.py`
（脚本内：清掉 NOTEPRESS_LLM_API_KEY，TEMP/TMP 指到工作目录，`pytest tests -q -p no:cacheprovider`，cwd 为仓库）

```
CMD ... python.exe -m pytest tests -q -p no:cacheprovider --basetemp E:\muse-bridge\work\TASK-088-notepress\pytest-tmp
CWD E:\muse-bridge\in\TASK-088-notepress
KEY_SET False
................................                                         [100%]
32 passed, 1 warning in 14.64s
```

警告原文：`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 测试仍通过。未因此重试。

## 5. 真实流程自测与 README 端口

命令：`E:\muse-bridge\work\TASK-088-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-088-notepress\run_live.py`

代理环境变量只记录是否存在，不记录值：HTTP_PROXY / HTTPS_PROXY / ALL_PROXY 及小写名均为 set=True。KEY_SET False。

live_selftest（端口 8155，脚本内弹出 NOTEPRESS_LLM_API_KEY）：

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
LIVE_EXIT 0 SECONDS 2.07
```

接着按 README 起 `app.py`，NOTEPRESS_DB / NOTEPRESS_MEDIA 指到工作目录，PORT=8000，NOTEPRESS_HOST=127.0.0.1。跑完后 `terminate`。服务日志：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:62890 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:62890 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:62890 - "GET /api/drafts HTTP/1.1" 401 Unauthorized
INFO:     127.0.0.1:62890 - "POST /api/login HTTP/1.1" 200 OK
INFO:     127.0.0.1:62890 - "GET /api/me HTTP/1.1" 200 OK
INFO:     127.0.0.1:62890 - "POST /api/generate HTTP/1.1" 200 OK
INFO:     127.0.0.1:62890 - "POST /api/generate HTTP/1.1" 200 OK
INFO:     127.0.0.1:62890 - "POST /api/drafts HTTP/1.1" 500 Internal Server Error
```

探测输出：

```
READY True
HEALTH 200 {"status":"ok","app_id":"notepress"}
HOME 200 len 25259
HOME_HAS_NOTEPRESS True
HOME_HAS_TITLE True
HOME_SNIP <title>notepress · 笔记工坊</title>
UNAUTH_DRAFTS 401
LOGIN 200 must_change True
ME 200 {"username":"admin","must_change":true,"llm_configured":false}
GEN 200 demo True titles ['用AI写周报，这样做超简单', '用AI写周报保姆级教程', '亲测！用AI写周报真的香'] body_len 284 tags ['AI工具', '普通人用AI', '效率提升', '职场干货', 'AI教程']
GEN_LONG 200 body_len 1078
```

GEN_LONG 是选题 `"题"*800` 的演示写稿，HTTP 200 且正文 1078 字。随后用 topic_id=999999 创建草稿，访问日志为 500。客户端读 body 超时（httpx.ReadTimeout），因为子进程 stdout 用了管道且当时没读，不能把这次超时写成服务挂死。进程已 terminate，SERVER_EXIT 1。

## 6. 边界与字体

命令：`...\python.exe E:\muse-bridge\work\TASK-088-notepress\probe_edges.py`

```
DEMO checklist topic_len 722 body_len 1000 over False
DEMO checklist topic_len 723 body_len 1001 over True
DEMO checklist topic_len 800 body_len 1078 over True
DEMO experience topic_len 800 body_len 1028 over True
DEMO pitfall topic_len 800 body_len 1016 over True
```

标题长度在这些用例里是 17/15/16，未超过 20。脚本在请求不存在的 topic_id 时抛出：

```
File "E:\muse-bridge\in\TASK-088-notepress\app.py", line 868, in create_draft
sqlite3.IntegrityError: FOREIGN KEY constraint failed
```

保存超长正文的请求没走到（脚本在上一请求退出）。

命令：`...\python.exe E:\muse-bridge\work\TASK-088-notepress\probe_font.py`

```
FONT_REGULAR C:/Windows/Fonts/msyh.ttc
FONT_BOLD C:/Windows/Fonts/msyhbd.ttc
```

## 7. 仓库是否被测试写脏

命令：`git -C E:\muse-bridge\in\TASK-088-notepress status --porcelain`

输出为空（修复前）。

## 8. P1-1 修复后的验证

改动：`app.py` 的 `ai_generate` 演示分支（约 350-357 行）返回前调用 `validate_title_body`。

命令：`...\python.exe E:\muse-bridge\work\TASK-088-notepress\probe_fix_p1.py`

```
SHORT 200 demo True body_len 284
EDGE722 200 body_len 1000
OVER723 400 {"detail":"正文超过上限 1000 字（当前 1001 字）"}
LONG800 400 {"detail":"正文超过上限 1000 字（当前 1028 字）"}
```

命令：`...\python.exe E:\muse-bridge\work\TASK-088-notepress\run_pytest.py`

```
32 passed, 1 warning in 14.89s
KEY_SET False
```

命令：`...\python.exe E:\muse-bridge\work\TASK-088-notepress\run_live_only.py`（live_selftest 端口 8156）

```
ALL PASS · 16 个检查点
LIVE_EXIT 0 SECONDS 2.11
```

命令：`git -C E:\muse-bridge\in\TASK-088-notepress status --porcelain`

```
 M app.py
```
