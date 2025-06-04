from io import StringIO
import pandas as pd
from pathlib import Path
import json
import ast


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
                df = pd.read_excel(excel_file, sheet_name=sheet_name, dtype=str)

                # Drop fully empty rows and columns
                df.dropna(how='all', inplace=True)
                df.dropna(axis=1, how='all', inplace=True)
                df.reset_index(drop=True, inplace=True)

                # Assume sheet_name is or contains the Figure ID
                figure_id = sheet_name.strip()

                # Save to memory as string
                csv_content = df.to_csv(index=False, header=True).strip()
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
            df = pd.read_excel(in_path, sheet_name=sheet, header=1, dtype=str)
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
        (metadata_df["Chart Status"] == "Ready") &
        (metadata_df["Apache Possible"] == "Yes") &
        (metadata_df["Automation Possible"] == "Yes") &
        (metadata_df["Dataset Status"] == "Ready")
    ]

    # Merge metadata with datasets
    charts = {}
    for _, row in filtered.iterrows():
        figure_id = str(row["Figure ID"]).strip()
        dataset = chart_datasets.get(figure_id)

        chart_entry = {
            "metadata": row.to_dict(),
            "dataset": dataset if dataset else None
        }

        if dataset is None:
            print(f"❗ No dataset found for {figure_id}")

        charts[figure_id] = chart_entry

    # Replace NaNs in metadata
    for chart in charts.values():
        chart["metadata"] = {k: (None if pd.isna(v) else v) for k, v in chart["metadata"].items()}

    return charts



def read_dataset(dataset_str, chart_id):
    try:
        # Prevent auto-conversion of missing indicators to NaN
        df = pd.read_csv(StringIO(dataset_str), keep_default_na=False)

        # Replace empty strings with Python None
        df = df.replace("", None)

        return df
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

def merge_templates(global_template, specific_template):
    merged = global_template.copy()

    def deep_merge(dict1, dict2):
        for key, value in dict2.items():
            if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
                deep_merge(dict1[key], value)
            else:
                dict1[key] = value

    deep_merge(merged, specific_template)
    return merged

def generate_chart(chart_id, metadata, dataset_str, template_path, output_dir, prepare_data_fn, suffix, global_template_path=None):
    print(f"Generating chart for {chart_id}...")
    print(f"Title: {metadata.get('Title')}")

    df = read_dataset(dataset_str, chart_id)
    if df is None:
        return

    specific_template = load_template(template_path)
    if specific_template is None:
        return

    if global_template_path:
        global_template = load_template(global_template_path)
        if global_template:
            chart_template = merge_templates(global_template, specific_template)
        else:
            chart_template = specific_template
    else:
        chart_template = specific_template

    try:
        prepare_data_fn(chart_template, df)
    except Exception as e:
        print(f"Error preparing chart data for {chart_id}: {e}")
        return

    save_chart_config(output_dir, f"{chart_id}_{suffix}.json", chart_template)


def common_prepare_data_wrapper(metadata, specific_prepare_fn):
    def wrapped(template, df):
        template["title"]["text"] = metadata.get("Title", "")
        template["title"]["subtext"] = metadata.get("Subtitle", "")

        # Set footnote if available
        footnote = metadata.get("Footnote", "")
        if "graphic" in template and isinstance(template["graphic"], list):
            for g in template["graphic"]:
                if g.get("type") == "text" and g["style"].get("text") == "":
                    g["style"]["text"] = footnote
                    break
        # Chart-specific logic
        specific_prepare_fn(template, df)
    return wrapped



