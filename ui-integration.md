# UI 项目接入指南 / UI Integration Guide

> ⚠️ 本指南仅供 pytest-attempt-summary 插件接入使用。插件遵循 MIT License。

本文档展示如何在 **UI 自动化项目**中集成 `pytest-attempt-summary` 插件。  
This document shows how to integrate the `pytest-attempt-summary` plugin in a **UI automation project**.

---

## 仓库结构示例 / Project Structure Example

```

your-ui-project/
├── conftest.py                    # 核心接入模板 / Core integration template
├── pytest.ini                     # pytest 配置（reruns、markers） / pytest configuration
├── requirements.txt               # 项目依赖 / Project dependencies
├── tests/
│   ├── test_login.py
│   └── test_logout.py
├── artifacts/                     # 失败用例证据 / Failure artifacts
├── videos/                        # Playwright 原始视频 / Playwright raw videos
├── tracing/                       # Playwright tracing 临时目录 / Tracing temporary files
└── .gitignore

````

---

## 安装依赖 / Install Dependencies

```bash
pip install pytest pytest-playwright pytest-rerunfailures playwright allure-pytest pytest-attempt-summary
````

或者通过 `requirements.txt` / Or via `requirements.txt`:

```txt
pytest>=7.0
pytest-playwright
pytest-rerunfailures
playwright>=1.35
allure-pytest>=2.13
pytest-attempt-summary
```

---

## pytest.ini 示例 / pytest.ini Example

```ini
[pytest]
addopts = --reruns 2 --alluredir=allure-results
```
---

## 完整 conftest.py 示例 / Full conftest.py Example

> ✅ 这个示例包含 **context/page fixture**、失败收集、视频/trace 保存、以及 **attempts** 信息更新。
> This example includes **context/page fixtures**, failure collection, video/trace saving, and **attempts** tracking.

