def check_file(self):
    """Verify that the data file exists and can be opened."""
    import os
    
    file = "netcdf_files/test_data_4000-4050.nc"
    
    # Check if file exists
    if not os.path.exists(file):
        print(f"File not found: {file}")
        print(f"Current working directory: {os.getcwd()}")
        print("Contents of current directory:")
        print(os.listdir('.'))
        if os.path.exists('netcdf_files'):
            print("\nContents of netcdf_files directory:")
            print(os.listdir('netcdf_files'))
        return False
        
    # Try opening the file
    try:
        with xr.open_dataset(file) as ds:
            print("\nFile successfully opened")
            print("Available variables:", list(ds.variables))
            print("\nTS variable info:")
            print(ds.TS)
            return True
    except Exception as e:
        print(f"Error opening file: {str(e)}")
        return False