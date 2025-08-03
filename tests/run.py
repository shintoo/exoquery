from jinja2 import Environment, FileSystemLoader
import json
from ollama import chat, ChatResponse
from embed.planetary_systems_columns_embedding import PlanetarySystemsColumnsEmbedding

env = Environment(loader=FileSystemLoader("tests/"))

def generate_column_search(user_query):
    prompt_template = env.get_template("generate_column_query.prompt.j2")
    return prompt_template.render({"USER_QUERY": user_query})

def generate_astroquery_search(user_query, columns_string):
    prompt_template = env.get_template("generate_astroquery.prompt.j2")

    prompt_data = {"USER_QUERY": user_query, "RELEVANT_COLUMNS": columns_string}
    return prompt_template.render(prompt_data)

def retrieve_columns(column_search):
    columns = []
    index = PlanetarySystemsColumnsEmbedding.load_from_file("assets/nexsci_ps_columns.faiss")
    for query in column_search["column_requests"]:
        results = index.query(query, top_k=2)
        print(f"{query=}:{results=}")
        columns.extend(results['columns'])

    return columns


def prompt(prompt):
    messages = [{"role": "user", "content": prompt}]

    response = chat(model='hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:UD-Q4_K_XL', messages=messages)

    return response.message.content

def run():
    # 1. Receive user query
    user_query = input("query> ")
    # 2. Retrieve column search query
    column_search_string = prompt(generate_column_search(user_query))
    column_search_string = column_search_string.replace("```json", "") 
    column_search_string = column_search_string.replace("```", "") 
    print(f"{column_search_string=}")
    column_search = json.loads(column_search_string)
    print(f"\n========COLUMN SEARCH========")
    print(column_search)
    print("=============================\n")
    # 3. Perform column search
    relevant_columns = retrieve_columns(column_search)
    print(f"\n========RETRIEVED COLUMNS====")
    print(relevant_columns)
    print("=============================\n")
    # 4. Generate astroquery search
    astroquery_search = prompt(generate_astroquery_search(user_query, relevant_columns))
    print(f"\n========ASTROQUERY SEARCH====")
    print(astroquery_search)
    print("=============================\n")

if __name__ == "__main__":
    run()