def process_charts(charts_data, charts_config, template_folder_path, output_dir, global_template_path):
    for chart_id, chart_info in charts_data.items():
        print("---")
        metadata = chart_info.get("metadata", {})
        dataset = chart_info.get("dataset", "")
        chart_type = metadata.get("Chart Type", "").strip().lower()
        style = charts_config.get(chart_id, {})

        if chart_type == "bar chart vertical":
            x_col = style.get("X Axis")
            y_col = style.get("Y Axis")
            if x_col and y_col:
                template_path = Path(template_folder_path) / "bar_chart_vertical_template.json"

                def specific_prepare(template, df):
                    if x_col not in df.columns or y_col not in df.columns:
                        raise ValueError(f"Missing columns: {x_col}, {y_col}")
                    template["xAxis"]["data"] = df[y_col].tolist()
                    template["xAxis"]["name"] = x_col
                    template["yAxis"]["name"] = y_col
                    template["series"][0]["data"] = df[x_col].tolist()

                prepare_data = common_prepare_data_wrapper(metadata, specific_prepare)
                generate_chart(chart_id, metadata, dataset, template_path, output_dir, prepare_data, "bar_chart_vertical", global_template_path)
            else:
                print(f"Missing styling for bar chart vertical: {chart_id}")

        elif chart_type == "bar chart horizontal":
            x_col = style.get("X Axis")
            y_col = style.get("Y Axis")
            if x_col and y_col:
                template_path = Path(template_folder_path) / "bar_chart_horizontal_template.json"

                def specific_prepare(template, df):
                    if x_col not in df.columns or y_col not in df.columns:
                        raise ValueError(f"Missing columns: {x_col}, {y_col}")
                    template["yAxis"]["data"] = df[y_col].tolist()
                    template["yAxis"]["name"] = y_col
                    template["xAxis"]["name"] = x_col
                    template["series"][0]["data"] = df[x_col].tolist()
                    
                    max_label_length = max(len(str(label)) for label in df[category_col])
                    template["grid"] = template.get("grid", {})
                    template["grid"]["left"] = max(100, min(300, int(max_label_length * 7)))  # Rough estimate

                prepare_data = common_prepare_data_wrapper(metadata, specific_prepare)
                generate_chart(chart_id, metadata, dataset, template_path, output_dir, prepare_data, "bar_chart_horizontal", global_template_path)
            else:
                print(f"Missing styling for horizontal bar chart: {chart_id}")

        elif chart_type == "pie chart":
            name_col = style.get("Category")
            value_col = style.get("Value")
            if name_col and value_col:
                template_path = Path(template_folder_path) / "pie_chart_template.json"

                def specific_prepare(template, df):
                    if name_col not in df.columns or value_col not in df.columns:
                        raise ValueError(f"Missing columns: {name_col}, {value_col}")
                    template["series"][0]["data"] = [
                        {"name": row[name_col], "value": row[value_col]}
                        for _, row in df.iterrows()
                    ]

                prepare_data = common_prepare_data_wrapper(metadata, specific_prepare)
                generate_chart(chart_id, metadata, dataset, template_path, output_dir, prepare_data, "pie_chart", global_template_path)
            else:
                print(f"Missing styling for pie chart: {chart_id}")
        
        elif chart_type == "doughnut chart":
            name_col = style.get("Category")
            value_col = style.get("Value")
            if name_col and value_col:
                template_path = Path(template_folder_path) / "doughnut_chart_template.json"

                def specific_prepare(template, df):
                    if name_col not in df.columns or value_col not in df.columns:
                        raise ValueError(f"Missing columns: {name_col}, {value_col}")
                    template["series"][0]["data"] = [
                        {"name": row[name_col], "value": row[value_col]}
                        for _, row in df.iterrows()
                    ]

                prepare_data = common_prepare_data_wrapper(metadata, specific_prepare)
                generate_chart(chart_id, metadata, dataset, template_path, output_dir, prepare_data, "doughnut_chart", global_template_path)
            else:
                print(f"Missing styling for doughnut chart: {chart_id}")
        
        elif chart_type == "bar chart categories horizontal":
            category_col = style.get("Category")
            series_cols = style.get("Value Series")
            if isinstance(series_cols, str):
                series_cols = [s.strip() for s in series_cols.split(',')]

            if category_col and series_cols:
                template_path = Path(template_folder_path) / "bar_chart_categories_horizontal_template.json"

                def specific_prepare(template, df):
                    if category_col not in df.columns:
                        raise ValueError(f"Missing category column: {category_col}")
                    for col in series_cols:
                        if col not in df.columns:
                            raise ValueError(f"Missing series column: {col}")
                    template["yAxis"]["data"] = df[category_col].tolist()
                    template["yAxis"]["name"] = category_col
                    template["series"] = [
                        {"name": col, "type": "bar", "data": df[col].tolist()}
                        for col in series_cols
                    ]
                    max_label_length = max(len(str(label)) for label in df[category_col])
                    template["grid"] = template.get("grid", {})
                    template["grid"]["left"] = max(100, min(300, int(max_label_length * 7)))  # Rough estimate

                prepare_data = common_prepare_data_wrapper(metadata, specific_prepare)
                generate_chart(chart_id, metadata, dataset, template_path, output_dir, prepare_data, "category_bar_chart_horizontal", global_template_path)
            else:
                print(f"Missing styling for bar chart categories: {chart_id}")

        elif chart_type == "bar chart categories vertical":
            category_col = style.get("Category")
            series_cols = style.get("Value Series")
            if isinstance(series_cols, str):
                series_cols = [s.strip() for s in series_cols.split(',')]

            if category_col and series_cols:
                template_path = Path(template_folder_path) / "bar_chart_categories_vertical_template.json"

                def specific_prepare(template, df):
                    if category_col not in df.columns:
                        raise ValueError(f"Missing category column: {category_col}")
                    for col in series_cols:
                        if col not in df.columns:
                            raise ValueError(f"Missing series column: {col}")

                    template["xAxis"]["data"] = df[category_col].tolist()
                    template["xAxis"]["name"] = category_col

                    template["series"] = [
                        {"name": col, "type": "bar", "data": df[col].tolist()}
                        for col in series_cols
                    ]

                prepare_data = common_prepare_data_wrapper(metadata, specific_prepare)
                generate_chart(chart_id, metadata, dataset, template_path, output_dir, prepare_data, "category_bar_chart_vertical", global_template_path)
            else:
                print(f"Missing styling for bar chart categories: {chart_id}")

        elif chart_type == "bar chart stacked vertical":
            category_col = style.get("Category")
            series_cols = style.get("Value Series")
            if isinstance(series_cols, str):
                series_cols = [s.strip() for s in series_cols.split(',')]

            if category_col and series_cols:
                template_path = Path(template_folder_path) / "bar_chart_stacked_vertical_template.json"

                def specific_prepare(template, df):
                    if category_col not in df.columns:
                        raise ValueError(f"Missing category column: {category_col}")
                    for col in series_cols:
                        if col not in df.columns:
                            raise ValueError(f"Missing series column: {col}")
                    template["xAxis"]["data"] = df[category_col].tolist()
                    template["xAxis"]["name"] = category_col
                    template["series"] = [
                        {
                            "name": col,
                            "type": "bar",
                            "stack": "total",
                            "label": {"show": True},
                            "emphasis": {"focus": "series"},
                            "data": df[col].tolist()
                        }
                        for col in series_cols
                    ]

                prepare_data = common_prepare_data_wrapper(metadata, specific_prepare)
                generate_chart(chart_id, metadata, dataset, template_path, output_dir, prepare_data, "bar_chart_vertical_stacked", global_template_path)
            else:
                print(f"Missing styling for vertical stacked bar chart: {chart_id}")

        elif chart_type == "bar chart stacked horizontal":
            category_col = style.get("Category")
            series_cols = style.get("Value Series")
            if isinstance(series_cols, str):
                series_cols = [s.strip() for s in series_cols.split(',')]
            if category_col and series_cols:
                template_path = Path(template_folder_path) / "bar_chart_horizontal_stacked_template.json"

                def specific_prepare(template, df):
                    if category_col not in df.columns:
                        raise ValueError(f"Missing category column: {category_col}")
                    for col in series_cols:
                        if col not in df.columns:
                            raise ValueError(f"Missing series column: {col}")
                    template["yAxis"]["data"] = df[category_col].tolist()
                    template["yAxis"]["name"] = category_col
                    template["series"] = [
                        {
                            "name": col,
                            "type": "bar",
                            "stack": "total",
                            "label": {"show": True},
                            "emphasis": {"focus": "series"},
                            "data": df[col].tolist()
                        }
                        for col in series_cols
                    ]

                    max_label_length = max(len(str(label)) for label in df[category_col])
                    template["grid"] = template.get("grid", {})
                    template["grid"]["left"] = max(100, min(300, int(max_label_length * 7)))

                prepare_data = common_prepare_data_wrapper(metadata, specific_prepare)
                generate_chart(chart_id, metadata, dataset, template_path, output_dir, prepare_data, "bar_chart_horizontal_stacked", global_template_path)
            else:
                print(f"Missing styling for horizontal stacked bar chart: {chart_id}")

        elif chart_type == "scatter chart":
            x_col = style.get("X Axis")
            y_col = style.get("Y Axis")
            if x_col and y_col:
                template_path = Path(template_folder_path) / "scatter_chart_template.json"

                def specific_prepare(template, df):
                    if x_col not in df.columns or y_col not in df.columns:
                        raise ValueError(f"Missing columns: {x_col}, {y_col}")
                    template["series"][0]["data"] = df[[x_col, y_col]].values.tolist()

                prepare_data = common_prepare_data_wrapper(metadata, specific_prepare)
                generate_chart(chart_id, metadata, dataset, template_path, output_dir, prepare_data, "scatter_chart", global_template_path)
            else:
                print(f"Missing styling for scatter chart: {chart_id}")

        elif chart_type == "scatter chart categories":
            category_col = style.get("Category")
            x_col = style.get("X Axis")
            y_col = style.get("Y Axis")

            if category_col and x_col and y_col:
                template_path = Path(template_folder_path) / "scatter_chart_categories_template.json"

                def specific_prepare(template, df):
                    for col in [category_col, x_col, y_col]:
                        if col not in df.columns:
                            raise ValueError(f"Missing column: {col}")
                    template["xAxis"]["name"] = x_col
                    template["yAxis"]["name"] = y_col
                    prototype_series = template["series"][0]
                    grouped = df.groupby(category_col)

                    template["series"] = [
                        {
                            **prototype_series,
                            "name": name,
                            "data": group_df[[x_col, y_col]].values.tolist()
                        }
                        for name, group_df in grouped
                    ]

                prepare_data = common_prepare_data_wrapper(metadata, specific_prepare)
                generate_chart(chart_id, metadata, dataset, template_path, output_dir, prepare_data, "scatter_categories", global_template_path)
            else:
                print(f"Missing styling for scatter chart categories: {chart_id}")

        elif chart_type == "line chart":
            x_col = style.get("X Axis")
            y_col = style.get("Y Axis")
            if x_col and y_col:
                template_path = Path(template_folder_path) / "line_chart_template.json"

                def specific_prepare(template, df):
                    if x_col not in df.columns or y_col not in df.columns:
                        raise ValueError(f"Missing columns: {x_col}, {y_col}")
                    template["xAxis"]["data"] = df[x_col].tolist()
                    template["series"][0]["data"] = df[y_col].tolist()
                    template["series"][0]["name"] = y_col
                    template["xAxis"]["name"] = x_col
                    template["yAxis"]["name"] = y_col

                prepare_data = common_prepare_data_wrapper(metadata, specific_prepare)
                generate_chart(chart_id, metadata, dataset, template_path, output_dir, prepare_data, "line_chart", global_template_path)
            else:
                print(f"Missing styling for line chart: {chart_id}")


        elif chart_type == "line chart multi":
            x_col = style.get("X Axis")
            y_cols = style.get("Y Axis Series")
            if isinstance(y_cols, str):
                y_cols = [s.strip() for s in y_cols.split(',')]

            if x_col and y_cols:
                template_path = Path(template_folder_path) / "line_chart_multi_template.json"

                def specific_prepare(template, df):
                    if x_col not in df.columns:
                        raise ValueError(f"Missing x column: {x_col}")
                    for col in y_cols:
                        if col not in df.columns:
                            raise ValueError(f"Missing y column: {col}")
                    template["xAxis"]["data"] = df[x_col].tolist()
                    template["series"] = [
                        {
                            "type": "line",
                            "name": col,
                            "data": df[col].tolist()
                        }
                        for col in y_cols
                    ]
                    template["xAxis"]["name"] = x_col
                    template["yAxis"]["name"] = ", ".join(y_cols)

                prepare_data = common_prepare_data_wrapper(metadata, specific_prepare)
                generate_chart(chart_id, metadata, dataset, template_path, output_dir, prepare_data, "line_chart_multi", global_template_path)
            else:
                print(f"Missing styling for multi-line chart: {chart_id}")

        elif chart_type == "line chart stacked":
            x_col = style.get("X Axis")
            series_cols = style.get("Y Axis Series")

            if isinstance(series_cols, str):
                series_cols = [s.strip() for s in series_cols.split(',')]

            if x_col and series_cols:
                template_path = Path(template_folder_path) / "line_chart_stacked_template.json"

                def specific_prepare(template, df):
                    if x_col not in df.columns:
                        raise ValueError(f"Missing category column: {x_col}")
                    for col in series_cols:
                        if col not in df.columns:
                            raise ValueError(f"Missing series column: {col}")
                    template["xAxis"]["data"] = df[x_col].tolist()
                    template["series"] = [
                        {
                            "name": col,
                            "type": "line",
                            "stack": "Total",
                            "data": df[col].tolist()
                        }
                        for col in series_cols
                    ]

                prepare_data = common_prepare_data_wrapper(metadata, specific_prepare)
                generate_chart(chart_id, metadata, dataset, template_path, output_dir, prepare_data, "line_chart_stacked", global_template_path)
            else:
                print(f"Missing styling for stacked line chart: {chart_id}")

        else:
            print(f"Skipping {chart_id}: Unsupported chart type '{chart_type}'")

        



def load_charts_config(filepath):
    def clean_value(val):
        """Clean a value by parsing lists and stripping quotes if necessary."""
        if isinstance(val, str):
            val = val.strip()
            # Detect comma-separated values (not quoted as a full string)
            if ',' in val:
                return [v.strip() for v in val.split(',')]
            try:
                val = ast.literal_eval(val)
            except (ValueError, SyntaxError):
                pass
            if isinstance(val, str) and val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
        return val

    # Read all sheet names
    all_sheets = pd.ExcelFile(filepath).sheet_names

    # Filter only sheets that start with "Module"
    module_sheets = [sheet for sheet in all_sheets if sheet.startswith("Module")]
    # Initialize the config dictionary
    charts_config = {}

    # Read and process each module sheet
    for sheet in module_sheets:
        df = pd.read_excel(filepath, sheet_name=sheet, dtype=str)  # force strings
        for _, row in df.iterrows():
            chart_code = row['Chart Code']
            prop = clean_value(row['Property'])
            val = str(row['Column Name']) if not pd.isna(row['Column Name']) else ''
            charts_config.setdefault(chart_code, {})[prop] = val

    return charts_config


def load_json_file(filepath):

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    
    return None  # Return None if an error occurred