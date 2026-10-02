"""代码审查 Agent 入口。"""
import argparse
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown

from agent.parser import CodeParser
from agent.prompt import PromptBuilder
from agent.llm_client import LLMClient
from agent.reporter import Reporter
from agent.tools import CodeRunner

console = Console()

# 文件后缀 → 语言标识（Python 走结构化解析，其他语言走 LLM 直接审查）
SUFFIX_TO_LANG = {
    ".py": "python",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript",
    ".ts": "typescript", ".tsx": "typescript",
    ".java": "java",
    ".c": "c", ".h": "c",
    ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".hpp": "cpp",
    ".go": "go",
    ".rs": "rust",
}


def review_source(source: str, name: str = "input.py", language: str = "python") -> str:
    """审查一段源码，返回 Markdown 报告。

    Gradio 前端和 review_file 都复用这个函数，避免逻辑重复。
    language：被审查代码的语言标识。python 走「ast 解析 + 代码执行」
    的完整路径；其他语言没有对应的解析器/执行环境，降级为
    「整文件 → LLM 直接审查」。
    """
    # 1. 解析
    parser = CodeParser()
    builder = PromptBuilder()
    client = LLMClient()
    reporter = Reporter()
    results = []

    if language == "python":
        parse_result = parser.parse(source)
        if parse_result.error:
            console.print(f"[yellow]解析提示：{parse_result.error}[/yellow]")
            return f"❌ 解析失败：{parse_result.error}"
        console.print(f"[green]解析到 {len(parse_result.units)} 个代码单元[/green]")

        # 2. 工具调用：执行整段代码，拿到运行时信息（能发现 ast 抓不到的运行时错误）
        runner = CodeRunner()
        runtime_info = runner.run(source)
        console.print("[cyan]代码执行工具已运行，已获取运行时信息[/cyan]")

        # 3. 推理：把运行结果作为上下文，交给 LLM 审查每个代码单元
        for unit in parse_result.units:
            console.print(f"[cyan]正在审查 {unit.type} `{unit.name}`...[/cyan]")
            messages = builder.build(unit, runtime_info=runtime_info, language="python")
            review = client.chat(messages)
            results.append({"unit": unit, "review": review})

        mode = "结构化解析（ast 拆分 + 代码执行）"
    else:
        # 非 Python：降级路径，整文件一个单元，LLM 直接审查
        parse_result = parser.parse_module(source, name)
        if parse_result.error:
            return f"❌ 解析失败：{parse_result.error}"
        console.print(f"[cyan]{name}：非 Python 代码，走 LLM 直接审查路径[/cyan]")

        for unit in parse_result.units:
            console.print(f"[cyan]正在审查 {unit.type} `{unit.name}`...[/cyan]")
            messages = builder.build(unit, runtime_info=None, language=language)
            review = client.chat(messages)
            results.append({"unit": unit, "review": review})

        mode = "LLM 直接审查（该语言暂无结构化解析支持）"

    # 4. 生成报告
    return reporter.generate(name, results, mode=mode)


def review_file(file_path: str, output_path: str = None):
    """审查一个代码文件。"""
    path = Path(file_path)
    if not path.exists():
        console.print(f"[red]文件不存在：{file_path}[/red]")
        return
    language = SUFFIX_TO_LANG.get(path.suffix.lower())
    if language is None:
        console.print(
            f"[red]不支持的文件类型：{path.suffix}（支持 "
            + " / ".join(sorted(set(SUFFIX_TO_LANG.values())))
            + "）[/red]"
        )
        return

    source = path.read_text(encoding="utf-8")
    report = review_source(source, file_path, language=language)

    if output_path:
        Reporter().save(report, output_path)
        console.print(f"[green]报告已保存到 {output_path}[/green]")
    else:
        console.print(Markdown(report))


def main():
    parser = argparse.ArgumentParser(description="代码审查 Agent")
    parser.add_argument("file", help="要审查的代码文件（.py 走结构化解析，.js/.java 等走 LLM 直接审查）")
    parser.add_argument("-o", "--output", help="报告输出路径", default=None)
    args = parser.parse_args()
    review_file(args.file, args.output)


if __name__ == "__main__":
    main()