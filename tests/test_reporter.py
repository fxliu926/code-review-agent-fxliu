"""测试 reporter 模块。"""
from agent.reporter import Reporter
from agent.parser import CodeUnit


def test_generate_report():
    reporter = Reporter()
    unit = CodeUnit(name="add", type="function", source="def add(a,b): return a+b", lineno=1)
    results = [{"unit": unit, "review": "## 问题列表\n- 无\n"}]
    report = reporter.generate("test.py", results)
    assert "# 代码审查报告" in report
    assert "add" in report
    assert "test.py" in report
    assert "审查单元数：1" in report


def test_generate_report_with_mode():
    """非 Python 路径：报告里应注明审查模式。"""
    reporter = Reporter()
    unit = CodeUnit(name="input.js", type="文件", source="let x = 1", lineno=1)
    results = [{"unit": unit, "review": "## 问题列表\n- 无\n"}]
    report = reporter.generate("input.js", results, mode="LLM 直接审查（该语言暂无结构化解析支持）")
    assert "审查模式：LLM 直接审查" in report
    assert "input.js" in report


def test_generate_report_without_mode():
    """不传 mode 时报告格式与原来一致。"""
    reporter = Reporter()
    unit = CodeUnit(name="add", type="function", source="def add(a,b): return a+b", lineno=1)
    results = [{"unit": unit, "review": "ok"}]
    report = reporter.generate("test.py", results)
    assert "审查模式" not in report


def test_save_report(tmp_path):
    reporter = Reporter()
    out = tmp_path / "report.md"
    reporter.save("# hello", str(out))
    assert out.read_text(encoding="utf-8") == "# hello"