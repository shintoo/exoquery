import faiss
import pickle
import torch
from sentence_transformers import SentenceTransformer

MODEL = "Qwen/Qwen3-Embedding-0.6B"

class PlanetarySystemsColumnsEmbedding:
    def __init__(self, schema_path: str): 
        self.model = SentenceTransformer(
            MODEL,
            trust_remote_code=True,
            model_kwargs={'torch_dtype': torch.bfloat16}
        )

        self.index = None
        self.schema_path = schema_path
        self.column_embeddings = None
        
        with open(schema_path) as f:
            self.columns = [l.strip() for l in f.readlines()]

    def create_column_embeddings(self):
        self.column_embeddings = self.model.encode(self.columns)

        return self.column_embeddings

    def create_index(self):
        self.column_embeddings = self.model.encode(self.columns)
        self.index = faiss.IndexFlatL2(self.column_embeddings.shape[1])
        self.index.add(self.column_embeddings)

        return self.index
    
    def save_to_file(self, index_path: str):
        with open(index_path, "wb") as f:
            pickle.dump((self.columns, self.schema_path, self.index), f)

    @classmethod
    def load_from_file(cls, index_path: str):
        with open(index_path, "rb") as f:
            columns, schema_path, index = pickle.load(f)

        idx = cls(schema_path)
        idx.columns, idx.schema_path, idx.index = columns, schema_path, index
        return idx

    def enhance_query(self, query):
        query = query.lower()
      
        with open("assets/telescopes") as f:
            telescopes = f.readlines()

        for telescope in telescopes:
            if telescope.lower() + " telescope" not in query:
                query = query.replace(telescope.lower(), query + " telescope")

        return query

    def query(self, query, top_k=7):
        query = self.enhance_query(query)
        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(query_embedding, top_k)

        return {"search_results": {"distances": distances, "indices": indices}, "columns": [self.columns[i] for i in indices[0]]}


    def format_column(self, column: str):
        commas = column.split(",")
        name = commas[0]
        desc = commas[1]
        longdesc = ", ".join(commas[2:])
        return f"Column: {name}. Description: {desc} - {longdesc}."


def test(query):
    print("Loading schema.", flush=True)
    index = PlanetarySystemsColumnsEmbedding("assets/nexsci_ps_columns.csv")
    print("Loaded schema.\nCreating index.", flush=True)
    index.create_index()
    print(f"Created index. Querying ({query=})...", flush=True)
    results = index.query(query)
    print("Query results:")

    search_results = results['search_results']
    columns = results['columns']

    for i in range(len(columns)):
        distance = search_results['distances'][i]
        column = columns[i]
        print(f"   {distance:.3f}: {column}")

def create_and_save_schema_to_index(schema_path, index_filepath):
    print(f"Loading schema {schema_path}.", flush=True)
    index = PlanetarySystemsColumnsEmbedding(schema_path)
    print(f"Loaded schema.\nCreating index.", flush=True)
    index.create_index()
    print(f"Created index. Saving to {index_filepath}")
    index.save_to_file(index_filepath)
    print("Done.")
   

def test_load(index_filepath):
    print(f"Loading embedding from {index_filepath}...")
    index = PlanetarySystemsColumnsEmbedding.load_from_file(index_filepath)
    print(f"Done.")
          
    return index

if __name__ == "__main__":
    import sys
    schema_path = "assets/nexsci_ps_columns.csv"
    index_filepath = "assets/nexsci_ps_columns.db"

    if "save" in sys.argv:
        create_and_save_schema_to_index(schema_path, index_filepath)
        quit()
    index = test_load(index_filepath)
    results = index.query(sys.argv[1])

    print("Query results:")

    search_results = results['search_results']
    columns = results['columns']

    print("\\n".join(columns).replace("\"", "'"))
    quit()

    for i in range(len(columns)):
        column = columns[i]
        distance = search_results['distances'][0][i]
        print(index.format_column(column))
        #print(f"\t{distance:.3f}: {column}")
