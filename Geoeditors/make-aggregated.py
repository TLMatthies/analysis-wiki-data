import duckdb as dd
import pandas as pd
import os
import glob

# Files are in format:
# geoeditors-monthly-{year}-{month-number}.tsv

con = dd.connect()

tsv_dir = os.path.join(".", "*.tsv")
tsv_files = glob.glob(tsv_dir)

main_df = con.execute(
"""
SELECT
    NULL::varchar AS wiki_db,
    NULL::varchar AS country,
    NULL::boolean AS high_activity,
    NULL::int64 AS lower_editor_bound,
    NULL::int64 AS upper_editor_bound,
    NULL::int32 AS year,
    NULL::int32 AS month,
WHERE FALSE
""").df()

for file in tsv_files:
    file_name = os.path.splitext(os.path.basename(file))[0]
    year, month = file_name.split('-')[2:4]
    

    df_to_add = con.execute(
        f"""
        SELECT 
            column0 AS wiki_db, 
            column1 AS country,
            column2 = '100 or more' AS high_activity,
            column3 AS lower_editor_bound,
            column4 AS upper_editor_bound,
            {year} AS year, 
            {month} AS month
        FROM read_csv('{file}', sep = '\t')
        """
    ).df()

    main_df = pd.concat([main_df, df_to_add], ignore_index=True)

con.sql("COPY main_df TO geoeditors_aggregate.parquet (FORMAT parquet)")