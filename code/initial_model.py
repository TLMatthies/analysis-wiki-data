import igraph as ig
import leidenalg as la
import duckdb as dd
import pandas as pd

con = dd.connect()
rel = con.sql("""
    SELECT prev, curr, n AS weight
    FROM '../Click-analysis/clickstream-enwiki-2025-10.parquet'
    WHERE type != 'external'
    """)
print(f"Completed query. Rows: \n{rel.count('prev')}")

cols = rel.fetchnumpy()
con.close()
print(f"Converted to numpy cols")

edges = zip(cols["prev"], cols["curr"], cols["weight"])
print("Extracted edges")
g = ig.Graph.TupleList(edges, directed=True, weights=True)
print("Graph created")

print("Starting model training")
res = 0.03
partition = la.find_partition(
    g, 
    la.RBConfigurationVertexPartition, 
    weights="weight", 
    resolution_parameter=res
)
print("Finished model")

# --- Map each page title to its community id and persist as Parquet ---
memberships = partition.membership
titles = g.vs["name"]
membership_df = pd.DataFrame({
    "title": titles,
    "group": memberships
})
file_string = f"page_groups_{f"{res:.20f}".partition(".")[2].rstrip("0")}_other.parquet"
membership_df.to_parquet(file_string, index=False)
print(f"Wrote page -> group mapping to {file_string}")

# --- Get communities as lists of original node names ---
communities = [[g.vs[v]["name"] for v in cluster] for cluster in partition]
print(f"# of communities: {len(communities)}")
print(f"Resolution parameter: {res}")
#print(communities)
