from temperature_surface import TemperatureSurfacePlot
from temperature_elevation import TemperatureElevation
from precipitation_rate import PrecipitationRatePlot
from long_lat_month import LongLatMonthPlot
from global_average import GlobalAveragePlot
from time_series import TimeSeriesPlot
from difference_plot import DifferencePlot
from difference_line import LineDifferencePlot
import mpld3

# render the graphs based on user selections
def render(html_data):
    print(f"\nhtml data:\n{html_data}\n")
    data = {}
    warning_messages = []

    # Extract graph type first
    data["graphType"] = html_data.getlist('graphType')
    if data["graphType"] == []:
        warning_messages.append('Must select a graph type')
    
    # Get plot variable
    data["plots"] = html_data.getlist('graphVariable')
    if data["plots"] == []:
        warning_messages.append('Must select a variable to plot')

    # Handle time periods based on graph type
    is_compare_mode = data["graphType"] and data["graphType"][0] == 'compare'
    
    if is_compare_mode:
        data["timePeriods"] = html_data.getlist('compareTimePeriod')
        if len(data["timePeriods"]) != 2:
            warning_messages.append('Must select two time periods to compare')
    else:
        data["timePeriods"] = html_data.getlist('singleTimePeriod')
        if len(data["timePeriods"]) != 1:
            warning_messages.append('Must select one time period')

    # Get other parameters
    data["color"] = html_data["color"] if is_compare_mode else html_data.get("color", "viridis")
    data["elevation"] = int(html_data["elevation"])
    data["months"] = html_data.getlist('month')

    # Check months requirement for spatial plots
    data["plots_requiring_months"] = ["tempSfc", "tempElev", "pcpRate", "longLatMonth"]
    if data["months"] == [] and any(plot in data["plots_requiring_months"] for plot in data["plots"]):
        warning_messages.append('Must select at least one month')

    # Handle coordinates
    if "globalTempAvg" in data["plots"] or "globalPrecipAvg" in data["plots"]:
        data["min_longitude"] = int(html_data.get("global_min_lon", "-180"))
        data["max_longitude"] = int(html_data.get("global_max_lon", "180"))
        data["min_latitude"] = int(html_data.get("global_min_lat", "-90"))
        data["max_latitude"] = int(html_data.get("global_max_lat", "90"))
    else:
        data["min_longitude"] = int(html_data["min_longitude"]) if html_data["min_longitude"] != '' else -180
        data["max_longitude"] = int(html_data["max_longitude"]) if html_data["max_longitude"] != '' else 180
        data["min_latitude"] = int(html_data["min_latitude"]) if html_data["min_latitude"] != '' else -90
        data["max_latitude"] = int(html_data["max_latitude"]) if html_data["max_latitude"] != '' else 90

    # Validate coordinates
    coordinate_prefix = "Global plot: " if ("globalTempAvg" in data["plots"] or "globalPrecipAvg" in data["plots"]) else ""
    if data["min_longitude"] >= data["max_longitude"]:
        warning_messages.append(f'{coordinate_prefix}Minimum longitude value must be less than maximum longitude value')
    if data["min_latitude"] >= data["max_latitude"]:
        warning_messages.append(f'{coordinate_prefix}Minimum latitude value must be less than maximum latitude value')

    data["num_std_dev"] = int(html_data["num_std_dev"]) if html_data["num_std_dev"] else 2

    if warning_messages:
        return {"warnings": warning_messages}

    print(f"\nparsed data:\n{data}\n")
    response = None

    # Get the show_percent parameter - add this near the start of the function
    show_percent = bool(html_data.get("show_percent", False))
    print(f"Debug - show_percent value: {show_percent}")

    # Handle plotting based on selection
    for plot in data["plots"]:
        print(f"User is requesting a {plot} plot")

        # For spatial plots in compare mode
        if is_compare_mode and plot in ["tempSfc", "tempElev", "pcpRate"]:
            variable = "temperature" if plot in ["tempSfc", "tempElev"] else "precipitation"
            testPlot = DifferencePlot(
                months=data["months"],
                time_periods=data["timePeriods"],
                variable=variable,
                color=data["color"],
                min_longitude=data["min_longitude"],
                max_longitude=data["max_longitude"],
                min_latitude=data["min_latitude"],
                max_latitude=data["max_latitude"],
                central_longitude=0,
                num_std_dev=data["num_std_dev"]
            )
            testPlot.show_percent = show_percent

        else:
            # Handle non-difference plots as before
            if plot == "tempSfc":
                testPlot = TemperatureSurfacePlot(
                    months=data["months"],
                    time_periods=data["timePeriods"],
                    color=data["color"],
                    min_longitude=data["min_longitude"],
                    max_longitude=data["max_longitude"],
                    min_latitude=data["min_latitude"],
                    max_latitude=data["max_latitude"],
                    central_longitude=0,
                    num_std_dev=data["num_std_dev"]
                )

            elif plot == "tempElev":
                testPlot = TemperatureElevation(
                    months=data["months"],
                    time_periods=data["timePeriods"],
                    elevation=data["elevation"],
                    color=data["color"],
                    min_longitude=data["min_longitude"],
                    max_longitude=data["max_longitude"],
                    min_latitude=data["min_latitude"],
                    max_latitude=data["max_latitude"],
                    central_longitude=0,
                    num_std_dev=data["num_std_dev"]
                )

            elif plot == "pcpRate":
                # Create precipitation rate plot
                testPlot = PrecipitationRatePlot(
                    months= data["months"], 
                    time_periods = data["timePeriods"], 
                    color = data["color"], 
                    min_longitude=data["min_longitude"], 
                    max_longitude=data["max_longitude"], 
                    min_latitude=data["min_latitude"], 
                    max_latitude=data["max_latitude"], 
                    central_longitude=0,
                    num_std_dev=data["num_std_dev"])

            elif plot == "longLatMonth":
                testPlot = LongLatMonthPlot(
                    months=data["months"],
                    time_periods=data["timePeriods"],
                    color=data["color"],
                    min_longitude=data["min_longitude"],
                    max_longitude=data["max_longitude"],
                    min_latitude=data["min_latitude"],
                    max_latitude=data["max_latitude"],
                    central_longitude=0,
                    num_std_dev=data["num_std_dev"])
            
            elif plot == "globalTempAvg":
                testPlot = GlobalAveragePlot(
                    time_periods=data["timePeriods"],
                    variable="temperature",
                    color=data["color"],
                    min_longitude=data["min_longitude"],
                    max_longitude=data["max_longitude"],
                    min_latitude=data["min_latitude"],
                    max_latitude=data["max_latitude"],
                    num_std_dev=data["num_std_dev"])
        
            elif plot == "globalPrecipAvg":
                testPlot = GlobalAveragePlot(
                    time_periods=data["timePeriods"],
                    variable="precipitation",
                    color=data["color"],
                    min_longitude=data["min_longitude"],
                    max_longitude=data["max_longitude"],
                    min_latitude=data["min_latitude"],
                    max_latitude=data["max_latitude"],
                    num_std_dev=data["num_std_dev"])
                
            elif plot == "tempTimeSeries":
                testPlot = TimeSeriesPlot(
                    variable="temperature",
                    color=data["color"],
                    min_longitude=data["min_longitude"],
                    max_longitude=data["max_longitude"],
                    min_latitude=data["min_latitude"],
                    max_latitude=data["max_latitude"],
                    num_std_dev=data["num_std_dev"]
                )

            # For precipitation time series
            elif plot == "precipTimeSeries":
                testPlot = TimeSeriesPlot(
                    variable="precipitation",
                    color=data["color"],
                    min_longitude=data["min_longitude"],
                    max_longitude=data["max_longitude"],
                    min_latitude=data["min_latitude"],
                    max_latitude=data["max_latitude"],
                    num_std_dev=data["num_std_dev"]
                )
                testPlot.show_percent = show_percent  # Only affects precipitation

            elif plot == "difference":
                if len(data["timePeriods"]) != 2:
                    warning_messages.append('Must select exactly two time periods for difference plot')
                    return {"warnings": warning_messages}
                    
                testPlot = DifferencePlot(
                    months=data["months"],
                    time_periods=data["timePeriods"],
                    variable=html_data.get("diffVariable", "temperature"),
                    color=data["color"],
                    min_longitude=data["min_longitude"],
                    max_longitude=data["max_longitude"],
                    min_latitude=data["min_latitude"],
                    max_latitude=data["max_latitude"],
                    central_longitude=0,
                    num_std_dev=data["num_std_dev"]
                )

            # For line difference plots
            elif plot == "longLatMonth" and is_compare_mode:
                testPlot = LineDifferencePlot(
                    months=data["months"],
                    time_periods=data["timePeriods"],
                    plot_type="longitude",
                    variable=variable,
                    color=data["color"],
                    min_longitude=data["min_longitude"],
                    max_longitude=data["max_longitude"],
                    min_latitude=data["min_latitude"],
                    max_latitude=data["max_latitude"],
                    num_std_dev=data["num_std_dev"]
                )
                testPlot.show_percent = show_percent

         # Create and handle the plot
        try:
            testPlot.create_plot()

            # Handle response based on plot type
            if plot in ["globalTempAvg", "globalPrecipAvg"]:
                avg_file, std_file = testPlot.export_to_csv()
                response = {
                    "graph": mpld3.fig_to_html(testPlot.fig),
                    "png": testPlot.png,
                    "pdf": testPlot.pdf,
                    "warnings": warning_messages,
                    "data_files": {
                        "averages": avg_file,
                        "std_dev": std_file
                    }
                }
            else:
                response = {
                    "graph": mpld3.fig_to_html(testPlot.fig),
                    "png": testPlot.png,
                    "pdf": testPlot.pdf,
                    "warnings": warning_messages
                }

        except Exception as e:
            print(f"Error creating plot: {str(e)}")
            warning_messages.append(f"Error creating plot: {str(e)}")
            return {"warnings": warning_messages}

    return response