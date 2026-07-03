import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog

class Task:
    def __init__(self, task, section, completed=False, flagged=False, category="General", is_yearly=False, yearly_date=""):
        self.task = task
        self.section = section
        self.completed = completed
        self.flagged = flagged
        self.category = category        # Track custom category list layout (e.g., Work, Study)
        self.is_yearly = is_yearly      # True if it's a yearly repeating reminder
        self.yearly_date = yearly_date  # Format: "MM-DD" (e.g., "12-25" for Dec 25)


class TodoUI:
    def __init__(self, app):
        self.app = app
        self.tasks = []
        
        # Tracking states
        self.current_filter = "All"      # General view tracker ("Today", "Flagged", "Completed", "All")
        self.current_category = None     # Track if a specific custom list is active (e.g., "Work")
        self.search_query = ""           
        
        # Pomodoro Timer Variables
        self.timer_running = False
        self.time_left = 25 * 60         # Default 25 minutes in seconds
        self.timer_id = None             # Tracks the Tkinter after() loop object
        
        # Predefined structural lists
        self.custom_lists = ["📝 Reminders", "💼 Work", "📚 Study", "🏠 Personal"]
        
        # Mapping generic keywords to text headers with icons for the right side
        self.filter_titles = {
            "Today": "📅 Today",
            "All": "📂 All Tasks",
            "Flagged": "🚩 Flagged",
            "Completed": "✅ Completed"
        }
        
        self.create_sidebar()
        self.create_main()
        self.load_tasks_from_file()

    def create_sidebar(self):
        # Clean re-initialization if sidebar layout updates dynamically
        if hasattr(self, 'sidebar'):
            self.sidebar.destroy()

        self.sidebar = ttk.Frame(self.app, width=280)
        self.sidebar.pack(side=LEFT, fill=Y)

        # Search Box
        self.search = ttk.Entry(self.sidebar, bootstyle="secondary")
        self.search.pack(fill=X, padx=15, pady=(20, 15))
        self.search.insert(0, "🔍 Search")
        
        self.search.bind("<KeyRelease>", self.search_tasks)
        self.search.bind("<FocusIn>", lambda e: self.search.delete(0, END) if self.search.get() == "🔍 Search" else None)
        self.search.bind("<FocusOut>", lambda e: self.search.insert(0, "🔍 Search") if self.search.get().strip() == "" else None)

        # Standard Tasks Navigation
        ttk.Label(
            self.sidebar,
            text="Tasks",
            font=("Arial", 16, "bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        menu = [
            ("📅 Today", "Today"),
            ("📂 All", "All"),
            ("🚩 Flagged", "Flagged"),
            ("✅ Completed", "Completed")
        ]

        for display_name, filter_type in menu:
            ttk.Button(
                self.sidebar,
                text=display_name,
                bootstyle="light",
                command=lambda f=filter_type: self.apply_general_filter(f)
            ).pack(fill=X, padx=15, pady=3)

        # Dynamic "My Lists" Category Section
        ttk.Label(
            self.sidebar,
            text="My Lists",
            font=("Arial", 16, "bold")
        ).pack(anchor="w", padx=15, pady=(25, 5))

        # Render custom collection lists
        for item in self.custom_lists:
            # Strip out structural emojis internally to match pure string references
            clean_name = item.split(" ", 1)[-1] if " " in item else item
            ttk.Button(
                self.sidebar, 
                text=item, 
                bootstyle="light",
                command=lambda c=clean_name, d=item: self.apply_category_filter(c, d)
            ).pack(fill=X, padx=15, pady=3)

        # Action Buttons Layout Frame (Add and Delete stacked)
        btn_frame = ttk.Frame(self.sidebar)
        btn_frame.pack(fill=X, padx=15, pady=20)

        # Functional Add Custom List button
        ttk.Button(
            btn_frame,
            text="➕ Add List",
            bootstyle="success",
            command=self.add_new_custom_list
        ).pack(fill=X, pady=3)

        # Functional Delete Custom List button
        ttk.Button(
            btn_frame,
            text="🗑️ Delete List",
            bootstyle="danger-outline",
            command=self.delete_custom_list
        ).pack(fill=X, pady=3)

    def create_main(self):
        self.main = ttk.Frame(self.app)
        self.main.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Clean Top Header (Only Title Now)
        header_frame = ttk.Frame(self.main)
        header_frame.pack(fill=X, padx=25, pady=(20, 10))

        self.title_label = ttk.Label(
            header_frame, text="📅 Today", font=("Arial", 30, "bold")
        )
        self.title_label.pack(side=LEFT, anchor="w")
        
        # Main timeframe layout segments
        self.morning_title = ttk.Label(self.main, text="🌅 Morning", font=("Arial", 16, "bold"))
        self.morning_sep = ttk.Separator(self.main)
        self.morning_frame = ttk.Frame(self.main)
        
        self.afternoon_title = ttk.Label(self.main, text="☀️ Afternoon", font=("Arial", 16, "bold"))
        self.afternoon_sep = ttk.Separator(self.main)
        self.afternoon_frame = ttk.Frame(self.main)
        
        self.tonight_title = ttk.Label(self.main, text="🌙 Tonight", font=("Arial", 16, "bold"))
        self.tonight_sep = ttk.Separator(self.main)
        self.tonight_frame = ttk.Frame(self.main)
        
        self.completed_frame = ttk.Frame(self.main)

        # Dedicated Yearly Reminders Split Frames
        self.yearly_title = ttk.Label(self.main, text="🎂 Yearly Reminders", font=("Arial", 16, "bold"))
        self.yearly_sep = ttk.Separator(self.main)
        self.yearly_frame = ttk.Frame(self.main)
        
        self.pack_main_sections()
        
        # Bottom Tool Action Bar
        self.bottom_bar = ttk.Frame(self.main)
        self.bottom_bar.pack(side=BOTTOM, fill=X, anchor="s", padx=25, pady=25)
        
        # FIXED: Changed alignment=CENTER to anchor="center"
        ttk.Button(
            self.bottom_bar,
            text="➕ Add Task",
            bootstyle="success",
            command=self.open_add_task_window
        ).pack(side=RIGHT, anchor="center")

        # Integrated Pomodoro Widget Container aligned on the Left side of the bottom bar
        self.create_pomodoro_widget(self.bottom_bar)

    def create_pomodoro_widget(self, parent):
        # Frame container packed to the left side of the bottom bar
        container_frame = ttk.Frame(parent)
        container_frame.pack(side=LEFT, anchor="w")

        # Title Label
        ttk.Label(container_frame, text="🍅 Pomodoro Timer", font=("Arial", 10, "bold"), bootstyle="primary").pack(anchor="w", padx=5)

        pomodoro_frame = ttk.Frame(container_frame, bootstyle="secondary")
        pomodoro_frame.pack(fill=BOTH, expand=True, pady=2, ipady=5, ipadx=10)

        # Time Display Label
        self.timer_label = ttk.Label(pomodoro_frame, text="25:00", font=("Arial", 18, "bold"))
        self.timer_label.pack(side=LEFT, padx=15)

        # Controls Buttons Inside Timer
        controls_frame = ttk.Frame(pomodoro_frame)
        controls_frame.pack(side=LEFT, padx=5)

        self.start_btn = ttk.Button(controls_frame, text="▶ Start", bootstyle="success-link", command=self.toggle_timer)
        self.start_btn.grid(row=0, column=0, padx=2)

        ttk.Button(controls_frame, text="🔄 Reset", bootstyle="secondary-link", command=self.reset_timer).grid(row=0, column=1, padx=2)

        # Quick Mode Selectors
        modes_frame = ttk.Frame(pomodoro_frame)
        modes_frame.pack(side=LEFT, padx=10)

        ttk.Button(modes_frame, text="Pomodoro", bootstyle="outline-primary-sm", command=lambda: self.set_timer_mode(25)).grid(row=0, column=0, padx=2)
        ttk.Button(modes_frame, text="Short Break", bootstyle="outline-success-sm", command=lambda: self.set_timer_mode(5)).grid(row=0, column=1, padx=2)
        ttk.Button(modes_frame, text="Long Break", bootstyle="outline-info-sm", command=lambda: self.set_timer_mode(15)).grid(row=0, column=2, padx=2)

    def toggle_timer(self):
        if self.timer_running:
            self.timer_running = False
            self.start_btn.config(text="▶ Start", bootstyle="success-link")
            if self.timer_id:
                self.app.after_cancel(self.timer_id)
        else:
            self.timer_running = True
            self.start_btn.config(text="⏸ Pause", bootstyle="warning-link")
            self.run_countdown()

    def run_countdown(self):
        if self.timer_running and self.time_left > 0:
            self.time_left -= 1
            mins, secs = divmod(self.time_left, 60)
            self.timer_label.config(text=f"{mins:02d}:{secs:02d}")
            self.timer_id = self.app.after(1000, self.run_countdown)
        elif self.time_left == 0:
            self.timer_running = False
            self.start_btn.config(text="▶ Start", bootstyle="success-link")
            messagebox.showinfo("Timer Finished", "Time's up! Take a well-deserved break or start your next focus session.")

    def reset_timer(self):
        if self.timer_id:
            self.app.after_cancel(self.timer_id)
        self.timer_running = False
        self.time_left = 25 * 60
        self.timer_label.config(text="25:00")
        self.start_btn.config(text="▶ Start", bootstyle="success-link")

    def set_timer_mode(self, minutes):
        if self.timer_id:
            self.app.after_cancel(self.timer_id)
        self.timer_running = False
        self.time_left = minutes * 60
        self.timer_label.config(text=f"{minutes:02d}:00")
        self.start_btn.config(text="▶ Start", bootstyle="success-link")

    def pack_main_sections(self):
        self.yearly_title.pack_forget()
        self.yearly_sep.pack_forget()
        self.yearly_frame.pack_forget()

        self.morning_title.pack(anchor="w", padx=25, pady=(10, 0))
        self.morning_sep.pack(fill=X, padx=25, pady=5)
        self.morning_frame.pack(fill=X, padx=35)
        
        self.afternoon_title.pack(anchor="w", padx=25, pady=(10, 0))
        self.afternoon_sep.pack(fill=X, padx=25, pady=5)
        self.afternoon_frame.pack(fill=X, padx=35)
        
        self.tonight_title.pack(anchor="w", padx=25, pady=(10, 0))
        self.tonight_sep.pack(fill=X, padx=25, pady=5)
        self.tonight_frame.pack(fill=X, padx=35)
        
        self.completed_frame.pack_forget()

    def pack_reminders_sections(self):
        self.morning_title.config(text="📌 Standard Reminders")
        self.morning_title.pack(anchor="w", padx=25, pady=(10, 0))
        self.morning_sep.pack(fill=X, padx=25, pady=5)
        self.morning_frame.pack(fill=X, padx=35)

        self.afternoon_title.pack_forget()
        self.afternoon_sep.pack_forget()
        self.afternoon_frame.pack_forget()
        self.tonight_title.pack_forget()
        self.tonight_sep.pack_forget()
        self.tonight_frame.pack_forget()
        self.completed_frame.pack_forget()

        self.yearly_title.pack(anchor="w", padx=25, pady=(20, 0))
        self.yearly_sep.pack(fill=X, padx=25, pady=5)
        self.yearly_frame.pack(fill=X, padx=35)

    def clear_task_frames(self):
        for frame in [self.morning_frame, self.afternoon_frame, self.tonight_frame, self.completed_frame, self.yearly_frame]:
            for widget in frame.winfo_children():
                widget.destroy()

    def refresh_ui(self):
        self.clear_task_frames()
        self.morning_title.config(text="🌅 Morning")

        if self.search_query:
            self.title_label.config(text=f"🔍 Search: '{self.search_query}'")
            self.pack_main_sections()
        elif self.current_category:
            self.title_label.config(text=self.display_category_title)
            if self.current_category == "Reminders":
                self.pack_reminders_sections()
            else:
                self.pack_main_sections()
        else:
            self.title_label.config(text=self.filter_titles.get(self.current_filter, self.current_filter))
            if self.current_filter == "Completed":
                self.hide_active_sections()
                self.completed_frame.pack(fill=X, padx=35)
            else:
                self.pack_main_sections()

        for task in self.tasks:
            if self.search_query and self.search_query not in task.task.lower():
                continue

            if self.current_category:
                if task.category == self.current_category and not task.completed:
                    if self.current_category == "Reminders" and task.is_yearly:
                        self.create_task_widget(task, target_frame=self.yearly_frame)
                    else:
                        self.create_task_widget(task)
            else:
                if task.is_yearly and self.current_filter != "All" and self.current_filter != "Completed":
                    continue
                
                if self.current_filter == "All":
                    if task.is_yearly:
                        self.create_task_widget(task, target_frame=self.morning_frame)
                    else:
                        self.create_task_widget(task)
                elif self.current_filter == "Today" and not task.completed:
                    self.create_task_widget(task)
                elif self.current_filter == "Flagged" and task.flagged and not task.completed:
                    self.create_task_widget(task)
                elif self.current_filter == "Completed" and task.completed:
                    if task.is_yearly:
                        self.create_task_widget(task, target_frame=self.completed_frame)
                    else:
                        self.create_task_widget(task)

    def hide_active_sections(self):
        self.morning_title.pack_forget()
        self.morning_sep.pack_forget()
        self.morning_frame.pack_forget()
        self.afternoon_title.pack_forget()
        self.afternoon_sep.pack_forget()
        self.afternoon_frame.pack_forget()
        self.tonight_title.pack_forget()
        self.tonight_sep.pack_forget()
        self.tonight_frame.pack_forget()
        self.yearly_title.pack_forget()
        self.yearly_sep.pack_forget()
        self.yearly_frame.pack_forget()

    def apply_general_filter(self, filter_type):
        self.current_filter = filter_type
        self.current_category = None  
        self.reset_search_bar()
        self.refresh_ui()

    def apply_category_filter(self, category_name, display_title):
        self.current_category = category_name
        self.display_category_title = display_title
        self.reset_search_bar()
        self.refresh_ui()

    def add_new_custom_list(self):
        new_list_name = simpledialog.askstring("New List", "Enter name for your custom list:")
        if new_list_name and new_list_name.strip():
            formatted_name = f"📝 {new_list_name.strip()}"
            self.custom_lists.append(formatted_name)
            self.create_sidebar()

    def delete_custom_list(self):
        if not self.custom_lists:
            return
        delete_window = ttk.Toplevel(self.app)
        delete_window.title("Delete List")
        delete_window.geometry("300x180")
        delete_window.grab_set()

        ttk.Label(delete_window, text="Select List to Delete:", font=("Arial", 11)).pack(pady=15)
        list_combo = ttk.Combobox(delete_window, values=self.custom_lists, state="readonly")
        list_combo.pack(padx=20, fill=X)
        list_combo.current(0)

        def confirm_delete():
            selected_list = list_combo.get()
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{selected_list}'?"):
                self.custom_lists.remove(selected_list)
                clean_name = selected_list.split(" ", 1)[-1] if " " in selected_list else selected_list
                if self.current_category == clean_name:
                    self.current_filter = "All"
                    self.current_category = None
                self.save_tasks_to_file()
                self.create_sidebar()
                self.refresh_ui()
                delete_window.destroy()

        ttk.Button(delete_window, text="Delete", bootstyle="danger", command=confirm_delete).pack(pady=20)

    def reset_search_bar(self):
        self.search_query = ""
        self.search.delete(0, END)
        self.search.insert(0, "🔍 Search")

    def open_add_task_window(self):
        self.window = ttk.Toplevel(self.app)
        self.window.title("Add Task")
        self.window.geometry("400x380")
        
        ttk.Label(self.window, text="Task Name:").pack(anchor="w", padx=20, pady=(15, 5))
        self.task_entry = ttk.Entry(self.window, width=40)
        self.task_entry.pack(padx=20)
        
        ttk.Label(self.window, text="Select Time Section:").pack(anchor="w", padx=20, pady=(10, 5))
        self.time_combo = ttk.Combobox(self.window, values=["Morning", "Afternoon", "Tonight"])
        self.time_combo.pack(padx=20)
        self.time_combo.current(0)

        ttk.Label(self.window, text="Assign to List layout:").pack(anchor="w", padx=20, pady=(10, 5))
        cleaned_categories = ["General"] + [item.split(" ", 1)[-1] if " " in item else item for item in self.custom_lists]
        self.category_combo = ttk.Combobox(self.window, values=cleaned_categories)
        self.category_combo.pack(padx=20)
        
        if self.current_category:
            try:
                self.category_combo.current(cleaned_categories.index(self.current_category))
            except ValueError:
                self.category_combo.current(0)
        else:
            self.category_combo.current(0)

        self.yearly_var = ttk.BooleanVar(value=False)
        
        def toggle_date_entry():
            if self.yearly_var.get():
                self.date_entry.pack(padx=20, before=self.save_btn)
                self.date_label.pack(anchor="w", padx=20, before=self.date_entry)
                self.category_combo.set("Reminders") 
            else:
                self.date_label.pack_forget()
                self.date_entry.pack_forget()

        chk_yearly = ttk.Checkbutton(self.window, text="Is this a Yearly Repeating Reminder?", variable=self.yearly_var, command=toggle_date_entry)
        chk_yearly.pack(anchor="w", padx=20, pady=15)

        self.date_label = ttk.Label(self.window, text="Enter Date (MM-DD, e.g., 10-25 for Oct 25):")
        self.date_entry = ttk.Entry(self.window, width=20)

        self.save_btn = ttk.Button(self.window, text="Save", command=self.save_task)
        self.save_btn.pack(pady=20)
    
    def save_task(self):
        task_text = self.task_entry.get().strip()
        time_section = self.time_combo.get()
        assigned_category = self.category_combo.get()
        is_yearly = self.yearly_var.get()
        yearly_date = self.date_entry.get().strip() if is_yearly else ""
        
        if task_text == "":
            return
        
        new_task = Task(task_text, time_section, category=assigned_category, is_yearly=is_yearly, yearly_date=yearly_date)
        self.tasks.append(new_task)
        self.save_tasks_to_file()
        self.refresh_ui()
        self.window.destroy()

    def create_task_widget(self, task, target_frame=None):
        if target_frame is not None:
            parent = target_frame
        elif task.completed:
            parent = self.completed_frame
        elif task.section == "Morning":
            parent = self.morning_frame
        elif task.section == "Afternoon":
            parent = self.afternoon_frame
        else:
            parent = self.tonight_frame

        task_frame = ttk.Frame(parent)
        task_frame.pack(fill=X, pady=3)
        
        var = ttk.BooleanVar(value=task.completed)

        def mark_done():
            task.completed = var.get()
            self.save_tasks_to_file()
            self.refresh_ui()

        display_text = f"{task.task}  [🎂 {task.yearly_date}]" if task.is_yearly and task.yearly_date else task.task
        check = ttk.Checkbutton(task_frame, text=display_text, variable=var, command=mark_done)
        check.pack(side=LEFT)
        
        if not task.completed:
            star_text = "⭐" if task.flagged else "☆"
            star_btn = ttk.Button(task_frame, text=star_text, bootstyle="warning-link")
            star_btn.config(command=lambda: self.toggle_star(star_btn, task))
            star_btn.pack(side=RIGHT, padx=5)
            
            ttk.Button(task_frame, text="🗑️", bootstyle="danger-link", command=lambda: self.delete_task(task)).pack(side=RIGHT)
            ttk.Button(task_frame, text="✏️", bootstyle="warning-link", command=lambda: self.edit_task(task_frame, task)).pack(side=RIGHT, padx=5)
        else:
            ttk.Button(task_frame, text="🗑️", bootstyle="danger-link", command=lambda: self.delete_task(task)).pack(side=RIGHT)

    def save_tasks_to_file(self):
        with open("tasks.txt", "w") as file:
            for task in self.tasks:
                file.write(f"{task.section}|{task.task}|{task.completed}|{task.flagged}|{task.category}|{task.is_yearly}|{task.yearly_date}\n")

    def edit_task(self, task_frame, task_obj):
        edit_window = ttk.Toplevel(self.app)
        edit_window.title("Edit Task")
        edit_window.geometry("350x200")
        ttk.Label(edit_window, text="Edit Task").pack(pady=10)
        
        entry = ttk.Entry(edit_window, width=30)
        entry.pack(pady=10)
        entry.insert(0, task_obj.task)
        
        def save_edit():
            new_task_text = entry.get().strip()
            if not new_task_text:
                return
            task_obj.task = new_task_text
            self.save_tasks_to_file()
            self.refresh_ui()
            edit_window.destroy()

        ttk.Button(edit_window, text="Save", bootstyle="success", command=save_edit).pack(pady=10)

    def load_tasks_from_file(self):
        try:
            with open("tasks.txt", "r") as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split("|")
                    
                    if len(parts) == 4:
                        section, task_text, completed, flagged = parts
                        category, is_yearly, yearly_date = "General", False, ""
                    elif len(parts) == 5:
                        section, task_text, completed, flagged, category = parts
                        is_yearly, yearly_date = False, ""
                    elif len(parts) == 7:
                        section, task_text, completed, flagged, category, is_yearly, yearly_date = parts
                    else:
                        continue
                        
                    new_task = Task(task_text, section, completed == "True", flagged == "True", category, is_yearly == "True", yearly_date)
                    self.tasks.append(new_task)
            self.refresh_ui()
        except FileNotFoundError:
            pass

    def delete_task(self, task_obj):
        if messagebox.askyesno("Delete Task", "Are you sure you want to delete this task?"):
            if task_obj in self.tasks:
                self.tasks.remove(task_obj)
            self.save_tasks_to_file()
            self.refresh_ui()
    
    def toggle_star(self, button, task_obj):
        task_obj.flagged = not task_obj.flagged
        self.save_tasks_to_file()
        self.refresh_ui()

    def search_tasks(self, event):
        text = self.search.get().strip().lower()
        if text == "🔍 search":
            self.search_query = ""
        else:
            self.search_query = text
        self.refresh_ui()


if __name__ == "__main__":
    root = ttk.Window(themename="litera")
    root.title("Todo App")
    root.geometry("800x630")
    app = TodoUI(root)
    root.mainloop()