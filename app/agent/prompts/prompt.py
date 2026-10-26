"""Prompt 模板加载：从 resources/prompts/<name>.yaml 读取并用 Jinja2 渲染。"""
from pathlib import Path

import yaml
from jinja2 import Template

PROMPT_BASE_DIR = Path(__file__).resolve().parent.parent / "resources" / "prompts"


def load_prompt_template(name: str, /, **kwargs) -> str:
    """渲染 <name>.yaml 中同名模板。

    name 为 positional-only，模板内的 {{ name }} 变量可通过关键字参数传入。

    Raises:
        FileNotFoundError: 模板文件不存在。
        KeyError: 文件中没有同名模板。
    """
    path = PROMPT_BASE_DIR / f"{name}.yaml"
    if not path.is_file():
        available = sorted(p.stem for p in PROMPT_BASE_DIR.glob("*.yaml"))
        raise FileNotFoundError(f"提示词模板文件不存在：{path}（可用模板：{available}）")

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if name not in data:
        raise KeyError(f"{path} 中没有名为 {name!r} 的模板，实际可用：{list(data)}")

    return Template(data[name]).render(**kwargs)
