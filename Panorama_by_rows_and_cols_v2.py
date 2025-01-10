import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import os
import subprocess
import sys

def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"command '{command}' failed with exit code {e.returncode}")
        sys.exit(1)
        

def get_fov():
    fov = simpledialog.askstring("Field of View", "Enter the field of view in degrees:", initialvalue="2.5", parent=root)
    if not fov:
        print("No field of view entered.")
        sys.exit(1)
    return fov

def select_files():
    #set the path for the default_dir file
    default_dir_path = os.path.expanduser("~/.default_dir")

    #determine the initial default directory
    if os.path.exists(default_dir_path):
        default_dir = open(default_dir_path, "r").read().strip()
    # If the .default_dir file does not exist or is empty, use ~/Desktop 
    else:
        default_dir = os.path.join(os.path.expanduser("~"), "Desktop")
    # Open the file selection dialog with the initial directory set
    files = filedialog.askopenfilenames(title="Select more than 2 images", initialdir=default_dir, filetypes=[("Image files", "*.TIF *.TIFF *.tif *.tiff *.jpg *.JPG")])
    if not files:
        print("No files selected. Exiting.")
        sys.exit(1)
    if files:
        #Get the directory of the first selected file
        selected_dir = os.path.dirname(files[0])
        #Write the selected directory to .default_dir
        with open(default_dir_path, "w") as f:
            f.write(selected_dir)
        return files
    else:
        print("No files selected. Exiting.")

#determine the number of rows and columns
def get_rows_columns(num_files):
    #loop to prompt the user for the number of rows and columns
    #until a valid combination of rows and columns is entered
    #open a single window 2 boxes for the user to enter the number of rows and columns
    #rows or columns can be left blank and the program will calculate the missing dimension
    #if both are left blank the program will exit
    #if the number of files chosen is not divisible by the number of rows or columns the program will exit
    #all prompts are displayed in a single window and the user can cancel the program if they wish
    while True:
        num_rows = simpledialog.askinteger("Grid Dimensions", "Enter number of Rows", parent=root)
        num_columns = simpledialog.askinteger("Grid Dimensions", "Enter number of Columns", parent=root)

        if not num_rows and not num_columns:
            messagebox.showwarning("Error", "You must specify at least one dimension (rows or columns).", parent=root)
            continue

        if num_rows and num_columns and num_files != num_rows * num_columns:
            messagebox.showwarning("Error", f"The number of files cannot be arranged into a grid of {num_columns} columns and {num_rows} rows.", parent=root)
            continue

        if not num_rows:
            if num_files % num_columns == 0:
                num_rows = num_files // num_columns
            else:
                messagebox.showwarning("Error", f"{num_files} files can't be arranged in {num_columns} columns.", parent=root)
                continue
        elif not num_columns:
            if num_files % num_rows == 0:
                num_columns = num_files // num_rows
            else:
                messagebox.showwarning("Error", f"{num_files} files can't be arranged in {num_rows} rows.", parent=root)
                continue

        return num_rows, num_columns
#create projects by rows and columns using panotools 
def create_projects(selected_files, fov, num_columns, by_row=True): 
    if by_row:
        descriptor = "row"
    else:
        descriptor = "column"

    for index in range(1, (len(selected_files) // num_columns) + 1):
        if by_row:
            files = selected_files[(index-1)*num_columns : index*num_columns]
        else:
            files = [selected_files[i] for i in range(index-1, len(selected_files), num_columns)]

        print(f"\n{descriptor}{index}:\n{files}\n")
        run_command(f"pto_gen --projection=0 -s 1 --fov={fov} -o {descriptor}{index}.pto {' '.join(files)}")
        run_command(f"cpfind -o {descriptor}{index}.pto --linearmatch {descriptor}{index}.pto")
        run_command(f"pto_var -o {descriptor}{index}.pto --opt r,TrX,TrY,!r0,!TrX0,!TrY0 {descriptor}{index}.pto")
        run_command(f"pano_modify --projection=0 -o {descriptor}{index}.pto {descriptor}{index}.pto")
        run_command(f"autooptimiser -n -o auto_optim_{descriptor}{index}.pto {descriptor}{index}.pto")

def main():
    # Prompt for FOV
    fov = get_fov()

    # File selection
    files = []
    while len(files) < 2:
        files = select_files()
        if len(files) < 2:
            messagebox.showwarning("Error", f"Only {len(files)} files selected. Select at least 2 files.")

    selected_dir = os.path.dirname(files[0])
    os.chdir(selected_dir)
    selected_files = [os.path.basename(f) for f in files]
    num_files = len(selected_files)

    # Save selected_dir in a file for future use in scripts
    with open(os.path.expanduser("~/.default_dir"), "w") as f:
        f.write(selected_dir)

    # Get rows and columns
    num_rows, num_columns = get_rows_columns(num_files)
    messagebox.showinfo("Confirmation", f"Panorama Grid:\n{num_columns} columns\nby\n{num_rows} rows.")

    # Create projects by rows
    if num_rows > 1:    
        create_projects(selected_files, fov, num_columns, by_row=False)
    else:
        messagebox.showinfo("Info", "Only one row detected.\nNo projects will be created by column.")

    # Create projects by columns
    if num_columns > 1:
        create_projects(selected_files, fov, num_rows, by_row=True) 
    else:
        messagebox.showinfo("Info", "Only one column detected.\nNo projects will be created by row.")

    messagebox.showinfo("Info", "Rows and Columns projects created successfully!")

   #if only one .pto file whose name starts with "auto_optim" file exists, use it to create additional projects,
   #assign the name of the file to the variable "source_pto"
   #else merge all auto_optim_ files into one named merged pto file and assign its name to the variable "source_pto" 

    if len([f for f in os.listdir() if f.startswith("auto_optim")]) == 1:
        source_pto = [f for f in os.listdir() if f.startswith("auto_optim")][0]
    else:
        source_pto = "merged.pto"
        run_command(f"pto_merge -o {source_pto} {' '.join([f for f in os.listdir() if f.startswith('auto_optim')])}")

    messagebox.showinfo("Info", "Projects merged successfully!")

    # Iterate trough the number of files selected and use pto_lensstack to assign a new lens to each image in the project
    for j in range(num_files):
        print (f"assigning lens for image index {j}")
        run_command(f"pto_lensstack -o {source_pto}  --new-lens i{j} {source_pto}") 

    messagebox.showinfo("Info", "Lenses assigned successfully!")

    #modify the projection to rectilinear
    run_command(f"pano_modify --projection=0 -o rectilinear_{source_pto} {source_pto}")

    messagebox.showinfo("Info", "Rectilinear projection created successfully!")
    #use pto_var to use r, TrX, TrY and exclude r0, TrX0, TrY0 from the optimisation.
    run_command(f"pto_var -o optimised_{source_pto} --opt r,TrX,TrY,!r0,!TrX0,!TrY0 rectilinear_{source_pto}")
    #use autooptimiser to create a final optimised pto file.
    run_command(f"autooptimiser -n -o final_{source_pto} optimised_{source_pto}")       

    messagebox.showinfo("Info", "Optimised pto file created successfully!")

   #run the main function when the script is executed directly 

if __name__ == "__main__":
    root = tk.Tk()
    #root.withdraw()  # Hide main window
    main()

