import duckdb as dd
import pandas as pd
import os
import glob

# Files are in format:
# clickstream-enwiki-{year}-{month-number}.tsv

con = dd.connect()

# Needs to be individual as memory cannot handle multiple of these
# files referenced in one script
tsv_dir = os.path.join(".", "clickstream-enwiki-2024-04.tsv")
tsv_files = glob.glob(tsv_dir)

main_df = con.execute(
"""
SELECT
    NULL::varchar AS prev,
    NULL::varchar AS curr,
    NULL::boolean AS type,
    NULL::int64 AS n,
WHERE FALSE
""").df()

for file in tsv_files:
    file_name = os.path.splitext(os.path.basename(file))[0]
    year, month = file_name.split('-')[2:4]
    

    df_to_add = con.execute(
        f"""
        SELECT 
            column0 AS prev, 
            column1 AS curr,
            column2 AS type,
            column3 AS n,
            {year} AS year, 
            {month} AS month
        FROM read_csv('{file}', sep = '\t')
        """
    ).df()

    con.sql(f"COPY df_to_add TO '{file_name}.parquet' (FORMAT parquet)")