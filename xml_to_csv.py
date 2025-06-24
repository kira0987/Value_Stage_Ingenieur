import os
import glob
import xml.etree.ElementTree as ET
import pandas as pd
from tkinter import Tk, filedialog

# Hide the main tkinter window
root = Tk()
root.withdraw()

# Open file dialog to select XML files
xml_files = filedialog.askopenfilenames(
    title="Select XML files to convert",
    filetypes=[("XML files", "*.xml")]
)

# Convert tuple to list
xml_files = list(xml_files)

def xml_to_dataframe(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    # Assume the first level of children are records
    records = []
    for record in root:
        row = {}
        for elem in record:
            row[elem.tag] = elem.text
        records.append(row)
    return pd.DataFrame(records)

for xml_file in xml_files:
    df = xml_to_dataframe(xml_file)
    csv_file = os.path.splitext(xml_file)[0] + '.csv'
    df.to_csv(csv_file, index=False)
    print(f"Converted {xml_file} to {csv_file}") 

