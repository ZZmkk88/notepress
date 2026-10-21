# TASK-100 notepress 核验运行记录

- 开始: 2026-10-22
- 工作目录: E:\muse-bridge\in\TASK-100-notepress
- 模式: 轻量核验（只判断上轮审查点是否修好）

## 步骤记录

### 0. 开工

已创建本文件。下一步：读 README、看最近提交、按 README 装环境并跑测试。

### 1. 仓库与提交（只读）

命令：`git -C E:\muse-bridge\in\TASK-100-notepress rev-parse HEAD`
输出：`2f5b7e781e8846a60506bf965df044c34925efd1`

命令：`git log --oneline`
输出：
```
2f5b7e7 fix(TASK-072): 落实 Grok 审查 P2 收口十项（前端演示模式文案统一；演示正文上限 400；标题标签超限 502；无效 topic 400；封面 basename；模板避第一；NOTES/README 写实）
```

命令：`git status --short`
输出：空（工作区干净）。

历史里只有这一笔提交，没有单独的 TASK-059 / TASK-064 提交。这两笔声称的改动若存在，只在当前树里。

命令：`python --version` 然后 `python -c "import fastapi, ..."`
输出：
```
Python 3.11.9
ModuleNotFoundError: No module named 'fastapi'
```
系统 Python 未装本项目依赖。venv 将建在工作目录，不写进仓库。

### 2. 体积与字体（只读）

命令：`python E:\muse-bridge\work\TASK-100-notepress\scan_files.py`
输出摘要：
```
COUNT 17
MAX 103113
OVER_2MB 0
---FONTS---
NONE
```
最大文件是 gitignore 的 pyc（103113 字节）。`git ls-files` 共 14 个路径，无 ttf/otf/woff/woff2/ttc。

### 3. 装依赖

命令：
`python -m venv E:\muse-bridge\work\TASK-100-notepress\venv`
退出码 0。

命令：
`E:\muse-bridge\work\TASK-100-notepress\venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt`
退出码 0。钉选版本均已在该 venv 中（fastapi 0.156.8、uvicorn 0.54.0、python-multipart 0.0.32、httpx 0.28.1、pillow 13.0.0、pytest 9.1.1）。未执行 pip 升级。

venv 放在工作目录，没有在仓库里建 `.venv`（本轮禁止写仓库）。临时库、pyc、pytest 临时目录通过环境变量指到 `E:\muse-bridge\work\TASK-100-notepress`。未设置 `NOTEPRESS_LLM_API_KEY`。

### 4. pytest

命令：
`E:\muse-bridge\work\TASK-100-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-100-notepress\run_pytest.py`

该脚本在仓库目录执行 README 中的：
`python -m pytest tests\ -q -p no:cacheprovider`

输出：
```
................................                                         [100%]
============================== warnings summary ===============================
..\..\work\TASK-100-notepress\venv\Lib\site-packages\fastapi\testclient.py:1
  E:\muse-bridge\work\TASK-100-notepress\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
32 passed, 1 warning in 15.97s
CMD ... -m pytest tests\ -q -p no:cacheprovider
CWD E:\muse-bridge\in\TASK-100-notepress
ELAPSED_SEC 17.32
EXIT 0
```

### 5. 真实流程自测（无密钥，本机 127.0.0.1:8155）

命令：
`E:\muse-bridge\work\TASK-100-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-100-notepress\run_live.py`

等价于在仓库目录执行 `python tests\live_selftest.py 8155`。脚本内 `env.pop("NOTEPRESS_LLM_API_KEY")`，httpx `trust_env=False`。

输出：
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
ELAPSED_SEC 2.87
EXIT 0
```

进程由脚本 `finally` 里的 `proc.terminate()` 结束。未使用 taskkill。

### 6. 声称修复的最小复现

命令：
`E:\muse-bridge\work\TASK-100-notepress\venv\Scripts\python.exe E:\muse-bridge\work\TASK-100-notepress\probe_claims.py`

退出码 0。数据库与图片在 `E:\muse-bridge\work\TASK-100-notepress\probe`。关键输出：

```
LOGIN 200 must_change True
TONE checklist status 200 demo True title_lens [13, 11, 12] body_len 281 tags [...] needle_hits []
TONE experience status 200 demo True title_lens [13, 11, 12] body_len 233 needle_hits []
TONE pitfall status 200 demo True title_lens [13, 11, 12] body_len 221 needle_hits []
LONG_TOPIC_STATUS 400
LONG_TOPIC_BODY {"detail":"演示稿正文 1175 字，超过 1000 字上限"}
MIXED_TITLE 502 {"detail":"AI 返回的标题超过 20 字（这是一个超过二十个字的标…），请重试"}
LONG_TAG 502 {"detail":"AI 返回的标签超过 20 字（标签标签标签标签标签标签…），请重试"}
MISSING_TOPIC 400 {"detail":"选题不存在"}
STRING_TOPIC 400 {"detail":"选题不存在"}
COVER_SIZE (1080, 1440)
TAG_LINE_LEN 90 WRAP_N 4 FIT_EQ_WRAP True
  line0 wrap_w=891.0
  line1 wrap_w=891.0
  line2 wrap_w=891.0
  line3 wrap_w=867.0
BOTTOM_ALIGN_TY 1050 FOOTER_Y 1290 LAST_LINE_TOP 1218
STATUS_ONLY 200 STALE_KEPT True
EXPORT 200 application/zip
EXPORT_PNG_IS_STALE False PNG_MAGIC b'\x89PNG\r\n\x1a\n' TEXT_HEAD 标题：旧标题
EDIT_TITLE 200 CARD_EXISTS_AFTER_EDIT False
EXPORT_AFTER_EDIT_TEXT 标题：新标题 CARD_BACK True
DOWNLOAD_ORPHAN 404 {"detail":"草稿不存在"}
API_DELETE 200 cover False card False dir False
CENTER_PIXEL (255, 0, 0)
BIG_UPLOAD 400 {"detail":"图片超过上限 10MB（当前 10.0MB）"}
BIG_FILE_BYTES 10485761
FIND_FONT C:/Windows/Fonts/msyh.ttc C:/Windows/Fonts/msyhbd.ttc
PROBE_DONE
```

`needle_hits` 检查演示稿里是否出现「第一」「最佳」「100%」。`CENTER_PIXEL (255, 0, 0)` 表示封面渲染打开的是 covers 目录里的红图，没有打开工作目录里的绿图（绝对路径写在 cover_file 里）。`BIG_UPLOAD` 的「当前 10.0MB」来自 `file.size` 分支，该分支在 `read` 之前。

### 7. 仓库是否被本轮写过

`git status --short` 在 pytest 之后、probe 之后各跑一次，输出都是空。
