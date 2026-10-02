"""Gradio 前端：开发者工具风格的代码审查界面。

布局参考 GitHub PR Review / 编辑器双栏：
    左栏 input.py（代码编辑器） → 右栏 report.md（审查报告）。
所有视觉样式集中在 CUSTOM_CSS，改样式不需要动布局代码。
"""
import re
import time

import gradio as gr

from main import review_source


# 展示名 → (语言标识, 默认文件名, 图标点颜色)
# Python 走后端结构化解析；其他语言走 LLM 直接审查（降级路径）
LANGUAGES = {
    "Python": ("python", "input.py", "#3572a5"),
    "JavaScript": ("javascript", "input.js", "#f1e05a"),
    "TypeScript": ("typescript", "input.ts", "#3178c6"),
    "Java": ("java", "input.java", "#b07219"),
    "C": ("c", "input.c", "#555555"),
    "C++": ("cpp", "input.cpp", "#f34b7d"),
    "Go": ("go", "input.go", "#00add8"),
    "Rust": ("rust", "input.rs", "#dea584"),
}

REPORT_PLACEHOLDER = (
    "**等待审查**\n\n"
    "在左侧选择语言、粘贴代码，点击「运行审查」，报告会在这里生成。\n\n"
    "审查维度：**潜在 Bug** / **代码质量** / **性能问题** / **改进建议**。"
)

MONO_STACK = "Consolas, 'Cascadia Mono', 'JetBrains Mono', 'Courier New', monospace"

