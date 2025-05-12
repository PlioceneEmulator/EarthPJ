from plot import Plot
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os

class GlobalAveragePlot(Plot):
    def __init__(self, time_periods, variable="temperature", color="viridis", 
                 min_longitude=-180, max_longitude=180, 
                 min_latitude=-90, max_latitude=90,
                 num_std_dev=2):
        """Initialize a GlobalAveragePlot instance for plotting annual cycles of global/regional averages."""
        super().__init__(
            months=[f"{i:02d}" for i in range(1, 13)],  # All months
            time_periods=time_periods,
            color=color,
            min_longitude=min_longitude,
            max_longitude=max_longitude,
            min_latitude=min_latitude,
            max_latitude=max_latitude,
            title=f"Regional Average {variable.title()}" + (" Difference" if len(time_periods) == 2 else ""),
            label="Value",
            file_name=f"regional_avg_{variable}.pdf"
        )
        
        self.variable = variable
        self.month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        self.export_data = {}
        self.period1_data = None
        self.period2_data = None
        self.is_difference = len(time_periods) == 2

    def get_time_period_data(self, time_period):
        """Get monthly regional averages for the specified time period and region."""
        try:
            file = "netcdf_files/test_data_4000-4050.nc"
            self.ds = xr.open_dataset(file, decode_times=False)
            
            start = (time_period * self.time_period_length * 12)
            end = start + ((self.time_period_length + 1) * 12)
            
            monthly_averages = np.zeros(12)
            monthly_std = np.zeros(12)
            
            # Select the spatial subset
            if self.min_longitude < 0:
                lon_subset = (self.ds.lon >= self.min_longitude + 360) | (self.ds.lon <= self.max_longitude)
            else:
                lon_subset = (self.ds.lon >= self.min_longitude) & (self.ds.lon <= self.max_longitude)
                
            lat_subset = (self.ds.lat >= self.min_latitude) & (self.ds.lat <= self.max_latitude)
            weights = np.cos(np.deg2rad(self.ds.lat.where(lat_subset, drop=True)))
            
            for month in range(12):
                month_indices = range(start + month, end, 12)
                
                if self.variable == "temperature":
                    data = self.ds.TS.isel(time=list(month_indices))
                else:
                    data = (self.ds.PRECC.isel(time=list(month_indices)) + 
                           self.ds.PRECL.isel(time=list(month_indices))) * 86400000
                
                data = data.where(lat_subset & lon_subset, drop=True)
                mean_data = (data * weights).mean(dim=('lat', 'lon')) / weights.mean()
                
                monthly_averages[month] = mean_data.mean().values
                monthly_std[month] = mean_data.std().values
            
            self.ds.close()
            
            # Store data for export
            self.export_data[f'period_{time_period}'] = {
                'averages': monthly_averages,
                'std_dev': monthly_std
            }
            
            return monthly_averages, monthly_std
            
        except Exception as e:
            print(f"Error processing data: {str(e)}")
            return None, None

    def set_data(self):
        """Process the data for plotting, handling both single period and difference plots."""
        if len(self.time_periods) <= 0:
            raise ValueError("At least one time period required")
            
        data1, std1 = self.get_time_period_data(self.time_period_a)
        
        if len(self.time_periods) == 2:
            # This is a difference plot
            data2, std2 = self.get_time_period_data(self.time_period_b)
            if data1 is None or data2 is None:
                raise ValueError("Failed to load data for one or both periods")
                
            # Calculate differences and combined standard deviation
            diff_data = data1 - data2
            # Combine standard deviations using error propagation
            diff_std = np.sqrt(std1**2 + std2**2)
            
            self.data = (diff_data, diff_std)
        else:
            # Single period plot
            self.data = (data1, std1)

    def make_fig(self):
        """Create the plot, handling both single period and difference plots."""
        self.fig, ax = plt.subplots(figsize=(12, 6))
        colors = plt.cm.get_cmap(self.color)
        
        if self.data is not None:
            data, std_dev = self.data
            
            if self.is_difference:
                # Plot difference
                ax.plot(range(12), data, '-', linewidth=2, color=colors(0.6))
                ax.fill_between(range(12), data - self.num_std_dev * std_dev,
                              data + self.num_std_dev * std_dev,
                              alpha=0.3, color=colors(0.6))
                # Add zero line for reference
                ax.axhline(y=0, color='k', linestyle='--', alpha=0.5)
                
                # Add difference statistics on the left
                mean_diff = np.mean(data)
                rms_diff = np.sqrt(np.mean(data**2))
                stats_text = (f'Mean difference: {mean_diff:.2f}\n'
                            f'RMS difference: {rms_diff:.2f}')
                ax.text(0.02, 0.98, stats_text,
                       transform=ax.transAxes,
                       verticalalignment='top',
                       fontsize=9,
                       bbox=dict(boxstyle='round',
                                facecolor='white',
                                alpha=0.8))
            else:
                # Single period plot
                ax.plot(range(12), data, '-', linewidth=2, color=colors(0.6))
                ax.fill_between(range(12), data - self.num_std_dev * std_dev,
                              data + self.num_std_dev * std_dev,
                              alpha=0.3, color=colors(0.6))
            
            # Customize the plot
            ax.set_xticks(range(12))
            ax.set_xticklabels(self.month_names)
            
            # Set y-axis label and adjust limits based on variable type
            if self.variable == "temperature":
                ax.set_ylabel('Temperature (K)', fontsize=12)
                current_yticks = ax.get_yticks()
                tick_range = current_yticks[-1] - current_yticks[0]
                ax.set_ylim(current_yticks[0] - 0.1 * tick_range, 
                           current_yticks[-1] + 0.1 * tick_range)
            else:
                ax.set_ylabel('Precipitation Rate (mm/day)', fontsize=12)
                current_yticks = ax.get_yticks()
                tick_range = current_yticks[-1] - current_yticks[0]
                ax.set_ylim(current_yticks[0] - 0.1 * tick_range, 
                           current_yticks[-1] + 0.1 * tick_range)
                
            ax.set_xlabel('Month', fontsize=12)
            if self.is_difference:
                period1_years = f"{4000 + self.time_period_a * 10}-{4000 + (self.time_period_a + 1) * 10}"
                period2_years = f"{4000 + self.time_period_b * 10}-{4000 + (self.time_period_b + 1) * 10}"
                ax.set_title(f"{self.title}\n{period1_years} minus {period2_years}")
            else:
                ax.set_title(self.title)
            
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Add region information
            region_text = (f'Region: {self.min_latitude}°-{self.max_latitude}°N, '
                         f'{self.min_longitude}°-{self.max_longitude}°E\n')
            info_text = (f'{region_text}'
                        f'Regional averages weighted by cos(latitude)\n'
                        f'Shading shows ±{self.num_std_dev} standard deviation' + 
                        ('s of inter-annual variability' if not self.is_difference 
                         else 's of combined uncertainty'))
            
            # Position the region info text to the right of any difference statistics
            text_x = 0.35 if self.is_difference else 0.02
            ax.text(text_x, 0.98, info_text,
                    transform=ax.transAxes,
                    verticalalignment='top',
                    fontsize=9,
                    bbox=dict(boxstyle='round',
                             facecolor='white',
                             alpha=0.8))
            
            plt.tight_layout()
            
        else:
            # Error plot
            ax.text(0.5, 0.5, 'Error processing data',
                   ha='center', va='center',
                   transform=ax.transAxes,
                   fontsize=14)
            ax.set_xticks([])
            ax.set_yticks([])
            
    def export_to_csv(self, output_dir="output"):
        """Export the plot data to CSV files."""
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a base filename
        base_filename = f"{self.variable}_"
        if self.is_difference:
            base_filename += f"diff_{self.time_period_a}_{self.time_period_b}"
        else:
            base_filename += f"{'_'.join(str(p) for p in self.time_periods)}"
            
        base_filename += f"_lon{self.min_longitude}-{self.max_longitude}"
        base_filename += f"_lat{self.min_latitude}-{self.max_latitude}"
        
        # Create DataFrames for averages and standard deviations
        data_dict = {}
        std_dict = {}
        
        for period, values in self.export_data.items():
            data_dict[f"{period}_avg"] = values['averages']
            std_dict[f"{period}_std"] = values['std_dev']
            
        if self.is_difference:
            # Add difference data
            diff_data, diff_std = self.data
            data_dict['difference'] = diff_data
            std_dict['difference_std'] = diff_std
        
        # Create and save the DataFrames
        df_avg = pd.DataFrame(data_dict, index=self.month_names)
        df_std = pd.DataFrame(std_dict, index=self.month_names)
        
        # Save to CSV
        avg_filename = os.path.join(output_dir, f"{base_filename}_averages.csv")
        std_filename = os.path.join(output_dir, f"{base_filename}_std_dev.csv")
        
        df_avg.to_csv(avg_filename)
        df_std.to_csv(std_filename)
        
        return avg_filename, std_filename