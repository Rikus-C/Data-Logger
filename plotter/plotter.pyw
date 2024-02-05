# Built in libraries
import os
import sys
import csv
import subprocess

# make sure all required modules are installed
try:
	import plotly
	from plotly.graph_objects import FigureWidget
	import plotly.graph_objects as go
	from PyQt5.QtCore import QTime
	from PyQt5.QtWidgets import QApplication
	from PyQt5.QtWidgets import QWidget
	from PyQt5.QtWidgets import QVBoxLayout
	from PyQt5.QtWidgets import QCheckBox
	from PyQt5.QtWidgets import QLabel
	from PyQt5.QtWidgets import QScrollArea
	from PyQt5.QtWidgets import QFrame
	from PyQt5.QtWidgets import QGridLayout
	from PyQt5.QtWidgets import QPushButton
	from PyQt5.QtWidgets import QTimeEdit
	from PyQt5.QtWidgets import QFileDialog
	from PyQt5.QtWebEngineWidgets import QWebEngineView
except:
	subprocess.check_call(["pip", "install", "plotly", "--user"])
	subprocess.check_call(["pip", "install", "PyQt5", "--user"])
	subprocess.check_call(["pip", "install", "PyQtWebEngine" ,"--user"])
    subprocess.check_call(["pip", "install", "ipywidgets" ,"--user"])
	sys.exit()


