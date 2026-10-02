"""测试 parser 模块。"""
from agent.parser import CodeParser


def test_parse_empty():
    parser = CodeParser()
    result = parser.parse("")
    assert result.error == "文件为空"


def test_parse_whitespace_only():
    parser = CodeParser()
    result = parser.parse("   \n\n  ")
    assert result.error == "文件为空"


def test_parse_syntax_error():
    parser = CodeParser()
    result = parser.parse("def f(:\n    pass")
    assert "语法错误" in result.error


def test_parse_function():
    parser = CodeParser()
    source = "def add(a, b):\n    return a + b\n"
    result = parser.parse(source)
    assert len(result.units) == 1
    assert result.units[0].name == "add"
    assert result.units[0].type == "function"
    assert result.units[0].lineno == 1


def test_parse_class():
    parser = CodeParser()
    source = "class A:\n    def m(self):\n        pass\n"
    result = parser.parse(source)
    names = [u.name for u in result.units]
    assert "A" in names
    assert "m" in names


def test_parse_no_units():
    parser = CodeParser()
    result = parser.parse("x = 1\ny = 2\n")
    assert result.error == "未找到函数或类"


def test_parse_module_fallback():
    """非 Python 语言：整段源码作为一个审查单元（LLM 直接审查）。"""
    parser = CodeParser()
    source = "function divide(a, b) { return a / b; }"
    result = parser.parse_module(source, name="input.js")
    assert not result.error
    assert len(result.units) == 1
    unit = result.units[0]
    assert unit.name == "input.js"
    assert unit.type == "文件"
    assert unit.source == source
    assert unit.lineno == 1


def test_parse_module_empty():
    parser = CodeParser()
    result = parser.parse_module("", name="input.js")
    assert result.error == "文件为空"