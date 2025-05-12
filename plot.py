import numpy as np
import cartopy.crs as ccrs
import geocat.viz as gv
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import base64
from io import BytesIO
from netCDF4 import Dataset
import math

class Plot:
    def __init__(self, months, time_periods=None, color="viridis", 
                 min_longitude=-180, max_longitude=180, 
                 min_latitude=-90, max_latitude=90, 
                 central_longitude=0, num_std_dev=2, 
                 title="Plot", label="", file_name="plot.pdf"):

        # Set the passed in variables
        self.months = [(int(month) - 1) for month in months]
        self.time_periods = time_periods
        self.time_period_length = 10
        
        # Add support for difference plots
        self.is_difference = len(time_periods) == 2 if time_periods else False
        if self.is_difference:
            self.color = color if color != "viridis" else "bwr"  # Default to blue-white-red for differences
        else:
            self.color = color
            
        self.central_longitude = central_longitude
        self.num_std_dev = num_std_dev
        self.title = title
        self.label = label
        self.file_name = file_name

        self.ds = None
        self.data = None
        self.difference_stats = None

        # Store coordinates as floats
        self.min_latitude = float(min_latitude)
        self.max_latitude = float(max_latitude)
        self.min_longitude = float(min_longitude)
        self.max_longitude = float(max_longitude)

        # Set latitude and longitude ranges with explicit floats
        self.latitude_range = np.arange(self.min_latitude, self.max_latitude + 2, 1.89)
        if self.min_longitude < 0 and self.max_longitude < 0:
            self.longitude_range = np.arange(self.min_longitude + 360, self.max_longitude + 362, 2.5)
        elif self.min_longitude < 0:
            lon_range1 = np.arange(0, self.max_longitude + 2, 2.5)
            lon_range2 = np.arange(self.min_longitude + 360, 362, 2.5)
            self.longitude_range = np.concatenate([lon_range1, lon_range2])
        else:
            self.longitude_range = np.arange(self.min_longitude, self.max_longitude + 2, 2.5)

        self.fig = None
        self.pdf = None
        self.png = None
        
        # Calculate plot dimensions
        width = float(self.max_longitude - self.min_longitude)
        height = float(self.max_latitude - self.min_latitude)
        
        # Determine the plot ratio with explicit float conversion
        min_dim = min(width, height)
        if min_dim == 0:  # Prevent division by zero
            min_dim = 1
        self.width_ratio = max(1, int(width / min_dim))
        self.height_ratio = max(1, int(height / min_dim))

        # Set minimum values for ticks
        self.xticks = max(2, int(6 / self.height_ratio))
        self.yticks = max(2, int(8 / self.width_ratio))

        # Only set time period variables if time_periods is provided
        if self.time_periods:
            self.time_period_a = int(self.time_periods[0])
            if len(self.time_periods) == 2:
                self.time_period_b = int(self.time_periods[1])
                if self.is_difference:
                    self.title = self.title + " Difference"
                self.file_name = "diff_" + self.file_name
                
    def set_data(self):
        """Enhanced data setting to handle difference plots."""
        # For time series plots that don't use time periods
        if self.time_periods is None:
            self.data = self.get_time_period_data(None)
            return

        if len(self.time_periods) <= 0:
            print("User needs to enter at least one time period to collect data for")
            exit()
        else:
            data1 = self.get_time_period_data(self.time_period_a)
            if len(self.time_periods) == 2:
                data2 = self.get_time_period_data(self.time_period_b)
                self.data = data1 - data2
                
                if self.is_difference:
                    # Calculate difference statistics
                    self.difference_stats = {
                        'mean': float(self.data.mean()),
                        'std': float(self.data.std()),
                        'min': float(self.data.min()),
                        'max': float(self.data.max()),
                        'rms': float(np.sqrt((self.data ** 2).mean()))
                    }
            else:
                self.data = data1

    def get_time_period_data(self, time_period):
        """To be implemented by child classes."""
        raise NotImplementedError("Subclasses must implement get_time_period_data")

    def make_fig(self):
        """To be implemented by child classes."""
        raise NotImplementedError("Subclasses must implement make_fig")

    def make_pdf(self):
        """Create PDF version of the plot."""
        buf_pdf = BytesIO()
        self.fig.savefig(buf_pdf, format="pdf")
        data = base64.b64encode(buf_pdf.getbuffer()).decode("ascii")
        self.pdf = f"<a href='data:image/pdf;base64,{data}' title='Plot pdf' download='{self.file_name}'>Download PDF of this graph</a>"
    
    def make_png(self):
        """Create PNG version of the plot."""
        buf_png = BytesIO()
        self.fig.savefig(buf_png, format="png", dpi=1200)
        data = base64.b64encode(buf_png.getbuffer()).decode("ascii")
        self.png = f"<img class='graph-png' width='80%' src='data:image/png;base64,{data}'/>"

    def create_plot(self):
        """Create all versions of the plot."""
        self.set_data()
        self.make_fig()
        self.make_pdf()
        self.make_png()