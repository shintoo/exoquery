import json
from io import StringIO

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from astroquery.ipac.nexsci.nasa_exoplanet_archive import NasaExoplanetArchive

from .query import generate_archive_query

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
)

@app.get("/api/query")
async def run_query(s):
    query = s
    archive_query = generate_archive_query(query)
    result = NasaExoplanetArchive.query_criteria(table="ps", format="csv", **archive_query)
    obuf = StringIO()
    result.write(obuf, format="ascii.csv", overwrite=True)
    return PlainTextResponse(obuf.getvalue())
