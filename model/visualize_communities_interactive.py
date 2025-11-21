"""Build an interactive community graph HTML using the 0.03 other resolution groups."""
from __future__ import annotations

import duckdb as dd
import pandas as pd
from pyvis.network import Network


CLICKSTREAM_PATH = "Click-analysis/clickstream-enwiki-2025-10.parquet"
GROUPS_PATH = "model/page_groups_03_other.parquet"
GROUP_NAMES_PATH = "model/page_groups_03_other_names.parquet"
TOP_COMMUNITIES = 50  # limit for readability
OUTPUT_HTML = "community_graph_03_other.html"


def build_graph() -> None:
    # Load page -> community assignments and community names
    groups = pd.read_parquet(GROUPS_PATH)
    names = pd.read_parquet(GROUP_NAMES_PATH)

    communities = groups.groupby("group").size().reset_index(name="size")
    communities = communities.nlargest(TOP_COMMUNITIES, "size")
    keep = set(communities["group"])

    con = dd.connect()
    con.register("groups", groups)
    edges = con.execute(
        f"""
        SELECT gp.group AS src, gc.group AS dst, SUM(cs.n) AS weight
        FROM '{CLICKSTREAM_PATH}' cs
        JOIN groups gp ON cs.prev = gp.title
        JOIN groups gc ON cs.curr = gc.title
        WHERE cs.type = 'link'
        GROUP BY 1, 2
        """
    ).df()
    con.close()

    edges = edges[edges["src"].isin(keep) & edges["dst"].isin(keep)]

    communities = communities.merge(names, on="group", how="left")
    communities["label"] = communities["name"].fillna(
        communities["group"].apply(lambda g: f"group {g}")
    )

    net = Network(
        height="900px",
        width="100%",
        bgcolor="#0f172a",
        font_color="#e2e8f0",
        directed=True,
    )
    net.force_atlas_2based(
        gravity=-40,
        central_gravity=0.005,
        spring_length=100,
        spring_strength=0.08,
        damping=0.5,
        overlap=0.6,
    )

    for _, row in communities.iterrows():
        group_id = int(row["group"])
        size = int(row["size"])
        label = str(row["label"])
        net.add_node(
            group_id,
            label=label,
            title=f"group {group_id}<br>size: {size:,}",
            value=size,
        )

    for _, row in edges.iterrows():
        weight = float(row["weight"])
        line_width = max(1.0, min(10.0, weight ** 0.25))
        net.add_edge(
            int(row["src"]),
            int(row["dst"]),
            value=weight,
            width=line_width,
            title=f"weight: {weight:,.0f}",
        )

    net.show_buttons(filter_=["physics"])
    net.write_html(OUTPUT_HTML)
    print(f"Wrote {OUTPUT_HTML}")


if __name__ == "__main__":
    build_graph()
