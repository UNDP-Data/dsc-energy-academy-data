# 🛠 Technical Documentation

## 1. Project Overview

This project is designed to automate the generation of standardized charts for the SEA region using structured input data and configurable templates. It provides a clear pipeline from raw data ingestion to chart output in both human-readable and reusable formats.

## 2. Folder Structure Explanation

```
.
├── 00_API/             # Static chart schema or examples (JSON, XML)
│   └── Charts/
├── 01_Code/            # Source code and notebooks
│   ├── charts_functions.py         # Main chart creation functions
│   └── SEA Chart Pipeline.ipynb    # Jupyter Notebook for execution
├── 02_Inputs/          # Input files and templates
│   ├── Metadata/
│   ├── Data/                        # Raw data files (CSV/XLSX)
│   └── Templates/                  # Chart layout/style templates
├── 03_Outputs/         # Auto-generated outputs
│   └── Charts/
├── 04_Documentation/   # Markdown docs
│   └── technical_documentation.md
│   └── user_guide.md
└── README.md           # Project summary
```

## 3. Dependencies & Setup

- **Python**: 3.9+
- Required libraries:
  ```bash
  pip install -r requirements.txt
  ```

- Recommended: Use a virtual environment

## 4. Code Modules

### `charts_functions.py`
Contains reusable functions for:
- Reading data
- Validating inputs
- Generating charts using matplotlib and seaborn
- Saving charts in appropriate formats

### `SEA Chart Pipeline.ipynb`
Notebook for end-to-end execution:
- Load inputs
- Process metadata
- Apply templates
- Export charts to `03_Outputs/Charts/`

## 5. Data Flow

```
Input Data (.csv/.xlsx) → Processed via Python Code → Styled with Templates → Exported as Charts
```

## 6. API Charts (00_API/)

If external API schemas are used for chart definitions, they're stored here.
- Format: JSON or XML
- Used primarily for static validation or future integration

## 7. Testing

Currently no formal testing suite.
Validation steps:
- Run notebook end-to-end
- Check file names, types, and visual output
- Verify all required fields are used

## 8. Deployment

This project is executed manually via Jupyter.
For automation:
- Use a cron job or GitHub Actions with a scheduled runner (not implemented yet)

## 9. Known Issues / Improvements

- Add unit tests for functions
- Automate template validation
- Improve error handling for corrupt input files

## 10. Contributing

- Fork the repo
- Create a feature branch
- Ensure code follows PEP8
- Submit PR with a detailed description

