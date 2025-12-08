import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def test_three_axis_chart():
    """Generate and display a test chart with three Y-axes."""
    # Create sample data
    dates = [datetime.now() - timedelta(days=i) for i in range(30)]
    df = pd.DataFrame({
        'datetime': dates,
        'temperature': 25 + np.random.normal(0, 1, 30).cumsum(),
        'salinity': 35 + np.random.normal(0, 0.2, 30).cumsum(),
        'pressure': np.linspace(0, 100, 30) + np.random.normal(0, 2, 30)
    })

    # Create figure and primary axis
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Plot first Y-axis (left)
    color = 'tab:red'
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Temperature (°C)', color=color)
    ax1.plot(df['datetime'], df['temperature'], color=color, marker='o')
    ax1.tick_params(axis='y', labelcolor=color)

    # Create second Y-axis (right)
    ax2 = ax1.twinx()
    color = 'tab:blue'
    ax2.set_ylabel('Salinity (PSU)', color=color)
    ax2.plot(df['datetime'], df['salinity'], color=color, marker='x')
    ax2.tick_params(axis='y', labelcolor=color)

    # Create third Y-axis (right, offset)
    ax3 = ax1.twinx()
    color = 'tab:green'
    ax3.spines['right'].set_position(('outward', 60))  # Offset the third axis
    ax3.set_ylabel('Pressure (dbar)', color=color)
    ax3.plot(df['datetime'], df['pressure'], color=color, marker='^')
    ax3.tick_params(axis='y', labelcolor=color)

    # Title and layout
    plt.title('Ocean Parameters Over Time')
    fig.tight_layout()
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # Show the plot
    plt.show()

def test_argo_data_chart():
    """Test with sample Argo float data structure."""
    # Sample data structure similar to what your API might return
    chart_data = {
        'type': 'three_axis_line',
        'title': 'Argo Float 2903578 - Profile Data',
        'x': list(range(0, 200, 5)),  # Depth in meters
        'xLabel': 'Depth (m)',
        'y1': [25 - (x/10) + np.random.normal(0, 0.5) for x in range(0, 200, 5)],  # Temperature
        'y1Label': 'Temperature (°C)',
        'y2': [35 + np.sin(x/30) * 0.5 + np.random.normal(0, 0.1) for x in range(0, 200, 5)],  # Salinity
        'y2Label': 'Salinity (PSU)',
        'y3': [x for x in range(0, 200, 5)],  # Pressure
        'y3Label': 'Pressure (dbar)'
    }
    
    # Create figure and primary axis
    fig, ax1 = plt.subplots(figsize=(12, 8))
    
    # Plot first Y-axis (left)
    ax1.set_xlabel(chart_data['xLabel'])
    ax1.set_ylabel(chart_data['y1Label'], color='tab:red')
    ax1.plot(chart_data['x'], chart_data['y1'], color='tab:red', marker='o', markersize=4, label=chart_data['y1Label'])
    ax1.tick_params(axis='y', labelcolor='tab:red')
    ax1.invert_xaxis()  # Depth increases downward
    ax1.grid(True, linestyle='--', alpha=0.6)

    # Create second Y-axis (right)
    ax2 = ax1.twinx()
    ax2.set_ylabel(chart_data['y2Label'], color='tab:blue')
    ax2.plot(chart_data['x'], chart_data['y2'], color='tab:blue', marker='x', markersize=4, label=chart_data['y2Label'])
    ax2.tick_params(axis='y', labelcolor='tab:blue')

    # Create third Y-axis (right, offset)
    ax3 = ax1.twinx()
    ax3.spines['right'].set_position(('outward', 60))
    ax3.set_ylabel(chart_data['y3Label'], color='tab:green')
    ax3.plot(chart_data['x'], chart_data['y3'], color='tab:green', linestyle='--', alpha=0.7, label=chart_data['y3Label'])
    ax3.tick_params(axis='y', labelcolor='tab:green')

    # Add title and adjust layout
    plt.title(chart_data['title'])
    fig.tight_layout()
    
    # Add legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    lines3, labels3 = ax3.get_legend_handles_labels()
    ax1.legend(lines1 + lines2 + lines3, labels1 + labels2 + labels3, loc='upper right')
    
    plt.show()

if __name__ == "__main__":
    print("Testing Three-Axis Chart with Sample Data...")
    test_three_axis_chart()
    
    print("\nTesting Argo Data Visualization...")
    test_argo_data_chart()
