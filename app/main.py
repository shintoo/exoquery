import json
from io import StringIO
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import PlainTextResponse
from astroquery.ipac.nexsci.nasa_exoplanet_archive import NasaExoplanetArchive

from .embed.planetary_systems_columns_embedding import PlanetarySystemsColumnsEmbedding
from .query import generate_archive_query, prompt

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
    archive_query = generate_archive_query(query, index)
    result = NasaExoplanetArchive.query_criteria(table="ps", format="csv", **archive_query)
    obuf = StringIO()
    result.write(obuf, format="ascii.csv", overwrite=True) # TODO convert csv to json? not supported by Astroquery ootb

    summary = "Found planets" # TODO WIP using db query and column descriptions to generate summary
    result_csv = obuf.getvalue()

    lines = result_csv.strip().split("\n")
    fields = [line.split(",") for line in lines]

    columns = fields[0]
    planets = fields[1:]

    hostname_count = len(set(field[1] for field in planets))

    response = {
        "columns": columns,
        "planets": planets,
        "summary": summary,
        "planet_count": len(planets),
        "hostname_count": hostname_count
    }

    return response
