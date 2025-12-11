"""Plot orbital cold case power data."""

from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# ============================================
# CONFIGURATION - Specify your CSV file(s) here
# ============================================
# For single file: provide a single path
# For multiple files: provide a list of paths (will be merged)
CSV_FILES = [
    r"c:\Users\chris\Desktop\A3S\utilities\MRR-analysis-files\Acubesat_11_12_25\Data\Orbital_cold_case_11_12_25_nominal_science_nominal_Yay_finally_Temperatures.csv",
    r"c:\Users\chris\Desktop\A3S\utilities\MRR-analysis-files\Acubesat_11_12_25\Data\Orbital_cold_case_11_12_25_nominal_science_nominal_Yay_finally_Temperatures (1).csv",
]


def process_model_combined_format(model_dir: Path, model_name: str, csv_files_input: list):
    """Process model with combined temperature and power CSV format (10_12_25 style)."""
    data_dir = model_dir / 'Data'
    
    # Create output folder based on CSV filename (e.g., "plots_hot_case" or "plots_cold_case")
    # Use first file to determine case type
    csv_name = csv_files_input[0].stem  # Get filename without extension
    if 'hot_case' in csv_name.lower():
        case_type = 'hot_case'
    elif 'cold_case' in csv_name.lower():
        case_type = 'cold_case'
    else:
        case_type = 'output'
    
    plots_dir = model_dir / f'plots_{case_type}'
    print(f"Output directory: {plots_dir}", flush=True)
    
    # Use the specified CSV files
    csv_files = csv_files_input
    
    if len(csv_files) > 1:
        print(f"Processing and merging {len(csv_files)} CSV files", flush=True)
    else:
        print(f"Processing CSV file: {csv_files[0].name}", flush=True)
    
    # Dictionary to store all data from all CSV files
    all_heater_data = {}
    all_sensor_data = {}
    
    for csv_filepath in csv_files:
        print(f"\nReading CSV: {csv_filepath.name}", flush=True)
        
        # Read the CSV, skipping the header rows
        df = pd.read_csv(csv_filepath, skiprows=5)
        
        # Parse element names from row 3
        element_row = pd.read_csv(csv_filepath, skiprows=2, nrows=1, header=None)
        element_names = element_row.iloc[0].values.tolist()
        
        print(f"  Elements found: {[e for e in element_names[1::2] if e and not pd.isna(e)]}", flush=True)
        
        # Heater mapping based on user's specifications
        # Only include specific heaters: H001 (Bag), H002/H003 (Chip), H007/H008 (Valves)
        heater_display_names = {
            'H001_powerApplied': 'Bag_Heater',
            'H002_powerApplied': 'Chip_Heater (Nominal)',
            'H003_powerApplied': 'Chip_Heater (Science)',
            'H007_powerApplied': 'Valve_1',
            'H008_powerApplied': 'Valve_2'
        }
        
        # Heaters to include (exclude H004, H005, H006)
        heaters_to_include = {'H001', 'H002', 'H003', 'H007', 'H008'}
        
        # Extract data by element type from this CSV
        for i in range(0, len(df.columns), 2):
            if i + 1 >= len(df.columns):
                break
            
            element_name = element_names[i + 1] if i + 1 < len(element_names) else None
            if not element_name or pd.isna(element_name):
                continue
            
            time_col = df.iloc[:, i]
            value_col = df.iloc[:, i + 1]
            valid_mask = ~(time_col.isna() | value_col.isna())
            
            if not valid_mask.any():
                continue
            
            times = time_col[valid_mask].values / 3600  # Convert to hours
            times_seconds = time_col[valid_mask].values  # Keep seconds for phase calculations
            values = value_col[valid_mask].values
            
            # Determine if this is power or temperature
            if 'powerApplied' in str(element_name):
                heater_name = element_name.split('_')[0]  # e.g., 'H001' from 'H001_powerApplied'
                # Skip heaters not in the include list
                if heater_name not in heaters_to_include:
                    continue
                display_name = heater_display_names.get(element_name, heater_name)
                # Only store if not already present (first file takes precedence)
                if heater_name not in all_heater_data:
                    all_heater_data[heater_name] = {
                        'times': times,
                        'times_seconds': times_seconds,
                        'power': values,
                        'display_name': display_name
                    }
                    avg_power = values.mean()
                    print(f"  Average power {heater_name} ({display_name}) [overall]: {avg_power:.4f} W", flush=True)
            else:
                # Temperature sensor - only store if not already present
                if element_name not in all_sensor_data:
                    all_sensor_data[element_name] = {
                        'times': times,
                        'temps': values
                    }
    
    # Use the merged data
    heater_data = all_heater_data
    sensor_data = all_sensor_data
    
    print(f"\nTotal: {len(heater_data)} heaters and {len(sensor_data)} temperature sensors", flush=True)
    
    # Check if this is a nominal-science-nominal sequence and calculate phase-specific averages
    if heater_data:
        max_time_seconds = max([data['times_seconds'].max() for data in heater_data.values()])
        # If data spans around 1,200,000 seconds, it's nominal-science-nominal
        if max_time_seconds > 1000000:
            print(f"\nDetected nominal-science-nominal sequence", flush=True)
            print(f"Phase 1 (Nominal): 0s to 500,000s", flush=True)
            print(f"Phase 2 (Science): 500,000s to 750,000s", flush=True)
            print(f"Phase 3 (Nominal): 750,000s to {max_time_seconds:.0f}s", flush=True)
            print(f"\nPhase-specific power consumption:", flush=True)
            
            # Organize results by phase for better clarity
            phase_results = {'Phase 1 (Nominal)': [], 'Phase 2 (Science)': [], 'Phase 3 (Nominal)': []}
            
            # Only include specified heaters
            heaters_to_include_phase = {'H001', 'H002', 'H003', 'H007', 'H008'}
            for heater_name, data in sorted(heater_data.items()):
                if heater_name not in heaters_to_include_phase:
                    continue
                    
                times_s = data['times_seconds']
                power = data['power']
                display_name = data['display_name']
                
                # Phase 1: Nominal (0 to 500,000s)
                mask_phase1 = times_s < 500000
                if mask_phase1.any():
                    avg_phase1 = power[mask_phase1].mean()
                    if avg_phase1 > 0.0001:  # Only show active heaters
                        phase_results['Phase 1 (Nominal)'].append(f"    {heater_name} ({display_name}): {avg_phase1:.4f} W")
                
                # Phase 2: Science (500,000 to 750,000s)
                mask_phase2 = (times_s >= 500000) & (times_s < 750000)
                if mask_phase2.any():
                    avg_phase2 = power[mask_phase2].mean()
                    if avg_phase2 > 0.0001:  # Only show active heaters
                        phase_results['Phase 2 (Science)'].append(f"    {heater_name} ({display_name}): {avg_phase2:.4f} W")
                
                # Phase 3: Nominal (750,000s to end)
                mask_phase3 = times_s >= 750000
                if mask_phase3.any():
                    avg_phase3 = power[mask_phase3].mean()
                    if avg_phase3 > 0.0001:  # Only show active heaters
                        phase_results['Phase 3 (Nominal)'].append(f"    {heater_name} ({display_name}): {avg_phase3:.4f} W")
            
            # Print results organized by phase
            for phase_name, heaters in phase_results.items():
                print(f"\n  {phase_name}:", flush=True)
                if heaters:
                    for heater_line in heaters:
                        print(heater_line, flush=True)
                else:
                    print(f"    No active heaters", flush=True)
    
    # Define coordinated colors - heaters and related sensors share colors
    # Component color mapping
    component_colors = {
        'Bag': '#26677F',           # Blue - Bag_2_P & H001
        'Chip': '#89374F',          # Burgundy - PDMS_Chip_P & H002/H003
        'Container': '#C46F3E',     # Orange - Container_3_P
        'Battery': '#B79E4B',       # Gold - ISIS_BatteryPack
        'MCU_COMMS': '#635C72',     # Purple-gray - MCU_COMMS
        'MCU_OBC_down': '#E74C3C',  # Red - MCU_OBC_ADCS_down
        'MCU_OBC_up': '#E67E22',    # Dark orange - MCU_OBC_ADCS_up
        'PFVHM_1': '#FFC000',       # Amber - PFVHM_1_P & H007 (Valve_1)
        'PFVHM_2': '#1ABC9C',       # Teal - PFVHM_2_P & H008 (Valve_2)
        'SU_MCU': '#9C27B0',        # Purple - SU_MCU_P
    }
    
    heater_colors = {
        'H001': component_colors['Bag'],
        'H002': component_colors['Chip'],
        'H003': component_colors['Chip'],
        'H004': component_colors['PFVHM_1'],
        'H005': component_colors['PFVHM_2'],
        'H007': component_colors['PFVHM_1'],  # Valve 1 → PFVHM_1
        'H008': component_colors['PFVHM_2']   # Valve 2 → PFVHM_2
    }
    
    # Temperature sensor color mapping
    sensor_color_map = {
        'Bag_2_P': component_colors['Bag'],
        'PDMS_Chip_P': component_colors['Chip'],
        'Container_3_P': component_colors['Container'],
        'ISIS_BatteryPack': component_colors['Battery'],
        'MCU_COMMS': component_colors['MCU_COMMS'],
        'MCU_OBC_ADCS_down': component_colors['MCU_OBC_down'],
        'MCU_OBC_ADCS_up': component_colors['MCU_OBC_up'],
        'PFVHM_1_P': component_colors['PFVHM_1'],
        'PFVHM_2_P': component_colors['PFVHM_2'],
        'SU_MCU_P': component_colors['SU_MCU'],
    }
    
    # Calculate max time for axis limits
    max_time = 0
    if heater_data:
        max_time = max([data['times'].max() for data in heater_data.values()])
    if sensor_data:
        max_sensor_time = max([data['times'].max() for data in sensor_data.values()])
        max_time = max(max_time, max_sensor_time)
    
    # Detect if this is a nominal-science-nominal sequence (11_12_25 style)
    # Check if max time is around 333 hours (1,200,000 seconds)
    transition_times = None
    phase_labels = None
    if max_time > 300:  # If data spans more than 300 hours, likely nominal-science-nominal
        # Transitions at 500,000s (~138.9h) and 750,000s (~208.3h)
        transition_times = [500000 / 3600, 750000 / 3600]
        phase_labels = [
            (transition_times[0] / 2, 'Nominal Mode'),
            ((transition_times[0] + transition_times[1]) / 2, 'Science Mode'),
            ((transition_times[1] + max_time) / 2, 'Nominal Mode')
        ]
    
    # Create plots directory if it doesn't exist
    plots_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Create POWER ONLY plot
    fig_power = plt.figure(figsize=(16, 6))
    ax_power = fig_power.add_subplot(111)
    
    # Only plot specified heaters
    heaters_to_plot = {'H001', 'H002', 'H003', 'H007', 'H008'}
    for heater_name, data in sorted(heater_data.items()):
        if heater_name not in heaters_to_plot:
            continue
        color = heater_colors.get(heater_name, '#000000')
        label = f"{heater_name} ({data['display_name']})"
        ax_power.plot(data['times'], data['power'], label=label, 
                linewidth=1.0, color=color, alpha=0.8)
    
    # Add transition lines and labels if detected
    if transition_times:
        ylim = ax_power.get_ylim()
        for i, t in enumerate(transition_times):
            ax_power.axvline(x=t, color='gray', linestyle='--', linewidth=1.5, alpha=0.7, zorder=10)
            ax_power.text(t + 2, ylim[1] * 0.95, f'{t:.1f}h', ha='left', fontsize=9, 
                         color='gray')
        # Add phase labels
        for center, label in phase_labels:
            ax_power.text(center, ylim[1] * 0.85, label, ha='center', fontsize=10, 
                         color='#26677F', weight='bold', alpha=0.7)
    
    ax_power.set_xlabel('Time (hours)', fontsize=11)
    ax_power.set_ylabel('Power Applied (W)', fontsize=11)
    ax_power.set_title(f'{model_name} - Heater Power Applied', fontsize=12, fontweight='bold')
    ax_power.legend(loc='upper right', fontsize=9, ncol=2)
    ax_power.grid(True, alpha=0.3)
    ax_power.set_xlim(0, max_time)
    
    fig_power.tight_layout()
    power_png = plots_dir / f'{model_name}_power.png'
    power_pdf = plots_dir / f'{model_name}_power.pdf'
    fig_power.savefig(power_png, dpi=150, facecolor='white', edgecolor='none')
    fig_power.savefig(power_pdf, format='pdf', facecolor='white', edgecolor='none')
    print(f"Saved power plot: {power_png}", flush=True)
    plt.close(fig_power)
    
    # 2. Create TEMPERATURE ONLY plot
    fig_temp = plt.figure(figsize=(16, 6))
    ax_temp = fig_temp.add_subplot(111)
    
    sensor_list = list(sensor_data.items())
    for i, (sensor_name, data) in enumerate(sensor_list):
        # Use coordinated color if available, otherwise use a default from component_colors
        color = sensor_color_map.get(sensor_name, list(component_colors.values())[i % len(component_colors)])
        ax_temp.plot(data['times'], data['temps'], label=sensor_name, 
                linewidth=1.0, color=color, alpha=0.7)
    
    # Add transition lines and labels if detected
    if transition_times:
        ylim = ax_temp.get_ylim()
        for i, t in enumerate(transition_times):
            ax_temp.axvline(x=t, color='gray', linestyle='--', linewidth=1.5, alpha=0.7, zorder=10)
            ax_temp.text(t + 2, ylim[1] * 0.95, f'{t:.1f}h', ha='left', fontsize=9, 
                         color='gray')
        # Add phase labels
        for center, label in phase_labels:
            ax_temp.text(center, ylim[1] * 0.85, label, ha='center', fontsize=10, 
                         color='#26677F', weight='bold', alpha=0.7)
    
    ax_temp.set_xlabel('Time (hours)', fontsize=11)
    ax_temp.set_ylabel('Temperature (°C)', fontsize=11)
    ax_temp.set_title(f'{model_name} - Temperatures', fontsize=12, fontweight='bold')
    ax_temp.legend(loc='upper right', fontsize=9, ncol=2)
    ax_temp.grid(True, alpha=0.3)
    ax_temp.set_xlim(0, max_time)
    
    fig_temp.tight_layout()
    temp_png = plots_dir / f'{model_name}_temperatures.png'
    temp_pdf = plots_dir / f'{model_name}_temperatures.pdf'
    fig_temp.savefig(temp_png, dpi=150, facecolor='white', edgecolor='none')
    fig_temp.savefig(temp_pdf, format='pdf', facecolor='white', edgecolor='none')
    print(f"Saved temperature plot: {temp_png}", flush=True)
    plt.close(fig_temp)
    
    # 3. Create COMBINED plot (power + temperatures)
    fig_combined, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))
    
    # Plot power on first subplot - only specified heaters
    for heater_name, data in sorted(heater_data.items()):
        if heater_name not in heaters_to_plot:
            continue
        color = heater_colors.get(heater_name, '#000000')
        label = f"{heater_name} ({data['display_name']})"
        ax1.plot(data['times'], data['power'], label=label, 
                linewidth=1.0, color=color, alpha=0.8)
    
    # Add transition lines and labels to power subplot
    if transition_times:
        ylim1 = ax1.get_ylim()
        for i, t in enumerate(transition_times):
            ax1.axvline(x=t, color='gray', linestyle='--', linewidth=1.5, alpha=0.7, zorder=10)
            ax1.text(t + 2, ylim1[1] * 0.95, f'{t:.1f}h', ha='left', fontsize=9, 
                     color='gray')
        # Add phase labels
        for center, label in phase_labels:
            ax1.text(center, ylim1[1] * 0.85, label, ha='center', fontsize=10, 
                     color='#26677F', weight='bold', alpha=0.7)
    
    ax1.set_xlabel('Time (hours)', fontsize=11)
    ax1.set_ylabel('Power Applied (W)', fontsize=11)
    ax1.set_title(f'{model_name} - Heater Power Applied', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=9, ncol=2)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, max_time)
    
    # Plot temperatures on second subplot
    sensor_list = list(sensor_data.items())
    for i, (sensor_name, data) in enumerate(sensor_list):
        # Use coordinated color if available, otherwise use a default
        color = sensor_color_map.get(sensor_name, list(component_colors.values())[i % len(component_colors)])
        ax2.plot(data['times'], data['temps'], label=sensor_name, 
                linewidth=1.0, color=color, alpha=0.7)
    
    # Add transition lines and labels to temperature subplot
    if transition_times:
        ylim2 = ax2.get_ylim()
        for i, t in enumerate(transition_times):
            ax2.axvline(x=t, color='gray', linestyle='--', linewidth=1.5, alpha=0.7, zorder=10)
            ax2.text(t + 2, ylim2[1] * 0.95, f'{t:.1f}h', ha='left', fontsize=9, 
                     color='gray')
        # Add phase labels
        for center, label in phase_labels:
            ax2.text(center, ylim2[1] * 0.85, label, ha='center', fontsize=10, 
                     color='#26677F', weight='bold', alpha=0.7)
    
    ax2.set_xlabel('Time (hours)', fontsize=11)
    ax2.set_ylabel('Temperature (°C)', fontsize=11)
    ax2.set_title(f'{model_name} - Temperatures', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=9, ncol=2)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, max_time)
    
    fig_combined.tight_layout()
    combined_png = plots_dir / f'{model_name}_combined.png'
    combined_pdf = plots_dir / f'{model_name}_combined.pdf'
    fig_combined.savefig(combined_png, dpi=150, facecolor='white', edgecolor='none')
    fig_combined.savefig(combined_pdf, format='pdf', facecolor='white', edgecolor='none')
    print(f"Saved combined plot: {combined_png}", flush=True)
    plt.close(fig_combined)


