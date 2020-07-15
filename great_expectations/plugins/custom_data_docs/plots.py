import json
import subprocess
import altair as alt
import pandas as pd

import great_expectations as ge


# TODO sort by suites
# TODO sort by time

results = {
    "suite_1": {
        "20200101": {
            "evaluated_expectations": 8,
            "successful_expectations": 0,
            "unsuccessful_expectations": 8,
            "success_percent": 0.0,
        },
        "20200102": {
            "evaluated_expectations": 8,
            "successful_expectations": 0,
            "unsuccessful_expectations": 8,
            "success_percent": 0.0,
        },
    },
    "suite_2": {
        "20200101": {
            "evaluated_expectations": 8,
            "successful_expectations": 0,
            "unsuccessful_expectations": 8,
            "success_percent": 0.0,
        },
        "20200102": {
            "evaluated_expectations": 8,
            "successful_expectations": 0,
            "unsuccessful_expectations": 8,
            "success_percent": 0.0,
        },
    },
}

def unpack_results_by_suite(validation_store):
    keys = validation_store.list_keys()
    print(f"Processing {len(keys)} keys...")
    results = {}
    for key in keys:
        try:
            result = validation_store.get(key)
            meta = result.meta
            suite_name = meta.get("expectation_suite_name", None)
            run_time = meta["run_id"].get("run_time", None)
            print(f"{run_time} - {suite_name}:")
            if suite_name not in results.keys():
                results[suite_name] = {}

            stats = result.statistics
            if run_time and stats:
                results[suite_name][run_time] = stats["success_percent"]
                results[suite_name][run_time] = stats["success_percent"]
        except (FileNotFoundError, ge.exceptions.InvalidKeyError) as fe:
            print(f"Skipping {key} - not found")

    return results


def plot_for_single_suite(suite_name, results, open=True):
    source = pd.DataFrame(
        {
            "timestamp": [k for k, v in results[suite_name].items()],
            "success_percent": [v for k, v in results[suite_name].items()],
        }
    )

    chart = (
        alt.Chart(source)
        .mark_line()
        .encode(
            x="timestamp",
            y="success_percent",
            # category="",
            tooltip=["timestamp", "success_percent"],
        )
        .properties(width=500, height=400, autosize="fit")
    )

    html_file = "chart.html"
    chart.save(html_file)
    if open:
        subprocess.call(["open", html_file])

# timestamp, suite name, metric


def unpack_results_by_time(validation_store) -> pd.DataFrame:
    keys = validation_store.list_keys()
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
    return pd.DataFrame(rows)

results = {
    "20200101": {
        "suite_1": {"success_percent": 0.0},
        "suite_2": {"success_percent": 0.5},
    }
}


def create_chart(df: pd.DataFrame):
    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x="timestamp",
            y="success_percent",
            color="suite_name:N",
            tooltip=["timestamp", "suite_name", "success_percent"],

        )
        .properties(width=1000, height=1000, autosize="fit")
    )
    return chart


if __name__ == "__main__":
    context = ge.data_context.DataContext()
    validation_store = context.validations_store
    # results = unpack_results_by_suite(validation_store)
    # plot_for_single_suite("drugs", results, open=True)

    results = unpack_results_by_time(validation_store)
    print(results)
    chart = create_chart(results)
    html_file = "chart.html"
    chart.save(html_file)
    if open:
        subprocess.call(["open", html_file])

