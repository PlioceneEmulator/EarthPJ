from flask import Blueprint, render_template, request, flash, redirect, send_file, url_for
from .render import *
import os
from io import BytesIO
import csv

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
def home():
    if request.method == "POST":
        # Handle existing plot creation logic
        if 'graphType' in request.form:
            renders = render(request.form)
            if renders['warnings'] != []:
                for message in renders['warnings']:
                    flash(message)
                return redirect(request.url)
            
            # Check if data files are available in the response
            template_args = {
                'graph': renders['graph'],
                'png': renders['png'],
                'pdf': renders['pdf']
            }
            
            # Add data_files to template args if they exist
            if 'data_files' in renders:
                template_args['data_files'] = renders['data_files']
            
            return render_template('graphs.html', **template_args)
        
        # Handle longitude/month data request
        elif 'longitude' in request.form and 'month' in request.form:
            try:
                longitude = float(request.form.get('longitude'))
                month = int(request.form.get('month'))
                color = request.form.get('color', 'viridis')
                
                if longitude is None or month is None:
                    flash('Please select both longitude and month')
                    return redirect(request.url)
                
                viewer = LongLatMonthPlot(longitude=longitude, month=month, color=color)
                viewer.create_plot()
                
                return render_template('graphs.html', 
                                     png=viewer.png,
                                     pdf=viewer.pdf)
                                     
            except (ValueError, TypeError) as e:
                flash('Please select valid longitude and month values')
                return redirect(request.url)
            except Exception as e:
                flash(f'Error retrieving data: {str(e)}')
                return redirect(request.url)
    
    return render_template('home.html')

@views.route('/download/<path:filename>')
def download_file(filename):
    """
    Download generated CSV files from the output directory
    """
    try:
        # Navigate up one directory from the website folder to the main project directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, 'output')
        file_path = os.path.join(output_dir, os.path.basename(filename))
        
        print(f"Attempting to download file: {file_path}")  # Debug print
        
        if not os.path.exists(file_path):
            flash("File not found")
            print(f"File not found at: {file_path}")  # Debug print
            return redirect(url_for('views.home'))
            
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        flash(f"Error downloading file: {str(e)}")
        print(f"Download error: {str(e)}")  # Debug print
        return redirect(url_for('views.home'))

@views.route('/download_timeseries/<variable>')
def download_timeseries(variable):
    """
    Download time series data as CSV
    """
    try:
        # Navigate up one directory from the website folder to the main project directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, 'output')
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        filename = f'timeseries_{variable}.csv'
        file_path = os.path.join(output_dir, filename)
        
        print(f"Generating time series file: {file_path}")  # Debug print
        
        # Generate the data
        plot = TimeSeriesPlot(variable=variable)
        values, times = plot.get_time_period_data(0)  # Time period doesn't matter for time series
        
        # Write data to CSV file
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Year', variable.capitalize()])
            for t, v in zip(times, values):
                writer.writerow([f'{t:.2f}', f'{v:.6f}'])
        
        print(f"File generated successfully at: {file_path}")  # Debug print
        
        if not os.path.exists(file_path):
            flash("Error generating time series file")
            print(f"Generated file not found at: {file_path}")  # Debug print
            return redirect(url_for('views.home'))
            
        return send_file(
            file_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f"Error generating time series data: {str(e)}")
        print(f"Time series generation error: {str(e)}")  # Debug print
        return redirect(url_for('views.home'))