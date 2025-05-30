# 📘 User Guide: SEA Chart Generator

This guide explains how to use the SEA Chart Pipeline to add and generate charts. It covers the key components of the system and provides step-by-step instructions for both manual and automated workflows.


## How to Add a Chart to the pipeline

### Step 1: Add to the Chart Tracker

- Open the **Chart Tracker Excel file** (`Charts Tracker.xlsx`)
- Go to the sheet of the relevant module
- Add a new row and fill out all columns
- Note that only permissible values may be entered (In-depth explanation of columns can be found here: [Chart Tracker](#chart-tracker))

 Reference: [Chart Tracker](#chart-tracker)


### Step 2: Add the Dataset

- Open the Excel file for datasets of the appropriate module (e.g., `Module 1 - Datasets for Charts.xlsx`)
- Create a new sheet named after the chart
- Format the dataset by removing all excess information (See formatting guidelines here: [Datasets](#datasets))
- Insert the dataset starting at cell **A1**

 Reference: [Datasets](#datasets)

 **Checklist**:
- Headers in Row 1
- No extra top or bottom rows
- No metadata or notes


### Step 3: Link the Dataset
- In the **Chart Tracker**, fill in the `Dataset Link` column with a hyperlink to the dataset sheet you just added.




The diagram illustrates the full end-to-end flow for adding a chart.
 *[Insert workflow image here]*

## How to Create a Chart with the pipeline

There are **two chart creation options**: automatic via the pipeline, or custom via the LLM prompt.
As a first step, check whether the chart needs to be recreated or can be used from source. 
If it needs to be recreated follow the two options:


### Option 1: Automatic Chart Creation

Here, common chart types can be generated fully automatically after correctly adding the dataset, metadata (**Charts Tracker**) and adding necessary logic for the chart generation (**Charts Config**)

#### Steps:

1. In the **Chart Tracker**:
   - Set `Category` to `Chart to Recreate`
   - Check if the chart type is supported [Templates](#templates)
   - If supported, set `Automated processing` to `true`
   - Enter the **exact chart type** corresponding to the [Templates](#templates) in the `Chart type` column

2. Fill in **Chart Config** with required parameters for the selected chart type
    - Open the **Chart Config Excel file** (`SEA Charts Config.xlsx`)
    - Check within the [Chart Config](#chart-config), which additional information of the chart has to be added to Chart config for your selected chart type
    - Add new rows to the chart config with the `Figure ID`, `Property` and `Value`.

3. The chart will be automatically processed and rendered with styling defined by the template.

 Reference:
- [Templates](#templates)
- [Chart Config](#charts-config)



### Option 2: Custom Chart with LLM Prompt

For **unsupported chart types**:

1. In the **Chart Tracker**:
   - Set `Category` to `Chart to Recreate`
   - Set `Automated processing` to `false`

2. Open the **Chart Prompt Template** ( *link TBD*), and fill in:
   - Metadata
   - Dataset
   - Further Instructions
   - Reference chart (Apache E-Chart, etc.)

3. Paste the completed prompt into an LLM (we recommend XY) to generate a chart rendering script.

 Reference: [Chart Prompt Template](#chart-prompt-template)




The diagram illustrates the full end-to-end flow for  generating a chart.
 *[Insert workflow image here]*





## Key Components

### Chart Tracker

The **Chart Tracker** is the central control file that manages chart metadata and status across modules. Each row represents one chart.
Below is a list of columns and their expected input values:

| Column | Description        | Expected Input Values    |
|--------|--------------------|--------------------------|
| Chapter      | Number of Capter  | Numerical (Integer) |
| #      | serial number within chapter  | Numerical (Integer)          |
| Figure ID    | Serial number to uniquely identify chart                | Text (String)                      |
| Title    | ...                | Text (String)                     |
| Subtitle    | ...                | Text (String)                      |
| Screenshot    | ...                | Image (JPG/PNG)                      |
| New Screenshot (if available)   | ...                | Image (JPG/PNG)                     |
| Category    | ...                | Factor (Chart to Recreate | Ready to Use)                      |
| Status    | ...                | ...                     |
| LEAD  | ...                | Text (String)                      |
| Source (APA)  | ...                | Text (String)                      |
| Source Link  | ...                | Text (String) with Hyperlink                      |
| Footnote  | ...                | Text (String)                         |
| Apache possible  | ...                | Boolean (False | True)                     |
| Automation possible  | ...                | Boolean (False | True)                         |
| Chart Type  | ...                | Factor (Bar Chart | Pie Chart | ...)                       |
| Dataset Status  | ...                | Factor (Chart to Recreate | Ready to Use)                     |
| Dataset Link  | ...                | Text (String) with Hyperlink                       |
| Apache Link  | ...                | Text (String) with Hyperlink                       |
| Notes  | ...                | Text (String)                      |


 **Note**: All columns must be filled out correctly to ensure smooth processing.

### Datasets


**Formatting Guidelines**:
- Start at cell **A1**
- Row 1 must contain **column headers**
- Data rows begin immediately after headers
- Remove all extraneous rows (titles, notes, metadata)

 Improper formatting could cause the pipeline to fail.


###  Templates

Templates define the **visual layout** and **styling** for each supported chart type.

- Stored in: `02_Inputs/Templates/`
- Predefined for each chart type
- Applied automatically during chart creation

Supports the following chart types:
| Chart Type |Description        | 
|--------|--------------------|
| Bar Chart       |  ... |
| Bar Chart (Categories)     | ... | 
| Pie Chart    | ... |

 Each chart type expects additional configuration information which needs to be added to the [Chart Config](#charts-config).

 **Templates are fixed** and cannot be modified by the user. Styling includes fonts, colors, labels, etc.



### Chart Config

This file provides **advanced configuration** for charts that need more than basic metadata, such as:

- Which columns of the dataset to use for X and Y axes
- Grouping or filtering logic
- Optional labels or scaling options

The following table lists the obligatory properties for each Chart Type:

| Chart Type |Properties        | 
|--------|--------------------|
| Bar Chart       |  x_col_name, y_col_name |
| Bar Chart (Categories)     | category_col, series_cols  | 
| Pie Chart    | ...           name_col, value_col |

Here is an example how the data should be stored:

| Chart Code  | Property      | Value                                     |
|-------------|---------------|-------------------------------------------|
| M1_C1_1     | name_col      | Sector                                    |
| M1_C1_1     | value_col     | 2021.0                                    |
| M1_C1_2    | x_col_name    | Category                                  |
| M1_C1_2    | y_col_name    | 2022 (watts per capita)                   |
| M1_C1_3   | category_col  | Category                                  |
| M1_C1_3   | series_cols   | 2015 (watts per capita), 2022 (watts per capita) |


### Chart Prompt Template

For unsupported chart types, a **Chart Prompt Template** is used to create charts via a Large Language Model (LLM), such as XY.

This template includes:
- Chart metadata
- Dataset 
- Reference chart
- Instructions for rendering

#TODO




##  Need Help?

For technical issues, submit a GitHub Issue or contact the maintainer.