def process_model_sequential_format(model_dir: Path, model_name: str, csv_file: Path):
    """Process model with sequential (chained) format (7_12_25 style)."""
    data_dir = model_dir / 'Data'
    
    # Create output folder based on CSV filename
    csv_name = csv_file.stem
    if 'hot_case' in csv_name.lower():
        case_type = 'hot_case'
    elif 'cold_case' in csv_name.lower():
        case_type = 'cold_case'
    else:
        case_type = 'output'
    
    plots_dir = model_dir / f'plots_{case_type}'
    print(f"Output directory: {plots_dir}", flush=True)
    
    # Read the power CSV, skipping the header rows
    power_filepath = data_dir / 'Orbital_cold_case_7_12_25_Power_Max_1W_SC_NOM.csv'
    
    # Read raw to parse the structure
    df_power = pd.read_csv(power_filepath, skiprows=5)
    
    # Columns are: Time[s], Value, Time[s], Value
    df_power.columns = ['Time_s_1', 'Power_chained_3', 'Time_s_2', 'Power_chained_4']
    
    # Get max time of chained_3 to offset chained_4
    max_time_1 = df_power['Time_s_1'].max()
    
    # Convert time to hours - chained_4 starts after chained_3 ends
    df_power['Time_h_1'] = df_power['Time_s_1'] / 3600
    df_power['Time_h_2'] = (df_power['Time_s_2'] + max_time_1) / 3600
    
    print(f"Loaded {len(df_power)} power data points", flush=True)
    print(f"Nominal mode time range: 0 to {max_time_1/3600:.1f}h", flush=True)
    print(f"Science mode time range: {max_time_1/3600:.1f} to {df_power['Time_h_2'].max():.1f}h", flush=True)
    
    # Calculate average power 
    avg_power_nominal = df_power['Power_chained_3'].mean()
    avg_power_science = df_power['Power_chained_4'].mean()
    
    print(f"Average power H001 (nominal mode): {avg_power_nominal:.4f} W", flush=True)
    print(f"Average power H001 (science mode): {avg_power_science:.4f} W", flush=True)
    
    # Read the additional heaters CSV (H002, H003, H004)
    heaters_filepath = data_dir / 'Orbital_cold_case_7_12_25_Max_1W_heater_2_3_4.csv'
    
    heater_data = {}
    if heaters_filepath.exists():
        df_heaters = pd.read_csv(heaters_filepath, skiprows=5)
        
        # Read element names from row 3
        heater_element_row = pd.read_csv(heaters_filepath, skiprows=2, nrows=1, header=None)
        heater_element_names = heater_element_row.iloc[0].values.tolist()
        
        # Structure: columns 0,1: H001 chained_3, 2,3: H001 chained_4, 4,5: H002 chained_4, 6,7: H003 chained_4, 8,9: H004 chained_4
        # Additional: 10,11: H007 chained_4, 12,13: H008 chained_4 (if present)
        # Extract H002, H003, H004, H007, H008 (all in chained_4, so offset by max_time_1)
        
        # H002: columns 4,5
        if len(df_heaters.columns) > 5:
            time_h2 = df_heaters.iloc[:, 4]
            power_h2 = df_heaters.iloc[:, 5]
            valid_mask = ~(time_h2.isna() | power_h2.isna())
            if valid_mask.any():
                time_h2_valid = time_h2[valid_mask].values
                power_h2_valid = power_h2[valid_mask].values
                heater_data['H002'] = {
                    'times': (time_h2_valid + max_time_1) / 3600,
                    'power': power_h2_valid
                }
                # Average power (time steps are equal, so simple mean is sufficient)
                avg_power_h2 = power_h2_valid.mean()
                print(f"Average power H002 (science mode): {avg_power_h2:.4f} W", flush=True)
        
        # H003: columns 6,7
        if len(df_heaters.columns) > 7:
            time_h3 = df_heaters.iloc[:, 6]
            power_h3 = df_heaters.iloc[:, 7]
            valid_mask = ~(time_h3.isna() | power_h3.isna())
            if valid_mask.any():
                time_h3_valid = time_h3[valid_mask].values
                power_h3_valid = power_h3[valid_mask].values
                heater_data['H003'] = {
                    'times': (time_h3_valid + max_time_1) / 3600,
                    'power': power_h3_valid
                }
                # Average power (time steps are equal, so simple mean is sufficient)
                avg_power_h3 = power_h3_valid.mean()
                print(f"Average power H003 (science mode): {avg_power_h3:.4f} W", flush=True)
        
        # H004: columns 8,9
        if len(df_heaters.columns) > 9:
            time_h4 = df_heaters.iloc[:, 8]
            power_h4 = df_heaters.iloc[:, 9]
            valid_mask = ~(time_h4.isna() | power_h4.isna())
            if valid_mask.any():
                time_h4_valid = time_h4[valid_mask].values
                power_h4_valid = power_h4[valid_mask].values
                heater_data['H004'] = {
                    'times': (time_h4_valid + max_time_1) / 3600,
                    'power': power_h4_valid
                }
                # Average power (time steps are equal, so simple mean is sufficient)
                avg_power_h4 = power_h4_valid.mean()
                print(f"Average power H004 (science mode): {avg_power_h4:.4f} W", flush=True)
        
        # H007: columns 10,11 (if present)
        if len(df_heaters.columns) > 11:
            time_h7 = df_heaters.iloc[:, 10]
            power_h7 = df_heaters.iloc[:, 11]
            valid_mask = ~(time_h7.isna() | power_h7.isna())
            if valid_mask.any():
                time_h7_valid = time_h7[valid_mask].values
                power_h7_valid = power_h7[valid_mask].values
                heater_data['H007'] = {
                    'times': (time_h7_valid + max_time_1) / 3600,
                    'power': power_h7_valid
                }
                avg_power_h7 = power_h7_valid.mean()
                print(f"Average power H007 Valve_1 (science mode): {avg_power_h7:.4f} W", flush=True)
        
        # H008: columns 12,13 (if present)
        if len(df_heaters.columns) > 13:
            time_h8 = df_heaters.iloc[:, 12]
            power_h8 = df_heaters.iloc[:, 13]
            valid_mask = ~(time_h8.isna() | power_h8.isna())
            if valid_mask.any():
                time_h8_valid = time_h8[valid_mask].values
                power_h8_valid = power_h8[valid_mask].values
                heater_data['H008'] = {
                    'times': (time_h8_valid + max_time_1) / 3600,
                    'power': power_h8_valid
                }
                avg_power_h8 = power_h8_valid.mean()
                print(f"Average power H008 Valve_2 (science mode): {avg_power_h8:.4f} W", flush=True)
    else:
        print(f"Warning: {heaters_filepath} not found, skipping additional heaters", flush=True)
    
    # Read the temperature CSV
    temp_filepath = data_dir / 'Orbital_cold_case_7_12_25_Temperatures_SC_NOM.csv'
    df_temp = pd.read_csv(temp_filepath, skiprows=5)
    
    # Read element names from row 3 (index 3, which is row 4 in file)
    element_row = pd.read_csv(temp_filepath, skiprows=2, nrows=1, header=None)
    element_names = element_row.iloc[0].values.tolist()
    
    # Pattern: For each element, columns are:
    # 0,1: Time[s]_3, Temp_3
    # 2,3: Time[s]_4, Temp_4
    # 4,5: Time[s]_3, Heat_3
    # 6,7: Time[s]_4, Heat_4
    # Then repeats for next element (columns 8-15, 16-23, etc.)
    
    # Extract temperature columns and combine nominal and science mode for each sensor
    # Dictionary to store combined data: {sensor_name: {'times': [...], 'temps': [...]}}
    sensor_data = {}
    
    num_cols = len(df_temp.columns)
    # Process in groups of 8 columns
    for start_col in range(0, num_cols, 8):
        # Get sensor name from element_names (column start_col+1 for nominal, start_col+3 for science)
        # They should be the same for the same physical sensor
        sensor_name = None
        
        if start_col + 1 < len(element_names):
            sensor_name = element_names[start_col + 1]
        
        # Process nominal mode (chained_3): columns start_col and start_col+1 (Time, Temp)
        if start_col + 1 < num_cols and sensor_name:
            time_col_3 = df_temp.iloc[:, start_col]
            temp_col_3 = df_temp.iloc[:, start_col + 1]
            valid_mask_3 = ~(time_col_3.isna() | temp_col_3.isna())
            if valid_mask_3.any():
                times_3 = time_col_3[valid_mask_3].values / 3600
                temps_3 = temp_col_3[valid_mask_3].values
                
                if sensor_name not in sensor_data:
                    sensor_data[sensor_name] = {'times': [], 'temps': []}
                sensor_data[sensor_name]['times'].append(times_3)
                sensor_data[sensor_name]['temps'].append(temps_3)
        
        # Process science mode (chained_4): columns start_col+2 and start_col+3 (Time, Temp)
        if start_col + 3 < num_cols and sensor_name:
            time_col_4 = df_temp.iloc[:, start_col + 2]
            temp_col_4 = df_temp.iloc[:, start_col + 3]
            valid_mask_4 = ~(time_col_4.isna() | temp_col_4.isna())
            if valid_mask_4.any():
                times_4 = (time_col_4[valid_mask_4].values + max_time_1) / 3600
                temps_4 = temp_col_4[valid_mask_4].values
                
                if sensor_name not in sensor_data:
                    sensor_data[sensor_name] = {'times': [], 'temps': []}
                sensor_data[sensor_name]['times'].append(times_4)
                sensor_data[sensor_name]['temps'].append(temps_4)
    
    # Combine all time segments for each sensor and sort
    for sensor_name in sensor_data:
        all_times = np.concatenate(sensor_data[sensor_name]['times'])
        all_temps = np.concatenate(sensor_data[sensor_name]['temps'])
        # Sort by time
        sort_idx = np.argsort(all_times)
        sensor_data[sensor_name]['times'] = all_times[sort_idx]
        sensor_data[sensor_name]['temps'] = all_temps[sort_idx]
    
    print(f"Found {len(sensor_data)} temperature sensors", flush=True)
    
    # Define coordinated colors - same as combined format
    component_colors = {
        'Bag': '#26677F',           # Blue - Bag_2_P & H001
        'Chip': '#89374F',          # Burgundy - PDMS_Chip_P & H002/H003
        'Container': '#C46F3E',     # Orange - Container_3_P
        'Battery': '#B79E4B',       # Gold - ISIS_BatteryPack
        'MCU_COMMS': '#635C72',     # Purple-gray - MCU_COMMS
        'MCU_OBC_down': '#E74C3C',  # Red - MCU_OBC_ADCS_down
        'MCU_OBC_up': '#E67E22',    # Dark orange - MCU_OBC_ADCS_up
        'PFVHM_1': '#FFC000',       # Amber - PFVHM_1_P & H007 (Valve_1)
        'PFVHM_2': '#1ABC9C',       # Teal - PFVHM_2_P & H008 (Valve_2)
        'SU_MCU': '#9C27B0',        # Purple - SU_MCU_P
    }
    
    heater_colors = {
        'H001': [component_colors['Bag'], component_colors['Bag']],  # [nominal, science] - same color
        'H002': component_colors['Chip'],
        'H003': component_colors['Chip'],
        'H007': component_colors['PFVHM_1'],  # Valve 1 → PFVHM_1
        'H008': component_colors['PFVHM_2']   # Valve 2 → PFVHM_2
    }
    
    # Only include these heaters in plots
    heaters_to_plot = {'H001', 'H002', 'H003', 'H007', 'H008'}
    
    # Temperature sensor color mapping
    sensor_color_map = {
        'Bag_2_P': component_colors['Bag'],
        'PDMS_Chip_P': component_colors['Chip'],
        'Container_3_P': component_colors['Container'],
        'ISIS_BatteryPack': component_colors['Battery'],
        'MCU_COMMS': component_colors['MCU_COMMS'],
        'MCU_OBC_ADCS_down': component_colors['MCU_OBC_down'],
        'MCU_OBC_ADCS_up': component_colors['MCU_OBC_up'],
        'PFVHM_1_P': component_colors['PFVHM_1'],
        'PFVHM_2_P': component_colors['PFVHM_2'],
        'SU_MCU_P': component_colors['SU_MCU'],
    }
    
    # Calculate max times for axis limits
    max_power_time = df_power['Time_h_2'].max()
    if heater_data:
        max_heater_time = max([data['times'].max() if len(data['times']) > 0 else 0 
                              for data in heater_data.values()])
        max_power_time = max(max_power_time, max_heater_time)
    
    max_time = df_power['Time_h_2'].max()
    if sensor_data:
        max_sensor_time = max([data['times'].max() if len(data['times']) > 0 else 0 
                              for data in sensor_data.values()])
        max_time = max(max_time, max_sensor_time)
    
    # Create plots directory if it doesn't exist
    plots_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Create POWER ONLY plot
    fig_power = plt.figure(figsize=(16, 6))
    ax_power = fig_power.add_subplot(111)
    
    ax_power.plot(df_power['Time_h_1'], df_power['Power_chained_3'], label='H001 Power (nominal mode)', 
            linewidth=1.0, color=heater_colors['H001'][0])
    ax_power.plot(df_power['Time_h_2'], df_power['Power_chained_4'], label='H001 Power (science mode)', 
            linewidth=1.0, color=heater_colors['H001'][1])
    
    # Plot additional heaters (only specified ones)
    for heater_name, data in heater_data.items():
        if heater_name not in heaters_to_plot:
            continue
        ax_power.plot(data['times'], data['power'], label=f'{heater_name} Power (science mode)', 
                linewidth=1.0, color=heater_colors.get(heater_name, '#000000'), alpha=0.8)
    
    # Add vertical line at transition
    ax_power.axvline(x=max_time_1/3600, color='gray', linestyle='--', linewidth=1.0, alpha=0.7)
    ax_power.text(max_time_1/3600, 1.05, 'Transition', ha='center', fontsize=9, color='gray')
    
    ax_power.set_xlabel('Time (hours)', fontsize=11)
    ax_power.set_ylabel('Power Applied (W)', fontsize=11)
    ax_power.set_title(f'{model_name} - Heater Power Applied (Sequential)', fontsize=12, fontweight='bold')
    ax_power.legend(loc='upper right', fontsize=9, ncol=2)
    ax_power.grid(True, alpha=0.3)
    ax_power.set_ylim(-0.05, 1.15)
    ax_power.set_xlim(0, max_power_time)
    
    fig_power.tight_layout()
    power_png = plots_dir / f'{model_name}_power.png'
    power_pdf = plots_dir / f'{model_name}_power.pdf'
    fig_power.savefig(power_png, dpi=150, facecolor='white', edgecolor='none')
    fig_power.savefig(power_pdf, format='pdf', facecolor='white', edgecolor='none')
    print(f"Saved power plot: {power_png}", flush=True)
    plt.close(fig_power)
    
    # 2. Create TEMPERATURE ONLY plot
    fig_temp = plt.figure(figsize=(16, 6))
    ax_temp = fig_temp.add_subplot(111)
    
    # Convert to list to ensure consistent ordering
    sensor_list = list(sensor_data.items())
    print(f"Plotting {len(sensor_list)} sensors with {len(temp_colors)} colors", flush=True)
    
    for i, (sensor_name, data) in enumerate(sensor_list):
        if len(data['times']) > 0:
            # Use coordinated color if available, otherwise use a default
            color = sensor_color_map.get(sensor_name, list(component_colors.values())[i % len(component_colors)])
            ax_temp.plot(data['times'], data['temps'], label=sensor_name, 
                    linewidth=1.0, color=color, alpha=0.7)
    
    # Add vertical line at transition
    ax_temp.axvline(x=max_time_1/3600, color='gray', linestyle='--', linewidth=1.0, alpha=0.7)
    ax_temp.text(max_time_1/3600, ax_temp.get_ylim()[1] * 0.95, 'Transition', ha='center', fontsize=9, color='gray')
    
    ax_temp.set_xlabel('Time (hours)', fontsize=11)
    ax_temp.set_ylabel('Temperature (°C)', fontsize=11)
    ax_temp.set_title(f'{model_name} - Temperatures (Sequential)', fontsize=12, fontweight='bold')
    ax_temp.legend(loc='upper right', fontsize=9, ncol=2)
    ax_temp.grid(True, alpha=0.3)
    ax_temp.set_xlim(0, max_time)
    
    fig_temp.tight_layout()
    temp_png = plots_dir / f'{model_name}_temperatures.png'
    temp_pdf = plots_dir / f'{model_name}_temperatures.pdf'
    fig_temp.savefig(temp_png, dpi=150, facecolor='white', edgecolor='none')
    fig_temp.savefig(temp_pdf, format='pdf', facecolor='white', edgecolor='none')
    print(f"Saved temperature plot: {temp_png}", flush=True)
    plt.close(fig_temp)
    
    # 3. Create COMBINED plot (power + temperatures)
    fig_combined, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))
    
    # Plot power on first subplot
    ax1.plot(df_power['Time_h_1'], df_power['Power_chained_3'], label='H001 Power (nominal mode)', 
            linewidth=1.0, color=heater_colors['H001'][0])
    ax1.plot(df_power['Time_h_2'], df_power['Power_chained_4'], label='H001 Power (science mode)', 
            linewidth=1.0, color=heater_colors['H001'][1])
    
    # Plot additional heaters (only specified ones)
    for heater_name, data in heater_data.items():
        if heater_name not in heaters_to_plot:
            continue
        ax1.plot(data['times'], data['power'], label=f'{heater_name} Power (science mode)', 
                linewidth=1.0, color=heater_colors.get(heater_name, '#000000'), alpha=0.8)
    
    # Add vertical line at transition
    ax1.axvline(x=max_time_1/3600, color='gray', linestyle='--', linewidth=1.0, alpha=0.7)
    ax1.text(max_time_1/3600, 1.05, 'Transition', ha='center', fontsize=9, color='gray')
    
    ax1.set_xlabel('Time (hours)', fontsize=11)
    ax1.set_ylabel('Power Applied (W)', fontsize=11)
    ax1.set_title(f'{model_name} - Heater Power Applied (Sequential)', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=9, ncol=2)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(-0.05, 1.15)
    ax1.set_xlim(0, max_power_time)
    
    # Plot temperatures on second subplot
    # Convert to list to ensure consistent ordering
    sensor_list = list(sensor_data.items())
    
    for i, (sensor_name, data) in enumerate(sensor_list):
        if len(data['times']) > 0:
            # Use coordinated color if available, otherwise use a default
            color = sensor_color_map.get(sensor_name, list(component_colors.values())[i % len(component_colors)])
            ax2.plot(data['times'], data['temps'], label=sensor_name, 
                    linewidth=1.0, color=color, alpha=0.7)
    
    # Add vertical line at transition
    ax2.axvline(x=max_time_1/3600, color='gray', linestyle='--', linewidth=1.0, alpha=0.7)
    ax2.text(max_time_1/3600, ax2.get_ylim()[1] * 0.95, 'Transition', ha='center', fontsize=9, color='gray')
    
    ax2.set_xlabel('Time (hours)', fontsize=11)
    ax2.set_ylabel('Temperature (°C)', fontsize=11)
    ax2.set_title(f'{model_name} - Temperatures (Sequential)', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=9, ncol=2)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, max_time)
    
    fig_combined.tight_layout()
    combined_png = plots_dir / f'{model_name}_combined.png'
    combined_pdf = plots_dir / f'{model_name}_combined.pdf'
    fig_combined.savefig(combined_png, dpi=150, facecolor='white', edgecolor='none')
    fig_combined.savefig(combined_pdf, format='pdf', facecolor='white', edgecolor='none')
    print(f"Saved combined plot: {combined_png}", flush=True)
    plt.close(fig_combined)


def main():
    # Use the CSV file(s) specified at the top of the script
    # Convert to list if single string provided
    if isinstance(CSV_FILES, str):
        csv_files_list = [Path(CSV_FILES)]
    else:
        csv_files_list = [Path(f) for f in CSV_FILES]
    
    # Check all files exist
    for csv_path in csv_files_list:
        if not csv_path.exists():
            print(f"Error: CSV file not found: {csv_path}", flush=True)
            return
    
    # Get model directory from first CSV path (parent's parent)
    model_dir = csv_files_list[0].parent.parent
    model_name = model_dir.name
    
    print(f"Processing model: {model_name}", flush=True)
    print(f"CSV file(s): {[f.name for f in csv_files_list]}", flush=True)
    
    print(f"\n{'='*60}", flush=True)
    print(f"Processing: {model_name}", flush=True)
    print(f"{'='*60}", flush=True)
    
    try:
        process_model_combined_format(model_dir, model_name, csv_files_list)
        print(f"\n[SUCCESS] Successfully processed {model_name}", flush=True)
    except Exception as e:
        print(f"\n[ERROR] Error processing {model_name}: {e}", flush=True)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