CUSTOM_CSS = f"""
/* ===== 全局 ===== */
body {{
    background: #f6f8fa !important;
}}
.gradio-container {{
    width: 100% !important;
    max-width: 1240px !important;
    margin: 0 auto !important;
    padding: 32px 24px 40px 24px !important;
    background: #f6f8fa !important;
    font-family: -apple-system, 'Segoe UI', 'Microsoft YaHei', sans-serif !important;
    color: #24292f !important;
}}
footer {{ display: none !important; }}

/* ===== 顶栏 ===== */
#app-header {{
    width: 100% !important;
    background: #ffffff !important;
    border: 1px solid #d0d7de !important;
    border-radius: 8px !important;
    padding: 0 !important;
    margin-bottom: 18px !important;
    overflow: hidden;
    box-shadow: 0 1px 2px rgba(140, 149, 159, 0.12);
}}
.hdr {{
    display: flex;
    align-items: center;
    padding: 14px 20px;
}}
.hdr-left {{ display: flex; align-items: center; gap: 11px; }}
.logo-mark {{
    width: 32px; height: 32px;
    background: #24292f;
    color: #ffffff;
    border-radius: 7px;
    display: flex; align-items: center; justify-content: center;
    font-family: {MONO_STACK};
    font-size: 12px; font-weight: 700;
    box-shadow: inset 0 -1px 0 rgba(255, 255, 255, 0.12);
}}
.hdr-title {{
    font-family: {MONO_STACK};
    font-size: 16px; font-weight: 700; color: #24292f;
    letter-spacing: -0.2px;
}}
.hdr-sub {{
    font-size: 12.5px; color: #57606a;
    line-height: 1.4;
}}

/* ===== 面板（编辑器窗口样式） ===== */
/* 宽屏下左右并排各占一半，容器本身撑满整页宽度 */
#main-panels {{ width: 100% !important; flex-wrap: nowrap !important; gap: 18px !important; }}
#panel-left, #panel-right {{
    flex: 1 1 0 !important;
    min-width: 0 !important;
    max-width: none !important;
}}
@media (max-width: 900px) {{
    #main-panels {{ flex-wrap: wrap !important; }}
    #panel-left, #panel-right {{ flex: 1 1 100% !important; }}
}}
.panel, #panel-left, #panel-right {{
    background: #ffffff !important;
    border: 1px solid #d0d7de !important;
    border-radius: 8px !important;
    padding: 0 !important;
    overflow: hidden;
    box-shadow: 0 1px 2px rgba(140, 149, 159, 0.10);
}}
.panel-head {{
    display: flex; align-items: center; gap: 8px;
    padding: 9px 16px;
    background: #f6f8fa;
    border-bottom: 1px solid #eaeef2;
}}
.file-dot {{ width: 10px; height: 10px; border-radius: 3px; flex: none; }}
.file-dot.python {{ background: #3572a5; }}
.file-dot.report {{ background: #8c959f; }}
.file-name {{
    font-family: {MONO_STACK};
    font-size: 12.5px; color: #24292f;
}}
.spacer {{ flex: 1; }}
.lang-tag {{
    font-family: {MONO_STACK};
    font-size: 10px; letter-spacing: 0.08em; color: #8c959f;
}}

/* ===== 左栏：代码编辑器 ===== */
/* 关掉 gr.Code 自带的标签栏和右下角图标条，只留纯粹的编辑器 */
#code-input {{
    border-width: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}}
#code-input > label[data-testid="block-label"] {{ display: none !important; }}
#code-input .icon-button-wrapper {{ display: none !important; }}
#code-input .cm-editor {{
    font-family: {MONO_STACK} !important;
    font-size: 13px !important;
    background: #ffffff !important;
}}
#code-input .cm-gutters {{
    background: #f6f8fa !important;
    border-right: 1px solid #eaeef2 !important;
    color: #8c959f !important;
}}

/* ===== 控制区 ===== */
.action-row {{
    flex-wrap: nowrap !important;
    gap: 9px !important;
    align-items: flex-end !important;
    margin: 12px 16px 0 16px !important;
}}
.action-row.run-row {{
    margin: 9px 16px 16px 16px !important;
    align-items: stretch !important;
}}
/* Gradio 把下拉框包在 .form 里并内联 min-width:160px，会把整行撑出去，这里解除 */
.action-row > .form {{ flex: 0 0 auto !important; width: 200px !important; min-width: 0 !important; }}
.action-row > .form > .block {{ min-width: 0 !important; }}
#lang-dd {{ flex-grow: 1 !important; width: 100% !important; min-width: 0 !important; }}
#lang-dd span[data-testid="block-info"] {{
    font-family: {MONO_STACK} !important;
    font-size: 10.5px !important;
    letter-spacing: 0.06em !important;
    color: #8c959f !important;
    margin-bottom: 3px !important;
}}
#lang-dd input {{ font-size: 13px !important; }}
#btn-run {{
    flex-grow: 1 !important;
    width: 100% !important;
    min-width: 0 !important;
    background: #1f883d !important;
    color: #ffffff !important;
    border: 1px solid rgba(31, 35, 40, 0.15) !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 0 rgba(31, 35, 40, 0.1) !important;
    transition: background 0.15s ease !important;
}}
#btn-run:hover {{ background: #1a7f37 !important; }}
#btn-clear {{
    flex: 0 0 auto !important;
    min-width: 0 !important;
    background: #f6f8fa !important;
    color: #24292f !important;
    border: 1px solid rgba(31, 35, 40, 0.15) !important;
    border-radius: 6px !important;
    box-shadow: 0 1px 0 rgba(31, 35, 40, 0.04) !important;
    transition: background 0.15s ease !important;
}}
#btn-clear:hover {{ background: #eef1f4 !important; }}

/* ===== 右栏：报告 ===== */
/* Gradio 默认给每个块 flex-grow，会把标题栏撑高、把正文挤到中间；这里显式重设高度分配 */
#file-head, #report-head {{
    padding: 0 !important;
    margin: 0 !important;
    flex-grow: 0 !important;
    flex-shrink: 0 !important;
    border: none !important;
}}
/* 标题栏内层容器自带内边距，会让标题条上下多出空白 */
#file-head .html-container, #report-head .html-container {{
    padding: 0 !important;
}}
#report {{
    padding: 0 !important;
    margin: 0 !important;
    flex-grow: 1 !important;
    align-self: stretch !important;
    justify-content: flex-start !important;
    align-items: stretch !important;
}}
#report > div, #report-head > div {{
    justify-content: flex-start !important;
    align-content: flex-start !important;
    align-items: stretch !important;
}}
#report .prose {{
    padding: 16px 26px 22px 26px !important;
    font-size: 14px !important;
    line-height: 1.75 !important;
    color: #24292f !important;
    align-self: stretch !important;
    max-height: 640px;
    overflow-y: auto;
}}
/* 报告正文顶部对齐：去掉 Gradio 各层包裹块自带的上下内距；
   .md 是 inline 容器，会在首段前生成一个空行盒，改成 block 消除 */
#report > div, #report > div > div {{
    padding-top: 0 !important;
    margin-top: 0 !important;
}}
#report .prose .md {{
    display: block !important;
    padding-top: 0 !important;
    margin-top: 0 !important;
}}
#report .prose > :first-child, #report .prose .md > :first-child {{
    margin-top: 0 !important;
}}
#report > .html-container, #report .prose {{ background: #ffffff !important; }}
#report .prose h1 {{
    font-size: 18px !important;
    font-weight: 700 !important;
    border-bottom: 1px solid #d0d7de;
    padding-bottom: 8px !important;
    margin-top: 0 !important;
}}
#report .prose h2 {{ font-size: 15px !important; font-weight: 700 !important; margin-top: 20px !important; }}
#report .prose hr {{ border: none !important; border-top: 1px solid #eaeef2 !important; }}
#report .prose code {{
    font-family: {MONO_STACK} !important;
    font-size: 12.5px !important;
    background: #f6f8fa !important;
    border: 1px solid #eaeef2 !important;
    border-radius: 4px !important;
    padding: 1px 5px !important;
    color: #24292f !important;
}}
#report .prose pre {{
    background: #f6f8fa !important;
    border: 1px solid #eaeef2 !important;
    border-radius: 6px !important;
}}
#report .prose pre code {{
    border: none !important; background: transparent !important; padding: 0 !important;
}}
#report .prose ul {{ padding-inline-start: 22px !important; }}
#report .prose li {{ margin-bottom: 4px !important; }}

/* ===== 报告中的严重程度徽章 ===== */
.sev {{
    font-family: {MONO_STACK};
    font-size: 11px;
    padding: 1px 7px;
    border-radius: 10px;
    border: 1px solid;
    margin-right: 3px;
    white-space: nowrap;
}}
.sev-critical {{ color: #cf222e; border-color: rgba(207, 34, 46, 0.35); background: rgba(207, 34, 46, 0.07); }}
.sev-major    {{ color: #9a6700; border-color: rgba(154, 103, 0, 0.35); background: rgba(154, 103, 0, 0.08); }}
.sev-minor    {{ color: #57606a; border-color: #d0d7de; background: #f6f8fa; }}

/* ===== 状态徽章 ===== */
.status {{
    font-family: {MONO_STACK};
    font-size: 11px; letter-spacing: 0.05em;
    padding: 2px 9px;
    border-radius: 10px;
    border: 1px solid;
    white-space: nowrap;
}}
.status-idle {{ color: #57606a; border-color: #d0d7de; background: #f6f8fa; }}
.status-ok   {{ color: #1a7f37; border-color: rgba(26, 127, 55, 0.35); background: rgba(26, 127, 55, 0.08); }}
.status-err  {{ color: #cf222e; border-color: rgba(207, 34, 46, 0.35); background: rgba(207, 34, 46, 0.07); }}
"""


