import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geocat.viz as gv
import xarray as xr
import matplotlib.pyplot as plt
from plot import Plot
import os

class DifferencePlot(Plot):
    def __init__(self, months, time_periods, variable="temperature", color="bwr", 
                 min_longitude=-180, max_longitude=180, 
                 min_latitude=-90, max_latitude=90, 
                 central_longitude=0, num_std_dev=2):
        """Initialize a DifferencePlot instance for comparing two time periods."""
        # First check if we can access the data file
        if not self.check_file():
            raise ValueError("Unable to access data file")

        if not time_periods or len(time_periods) != 2:
            raise ValueError("DifferencePlot requires exactly 2 time periods")

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
            title=f"Difference in {variable.title()}",
            label=f"Difference in {variable.title()}" + (" (K)" if variable == "temperature" else " (mm/day)"),
            file_name=f"difference_{variable}.pdf"
        )
        
        self.variable = variable
        self.period1_data = None
        self.period2_data = None
        self.difference_stats = None

    def check_file(self):
        """Verify that the data file exists and can be opened."""
        file = "netcdf_files/test_data_4000-4050.nc"
        
        try:
            with xr.open_dataset(file) as ds:
                return True
        except Exception as e:
            print(f"Error opening file: {str(e)}")
            return False

    def get_time_period_data(self, time_period):
        """Get data for a specific time period."""
        try:
            file = "netcdf_files/test_data_4000-4050.nc"
            self.ds = xr.open_dataset(file, decode_times=False)
            
            start = (time_period * self.time_period_length * 12)
            end = start + ((self.time_period_length + 1) * 12)
            
            month_indices = []
            for jan_index in range(start, end, 12):
                for month_index in self.months:
                    month_indices.append(jan_index + month_index)
            
            if self.variable == "temperature":
                data = self.ds.TS.isel(time=month_indices)
            else:
                data = (self.ds.PRECC.isel(time=month_indices) + 
                       self.ds.PRECL.isel(time=month_indices))
                data *= 86400000  # Convert to mm/day
            
            data = gv.xr_add_cyclic_longitudes(data, "lon")
            
            if data.lon.max() > 180:
                data.coords['lon'] = (((data.coords['lon'] + 180) % 360) - 180)
                data = data.sortby('lon')
            
            lat_slice = slice(self.min_latitude, self.max_latitude)
            lon_slice = slice(self.min_longitude, self.max_longitude)
            
            data = data.sel(lat=lat_slice)
            data = data.sel(lon=lon_slice)
            
            data = data.mean('time')
            
            self.ds.close()
            return data
            
        except Exception as e:
            print(f"Error processing data: {str(e)}")
            return None

    def set_data(self):
        """Calculate the difference between two time periods."""
        self.period1_data = self.get_time_period_data(self.time_period_a)
        self.period2_data = self.get_time_period_data(self.time_period_b)
        
        if self.period1_data is None or self.period2_data is None:
            raise ValueError("Failed to load data for one or both periods")
            
        if hasattr(self, 'show_percent') and self.show_percent:
            denominator = self.period2_data.where(self.period2_data != 0)
            self.data = ((self.period1_data - self.period2_data) / denominator) * 100
            self.label = "Percentage Change (%)"
        else:
            self.data = self.period1_data - self.period2_data
        
        self.difference_stats = {
            'mean': float(self.data.mean()),
            'std': float(self.data.std()),
            'min': float(self.data.min()),
            'max': float(self.data.max()),
            'rms': float(np.sqrt((self.data ** 2).mean()))
        }

    def make_fig(self):
        """Create the difference plot using pcolormesh."""
        try:
            plt.clf()
            self.fig = plt.figure(figsize=(10 * self.width_ratio, 6 * self.height_ratio))
            
            data_proj = ccrs.PlateCarree()
            ax = plt.axes(projection=data_proj)
            
            lons = self.data.lon.values
            lats = self.data.lat.values
            plot_data = self.data.values
            
            lon_mesh, lat_mesh = np.meshgrid(lons, lats)
            
            if hasattr(self, 'show_percent') and self.show_percent:
                max_abs = float(max(abs(plot_data.min()), abs(plot_data.max())))
                max_abs = max(2.0, max_abs)
                vmin, vmax = -max_abs, max_abs
            else:
                max_abs = float(max(abs(plot_data.min()), abs(plot_data.max())))
                vmin, vmax = -max_abs, max_abs
            
            cmap = 'RdBu_r' if (hasattr(self, 'show_percent') and self.show_percent) else self.color

            mesh = ax.pcolormesh(lon_mesh, lat_mesh, plot_data,
                            transform=data_proj,
                            cmap=cmap,
                            vmin=vmin, vmax=vmax,
                            shading='auto')
            
            ax.coastlines(resolution='50m')
            ax.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.3)
            ax.add_feature(cfeature.OCEAN, facecolor='white', alpha=0.3)
            
            period1_years = f"{4000 + self.time_period_a * 10}-{4000 + (self.time_period_a + 1) * 10}"
            period2_years = f"{4000 + self.time_period_b * 10}-{4000 + (self.time_period_b + 1) * 10}"
            ax.set_title(f"{self.title}\n{period1_years} minus {period2_years}", pad=10)

            # Create a specific axes for the colorbar with wider width
            cax = self.fig.add_axes([0.2625, 0.08, 0.5, 0.03]) # Adjusted y position
            cbar = self.fig.colorbar(mesh, cax=cax, orientation='horizontal')
            cbar.ax.tick_params(labelsize=8)
            cbar.set_label(self.label, size=9)
            
            gl = ax.gridlines(draw_labels=True, 
                            linestyle='--',
                            linewidth=0.5,
                            color='gray',
                            alpha=0.5)
            gl.top_labels = False
            gl.right_labels = False
            
            ax.set_extent([self.min_longitude, self.max_longitude,
                        self.min_latitude, self.max_latitude],
                        crs=data_proj)
            
            if hasattr(self, 'difference_stats'):
                stats_text = (
                    f"Mean diff: {self.difference_stats['mean']:.2f}\n"
                    f"Std diff: {self.difference_stats['std']:.2f}\n"
                    f"RMS diff: {self.difference_stats['rms']:.2f}\n"
                    f"Range: [{self.difference_stats['min']:.2f}, {self.difference_stats['max']:.2f}]"
                )
                
                ax.text(0.02, 0.98, stats_text,
                    transform=ax.transAxes,
                    verticalalignment='top',
                    fontsize=9,
                    bbox=dict(boxstyle='round',
                                facecolor='white',
                                alpha=0.8))
            
        except Exception as e:
            plt.clf()
            self.fig = plt.figure(figsize=(10, 6))
            ax = plt.axes()
            plt.text(0.5, 0.5, f'Error creating plot: {str(e)}',
                    ha='center', va='center',
                    transform=ax.transAxes)
            plt.tight_layout()