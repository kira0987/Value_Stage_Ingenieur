import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox

# Create the main window
root = tk.Tk()
root.title("CSV Viewer")
root.geometry("800x400")

# Function to load and display CSV
def load_csv():
    file_path = filedialog.askopenfilename(
        title="Select CSV file",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    if not file_path:
        return
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file_path, encoding='windows-1256')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file: {e}")
            return
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read file: {e}")
        return
    # Display first 5 rows
    text.delete(1.0, tk.END)
    text.insert(tk.END, df.head().to_string(index=False))

# Add a button to load CSV
btn = tk.Button(root, text="Open CSV", command=load_csv)
btn.pack(pady=10)

# Add a text widget to display the dataframe
text = tk.Text(root, wrap=tk.NONE, font=("Courier", 10))
text.pack(expand=True, fill=tk.BOTH)

# Start the Tkinter event loop
root.mainloop()