def _status(text: str, kind: str) -> str:
    """生成状态徽章的 HTML。kind: idle / ok / err"""
    return f'<span class="status status-{kind}">{text}</span>'


# 报告里的 [Critical] / [Major] / [Minor] 转成分级徽章，比纯文本更容易扫读
SEVERITY_PATTERN = re.compile(r"\[(Critical|Major|Minor)\]")


def _decorate_report(report: str) -> str:
    """把严重程度标记替换成彩色徽章（需要 gr.Markdown(sanitize_html=False)）。"""
    return SEVERITY_PATTERN.sub(
        lambda m: f'<span class="sev sev-{m.group(1).lower()}">{m.group(1)}</span>',
        report,
    )


def _report_head(status_html: str) -> str:
    """右栏面板标题栏（含状态徽章），审查状态变化时整体刷新。"""
    return f"""
    <div class="panel-head">
        <span class="file-dot report"></span>
        <span class="file-name">report.md</span>
        <span class="spacer"></span>
        {status_html}
    </div>
    """


def _file_head(lang_display: str) -> str:
    """左栏面板标题栏：随语言选择切换文件名、语言标签和图标颜色。"""
    key, file_name, color = LANGUAGES.get(lang_display, ("python", "input.py", "#3572a5"))
    return f"""
    <div class="panel-head">
        <span class="file-dot" style="background: {color};"></span>
        <span class="file-name">{file_name}</span>
        <span class="spacer"></span>
        <span class="lang-tag">{key.upper()}</span>
    </div>
    """


