from datetime import datetime
import json

from ollama import chat, ChatResponse
from jinja2 import Environment, FileSystemLoader

from .embed.planetary_systems_columns_embedding import PlanetarySystemsColumnsEmbedding

env = Environment(loader=FileSystemLoader("assets/prompts"))
MODEL = 'hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:UD-Q4_K_XL'


def generate_column_search(user_query):
    prompt_template = env.get_template("generate_column_query.prompt.j2")
    return prompt_template.render({"USER_QUERY": user_query})

def generate_astroquery_search(user_query, columns_string):
    prompt_template = env.get_template("generate_astroquery.prompt.j2")

    date = str(datetime.now()).split(" ")[0]

    prompt_data = {"USER_QUERY": user_query, "RELEVANT_COLUMNS": columns_string, "CURRENT_DATE": date}
    return prompt_template.render(prompt_data)

def retrieve_columns(column_search, index):
    columns = []

    for query in column_search["column_requests"]:
        results = index.query(query, top_k=2)
        columns.extend(results['columns'])

    return columns

def prompt(prompt):
    messages = [{"role": "user", "content": prompt}]
    response = chat(model=MODEL, messages=messages)
    return response.message.content

def run_interactive():
    index = PlanetarySystemsColumnsEmbedding.load_from_file("assets/nexsci_ps_columns.db")
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
    relevant_columns = retrieve_columns(column_search, index)
    print(f"\n========RETRIEVED COLUMNS====")
    print(relevant_columns)
    print("=============================\n")
    # 4. Generate astroquery search
    astroquery_search = prompt(generate_astroquery_search(user_query, relevant_columns))
    print(f"\n========ASTROQUERY SEARCH====")
    print(astroquery_search)
    print("=============================\n")

def generate_archive_query(query) -> dict:
    # 0. Load column embeddings
    if __debug__: print("Loading column embeddings...", end='', flush=True)
    try:
        index = PlanetarySystemsColumnsEmbedding.load_from_file("assets/nexsci_ps_columns.db")
    except Exception as e:
        print(f"Failed to load embeddings database from assets/nexsci_ps_columns.db. Generate it with `python embed/planetary_systems_columns_embeddings.py save`. error: {e}.")
        raise e
    if __debug__: print("Done.", flush=True)

    # Generate prompt for column search
    column_search_prompt = generate_column_search(query)

    # Retrieve genenerated column search query
    if __debug__: print("Prompting LLM for column search queries...", end='', flush=True)
    column_search_string = prompt(column_search_prompt)
    if __debug__: print("Done.", flush=True)

    # Clean up generation string
    column_search_string = column_search_string.replace("```json", "")
    column_search_string = column_search_string.replace("```", "")

    # Load generation from json
    column_search_query = json.loads(column_search_string)

    # Query column embedding using generated column search query
    if __debug__: print("Querying column embedding database for relevant columns...", end='', flush=True)
    relevant_columns = retrieve_columns(column_search_query, index)
    if __debug__: print("Done.", flush=True)

    # Generate prompt using retrieved columns and original query
    astroquery_search_prompt = generate_astroquery_search(query, relevant_columns)

    # Generate astroquery search
    if __debug__: print("Prompting LLM for astroquery search query...", end='', flush=True)
    astroquery_search = prompt(astroquery_search_prompt)
    if __debug__: print("Done.", flush=True)

    # Load from json string
    archive_query = json.loads(astroquery_search)

    # Ensure pl_name is queried
    if "pl_name" not in archive_query["select"]:
        archive_query["select"] = "pl_name, " + archive_query["select"]

    # Final checks and improvements
    archive_query = enhance_query(archive_query)

    print(f"ARCHIVE_QUERY: {archive_query}")
    return archive_query


def enhance_query(archive_query):
    # Ensure we only query for the default parameter set for each planet
    if "where" not in archive_query:
        archive_query["where"] = "default_flag = 1"
    elif "default_flag" not in archive_query["where"]:
        if len(archive_query["where"]) > 0:
            archive_query["where"] += " AND "

        archive_query["where"] += "default_flag = 1"

    # If pl_radj or pl_rade is included, include the other.
    if "pl_radj" in archive_query["select"]:
        archive_query["select"] = archive_query["select"].replace("pl_radj", "pl_rade, pl_radj")
    elif "pl_rade" in archive_query["select"]:
        archive_query["select"] = archive_query["select"].replace("pl_rade", "pl_rade, pl_radj")

    # Same for pl_massj/pl_masse.
    if "pl_massj" in archive_query["select"]:
        archive_query["select"] = archive_query["select"].replace("pl_massj", "pl_masse, pl_massj")
    elif "pl_masse" in archive_query["select"]:
        archive_query["select"] = archive_query["select"].replace("pl_masse", "pl_masse, pl_massj")

    return archive_query


def test_queries_from_file(queries_filename, target_filename):
    with open(queries_filename, "r") as f:
        queries = [l.strip() for l in f.readlines()]

    records = {}

    total = len(queries)
    current = 1
    print("Processing ", end='', flush=True)

    for q in queries:
        print(f"{current} ", end='', flush=True)
        result = generate_archive_query(q)
        records[q] = result
        current += 1

    print()

    with open(target_filename, "w") as f:
        json.dump(records, f, indent=4)



if __name__ == "__main__":
    import sys
    queries_file = sys.argv[1]
    results_file = "".join(queries_file.split(".")[:-1]) + "_results.json"
    print(f"Testing queries from ({queries_file})")
    test_queries_from_file(queries_file, results_file)
    print(f"Results written to ({results_file})")
