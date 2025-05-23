import numpy as np
import cartopy.crs as ccrs
import geocat.viz as gv
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import base64
from io import BytesIO
from netCDF4 import Dataset
from plot import Plot
import cartopy.feature as cfeature

# INFORMATION ON TS ATTRIBUTE FOR NETCDF DATA
# filling on, default _FillValue of 9.969209968386869e+36 used, 'TS': <class 'netCDF4._netCDF4.Variable'>
# float32 TS(time, lat, lon)
#     units: K
#     long_name: Surface temperature (radiative)
#     cell_methods: time: mean
# unlimited dimensions: time
# current shape = (612, 96, 144)

class TemperatureSurfacePlot(Plot):

    def __init__(self, months, time_periods, color="viridis", min_longitude=-180, max_longitude=180, min_latitude=-90, max_latitude=90, central_longitude=0, num_std_dev=2):

        # Initiate instance of super class: Plot
        super().__init__(months, time_periods, color, min_longitude, max_longitude, min_latitude, max_latitude, central_longitude, num_std_dev, "Global Surface Temperature", "K", "sfc_temp_plot.pdf")

    def get_time_period_data(self, time_period):
        
        try:
            
            file = "netcdf_files/test_data_4000-4050.nc"
            self.ds = xr.open_dataset(file, decode_times=False)

        # Another error occurred while accessing the data
        except Exception as error:
            print("Something went wrong while accessing the data file. See error below:")
            print(error)
            exit()

        # Time period indexing is going to start at intervals 0, 120, 240, 360, 480
        # Each interval will cover 11 years, even though the time period length is 10
        # Indexing lengths will be 132 since each index represents one month, we have 11 * 12 = 132 for 11 years of data
        # Intervals for a 51 year file split into 5 time periods:
        # 0   - 132, 120 - 252, 240 - 372, 360 - 492, 480 - 612
        # The intervals will overlap by one year while averaging, but they are all equal in length (132 = 11 * 12 -> 11 years of data)
        start = (time_period * self.time_period_length * 12)
        end = start + ((self.time_period_length + 1) * 12)

        # Create a list of indexes to extract the data that the user is requesting
        # If the user requests the first time period, and months January, July, and December:
        # indexes = [0, 6, 11, 12, 18, 23, 24, 30, 35, 36, 42, 47, 48, 54, 59, 60, 66, 71, 72, 78, 83, 84, 90, 95, 96, 102, 107, 108, 114, 119, 120, 126, 131]
        indexes = []
        for jan_index in range(start, end, 12):
            for month_index in self.months:
                indexes.append(jan_index + month_index)

        # Select all of the time slices out of surface temperature data
        selected_data = self.ds.TS.isel(time=[index for index in indexes])
        # Interpolate longitude values so it goes from (0, 357) -> (0, 360)
        selected_data = gv.xr_add_cyclic_longitudes(selected_data, "lon")
        # Select the latitude and longitude values based on min/max lat/lon values that user enters
        selected_data = selected_data.sel(lat=self.latitude_range, method='nearest', tolerance=2)
        selected_data = selected_data.sel(lon=self.longitude_range, method='nearest', tolerance=2)
        # Average the data over time variable
        selected_data = selected_data.mean('time')

        # Close the data set
        self.ds.close()

        # Return selected, interpolated, averaged data to be plotted
        return selected_data
    
    def make_fig(self):
        """Create a surface temperature plot using cartopy and matplotlib."""
        try:
            # Clear any existing figures
            plt.clf()
            
            # Create figure with specific size based on the ratio
            self.fig = plt.figure(figsize=(10 * self.width_ratio, 6 * self.height_ratio))
            
            # Set up the map projection
            data_proj = ccrs.PlateCarree()
            ax = plt.axes(projection=data_proj)
            
            # Get the data and coordinates
            lons = self.data.lon.values
            lats = self.data.lat.values
            plot_data = self.data.values
            
            # Create coordinate meshgrids
            lon_mesh, lat_mesh = np.meshgrid(lons, lats)
            
            # Calculate the color range based on standard deviations
            mean = float(plot_data.mean())
            std = float(plot_data.std())
            vmin = mean - self.num_std_dev * std
            vmax = mean + self.num_std_dev * std
            
            # Create the plot using pcolormesh for better performance
            mesh = ax.pcolormesh(lon_mesh, lat_mesh, plot_data,
                            transform=data_proj,
                            cmap=self.color,
                            vmin=vmin, vmax=vmax,
                            shading='auto')
            
            # Add map features
            ax.coastlines(resolution='50m')
            ax.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.3)
            ax.add_feature(cfeature.OCEAN, facecolor='white', alpha=0.3)
            
            # Add gridlines
            gl = ax.gridlines(draw_labels=True,
                            linestyle='--',
                            linewidth=0.5,
                            color='gray',
                            alpha=0.5)
            gl.top_labels = False
            gl.right_labels = False
            
            # Set map extent
            ax.set_extent([self.min_longitude, self.max_longitude,
                        self.min_latitude, self.max_latitude],
                        crs=data_proj)
            
            # Add colorbar
            cax = self.fig.add_axes([0.2, 0.08, 0.6, 0.03])  # [x, y, width, height]
            cbar = self.fig.colorbar(mesh, cax=cax, orientation='horizontal')
            cbar.ax.tick_params(labelsize=8)
            cbar.set_label(self.label, size=9)
            
            # Add title
            period_years = f"{4000 + int(self.time_periods[0]) * 10}-{4000 + (int(self.time_periods[0]) + 1) * 10}"
            plt.title(f"{self.title}\n{period_years}")
            
            # Add statistics text box
            stats_text = (f"Mean: {mean:.2f} K\n"
                        f"Std Dev: {std:.2f} K\n"
                        f"Range: [{float(plot_data.min()):.2f}, {float(plot_data.max()):.2f}] K")
            
            ax.text(0.02, 0.98, stats_text,
                    transform=ax.transAxes,
                    verticalalignment='top',
                    fontsize=9,
                    bbox=dict(boxstyle='round',
                            facecolor='white',
                            alpha=0.8))
            
        except Exception as e:
            print(f"Error in make_fig: {str(e)}")
            import traceback
            print("Full traceback:")
            print(traceback.format_exc())
            
            # Create empty plot with error message if plotting fails
            plt.clf()
            self.fig = plt.figure(figsize=(10, 6))
            ax = plt.axes()
            plt.text(0.5, 0.5, f'Error creating plot: {str(e)}',
                    ha='center', va='center',
                    transform=ax.transAxes)
            plt.tight_layout()