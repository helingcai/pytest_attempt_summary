def build_retry_insight(attempts: list[dict]) -> list[str]:
    if not attempts:
        return ""

    """生成RetryInsight文本"""
    lines = []

    failed = [a for a in attempts if a.get('status') == "FAILED"]
    passed = [a for a in attempts if a.get('status') == "PASSED"]

    if failed and passed:
        lines.append(
            f"• Failed {len(failed)} times, then passed on retry"
        )
        lines.append("• Likely flaky test (unstable behavior)")
    elif len(failed) == len(attempts):
        lines.append(
            f"• All {len(attempts)} attempts failed"
        )

    errors = {
        a.get('error') for a in attempts
        if isinstance(a, dict) and a.get('error')
    }
    if len(errors) == 1 and failed:
        lines.append("• Same error across failed attempts")
    elif len(errors) > 1:
        lines.append("• Error message changed between attempts")

    urls = {
        a.get('url') for a in attempts
        if isinstance(a, dict) and a.get('url')
    }
    if len(urls) > 1:
        lines.append("• Failed at different URLs")
    return lines
