import json
import os
import re
import arcpy
import requests
import tkinter as tk
from tkinter import messagebox
from tkinter.filedialog import askdirectory


# Function to sanitize layer names for ArcGIS
def sanitize_layer_name(name):
    sanitized_name = re.sub(r'\W+', '_', name)
    sanitized_name = sanitized_name.strip('_')
    if sanitized_name and not sanitized_name[0].isalpha():
        sanitized_name = 'Layer_' + sanitized_name
    return sanitized_name

# Function to process each layer individually
def process_layer(layer_num, layer_name, output_gdb, base_url):
    sanitized_layer_name = sanitize_layer_name(layer_name)
    url = f"{base_url}/{layer_num}/query"
    metadata_url = f"{base_url}/{layer_num}?f=json"  # URL to fetch metadata
    debug_text.insert(tk.END, f"Processing layer {layer_num} - {layer_name} from URL: {url}\n")
    debug_text.see(tk.END)  # Scroll to the end

    params = {
        'where': '1=1',
        'outFields': '*',
        'returnGeometry': True,
        'f': 'json'
    }

    response = requests.get(url, params=params)
    metadata_response = requests.get(metadata_url)

    if response.status_code == 200 and response.json().get("features"):
        json_data = response.json()
        json_path = rf'C:\NLSA_Test\Scripts\featureserver_script\{sanitized_layer_name}_features.json'
        output_fc = os.path.join(output_gdb, f'{sanitized_layer_name}_fc')
        os.makedirs(os.path.dirname(json_path), exist_ok=True)

        try:
            with open(json_path, 'w') as f:
                json.dump(json_data, f)

            arcpy.JSONToFeatures_conversion(json_path, output_fc)
            debug_text.insert(tk.END, f"Conversion to Feature Class completed: {output_fc}\n")
            debug_text.see(tk.END)

            # Calculate area and length if applicable
            geometry_type = arcpy.Describe(output_fc).shapeType
            area_field_candidates = ['Shape_Area', 'Area']
            length_field_candidates = ['Shape_Length', 'Length']

            fields = [f.name for f in arcpy.ListFields(output_fc)]
            area_field = next((field for field in area_field_candidates if field in fields), None)
            length_field = next((field for field in length_field_candidates if field in fields), None)

            with arcpy.da.UpdateCursor(output_fc, ['SHAPE@'] + ([area_field] if area_field else []) + ([length_field] if length_field else [])) as update_cursor:
                for row in update_cursor:
                    if row[0] is not None:
                        row_data = list(row)

                        if geometry_type == "Polygon":
                            if area_field:
                                row_data[1] = row[0].getArea("PLANAR", "SQUAREMETERS")
                            if length_field:
                                row_data[2 if area_field else 1] = row[0].getLength("PLANAR", "METERS")

                        elif geometry_type == "Polyline" and length_field:
                            row_data[1] = row[0].getLength("PLANAR", "METERS")

                        update_cursor.updateRow(row_data)

            debug_text.insert(tk.END, f"Area and length calculations completed for: {output_fc}\n")
            debug_text.see(tk.END)

            # NEW: Apply metadata from API response to the feature class
            if metadata_response.status_code == 200:
                metadata = metadata_response.json()
                fc_metadata = arcpy.metadata.Metadata(output_fc)
                fc_metadata.title = metadata.get("name", layer_name)
                fc_metadata.tags = metadata.get("type", "Layer")
                fc_metadata.summary = metadata.get("description", "No description provided.")
                fc_metadata.credits = metadata.get("copyrightText", "")
                fc_metadata.save()
                debug_text.insert(tk.END, f"Metadata applied to Feature Class: {output_fc}\n")
                debug_text.see(tk.END)
            else:
                debug_text.insert(tk.END, f"Failed to retrieve metadata for layer {layer_num} (Status Code: {metadata_response.status_code})\n")
                debug_text.see(tk.END)

        except Exception as e:
            debug_text.insert(tk.END, f"An error occurred while processing layer {layer_num} ({layer_name}): {e}\n")
            debug_text.see(tk.END)
    else:
        debug_text.insert(tk.END, f"No data or request error for layer {layer_num} ({layer_name}) (Status Code: {response.status_code})\n")
        debug_text.see(tk.END)

# Function to start the processing
def start_processing():
    output_gdb = gdb_entry.get()
    base_url = api_entry.get()

    if not os.path.exists(output_gdb):
        debug_text.insert(tk.END, f"Geodatabase path does not exist: {output_gdb}\n")
        debug_text.see(tk.END)
        return

    selected_layers = [layer_id for layer_id, var in layer_vars.items() if var.get() == 1]

    if not selected_layers:
        messagebox.showinfo("No Layers Selected", "Please select at least one layer to process.")
        return

    for layer_id in selected_layers:
        layer_name = layer_info_dict[layer_id]['name']
        process_layer(layer_id, layer_name, output_gdb, base_url)
    debug_text.insert(tk.END, "Processing completed for all selected layers.\n")
    debug_text.see(tk.END)

# Function to retrieve and display layers in a pop-out window for selection
def fetch_layers():
    base_url = api_entry.get()
    layer_info_url = f"{base_url}?f=json"
    layer_info_response = requests.get(layer_info_url)

    if layer_info_response.status_code == 200:
        layer_info = layer_info_response.json()
        layers = layer_info.get("layers", [])

        global layer_vars, layer_info_dict
        layer_vars = {}
        layer_info_dict = {}

        # Create a pop-out window
        layer_window = tk.Toplevel(root)
        layer_window.title("Select Layers")

        # Add checkboxes for each layer
        for layer in layers:
            layer_id = layer['id']
            layer_info_dict[layer_id] = layer
            var = tk.IntVar()
            layer_vars[layer_id] = var
            tk.Checkbutton(layer_window, text=layer["name"], variable=var).pack(anchor='w')

        # Button to close the pop-out window
        tk.Button(layer_window, text="Done", command=layer_window.destroy).pack()
    else:
        debug_text.insert(tk.END, f"Failed to retrieve layer metadata (Status Code: {layer_info_response.status_code})\n")
        debug_text.see(tk.END)

# Function to open file dialog and set geodatabase path
def browse_gdb():
    file_path = askdirectory(title="Select Geodatabase")
    if file_path:
        gdb_entry.delete(0, tk.END)  # Clear the entry box
        gdb_entry.insert(0, file_path)  # Insert the selected file path

# GUI Setup
root = tk.Tk()
root.title("REST to GDB")

# Input fields in the main GUI
tk.Label(root, text="Geodatabase Location:").pack()
gdb_entry = tk.Entry(root)
gdb_entry.pack()

# Add a browse button for the geodatabase
browse_button = tk.Button(root, text="Browse", command=browse_gdb)
browse_button.pack()

tk.Label(root, text="API Link:").pack()
api_entry = tk.Entry(root)
api_entry.pack()

fetch_button = tk.Button(root, text="Fetch Layers", command=fetch_layers)
fetch_button.pack()

# Button to trigger processing
process_button = tk.Button(root, text="Process Selected Layers", command=start_processing)
process_button.pack()

# Debug Text Box
debug_text = tk.Text(root, height=10, width=80)
debug_text.pack()

# Run the GUI
root.mainloop()