class ChecklistApp(QWidget):
	def __init__(self):
		super().__init__()

		# Some basic set-ups
		self.newest_files_dir = "../data/logs/"
		self.back_files_dir = "../data/dumps/"
		self.available_files = []
		self.file_names = []
		self.selected_file_dir = ""
		self.selected_files = []
		self.variables_present = []
		self.selected_variables = []
		self.plot_start_time = "00:00:00"
		self.plot_stop_time = "23:59:59"
		self.file_pointer = None

		# create the plotly figure
		fig = FigureWidget()
		fig.update_layout(
		legend=dict(orientation='h', 
		yanchor='bottom', y=1.02, 
		xanchor='right', x=1),
		xaxis_title='X-axis',
		yaxis_title='Y-axis',
		title='Scatter Plot with Legend Above',
		template='plotly_white')
		html = '<html><body>'
		html += plotly.offline.plot(
		fig, output_type='div', 
		include_plotlyjs='cdn')
		html += '</body></html>'
		self.plot_widget = QWebEngineView()
		self.plot_widget.setHtml(html)

		# Create a file selector widget
		self.file_selector = QScrollArea(self)
		self.file_selector.setWidgetResizable(True)
		self.file_checklist = QWidget()
		self.file_list_layout = QVBoxLayout(self.file_checklist)
		self.file_selector.setWidget(self.file_checklist)

		# Create a variable selector widget
		self.variable_selector = QScrollArea(self)
		self.variable_selector.setWidgetResizable(True)
		self.variable_checklist = QWidget()
		self.variable_list_layout = QVBoxLayout(self.variable_checklist)
		self.variable_selector.setWidget(self.variable_checklist)

		# Create time interval selectors
		self.start_time = QTimeEdit(self)
		self.start_time.setDisplayFormat("HH:mm:ss")
		self.start_time.setTime(QTime(0, 0, 0))
		self.stop_time = QTimeEdit(self)
		self.stop_time.setDisplayFormat("HH:mm:ss")
		self.stop_time.setTime(QTime(23, 59, 59))

		# Create frame widget for selecting a time
		self.time_frame = QFrame(self)
		self.time_frame.setFrameShape(QFrame.Shape.StyledPanel)
		self.time_frame.setFrameShadow(QFrame.Shadow.Raised)

		# Create the required buttons
		self.newest_files = QPushButton("Newest Files")
		self.all_files = QPushButton("All Files")
		self.manual_select = QPushButton("Select File Manually")
		self.get_variables = QPushButton("Update Variables")
		self.reset_variables = QPushButton("Reset Variables")
		self.reset_time = QPushButton("Reset Selected Time")
		self.generate_plots = QPushButton("Generate Plot(s)")
		# self.get_live_var = QPushButton("Get Live Variables")
		# self.live_plot = QPushButton("Start Live Plot")

		# Create button callbacks
		self.newest_files.clicked.connect(self.list_newest_files)
		self.all_files.clicked.connect(self.list_all_files)
		self.manual_select.clicked.connect(self.manually_select_file)
		self.get_variables.clicked.connect(self.update_variables)
		self.reset_variables.clicked.connect(self.reset_selected_variables)
		self.reset_time.clicked.connect(self.reset_time_selectors)
		self.generate_plots.clicked.connect(self.generate_variable_plots)
		# self.get_live_var.clicked.connect(self.get_live_variables)
		# self.live_plot.clicked.connect(self.show_live_plots)

		# Create Labels
		self.start_label = QLabel("Select Start Time:", self)
		self.stop_label = QLabel("Select Stop Time:", self)

		# Populate time selector menu
		self.time_menu_layout = QVBoxLayout()
		self.time_menu_layout.addWidget(self.reset_time)
		self.time_menu_layout.addWidget(self.start_label)
		self.time_menu_layout.addWidget(self.start_time)
		self.time_menu_layout.addWidget(self.stop_label)
		self.time_menu_layout.addWidget(self.stop_time)
		self.time_menu_layout.addWidget(self.generate_plots)
		self.time_frame.setLayout(self.time_menu_layout)

		# Create a grid layout(s)
		gui_layout = QGridLayout()

		# Populate the grid layouts
		gui_layout.addWidget(self.newest_files, 0, 0)
		gui_layout.addWidget(self.all_files, 0, 1)
		gui_layout.addWidget(self.manual_select, 0, 2)
		gui_layout.addWidget(self.get_variables, 0, 4)
		gui_layout.addWidget(self.reset_variables, 0, 5)
		# gui_layout.addWidget(self.get_live_var, 0, 5)
		# gui_layout.addWidget(self.live_plot, 0, 6)
		gui_layout.addWidget(self.file_selector, 1, 0, 1, 3)
		gui_layout.addWidget(self.variable_selector, 1, 3, 1, 3)
		gui_layout.addWidget(self.time_frame, 1, 6)
		gui_layout.addWidget(self.plot_widget, 2, 0, 1, 7)

        # Set the layout for the main window
		self.setLayout(gui_layout)

        # Set window properties
		self.setGeometry(100, 100, 1800, 700)
		self.setWindowTitle("Trend Viewer")
		self.resizeEvent = self.update_graph_height

	def update_graph_height(self, event):
		self.plot_widget.setMinimumHeight(int(0.6*self.height()))

	def generate_variable_plots(self):
		self.plot_start_time = self.start_time.time().toString("HH:mm:ss") + "'00"
		self.plot_stop_time = self.stop_time.time().toString("HH:mm:ss") + "'00"

		# Check that all required data/flags is met
		if len(self.selected_variables) < 1: return
		if self.file_pointer == None: return 

		# Read data from csv into lists
		all_data_to_plot = []
		self.file_pointer = open(self.selected_file_dir, 
		"r", newline="", encoding="utf-8")
		csv_reader = csv.DictReader(self.file_pointer)

		traces = []
		time_lists = []
		all_data_to_plot = [[] for _ in range(len(self.selected_variables))]

		for row in csv_reader:
			for col in range(len(self.selected_variables)):
				all_data_to_plot[col].append(float(row[self.selected_variables[col]]))
			time_lists.append(row["time"])

		# Filter Data
		start_index = 0
		stop_index = 1
		for time_stamp in time_lists:
			if time_stamp < self.plot_start_time:
				start_index += 1
			elif time_stamp > self.plot_stop_time:
				stop_index += 1

		for i in range(len(all_data_to_plot)):
			all_data_to_plot[i] = all_data_to_plot[i][start_index:-stop_index]
		time_lists = time_lists[start_index:-stop_index]

		# Plot the traces
		for i in range(len(all_data_to_plot)):
			traces.append(go.Scatter(
				x=time_lists, 
				y=all_data_to_plot[i], 
				mode='lines', 
				name=self.selected_variables[i]))

		# Create layout
		layout = go.Layout(title='Multiple Plots in Plotly', xaxis=dict(title='X-axis'), yaxis=dict(title='Y-axis'))
		fig = go.Figure(data=traces, layout=layout)

		fig.update_layout(
		legend=dict(orientation='h', 
		yanchor='bottom', y=1.02, 
		xanchor='right', x=1),
		xaxis_title='X-axis',
		yaxis_title='Y-axis',
		title='Scatter Plot with Legend Above',
		template='plotly_white')

		html = '<html><body>'
		html += plotly.offline.plot(
		fig, output_type='div', 
		include_plotlyjs='cdn')
		html += '</body></html>'
		self.plot_widget.setHtml(html)

	def reset_time_selectors(self):
		self.start_time.setTime(QTime(0, 0, 0))
		self.stop_time.setTime(QTime(23, 59, 59))

	def clear_variables_in_window(self):
		self.selected_variables = []
        # Remove all items from the layout
		while self.variable_list_layout.count():
			item = self.variable_list_layout.takeAt(0)
			widget = item.widget()
			if widget:
				widget.deleteLater()

	def update_selected_variables(self, state, index):
		if state == 2:
			self.selected_variables.append(index)
		else:
			self.selected_variables.remove(index)

	def show_variables_in_window(self):
		self.clear_variables_in_window()
		for item_text in self.variables_present:
			check_box = QCheckBox(item_text)
			check_box.stateChanged.connect(lambda state, 
			index = item_text: self.update_selected_variables(state, index))
			self.variable_list_layout.addWidget(check_box)

	def reset_selected_variables(self):
		self.selected_variables = []
		self.show_variables_in_window()

	def update_variables(self):
		self.file_pointer = None
		if len(self.selected_files) != 1:
			if self.selected_file_dir == "": return
			self.file_pointer = open(self.selected_file_dir, "r", newline="", encoding="utf-8")
		else:
			try:
				self.selected_file_dir = self.newest_files_dir + self.selected_files[0] + ".csv"
				self.file_pointer = open(self.selected_file_dir, "r", newline="", encoding="utf-8")
			except:
				self.selected_file_dir = self.back_files_dir + self.selected_files[0] + ".csv"
				self.file_pointer = open(self.selected_file_dir, "r", newline="", encoding="utf-8")

		self.variables_present = csv.DictReader(self.file_pointer).fieldnames
		self.variables_present.remove("date")
		self.variables_present.remove("time")
		self.file_pointer.close()
		self.show_variables_in_window()

	def update_selected_files(self, state, index):
		if state == 2:
			self.selected_files.append(index)
		else:
			self.selected_files.remove(index)

	def show_files_in_window(self):
		self.selected_files = []
		self.file_names.sort(reverse = True)
		for item_text in self.file_names:
			check_box = QCheckBox(item_text)
			check_box.stateChanged.connect(lambda state, 
			index = item_text: self.update_selected_files(state, index))
			self.file_list_layout.addWidget(check_box)
    
	def clear_files_in_window(self):
        # Remove all items from the layout
		while self.file_list_layout.count():
			item = self.file_list_layout.takeAt(0)
			widget = item.widget()
			if widget:
				widget.deleteLater()

	def list_files(self, current_dir):
		# Iterate over all files in the directory
		for file_name in os.listdir(current_dir):
			# Join the directory path and file name
			filepath = os.path.join(current_dir, file_name)
				
			# Check if it's a file (not a subdirectory)
			if os.path.isfile(filepath):
				if file_name.split(".")[1] == "csv":
					self.available_files.append(filepath)
					self.file_names.append(file_name.split(".")[0])
		
	def list_newest_files(self):
		self.file_names = []
		self.available_files = []
		self.clear_files_in_window()
		self.list_files(self.newest_files_dir)
		self.show_files_in_window()

	def list_all_files(self):
		self.file_names = []
		self.available_files = []
		self.clear_files_in_window()
		for dir in [self.newest_files_dir, self.back_files_dir]:
			self.list_files(dir)
		self.show_files_in_window()

	def manually_select_file(self):
		self.selected_files = []
		options = QFileDialog.Option.ReadOnly  # Optional: Set the dialog to read-only mode

		# Open the file dialog and get the selected file path
		file_dialog = QFileDialog(self)
		selected_file, _ = file_dialog.getOpenFileName(self, 
		"Open File", "", "All Files (*)", options=options)

		if selected_file:
			file_name = selected_file.split("/")

			if file_name[len(file_name)-1].split(".")[1] == "csv":
				self.selected_file_dir = selected_file
				self.file_names = [file_name[len(file_name)-1].split(".")[0]]
				self.available_files = [selected_file]
				self.clear_files_in_window()
				self.update_variables()

	
if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = ChecklistApp()
	window.setWindowTitle("Data Plotter")
	window.show()
	sys.exit(app.exec())