```python
import time
from playwright.sync_api import sync_playwright
from pathlib import Path
import pytest, shutil, json, allure
from pytest_attempt_summary.attempt_summary import attach_attempt_summary

# ================== Session Fixtures / Session Fixtures ==================
@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as p:
        yield p

@pytest.fixture(scope="session")
def browser(playwright_instance):
    """浏览器只启动一次 / Browser launches once per session"""
    browser = playwright_instance.chromium.launch(headless=True)
    yield browser
    browser.close()

# ================== Function Fixtures / Function Fixtures ==================
@pytest.fixture(scope="function")
def context(browser, request):
    """每个测试方法一个全新 context / Each test gets a new browser context"""
    attempt = getattr(request.node, "execution_count", 1)
    request.node._current_attempt = attempt

    attempt_dir = f"attempt_{attempt}"
    record_video_dir = Path("videos") / attempt_dir
    record_tracing_dir = Path("tracing") / attempt_dir
    record_video_dir.mkdir(parents=True, exist_ok=True)
    record_tracing_dir.mkdir(parents=True, exist_ok=True)

    need_login = request.node.get_closest_marker("need_login") is not None

    context = browser.new_context(
        storage_state="storage/login.json" if need_login else None,
        record_video_dir=str(record_video_dir),
        record_video_size={"width": 1920, "height": 1080},
        viewport={"width": 1920, "height": 1080}
    )

    context.tracing.start(
        name=attempt_dir,
        screenshots=True,
        snapshots=True,
        sources=True
    )

    yield context

    trace_path = record_tracing_dir / "trace.zip"
    try:
        context.tracing.stop(path=trace_path)
    finally:
        context.close()

    failed = getattr(request.node, "_failed", False)
    if not failed:
        shutil.rmtree(record_video_dir, ignore_errors=True)
        shutil.rmtree(record_tracing_dir, ignore_errors=True)
        return

    module = request.node.module.__name__.split(".")[-1]
    cls = request.node.cls.__name__ if request.node.cls else "no_class"
    name = request.node.name

    target_dir = get_attempt_dir(module, cls, name, attempt)
    move_artifacts(record_video_dir, trace_path, target_dir)

    attempts = getattr(request.node, "_attempts", [])
    current = next(a for a in attempts if a["attempt"] == attempt)
    current.update({
        "has_screenshot": (target_dir / "failure.png").exists(),
        "has_video": any(target_dir.glob("*.webm")),
        "has_trace": (target_dir / "trace.zip").exists(),
        "url": (target_dir / "url.txt").read_text(encoding="utf-8") if (target_dir / "url.txt").exists() else None,
        "base_dir": str(target_dir)
    })

    attach_artifacts_to_allure(target_dir)

@pytest.fixture(scope="function")
def page(context):
    page = context.new_page()
    console_error = []
    page.on("console", lambda msg: console_error.append({
        "type": msg.type,
        "text": msg.text,
        "location": msg.location
    }) if msg.type == "error" else None)
    page._console_errors = console_error
    yield page
    page.close()

# ================== Pytest Hook / Pytest Hook ==================
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    start = time.time()
    outcome = yield
    rep = outcome.get_result()
    duration = round(time.time() - start, 2)

    if rep.when != "call":
        return

    if not hasattr(item, "_attempts"):
        item._attempts = []

    attempt = len(item._attempts) + 1
    item._attempts.append({
        "attempt": attempt,
        "status": "FAILED" if rep.failed else "PASSED",
        "duration": duration,
        "error": str(rep.longrepr) if rep.failed else ""
    })

    if not rep.failed:
        return

    page = item.funcargs.get("page")
    if not page:
        return

    page._test_error = str(rep.longrepr)
    item._failed = True

    module_name = item.module.__name__.split(".")[-1]
    class_name = item.cls.__name__ if item.cls else "no_class"
    test_name = item.name
    attempt_dir = f"attempt_{attempt}"
    base_dir = Path("artifacts") / module_name / class_name / test_name / attempt_dir
    base_dir.mkdir(parents=True, exist_ok=True)

    save_failure_artifacts(page, base_dir)

# ================== Utility Functions / Utility Functions ==================
def get_attempt_dir(module, cls, test_name, attempt):
    target_dir = Path("artifacts") / module / cls / test_name / f"attempt_{attempt}"
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir

def save_failure_artifacts(page, base_dir):
    page.screenshot(path=base_dir / "failure.png", full_page=True)
    (base_dir / "url.txt").write_text(page.url, encoding="utf-8")
    console_errors = getattr(page, "_console_errors", [])
    (base_dir / "browser_console_errors.json").write_text(json.dumps(console_errors, indent=2, ensure_ascii=False), encoding="utf-8")
    if getattr(page, "_test_error", None):
        (base_dir / "test_failure_errors.txt").write_text(page._test_error, encoding="utf-8")

def move_artifacts(src_video_dir, src_trace, dst_dir):
    for video_file in src_video_dir.glob("*.webm"):
        shutil.move(str(video_file), dst_dir / video_file.name)
    if src_trace.exists():
        shutil.move(str(src_trace), dst_dir / "trace.zip")

def attach_artifacts_to_allure(target_dir):
    for video in target_dir.glob("*.webm"):
        allure.attach.file(video, name="📎 Video", attachment_type=allure.attachment_type.WEBM)
    trace = target_dir / "trace.zip"
    if trace.exists():
        allure.attach.file(trace, name="📎 Playwright-Trace.zip")
```

---

## 使用步骤 / Usage Steps

1. **在 UI 项目中放置 conftest.py / Place conftest.py in your UI project**
2. **在测试用例中使用 `page` / `context` fixture / Use `page` / `context` fixtures in your tests**
3. **运行 pytest 并生成 Allure Report / Run pytest and generate Allure Report**:

```bash
pytest --alluredir=allure-results
allure serve allure-results
```

4. **查看 Attempt Summary / View Attempt Summary**：

   * 显示每次 attempt 状态、耗时、错误信息 / Shows attempt status, duration, and errors
   * 点击 **▶ View Failure Details** 展开 Failure Panel / Click **▶ View Failure Details** to expand panel
   * 视频 / trace 文件实际存放在 `artifacts/<module>/<class>/<test>/attempt_x/` / Videos/traces are stored in `artifacts/<module>/<class>/<test>/attempt_x/`

---

## 示意图 / Visual Example

```
🔁 Attempts: 3 / 3 failed
🧠 Retry Insight / Retry Insight
• Flaky behavior detected
🔍 Attempt Diff Analysis / Attempt Diff Analysis
≠ Error Differences
≠ Duration Differences

Attempt 1   Attempt 2   Attempt 3
Attempt 2 ❌ FAILED
🕑 Duration: 0.01s

▶ View Failure Details (Attempt 2)
❌ Failure Panel (Attempt2)
🔗 Page URL
🧯 Browser Console Errors
❌ Test Failure Errors
📸 Screenshot
🎥 Video
🧭 Trace
```

> ⚠️ 注意 / Note: 视频 / trace 文件在 **context fixture teardown** 阶段生成，Attempt Summary 仅用于指引用户查看 / video/trace files are generated at context teardown; Attempt Summary only guides where to view.

```