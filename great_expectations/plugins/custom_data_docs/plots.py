#!/usr/bin/env python

import subprocess
import altair as alt
import pandas as pd

import great_expectations as ge


def get_validation_results_metrics_dataframe(validation_store) -> pd.DataFrame:
    keys = validation_store.list_keys()
    if len(keys) == 0:
        raise ValueError("No keys found")
    print(f"Processing {len(keys)} keys...")
    rows = []
    for key in keys:
        try:
            result = validation_store.get(key)
            meta = result.meta
            run_time = meta["run_id"]["run_time"]
            suite_name = meta.get("expectation_suite_name", None)
            print(f"{run_time} - {suite_name}:")

            stats = result.statistics
            if run_time and stats:
                rows.append(
                    {
                        "timestamp": run_time,
                        "suite_name": suite_name,
                        "success_percent": stats["success_percent"],
                    }
                )
        except (FileNotFoundError, ge.exceptions.InvalidKeyError) as fe:
            print(f"Skipping {key} - not found")
    df = pd.DataFrame(rows)
    df.columns = ["timestamp", "suite_name", "success_percent"]
    print(df.columns)

    return df.sort_values(by="timestamp", axis="index")


def create_chart(df: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x="timestamp:T",
            y="success_percent:Q",
            color="suite_name:N",
            tooltip=["timestamp", "suite_name", "success_percent"],
        )
        .properties(width=1000, height=1000, autosize="fit")
    )


def save_chart(chart, open_chart):
    html_file = "chart.html"
    chart.save(html_file)
    if open_chart:
        subprocess.call(["open", html_file])


if __name__ == "__main__":
    context = ge.data_context.DataContext()
    validation_store = context.validations_store
    results = get_validation_results_metrics_dataframe(validation_store)
    print(results)

    chart = create_chart(results)
    save_chart(chart, open_chart=True)
