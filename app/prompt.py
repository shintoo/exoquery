import json

from ollama import chat, ChatResponse
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("app/assets/prompts"))
MODEL = 'hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:UD-Q4_K_XL'


def prompt(prompt):
    messages = [{"role": "user", "content": prompt}]
    response = chat(model=MODEL, messages=messages)

    return response.message.content

def prompt_from_template(template, values):
    prompt_template = env.get_template(template)
    prompt_text = prompt_template.render(values)

    return prompt(prompt_text)

def prompt_dict_from_template(template, values):
    raw = prompt_from_template(template, values)
    json_string = raw[raw.find("{"):raw.rfind("}")+1]
    res = json.loads(json_string)

    return res
