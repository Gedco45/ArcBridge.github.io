import requests
import tkinter as tk
from tkinter import filedialog
import os
import datetime


# Function to fetch layers and save images to a folder
def fetch_layers():
    base_url = api_entry.get()  # Get the API link from the entry widget
    selected_format = format_var.get()  # Get the selected format from dropdown
    layer_selection = layers_entry.get()



    # Request parameters
    params = {
        'f': 'image',  # Response format (image)
        'bbox': '-2271872.583082739,1386016.2667604391,-60872.5830827388,3783016.266760439',  # Bounding box
        'layers': f'show:{layer_selection}',  # Uses the input layers from the GUI
        'bboxSR': '102002',   # Spatial reference system
        'size': '800,600',  # Image size
        'format': selected_format.lower(),  # Image format based on user selection
        'transparent': True  # enables transparency for the image background
    }

    print(f"Making request to: {base_url} with params {params}")
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        print("Request successful.")
        save_folder = os.path.normpath(output_entry.get())  # Folder path from the entry widget

        # Ensure the save folder is valid
        if not save_folder:
            print("Error: No folder path selected.")
            debug_text.insert(tk.END, "Error: No folder path selected.\n")
            return

        # Ensure the directory exists
        if not os.path.exists(save_folder):
            print(f"Directory '{save_folder}' does not exist, creating it...")
            try:
                os.makedirs(save_folder)
            except PermissionError:
                print(f"Error: Permission denied when trying to create directory '{save_folder}'.")
                debug_text.insert(tk.END, f"Error: Permission denied when trying to create directory '{save_folder}'.\n")
                return

        # Generate a filename (e.g., using the current timestamp or an incremental approach)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_input = outputname_entry.get()
        filename = filename = f"{filename_input}_image_{timestamp}.{selected_format.lower()}"
        save_path = os.path.join(save_folder, filename)

        # Save the image to the file
        try:
            with open(save_path, 'wb') as file:
                file.write(response.content)
            print(f"Image saved as '{save_path}'")
            debug_text.insert(tk.END, f"Image saved as '{save_path}'\n")
        except PermissionError:
            print(f"Error: Permission denied when trying to save image to '{save_path}'.")
            debug_text.insert(tk.END, f"Error: Permission denied when trying to save image to '{save_path}'.\n")
        except Exception as e:
            print(f"Error: Failed to save image due to {e}")
            debug_text.insert(tk.END, f"Error: Failed to save image due to {e}\n")
    else:
        print(f"Error: Failed to fetch image. Status code: {response.status_code}")
        debug_text.insert(tk.END, f"Error: Failed to fetch image. Status code: {response.status_code}\n")

# Function to browse and select a save location (folder)
def browse_gdb():
    selected_format = format_var.get()  # Get selected format
    file_extension = f".{selected_format.lower()}"  # Use chosen format as file extension

    # Ask the user to select a folder (not a file)
    folder_path = filedialog.askdirectory()  # Ask for folder path, not a file
    if not folder_path:
        print("Error: No folder selected.")
        debug_text.insert(tk.END, "Error: No folder selected.\n")
        return

    output_entry.delete(0, tk.END)
    output_entry.insert(0, folder_path)

# GUI Setup
root = tk.Tk()
root.title("Imagery_to_Desktop")

# Input fields in the main GUI
tk.Label(root, text="Output Location").pack()
output_entry = tk.Entry(root)
output_entry.pack()

# Add a browse button for the folder
browse_button = tk.Button(root, text="Browse", command=browse_gdb)
browse_button.pack()

#API input link
tk.Label(root, text="API Link:").pack()
api_entry = tk.Entry(root)
api_entry.pack()

#Layer selection input
tk.Label(root, text= "Layer from API:").pack()
layers_entry = tk.Entry(root)#Entry widget for layers
layers_entry.pack()

# Name the output image
tk.Label(root, text="Output name:").pack()
outputname_entry = tk.Entry(root)
outputname_entry.pack()

# A dropdown menu for format selection for the images
tk.Label(root, text="Select Format:").pack()
format_var = tk.StringVar(value="PNG")  # Default format
format_menu = tk.OptionMenu(root, format_var, "PDF", "PNG32", "PNG24", "PNG", "JPG", "DIB", "TIFF", "EMF", "PS", "GIF", "SVG", "SVGZ", "BMP")
format_menu.pack()

# Button to fetch layers based on the API link
fetch_button = tk.Button(root, text="Fetch Layer", command=fetch_layers)
fetch_button.pack()

# Debug Text Box
debug_text = tk.Text(root, height=10, width=80)
debug_text.pack()

# Run the GUI
root.mainloop()
