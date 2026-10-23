# app/agent/prompts/prompt.py
from pathlib import Path

import yaml
from jinja2 import Template

PROMPT_BASE_DIR = Path(__file__).resolve().parent.parent / "resources" / "prompts"


def load_prompt_template(name: str, /, **kwargs) -> str:
    """读取 resources/prompts/<name>.yaml 并渲染成字符串。

    yaml 的第一层 key 就是模板名（原来是写死的 "enterprise_inquiry"，
    导致传别的 name 时读到的是错的模板）。

    `name` 被标记为 positional-only，这样模板里如果有 `{{ name }}` 变量，
    可以用 load_prompt_template("greet", name="世界") 正常传入而不会撞名。
    """
    path = PROMPT_BASE_DIR / f"{name}.yaml"
    if not path.is_file():
        # PROMPT_BASE_DIR.glob("*.yaml") → 找出目录下所有 .yaml 文件
        # p.stem → 取文件名去掉扩展名
        available = sorted(p.stem for p in PROMPT_BASE_DIR.glob("*.yaml"))
        raise FileNotFoundError(
            f"提示词模板文件不存在：{path}（可用模板：{available}）"
        )

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if name not in data:
        raise KeyError(
            f"{path} 中没有名为 {name!r} 的模板，实际可用：{list(data)}"
        )

    return Template(data[name]).render(**kwargs)
