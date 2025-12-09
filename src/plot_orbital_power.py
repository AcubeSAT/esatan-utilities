"""Plot orbital cold case power data."""

from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def process_model(model_dir: Path, model_name: str):
    """Process a single model and create all plots."""
    data_dir = model_dir / 'Data'
    # Check for both 'Plots' and 'plots' directory names
    if (model_dir / 'Plots').exists():
        plots_dir = model_dir / 'Plots'
    else:
        plots_dir = model_dir / 'plots'
    
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
        # Extract H002, H003, H004 (all in chained_4, so offset by max_time_1)
        
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
    
    # Define colors
    heater_colors = {
        'H001': ['#26677F', '#C46F3E'],  # [nominal, science]
        'H002': '#635C72',
        'H003': '#89374F',
        'H004': '#B79E4B'
    }
    # 10 distinct colors for temperature sensors
    temp_colors = [
        '#26677F',  # Blue
        '#635C72',  # Purple-gray
        '#89374F',  # Burgundy
        '#C46F3E',  # Orange
        '#B79E4B',  # Gold
        '#5B9BD5',  # Light blue
        '#70AD47',  # Green
        '#FFC000',  # Amber
        '#E74C3C',  # Red
        '#9C27B0',  # Purple
    ]
    
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
    
    # Plot additional heaters (H002, H003, H004)
    for heater_name, data in heater_data.items():
        ax_power.plot(data['times'], data['power'], label=f'{heater_name} Power (science mode)', 
                linewidth=1.0, color=heater_colors[heater_name], alpha=0.8)
    
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
            # Use direct indexing - we have 10 colors for up to 10 sensors
            color_idx = min(i, len(temp_colors) - 1)
            ax_temp.plot(data['times'], data['temps'], label=sensor_name, 
                    linewidth=1.0, color=temp_colors[color_idx], alpha=0.7)
    
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
    
    # Plot additional heaters (H002, H003, H004)
    for heater_name, data in heater_data.items():
        ax1.plot(data['times'], data['power'], label=f'{heater_name} Power (science mode)', 
                linewidth=1.0, color=heater_colors[heater_name], alpha=0.8)
    
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
            # Use direct indexing - we have 10 colors for up to 10 sensors
            color_idx = min(i, len(temp_colors) - 1)
            ax2.plot(data['times'], data['temps'], label=sensor_name, 
                    linewidth=1.0, color=temp_colors[color_idx], alpha=0.7)
    
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
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent
    data_dir = project_dir / 'MRR-analysis-files'
    
    # Find all model directories (exclude 'plots' directory)
    model_dirs = [d for d in data_dir.iterdir() 
                  if d.is_dir() and not d.name.startswith('.') and d.name.lower() != 'plots']
    
    if not model_dirs:
        print("No model directories found!", flush=True)
        return
    
    print(f"Found {len(model_dirs)} model(s)", flush=True)
    
    # Process each model
    for model_dir in sorted(model_dirs):
        model_name = model_dir.name
        print(f"\n{'='*60}", flush=True)
        print(f"Processing model: {model_name}", flush=True)
        print(f"{'='*60}", flush=True)
        
        try:
            process_model(model_dir, model_name)
            print(f"✓ Successfully processed {model_name}", flush=True)
        except Exception as e:
            print(f"✗ Error processing {model_name}: {e}", flush=True)
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
