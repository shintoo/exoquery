from datetime import datetime
import json
from .prompt import prompt_from_template, prompt_dict_from_template

from .embed.planetary_systems_columns_embedding import PlanetarySystemsColumnsEmbedding

MODEL = 'hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:UD-Q4_K_XL'


def retrieve_columns(column_search: dict, index: PlanetarySystemsColumnsEmbedding):
    columns = []

    for query in column_search["column_requests"]:
        results = index.query(query, top_k=2)
        columns.extend(results['columns'])

    return columns


def generate_archive_query(query: str, index: PlanetarySystemsColumnsEmbedding) -> dict:
    # Retrieve genenerated column search query
    if __debug__: print("Prompting LLM for column search queries...", end='', flush=True)
    column_search = prompt_dict_from_template("generate_column_query.prompt.j2", {"USER_QUERY": query})
    if __debug__: print("Done.", flush=True)

    # Query column embedding using generated column search query
    if __debug__: print("Querying column embedding database for relevant columns...", end='', flush=True)
    relevant_columns = retrieve_columns(column_search, index)
    if __debug__: print("Done.", flush=True)

    # Generate astroquery search
    if __debug__: print("Prompting LLM for astroquery search query...", end='', flush=True)
    archive_query = prompt_dict_from_template("generate_astroquery.prompt.j2", {
        "USER_QUERY": query,
        "RELEVANT_COLUMNS": relevant_columns,
        "CURRENT_DATE": datetime.now().strftime("%Y-%m-%d")
    })
    if __debug__: print("Done.", flush=True)

    # Final checks and improvements
    archive_query = enhance_query(archive_query)

    columns = [col.strip() for col in archive_query["select"].split(",")]

    if __debug__: print(f"Final archive query: {archive_query}")
    return archive_query, columns


def enhance_query(archive_query):
    # Ensure pl_hostname is queried
    if "hostname" not in archive_query["select"]:
        if "pl_name" in archive_query["select"]:
            archive_query["select"] = archive_query["select"].replace("pl_name", "pl_name, hostname")
        else:
            archive_query["select"] = "hostname, " + archive_query["select"]

    # Ensure pl_name is queried
    if "pl_name" not in archive_query["select"]:
        archive_query["select"] = "pl_name, " + archive_query["select"]
    if "where" not in archive_query:
        archive_query["where"] = "default_flag = 1"


    # Ensure we only query for the default parameter set for each planet
    # TODO should we be using pscomppars instead? need to rerun vec embed
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
