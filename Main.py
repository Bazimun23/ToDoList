import ttkbootstrap as ttk
from ui import TodoUI

# Create the main window
app = ttk.Window(themename="flatly")
app.title("To-Do App")
app.geometry("1200x700")
app.minsize(1000, 600)

# Create the UI
TodoUI(app)

# Start the application
app.mainloop()