def on_language_change(lang_display: str):
    """切换语言：更新编辑器高亮语言和左栏标题栏。"""
    key, _, _ = LANGUAGES.get(lang_display, ("python", "input.py", None))
    return gr.update(language=key), _file_head(lang_display)


def review_code(code: str, lang_display: str):
    """Gradio 回调：审查代码，返回 (报告, 面板头HTML)。"""
    lang_display = lang_display or "Python"
    key, file_name, _ = LANGUAGES.get(lang_display, ("python", "input.py", None))
    if not code or not code.strip():
        return f"请先在左侧粘贴 {lang_display} 代码，再点击「运行审查」。", _report_head(_status("EMPTY", "err"))
    try:
        report = review_source(code, name=file_name, language=key)
        # 后端的错误提示带了 emoji，这里统一清掉，保持界面克制
        report = report.replace("❌ ", "").replace("⚠️ ", "")
        return _decorate_report(report), _report_head(_status("DONE · " + time.strftime("%H:%M:%S"), "ok"))
    except Exception as e:
        return f"审查出错：{e}", _report_head(_status("ERROR", "err"))


def reset_view():
    """清空代码时，同时把报告和状态恢复到初始样子。"""
    return REPORT_PLACEHOLDER, _report_head(_status("READY", "idle"))


with gr.Blocks(
    title="code-review-agent",
    # 注：Gradio 5.x 会提示 theme/css 参数将在 6.0 迁移到 launch()，
    # 这里按 5.x 的写法保留，等升级到 Gradio 6 时再改。
    theme=gr.themes.Base(
        primary_hue=gr.themes.colors.green,
        neutral_hue=gr.themes.colors.slate,
    ),
    css=CUSTOM_CSS,
) as demo:
    # ---- 顶栏：像编辑器的标题栏，左对齐，不做居中大标题 ----
    with gr.Column(elem_id="app-header"):
        gr.HTML(
            """
            <div class="hdr">
                <div class="hdr-left">
                    <div class="logo-mark">&lt;/&gt;</div>
                    <span class="hdr-title">code-review-agent</span>
                    <span class="hdr-sub">多语言代码审查</span>
                </div>
            </div>
            """
        )

    # ---- 双栏：左编辑器、右报告 ----
    with gr.Row(equal_height=True, elem_id="main-panels"):
        with gr.Column(scale=1, min_width=420, elem_id="panel-left"):
            # 左栏标题栏：随语言选择动态刷新（文件名 / 语言标签 / 图标颜色）
            file_head = gr.HTML(_file_head("Python"), elem_id="file-head")
            code_input = gr.Code(
                value="",
                language="python",
                lines=26,
                label="input.py",
                show_label=False,
                elem_id="code-input",
            )
            with gr.Row(elem_classes="action-row"):
                lang_dd = gr.Dropdown(
                    choices=list(LANGUAGES),
                    value="Python",
                    label="语言",
                    elem_id="lang-dd",
                    scale=0,
                )
                clear_btn = gr.Button("清空", elem_id="btn-clear")
            with gr.Row(elem_classes="action-row run-row"):
                review_btn = gr.Button("运行审查", variant="primary", elem_id="btn-run")

        with gr.Column(scale=1, min_width=420, elem_id="panel-right"):
            report_head = gr.HTML(_report_head(_status("READY", "idle")), elem_id="report-head")
            report_output = gr.Markdown(REPORT_PLACEHOLDER, elem_id="report", sanitize_html=False)

    # ---- 交互 ----
    review_btn.click(
        fn=review_code,
        inputs=[code_input, lang_dd],
        outputs=[report_output, report_head],
    )
    clear_btn.click(fn=reset_view, inputs=None, outputs=[report_output, report_head])
    lang_dd.change(
        fn=on_language_change,
        inputs=lang_dd,
        outputs=[code_input, file_head],
    )


if __name__ == "__main__":
    demo.queue().launch()
