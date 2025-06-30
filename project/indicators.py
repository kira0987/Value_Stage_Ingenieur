# Import required libraries
import wbgapi as wb
import pandas as pd
import sys

# Function to fetch all indicators for Tunisia (2018-2025)
def fetch_tunisia_indicators():
    try:
        # Set the World Bank database to World Development Indicators (default is db=2)
        wb.db = 2
        
        # Fetch all indicators for Tunisia ('TUN') from 2018 to 2025
        df = wb.data.DataFrame('all', 'TUN', time=range(2018, 2027))
        
        # Check if DataFrame is empty
        if df.empty:
            print("No data retrieved. Check the World Bank API or data availability for 2025.")
            return None
        
        # Reset index to make series and years columns
        df = df.reset_index()
        
        # Save the data to a CSV file
        output_file = 'tunisia_indicators_2018_2026.csv'
        df.to_csv(output_file, index=False)
        print(f"Data successfully saved to {output_file}")
        
        return df
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

# Main execution
if __name__ == "__main__":
    try:
        # Ensure wbgapi is installed
        import wbgapi
    except ImportError:
        print("wbgapi not found. Installing now...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "wbgapi"])
        import wbgapi
    
    # Fetch and process the data
    result = fetch_tunisia_indicators()
    
    # Display the first few rows of the DataFrame if data was retrieved
    if result is not None:
        print("\nFirst few rows of the retrieved data:")
        print(result.head())
    else:
        print("Failed to retrieve data.")