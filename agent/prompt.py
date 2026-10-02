"""Prompt 模块：集中管理所有 Prompt，方便调整。

Prompt 支持多语言审查：
- Python：配合 ast 拆分的单元（function / class）逐个审查；
- 其他语言（JavaScript / Java / C++ 等）：整文件作为一个单元，
  由 LLM 直接审查（没有 ast 拆分和代码执行工具的辅助）。
"""

SYSTEM_PROMPT_TEMPLATE = """你是一位资深的 {language} 代码审查员，擅长发现代码中的 Bug、\
代码质量问题、性能问题和安全隐患。你的审查风格是：
1. 客观、具体，指出问题时给出理由
2. 按严重程度分类：Critical / Major / Minor
3. 给出可操作的改进建议
4. 输出结构化 Markdown，方便程序解析
"""

REVIEW_PROMPT_TEMPLATE = """请审查以下 {language} {unit_type}：

```{lang_tag}
{source}
```

请从以下四个维度分析：
1. **潜在 Bug**：逻辑错误、边界情况、异常处理、空值处理
2. **代码质量**：命名、可读性、重复代码、注释
3. **性能问题**：不必要的循环、低效操作、内存占用
4. **改进建议**：给出修改后的代码片段

输出格式必须严格如下：

## 问题列表
- [Critical/Major/Minor] 问题描述（附行号）
- ...

## 改进建议
```{lang_tag}
修改后的代码
```

## 总结
一句话总结这个 {unit_type} 的整体质量。
"""

# 语言标识 → prompt 中的展示名（fence 标签直接用语言标识，如 ```javascript）
LANG_DISPLAY = {
    "python": "Python",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "java": "Java",
    "c": "C",
    "cpp": "C++",
    "go": "Go",
    "rust": "Rust",
}


class PromptBuilder:
    """构造审查 Prompt。"""

    def build(self, unit, runtime_info: str = None, language: str = "python") -> list:
        """返回 messages 列表，供 LLM 调用。

        runtime_info：代码执行工具返回的运行结果，可选
        （仅 Python 有，其他语言没有代码执行工具）。
        language：被审查代码的语言标识，如 "python" / "javascript"。
        """
        display = LANG_DISPLAY.get(language, language.capitalize())
        user_content = REVIEW_PROMPT_TEMPLATE.format(
            language=display,
            unit_type=unit.type,
            source=unit.source,
            lang_tag=language,
        )
        if runtime_info:
            user_content += (
                "\n\n以下是整段代码的运行结果，供你审查时参考：\n"
                "```text\n"
                f"{runtime_info}\n"
                "```\n"
                "若运行结果包含错误，请在「潜在 Bug」中重点说明。"
            )
        return [
            {"role": "system", "content": SYSTEM_PROMPT_TEMPLATE.format(language=display)},
            {"role": "user", "content": user_content},
        ]
