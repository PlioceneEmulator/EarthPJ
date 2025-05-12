import xarray as xr
import numpy as np
from plot import Plot
import matplotlib.pyplot as plt

class LongLatMonthPlot(Plot):
    def __init__(self, months, time_periods, color="viridis", min_longitude=-180, max_longitude=180, min_latitude=-90, max_latitude=90, central_longitude=0, num_std_dev=2):
        # Call parent class constructor
        super().__init__(
            months=months,
            time_periods=time_periods,
            color=color,
            min_longitude=min_longitude,
            max_longitude=max_longitude,
            min_latitude=min_latitude,
            max_latitude=max_latitude,
            central_longitude=central_longitude,
            num_std_dev=num_std_dev,
            title=f"Longitudinal Average Temperature Distribution",
            label="Temperature (K)",
            file_name="long_lat_month_plot.pdf"
        )
        
        # For debugging
        print(f"Selected months: {months}")

    def get_time_period_data(self, time_period):
        try:
            file = "netcdf_files/test_data_4000-4050.nc"
            self.ds = xr.open_dataset(file, decode_times=False)
            
            # Calculate start and end indices for the time period
            start = (time_period * self.time_period_length * 12)
            end = start + ((self.time_period_length + 1) * 12)
            
            # Debug print statements
            print(f"Time period: {time_period}")
            print(f"Start index: {start}")
            print(f"End index: {end}")

            # Create month indices array
            month_indices = []
            for year_start in range(start, end, 12):
                for month_str in self.months:
                    # Convert month string to integer and subtract 1 for zero-based indexing
                    month = int(month_str)  # This will convert '02' to 2
                    month_index = year_start + (month - 1)  # Subtract 1 for zero-based indexing
                    month_indices.append(month_index)
                    # print(f"Adding index {month_index} for month {month}")
            
            # Debug print
            print(f"Final month indices: {month_indices}")
            
            # Select data for specific time indices
            selected_data = self.ds.TS.isel(time=month_indices)
            
            # Handle longitude wrapping for negative values
            if self.min_longitude < 0:
                min_lon = self.min_longitude + 360 if self.min_longitude < 0 else self.min_longitude
                max_lon = self.max_longitude + 360 if self.max_longitude < 0 else self.max_longitude
            else:
                min_lon = self.min_longitude
                max_lon = self.max_longitude
            
            # Select the longitude and latitude ranges
            selected_data = selected_data.sel(
                lon=slice(min_lon, max_lon),
                lat=slice(self.min_latitude, self.max_latitude)
            )
            
            # Calculate weighted average across longitudes (weighted by cosine of latitude)
            weights = np.cos(np.deg2rad(selected_data.lat))
            lon_avg = (selected_data * weights).mean(dim='lon') / weights
            
            # Average across time
            avg_data = lon_avg.mean(dim='time')
            
            # Close the dataset
            self.ds.close()
            
            return avg_data
            
        except Exception as e:
            print(f"Error processing data: {str(e)}")
            return None

    def make_fig(self):
        """Create a line plot showing temperature variation across latitudes"""
        self.fig, ax = plt.subplots(figsize=(10, 6))
        
        if self.data is not None:
            # Plot the data with the specified color scheme
            colors = plt.cm.get_cmap(self.color)
            ax.plot(self.data.lat, self.data.values, '-', linewidth=2, color=colors(0.6))
            
            # Fill between the line and the bottom of the plot
            ax.fill_between(self.data.lat, self.data.values, 
                           min(self.data.values), 
                           alpha=0.3, 
                           color=colors(0.6))
            
            # Customize the plot
            ax.set_xlabel('Latitude (degrees)', fontsize=10)
            ax.set_ylabel('Temperature (K)', fontsize=10)
            
            # Update title based on whether a specific region was selected
            if (self.min_longitude == -180 and self.max_longitude == 180 and 
                self.min_latitude == -90 and self.max_latitude == 90):
                region_text = "Global"
            else:
                region_text = f"Region: {self.min_longitude}°-{self.max_longitude}°E"
            
            # Get month names for title
            month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December']
            selected_months = [month_names[int(m)] for m in self.months]
            months_text = ", ".join(selected_months)
            
            ax.set_title(f"{region_text} Longitudinal Average Temperature Distribution\nfor {months_text}", 
                        fontsize=14, pad=20)
            
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.set_xlim(self.min_latitude, self.max_latitude)
            
            # Include region information in the text box
            if (self.min_longitude != -180 or self.max_longitude != 180 or 
                self.min_latitude != -90 or self.max_latitude != 90):
                region_info = (f'Region: {self.min_longitude}°-{self.max_longitude}°E, '
                             f'{self.min_latitude}°-{self.max_latitude}°N\n')
            else:
                region_info = 'Region: Global\n'
                
            info_text = (f'{region_info}'
                        f'Months: {", ".join(selected_months)}\n'
                        f'Data averaged across longitudes (weighted by cos(latitude))\n'
                        f'and averaged across all years')
            
            ax.text(0.02, 0.98, info_text,
                    transform=ax.transAxes,
                    verticalalignment='top',
                    fontsize=9,
                    bbox=dict(boxstyle='round',
                             facecolor='white',
                             alpha=0.8,
                             edgecolor='none',
                             pad=1))
            
            plt.tight_layout()
            
        else:
            # If data processing failed, create an error plot
            ax.text(0.5, 0.5, 'Error processing data',
                   ha='center', va='center',
                   transform=ax.transAxes,
                   fontsize=14)
            ax.set_xticks([])
            ax.set_yticks([])