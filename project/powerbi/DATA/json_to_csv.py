import json
import csv
import tkinter as tk
from tkinter import filedialog
import os

# Initialize tkinter
root = tk.Tk()
root.withdraw()  # Hide the main window

# Open dialog to select input JSON file
input_file = filedialog.askopenfilename(
    title="Select JSON file",
    filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
)

if not input_file:
    print("No input file selected. Exiting.")
    exit()

# Open dialog to select output CSV file location
output_file = filedialog.asksaveasfilename(
    title="Save CSV file as",
    defaultextension=".csv",
    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
)

if not output_file:
    print("No output file selected. Exiting.")
    exit()

# Read the JSON file
try:
    with open(input_file, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

    # Extract field names for CSV header
    fields = [field['id'] for field in data['fields']]

    # Write to CSV file
    with open(output_file, 'w', encoding='utf-8', newline='') as csv_file:
        writer = csv.writer(csv_file)
        
        # Write header
        writer.writerow(fields)
        
        # Write records
        for record in data['records']:
            writer.writerow(record)

    print(f"CSV file '{os.path.basename(output_file)}' has been created successfully.")

except Exception as e:
    print(f"An error occurred: {str(e)}")

# Destroy the tkinter instance
root.destroy()