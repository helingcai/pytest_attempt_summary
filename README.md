# pytest-attempt-summary

**Allure 报告增强版 Attempt Summary（Pytest + Playwright） 
Enhanced Attempt Summary for Allure Reports (Pytest + Playwright)**

`pytest-attempt-summary` 是一个 Pytest 插件，用于收集 **每个测试用例的多次执行（reruns）**，并在 Allure 报告中以清晰、可交互的 **Attempt Summary** 展示。  
`pytest-attempt-summary` is a Pytest plugin that collects **multiple test attempts (reruns)** and presents them as a clear, interactive **Attempt Summary** in Allure Reports.

适用于使用 **Pytest + Playwright + Allure** 的 **UI 自动化项目**。  
It is designed for **UI automation projects** using **Pytest + Playwright + Allure**.

---

## 功能展示 / What You Get

失败用例在 Allure 中会附带 **Attempt Summary**：  
**Attempt Summary** attached to failed test cases in Allure:

```

🔁 Attempts: 3 / 3 failed

Attempt 1 | Attempt 2 | Attempt 3 - Latest

Attempt 3 ❌ FAILED
🕑 Duration: 0.01s

▼ View Failure Details
├─ Page URL
├─ Browser Console Errors
├─ Test Failure Errors
├─ Screenshot
├─ Video (see Tear down)
└─ Trace (see Tear down)

````

---

## 核心特性 / Key Features

收集每个测试用例的 **所有重跑尝试** / Collects **all rerun attempts** per test case

支持 `pytest-rerunfailures` / Supports `pytest-rerunfailures`

可交互 **展开 / 收起失败详情** / Interactive **expand / collapse Failure Details**  

高亮显示尝试之间的 **错误 / 耗时差异** / Highlights **error / duration differences** between attempts  

集成 Playwright **视频**和 **trace** / Integrates with Playwright **video** and **trace**  

轻量 HTML 附件（不会让 Allure 报告臃肿） / Lightweight HTML attachment (does not bloat Allure pages)  

---

## 安装 / Installation

```bash
pip install pytest-attempt-summary
````

依赖 / Requirements：

* `pytest >= 7.0`
* `allure-pytest >= 2.13`

---

## 基本用法 / Basic Usage

在项目中启用 reruns（示例）：/
Enable reruns in your project (example):

```ini
# pytest.ini
[pytest]
reruns = 2
```

运行测试并生成 Allure 报告：/
Run tests with Allure:

```bash
pytest --alluredir=allure-results
allure serve allure-results
```

在 Allure中打开 **失败用例** →**Attempt Summary** 会显示在Test Body中。/
Open a **failed test case** in Allure →**Attempt Summary** will appear in the Test Body.



---

## 注意事项 / Important Notes

🎥 视频和 🧭 Trace 文件由 UI 项目生成可在以下位置查看。 /
🎥 **Video** and 🧭 **Trace** files are attached by your UI framework and are visible under.

```
Allure → Tear down → context
```

Attempt Summary **不直接嵌入视频或 trace**，它仅指引用户到哪里查看。/ 
Attempt Summary **does not embed videos or traces**, it only guides you where to find them.

本插件 **不会自动记录 attempt** 需要 UI 项目自己收集每次尝试的数据（状态、错误、耗时、附件）。/
This plugin **does not record attempts by itself** your UI project must collect attempt data (status, error, duration, artifacts).

---

## 预期 Attempt 数据格式 / Expected Attempt Data Format

UI 自动化项目应提供类似的 attempt 数据：/
Your UI automation framework should provide attempt data like:

```json
[
  {
    "attempt": 1,
    "status": "FAILED",
    "duration": 0.5,
    "error": "AssertionError: ...",
    "url": "https://example.com",
    "has_video": true,
    "has_trace": true
  },
  {
    "attempt": 2,
    "status": "PASSED",
    "duration": 0.3
  }
]
```

---

## 适用场景 / Designed For

Playwright + Pytest UI 自动化框架 / 
Playwright + Pytest UI automation frameworks

使用 reruns 分析不稳定用例的团队 / 
Teams using reruns to analyze flaky tests

关注 **重试洞察** 的工程师，而不仅仅是成功/失败 / 
Engineers who want **retry insight**, not just pass/fail

---

## 许可 / License

MIT License

---

### 核心一句话 / One-line Summary

**Attempt Summary 帮助你理解 *为什么* 重试失败，而不仅仅是 *失败了*。** / 
**Attempt Summary helps you understand *why* retries fail, not just *that* they failed.**