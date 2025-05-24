# 📊 Chart Generation Pipeline

A Python-based data pipeline for converting structured metadata and tabular datasets into JSON chart configurations. Used in the context of data visualization for the UNDP Sustainable Energy Hub Academy.

---

## 🚀 Overview

This project automates the generation of chart configuration files based on:
- Metadata (e.g., chart type, title, styling) (Excel)
- Raw datasets (Excel)
- Chart templates (JSON)

---

## 🛠 Pipeline Summary

```
 Metadata + datasets → merged chart data 
 merged chart data + templates → JSON chart configs
```

---

## 📁 Folder Structure

```
.
├── 00_API/
│   └── Charts/
│
├── 01_Code/
│   ├── charts_functions.py
│   └── SEA Chart Pipeline.ipynb
│
├── 02_Inputs/
│   ├── Metadata/
│   ├── Data/
│   └── Templates/
│
├── 03_Outputs/
│   └── Charts/
│
├── 04_Documentation/
│   └── technical_documentation.md
│   └── user_guide.md
│
├── README.md

```

---

## ⚙️ How to Run

```bash
python scripts/charts_pipeline.py
```

---

## 🧩 Dependencies

- Python >= 3.9
- pandas
- json
- openpyxl
- ipykernel

Install with:

```bash
pip install -r requirements.txt
```

---

## 📚 Documentation

- [Technical Documentation](04_Documentation/technical_documentation.md)
- [User Guide & Best Practices](04_Documentation/user_guide.md)

---

