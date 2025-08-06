import json
from io import StringIO
import os

from astroquery.ipac.nexsci.nasa_exoplanet_archive import NasaExoplanetArchive
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import PlainTextResponse
from jinja2 import Environment, FileSystemLoader

from .embed.planetary_systems_columns_embedding import PlanetarySystemsColumnsEmbedding
from .query import generate_archive_query, prompt, env

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

index = PlanetarySystemsColumnsEmbedding.load_from_file("app/assets/nexsci_ps_columns.db")

@app.get("/api/query")
async def run_query(s):
    query = s
    archive_query, columns = generate_archive_query(query, index)
    column_descriptions = [index.get_description(c) for c in columns]
    print(f"COLUMNS (should be a list of the actual names): {columns=}")

    result = NasaExoplanetArchive.query_criteria(table="ps", format="csv", **archive_query)
    obuf = StringIO()
    result.write(obuf, format="ascii.csv", overwrite=True) # TODO convert csv to json? not supported by Astroquery ootb

    summary = "Found planets" # TODO WIP using db query and column descriptions to generate summary

    query_summary_prompt_template = env.get_template("generate_query_summary.prompt.j2")
    query_summary_prompt = query_summary_prompt_template.render({
        "DATABASE_QUERY": archive_query,
        "COLUMN_DESCRIPTIONS": [f"{columns[i]}: {column_descriptions[i]}" for i in range(len(columns))]
    })
    summary_json = prompt(query_summary_prompt)

    try:
        summary = json.loads(summary_json)["translation"]
    except Exception as e:
        print(f"Error generating query summary: {e}")
        summary = "Found {planet_count} planets."

    result_csv = obuf.getvalue()

    lines = result_csv.strip().split("\n")
    fields = [line.split(",") for line in lines]

    columns = fields[0]
    planets = fields[1:]
    planet_count = len(planets)
    summary = summary.replace("Found planets", f"Found {planet_count} planets")

    hostname_count = len(set(field[1] for field in planets))

    response = {
        "columns": columns,
        "column_descriptions": [index.get_description(c).split(":")[0] for c in columns],
        "planets": planets,
        "summary": summary,
        "planet_count": planet_count,
        "hostname_count": hostname_count
    }

    return response
