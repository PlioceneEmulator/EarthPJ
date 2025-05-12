import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from plot import Plot

class TimeSeriesPlot(Plot):
    def __init__(self, variable="temperature", color="viridis", 
                 min_longitude=-180, max_longitude=180, 
                 min_latitude=-90, max_latitude=90,
                 num_std_dev=2):
        """
        Initialize a TimeSeriesPlot instance for visualizing temporal evolution.
        """
        # Initialize with all months and no time periods
        super().__init__(
            months=[f"{i:02d}" for i in range(1, 13)],  # All months
            time_periods=None,  # Time series doesn't use time periods
            color=color,
            min_longitude=min_longitude,
            max_longitude=max_longitude,
            min_latitude=min_latitude,
            max_latitude=max_latitude,
            title=f"Regional Average {variable.title()} Time Series",
            label="Value",
            file_name=f"timeseries_{variable}.pdf"
        )
        
        self.variable = variable
        self.data_series = None
        self.time_axis = None
        self.show_percent = False  # Default to absolute values
        self.baseline = None  # For storing baseline when showing percentages


    def get_time_period_data(self, time_period):
        """Process data for the entire time series. time_period parameter is ignored."""
        try:
            file = "netcdf_files/test_data_4000-4050.nc"
            self.ds = xr.open_dataset(file, decode_times=False)
            
            # Select the spatial domain
            if self.min_longitude < 0:
                lon_subset = (self.ds.lon >= self.min_longitude + 360) | (self.ds.lon <= self.max_longitude)
            else:
                lon_subset = (self.ds.lon >= self.min_longitude) & (self.ds.lon <= self.max_longitude)
                
            lat_subset = (self.ds.lat >= self.min_latitude) & (self.ds.lat <= self.max_latitude)
            
            # Calculate weights for the selected latitudes
            weights = np.cos(np.deg2rad(self.ds.lat.where(lat_subset, drop=True)))
            
            if self.variable == "temperature":
                data = self.ds.TS
            else:
                # For precipitation, combine convective and large-scale
                data = (self.ds.PRECC + self.ds.PRECL) * 86400000  # Convert to mm/day
            
            # Apply spatial subsetting
            data = data.where(lat_subset & lon_subset, drop=True)
            
            # Calculate weighted spatial average
            self.data_series = data.weighted(weights).mean(dim=('lat', 'lon'))
            
            # Create time axis (assuming monthly data)
            self.time_axis = np.arange(len(self.data_series)) / 12 + 4000
            
            self.ds.close()
            return self.data_series.values, self.time_axis
            
        except Exception as e:
            print(f"Error processing data: {str(e)}")
            return None, None

    def make_fig(self):
        """Create the time series plot."""
        self.fig, ax = plt.subplots(figsize=(12, 6))
        
        if self.data is not None:
            values, times = self.data
            
            # Get colormap
            colors = plt.cm.get_cmap(self.color)
            
            # Plot the main time series
            ax.plot(times, values, '-', linewidth=1, color=colors(0.6), alpha=0.8)
            
            # Add running mean
            window = 12  # 12-month running mean
            running_mean = np.convolve(values, np.ones(window)/window, mode='valid')
            running_time = times[window-1:]
            ax.plot(running_time, running_mean, '-', linewidth=2, 
                   color=colors(0.8), label='12-month running mean')
            
            # Add trend line
            z = np.polyfit(times, values, 1)
            p = np.poly1d(z)
            ax.plot(times, p(times), '--', color=colors(0.3), 
                   label=f'Trend: {z[0]:.2e} per year')
            
            # Customize the plot
            if self.variable == "temperature":
                ax.set_ylabel('Temperature (K)')
            else:
                ax.set_ylabel('Precipitation Rate (mm/day)')
            
            ax.set_xlabel('Model Year')
            ax.set_title(self.title)
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Move legend to upper right corner inside the plot
            ax.legend(loc='upper right', bbox_transform=ax.transAxes,
                     bbox_to_anchor=(0.98, 0.98))
            
            # Add info text
            region_text = (f'Region: {self.min_latitude}°-{self.max_latitude}°N, '
                         f'{self.min_longitude}°-{self.max_longitude}°E')
            
            info_text = (f'{region_text}\n'
                        f'Regional averages weighted by cos(latitude)')
            if self.variable == "precipitation" and self.show_percent:
                info_text += f'\nShowing % change relative to {int(times[0])} baseline'
            
            # Position the region info text in the upper left
            ax.text(0.02, 0.98, info_text,
                    transform=ax.transAxes,
                    verticalalignment='top',
                    fontsize=9,
                    bbox=dict(boxstyle='round',
                             facecolor='white',
                             alpha=0.8))
            
            # Use tight layout
            plt.tight_layout()
        else:
            ax.text(0.5, 0.5, 'Error processing data',
                   ha='center', va='center',
                   transform=ax.transAxes,
                   fontsize=14)
            ax.set_xticks([])
            ax.set_yticks([])