import json

from astroquery.ipac.nexsci.nasa_exoplanet_archive import NasaExoplanetArchive

from query import generate_archive_query

def run_interactive():
    query = input("What would you like to know about exoplanets?\n> ")
    archive_query = generate_archive_query(query)
    if __debug__: print(f"Archive query:\n{json.dumps(archive_query, indent=4)}")
    result = NasaExoplanetArchive.query_criteria(table="ps", **archive_query)
    print(result)

if __name__ == "__main__": 
    run_interactive()
