# ESATAN Thermal Analysis Plotting Tool

## Overview
Processes ESATAN thermal analysis CSV files and generates power and temperature plots.

## Usage

### 1. Configure CSV File(s)
Edit `src/plot_orbital_power.py` - update the `CSV_FILES` configuration at the top:

**Single file:**
```python
CSV_FILES = [r"path\to\your\file.csv"]
```

**Multiple files (will be merged):**
```python
CSV_FILES = [
    r"path\to\file1.csv",
    r"path\to\file2.csv",
]
```

### 2. Run the Script
```bash
python src/plot_orbital_power.py
```

### 3. Outputs
Plots are saved in separate folders based on case type:
- `plots_hot_case/` - Hot case analysis
- `plots_cold_case/` - Cold case analysis

Each folder contains:
- `{model_name}_power.png/pdf` - Heater power over time
- `{model_name}_temperatures.png/pdf` - Temperature sensors over time
- `{model_name}_combined.png/pdf` - Combined plot

Terminal displays average power consumption (overall and per phase).

## Supported Heaters
- **H001** - Bag Heater (blue)
- **H002** - Chip Heater Nominal (burgundy)
- **H003** - Chip Heater Science (burgundy)
- **H007** - Valve 1 / PFVHM_1 (amber)
- **H008** - Valve 2 / PFVHM_2 (teal)

## Color Coordination
Heaters and their related temperature sensors use matching colors for easy visual correlation.
