from io import StringIO
import pandas as pd
from pathlib import Path
import json


def extract_dataset(in_dir):
    input_dir = Path(in_dir)
    charts = {}

    # Loop through all Excel files
    for excel_file in input_dir.glob("Module * - Datasets for Charts.xlsx"):
        module_name = excel_file.stem.split(" -")[0].replace(" ", "")  # e.g., "Module1"

        # Load Excel file
        xls = pd.ExcelFile(excel_file)
        for sheet_name in xls.sheet_names:
            try:
                df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)

                # Drop fully empty rows and columns
                df.dropna(how='all', inplace=True)
                df.dropna(axis=1, how='all', inplace=True)
                df.reset_index(drop=True, inplace=True)

                # Assume sheet_name is or contains the Figure ID
                figure_id = sheet_name.strip()

                # Save to memory as string
                csv_content = df.to_csv(index=False, header=False).strip()
                charts[figure_id] = csv_content

            except Exception as e:
                print(f"Failed to read sheet '{sheet_name}' in '{excel_file.name}': {e}")

    return charts


def extract_metadata(in_path):
    xls = pd.ExcelFile(in_path)
    sheet_names = [name for name in xls.sheet_names if name.lower().startswith("module")]

    df_list = []
    for sheet in sheet_names:
        try:
            df = pd.read_excel(in_path, sheet_name=sheet, header=1)
            df['module'] = sheet
            df_list.append(df)
        except Exception as e:
            print(f"Error reading sheet '{sheet}': {e}")

    combined_df = pd.concat(df_list, ignore_index=True)
    return combined_df


def merge_data_metadata(metadata_df, chart_datasets, out_path):

    # Filter metadata
    filtered = metadata_df[
        (metadata_df["Category"] == "Chart to recreate") &
        (metadata_df["Status"] == "Ready") &
        (metadata_df["Apache possible?"]) &
        (metadata_df["Dataset Status"] == "Ready")
    ]

    # Merge metadata with datasets
    charts = {}
    for _, row in filtered.iterrows():
        figure_id = str(row["Figure ID"]).strip()
        dataset = chart_datasets.get(figure_id)

        chart_entry = {
            "metadata": row.drop(labels=["Apache possible?"]).to_dict(),
            "dataset": dataset if dataset else None
        }

        if dataset is None:
            print(f"❗ No dataset found for {figure_id}")

        charts[figure_id] = chart_entry

    # Replace NaNs in metadata
    for chart in charts.values():
        chart["metadata"] = {k: (None if pd.isna(v) else v) for k, v in chart["metadata"].items()}

    return charts

import pandas as pd
import json
from pathlib import Path
from io import StringIO


def read_dataset(dataset_str, chart_id):
    try:
        return pd.read_csv(StringIO(dataset_str))
    except Exception as e:
        print(f"Failed to read dataset for {chart_id}: {e}")
        return None


def load_template(template_path):
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Template not found at {template_path}")
        return None


def save_chart_config(output_dir, filename, chart_data):
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / filename
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chart_data, f, indent=2)
    print(f"Saved chart to {output_path}")


def generate_chart(chart_id, metadata, dataset_str, template_path, output_dir, prepare_data_fn, suffix):
    print(f"Generating chart for {chart_id}...")
    print(f"Title: {metadata.get('Title')}")

    df = read_dataset(dataset_str, chart_id)
    if df is None:
        return

    chart_template = load_template(template_path)
    if chart_template is None:
        return

    try:
        prepare_data_fn(chart_template, df)
    except Exception as e:
        print(f"Error preparing chart data for {chart_id}: {e}")
        return

    save_chart_config(output_dir, f"{chart_id}_{suffix}.json", chart_template)


def process_charts(charts_data, styling_data, template_folder_path, output_dir):
    for chart_id, chart_info in charts_data.items():
        metadata = chart_info.get("metadata", {})
        dataset = chart_info.get("dataset", "")
        chart_type = metadata.get("Chart Type", "").strip().lower()
        style = styling_data.get(chart_id, {})

        if chart_type == "bar chart":
            x_col = style.get("x_col_name")
            y_col = style.get("y_col_name")
            if x_col and y_col:
                template_path = Path(template_folder_path) / "bar_chart_template.json"

                def prepare_data(template, df):
                    if x_col not in df.columns or y_col not in df.columns:
                        raise ValueError(f"Missing columns: {x_col}, {y_col}")
                    template["xAxis"]["data"] = df[x_col].tolist()
                    template["series"][0]["data"] = df[y_col].tolist()

                generate_chart(chart_id, metadata, dataset, template_path, output_dir, prepare_data, "bar_chart")
            else:
                print(f"Missing styling for bar chart: {chart_id}")

        elif chart_type == "pie chart":
            name_col = style.get("name_col")
            value_col = style.get("value_col")
            if name_col and value_col:
                template_path = Path(template_folder_path) / "pie_chart_template.json"

                def prepare_data(template, df):
                    if name_col not in df.columns or value_col not in df.columns:
                        raise ValueError(f"Missing columns: {name_col}, {value_col}")
                    template["series"][0]["data"] = [
                        {"name": row[name_col], "value": row[value_col]}
                        for _, row in df.iterrows()
                    ]

                generate_chart(chart_id, metadata, dataset, template_path, output_dir, prepare_data, "pie_chart")
            else:
                print(f"Missing styling for pie chart: {chart_id}")

        elif chart_type == "bar chart categories":
            category_col = style.get("category_col")
            series_cols = style.get("series_cols")
            if category_col and series_cols:
                template_path = Path(template_folder_path) / "bar_chart_categories_template.json"

                def prepare_data(template, df):
                    if category_col not in df.columns:
                        raise ValueError(f"Missing category column: {category_col}")
                    for col in series_cols:
                        if col not in df.columns:
                            raise ValueError(f"Missing series column: {col}")
                    template["title"]["text"] = metadata.get("Title", "")
                    template["yAxis"]["data"] = df[category_col].tolist()
                    template["series"] = [
                        {"name": col, "type": "bar", "data": df[col].tolist()}
                        for col in series_cols
                    ]

                generate_chart(chart_id, metadata, dataset, template_path, output_dir, prepare_data, "category_bar_chart")
            else:
                print(f"Missing styling for bar chart categories: {chart_id}")

        else:
            print(f"Skipping {chart_id}: Unsupported chart type '{chart_type}'")
