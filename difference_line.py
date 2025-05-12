import numpy as np
import matplotlib.pyplot as plt
from plot import Plot
import xarray as xr

class LineDifferencePlot(Plot):
    """A class for creating difference plots between two time periods for line-based visualizations"""
    
    def __init__(self, months, time_periods, plot_type="longitude", variable="temperature",
                 color="bwr", min_longitude=-180, max_longitude=180, 
                 min_latitude=-90, max_latitude=90, num_std_dev=2):
        """
        Initialize a LineDifferencePlot instance.
        
        Args:
            months: List of months to analyze
            time_periods: List of two time periods to compare
            plot_type: "longitude" for longitudinal averages or "time" for time series
            variable: "temperature" or "precipitation"
            color: Colormap to use
            min/max_longitude/latitude: Spatial bounds
            num_std_dev: Number of standard deviations for error bars
        """
        if len(time_periods) != 2:
            raise ValueError("LineDifferencePlot requires exactly 2 time periods")
            
        super().__init__(
            months=months,
            time_periods=time_periods,
            color=color,
            min_longitude=min_longitude,
            max_longitude=max_longitude,
            min_latitude=min_latitude,
            max_latitude=max_latitude,
            title=f"{variable.title()} Difference",
            label=f"Difference in {variable.title()}" + (" (K)" if variable == "temperature" else " (mm/day)"),
            file_name=f"line_difference_{variable}.pdf"
        )
        
        self.plot_type = plot_type
        self.variable = variable
        self.period1_data = None
        self.period2_data = None
        self.show_percent = False  # Default to absolute differences

    def get_time_period_data(self, time_period):
        """Get data for a specific time period based on plot type."""
        try:
            file = "netcdf_files/test_data_4000-4050.nc"
            self.ds = xr.open_dataset(file, decode_times=False)
            
            start = (time_period * self.time_period_length * 12)
            end = start + ((self.time_period_length + 1) * 12)
            
            # Create indices for requested months
            month_indices = []
            for year_start in range(start, end, 12):
                for month in self.months:
                    month_indices.append(year_start + int(month) - 1)
            
            # Select appropriate variable and handle coordinates
            if self.variable == "temperature":
                data = self.ds.TS.isel(time=month_indices)
            else:
                data = (self.ds.PRECC.isel(time=month_indices) + 
                       self.ds.PRECL.isel(time=month_indices)) * 86400000  # Convert to mm/day
            
            # Handle coordinate selection and averaging
            if self.plot_type == "longitude":
                # For longitudinal averages, average across longitudes with latitude weighting
                weights = np.cos(np.deg2rad(data.lat))
                data = (data * weights).mean(dim='lon') / weights
                data = data.mean(dim='time')
            else:
                # For time series, do spatial averaging
                weights = np.cos(np.deg2rad(data.lat))
                data = (data * weights).mean(dim=('lat', 'lon')) / weights.mean()
            
            self.ds.close()
            return data
            
        except Exception as e:
            print(f"Error processing data: {str(e)}")
            return None

    def make_fig(self):
        """Create the difference plot."""
        self.fig, ax = plt.subplots(figsize=(12, 6))
        
        if self.data is not None:
            colors = plt.cm.get_cmap(self.color)
            
            if self.plot_type == "longitude":
                # Calculate percentage change if selected and if it's precipitation or user explicitly wants it
                if self.show_percent and (self.variable == "precipitation" or hasattr(self, 'force_percent')):
                    # Avoid division by zero
                    denominator = self.period2_data.where(self.period2_data != 0)
                    plot_data = ((self.period1_data - self.period2_data) / denominator) * 100
                    y_label = "Percent Change (%)"
                else:
                    plot_data = self.data
                    y_label = self.label

                # Plot the data
                ax.plot(self.data.lat, plot_data.values, '-', 
                       linewidth=2, color=colors(0.8))
                ax.fill_between(self.data.lat, plot_data.values, 0,
                              where=plot_data.values >= 0, color=colors(0.7), alpha=0.3)
                ax.fill_between(self.data.lat, plot_data.values, 0,
                              where=plot_data.values < 0, color=colors(0.2), alpha=0.3)
                ax.set_xlabel('Latitude (degrees)')
                ax.set_ylabel(y_label)
                
            else:
                # Plot time series differences
                time_axis = np.arange(len(self.data)) / 12 + 4000
                ax.plot(time_axis, self.data.values, '-', 
                       linewidth=1, color=colors(0.8), alpha=0.8)
                ax.fill_between(time_axis, self.data.values, 0,
                              where=self.data.values >= 0, color=colors(0.7), alpha=0.3)
                ax.fill_between(time_axis, self.data.values, 0,
                              where=self.data.values < 0, color=colors(0.2), alpha=0.3)
                ax.set_xlabel('Model Year')
            
            # Add grid and labels
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.set_ylabel(self.label)
            
            # Add zero line for reference
            ax.axhline(y=0, color='k', linestyle='--', alpha=0.5)
            
            # Add region information
            region_text = (f'Region: {self.min_longitude}°-{self.max_longitude}°E, '
                         f'{self.min_latitude}°-{self.max_latitude}°N\n')
            
            # Get period information
            period1_years = f"{4000 + self.time_period_a * 10}-{4000 + (self.time_period_a + 1) * 10}"
            period2_years = f"{4000 + self.time_period_b * 10}-{4000 + (self.time_period_b + 1) * 10}"
            
            # Add statistics
            if hasattr(self, 'show_percent') and self.show_percent:
                stats_text = (f'{region_text}'
                            f'Difference: {period1_years} minus {period2_years}\n'
                            f'Mean % diff: {float(plot_data.mean()):.2f}%\n'
                            f'RMS % diff: {float(np.sqrt((plot_data ** 2).mean())):.2f}%')
            else:
                stats_text = (f'{region_text}'
                            f'Difference: {period1_years} minus {period2_years}\n'
                            f'Mean diff: {float(self.data.mean()):.2f}\n'
                            f'RMS diff: {float(np.sqrt((self.data ** 2).mean())):.2f}')
            
            ax.text(0.02, 0.98, stats_text,
                   transform=ax.transAxes,
                   verticalalignment='top',
                   fontsize=9,
                   bbox=dict(boxstyle='round',
                           facecolor='white',
                           alpha=0.8))
            
            plt.title(f"{self.title}\n{period1_years} minus {period2_years}")
            plt.tight_layout()
            
        else:
            ax.text(0.5, 0.5, 'Error processing data',
                   ha='center', va='center',
                   transform=ax.transAxes,
                   fontsize=14)
            ax.set_xticks([])
            ax.set_yticks([])