from os import path
import tkinter as tk
from tkinter import scrolledtext
from tkinter import filedialog
from enum import Enum
from ntpath import basename
import re
import csv
import plotly
import plotly.graph_objs as go
import datetime
from collections import OrderedDict
from plotly import tools
x = 0
y = 0
z = 0


# We have an enum defined here so we can use it instead of the strings 'gas' and 'electricity'
class FuelType(Enum):
    electricity = 1
    gas = 2


class EnergyMonitor:

    def __init__(self, parent):
        self.parent = parent

        self.file_dirname = ''
        self.house_list = []

        self.data_container = OrderedDict()
        self.monthly_data = OrderedDict()
        self.loaded_ids = []
        self.loaded_fuels = []

        self.welcome_label = tk.Label(self.parent, text='Welcome to the Energy Monitor!', font=('Calibri', 32))
        self.welcome_label.configure(background='#c6e2ff')
        self.welcome_label.pack()

        self.message_label = tk.Label(self.parent,
                                      text='Please use the dialog below to load a CSV file, which will be displayed'
                                      + 'in the box below.', font=('Calibri', 14), wraplength=540)
        self.message_label.configure(background='#c6e2ff')
        self.message_label.pack(pady=20)

        self.btn_file = tk.Button(self.parent, text="Load file", command=self.load_file)
        self.btn_file.pack(pady=20)

        self.scrolled_text = tk.scrolledtext.ScrolledText(self.parent, width=40, height=10)
        self.scrolled_text.pack()

        self.btn_monthly_data = tk.Button(self.parent, text='Monthly Data', command=self.generate_monthly_data)
        self.btn_monthly_data.pack()

        self.btn_graph_annual = tk.Button(self.parent, text='Scatter Graph (With Trend Lines)',
                                          command=self.generate_annual_graph_singlehouse)
        self.btn_graph_annual.pack()

        self.btn_graph_annual = tk.Button(self.parent, text='Bar Graph',
                                          command=self.generate_graph)
        self.btn_graph_annual.pack()

    # This method handles the loading of a simple file, and processing the data in it into a data storage
    def load_file(self, file=None):
        if file is None:
            file = filedialog.askopenfilename(initialdir=path.dirname(__file__))

        elif not path.isfile(file):
            raise ValueError("This file does not exist or is not readable.")

        print(file)
        self.file_dirname = file
        re_single_house = re.compile('^(.*?)_both_daily$')
        re_multiple_houses = re.compile('^(gas|electricity)_daily$')

        filename = basename(file).split('.')[0]
        single_match = re_single_house.search(filename)
        multiple_match = re_multiple_houses.search(filename)

        if single_match is not None:
            self.process_single_file(file, single_match.group(1))
        elif multiple_match is not None:
            self.process_multiple_file(file)
        else:
            raise ValueError("File format is not correct, must be one of '{fuel-type}_daily.csv" +
                             " or '{house-id}_both_daily.csv is invalid")

        self.btn_graph_annual.pack(pady=5)

    # This method is a separation fo the previous method that could potentially handle
    # different sorts of files, whereas this is specific to this single file
    def process_single_file(self, file, house_id):
        print("This file is a single house with both fuel types. The house id is '%s'." % house_id)
        print("Deleting old data")
        self.data_container.clear()
        self.loaded_ids.clear()
        self.loaded_fuels.clear()

        with open(file, 'r') as file_contents:
            reader = csv.reader(file_contents)
            header = next(reader, None)

            if header[1].lower() != 'electricity' or header[2].lower() != 'gas':
                raise ValueError('File is not in correct format. First column must be electricity, second must be gas.')

            for row in reader:
                print(row)
                this_date = datetime.datetime.strptime(row[0], '%Y%m%d').date()

                self.data_container[this_date] = {house_id: {FuelType.electricity: float(row[1]),
                                                             FuelType.gas: float(row[2])}}

            # Since we have only loaded one file, set the id directly
            self.loaded_ids.append(house_id)
            self.loaded_fuels.extend([FuelType.electricity, FuelType.gas])
            global x
            x += 1
            global y
            y += 2
            if y > 2:
                y = 2
            self.scrolled_text.insert(tk.INSERT, ('There is', x, 'houses and', y, 'fuel types\n'))
            self.scrolled_text.pack()

    def process_multiple_file(self, file):
        self.data_container.clear()
        self.loaded_ids.clear()
        self.loaded_fuels.clear()

        with open(file, 'r') as file_contents:
            reader = csv.reader(file_contents)
            header = next(reader, None)

            if len(header) <= 1 or header[0].lower() != 'date':
                raise ValueError('File is not in the correct format.')

            house_list = header.copy()
            house_list.pop(0)

            for row in reader:
                print(row)
                this_date = datetime.datetime.strptime(row[0], '%Y%m%d').date()

                self.data_container[this_date] = {}

                for i in range(0, len(house_list)):
                    self.data_container[this_date][house_list[i]] = float(row[i + 1])

            self.loaded_ids.append(self)
            self.loaded_fuels.extend(house_list)
            self.house_list = house_list.copy()
            global x
            x += 4
            global y
            y += 1
            if y > 2:
                y = 2
            self.scrolled_text.insert(tk.INSERT, ('There is', x, 'houses and', y, 'fuel types\n'))
            self.scrolled_text.pack()

    def generate_monthly_data(self):
        print('Generating monthly data')
        with open(self.file_dirname, 'r') as file_contents:
            reader = csv.reader(file_contents)
            header = next(reader, None)

        date_range = list(self.data_container.keys())

        house_list = []

        global z
        z = 0

        for i in range(0, len(self.house_list)):
            house_list.append([])

        if header[1].lower() == 'electricity' and header[2].lower() == 'gas':
            for row in reader:
                print(row)
                this_date = datetime.datetime.strptime(row[0], '%Y%m%d').date()

                self.data_container[this_date] = {FuelType.electricity: float(row[1]),
                                                  FuelType.gas: float(row[2])}

        else:
            for date in date_range:
                for i in range(0, len(house_list)):
                    if self.house_list[i] not in self.data_container[date]:
                        raise KeyError("Wrong.")

                    house_list[i].append(self.data_container[date][self.house_list[i]])
                    print(house_list[i])

    def generate_graph(self):
        print("Stub method for generating graphs. Use this to spin off other methods for different graphs.")

        with open(self.file_dirname, 'r') as file_contents:
            reader = csv.reader(file_contents)
            header = next(reader, None)

        if header[1].lower() == 'electricity' and header[2].lower() == 'gas':

            house_id = self.loaded_ids[0]

            date_range = list(self.data_container.keys())
            (gas_values, electricity_values) = ([], [])

            for date in date_range:

                if FuelType.gas not in self.data_container[date][house_id] \
                        or FuelType.electricity not in self.data_container[date][house_id]:
                    raise KeyError("Both fuel values must be present to display this graph correctly.")

                gas_values.append(self.data_container[date][house_id][FuelType.gas])
                electricity_values.append(self.data_container[date][house_id][FuelType.electricity])

            gas_trace = go.Bar(
                x=date_range,
                y=gas_values,
                name='gas trace'
            )

            electricity_trace = go.Bar(
                x=date_range,
                y=electricity_values,
                name='electricity trace',
                yaxis='y2'
            )
            graph_data = [gas_trace, electricity_trace]

            layout = go.Layout(
                title='Single House Both Fuels',
                yaxis=dict(
                    title='Usage (kWh)'
                ),
                yaxis2=dict(
                    title='yaxis2 title',
                    titlefont=dict(
                        color='rgb(36, 36, 36)'
                    ),
                    tickfont=dict(
                        color='rgb(36, 36, 36)'
                    ),
                    overlaying='y',
                    side='right'
                )
            )

            fig = go.Figure(data=graph_data, layout=layout)
            plotly.offline.plot(fig, auto_open=True)

        else:

            date_range = list(self.data_container.keys())

            house_list = []

            for i in range(0, len(self.house_list)):
                house_list.append([])

            for date in date_range:
                for i in range(0, len(house_list)):
                    if self.house_list[i] not in self.data_container[date]:

                        raise KeyError("Wrong values to display this graph correctly.")

                    house_list[i].append(self.data_container[date][self.house_list[i]])

            traces = tools.make_subplots(rows=2, cols=1, shared_xaxes=True)

            for i in range(0, len(house_list)):
                i = go.Bar(
                    x=date_range,
                    y=house_list[i],
                    name=('House' + str(i)),
                    marker=dict(
                        color='rgb(36, 36, 36)'
                    )
                )
                traces.append_trace(i, 2, 1)

            layout = go.Layout(
                title='House comparision',
                xaxis=dict(tickangle=-45),
                barmode='group',
            )

            fig = go.Figure(data=traces, layout=layout)
            plotly.offline.plot(fig, auto_open=True)

    def generate_annual_graph_singlehouse(self):
        with open(self.file_dirname, 'r') as file_contents:
            reader = csv.reader(file_contents)
            header = next(reader, None)

        if header[1].lower() == 'electricity' or header[2].lower() == 'gas':

            house_id = self.loaded_ids[0]

            date_range = list(self.data_container.keys())
            (gas_values, electricity_values) = ([], [])

            for date in date_range:

                if FuelType.gas not in self.data_container[date][house_id] \
                        or FuelType.electricity not in self.data_container[date][house_id]:

                    raise KeyError("Both fuel values must be present to display this graph correctly.")

                gas_values.append(self.data_container[date][house_id][FuelType.gas])
                electricity_values.append(self.data_container[date][house_id][FuelType.electricity])

            gas_trace = go.Scatter(
                x=date_range,
                y=gas_values,
                name='gas trace'
            )

            electricity_trace = go.Scatter(
                x=date_range,
                y=electricity_values,
                name='electricity trace',
                yaxis='y2'
            )
            graph_data = [gas_trace, electricity_trace]

            layout = go.Layout(
                title='Single House Both Fuels',
                yaxis=dict(
                    title='Usage (kWh)'
                ),
                yaxis2=dict(
                    title='Usage (Gallon)',
                    titlefont=dict(
                        color='rgb(15, 15, 15)'
                    ),
                    tickfont=dict(
                        color='rgb(15, 15, 15)'
                    ),
                    overlaying='y',
                    side='right'
                )
            )

            fig = go.Figure(data=graph_data, layout=layout)
            plotly.offline.plot(fig, auto_open=True)

        else:

            date_range = list(self.data_container.keys())

            house_list = []

            for i in range(0, len(self.house_list)):
                house_list.append([])

            for date in date_range:
                for i in range(0, len(house_list)):
                    if self.house_list[i] not in self.data_container[date]:

                        raise KeyError("Wrong values to display this graph correctly.")

                    house_list[i].append(self.data_container[date][self.house_list[i]])

            traces = tools.make_subplots(rows=2, cols=1, shared_xaxes=True)

            for i in range(0, len(house_list)):
                i = go.Scatter(
                    x=date_range,
                    y=house_list[i],
                    name=('House' + str(i)),
                    marker=dict(
                        color='rgb(15, 15, 15)'
                    )
                )
                traces.append_trace(i, 2, 1)

            layout = go.Layout(
                title='House comparision',
                xaxis=dict(tickangle=-45),
            )

            fig = go.Figure(data=traces, layout=layout)
            plotly.offline.plot(fig, auto_open=True)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Energy Monitor")
    root.geometry('600x750')
    root.configure(background='#c6e2ff')

    plotly.tools.set_credentials_file(api_key='88WEfeAbijJLEaG234D4', username='t-mccarthy')
    print(plotly.__version__)

    gui = EnergyMonitor(root)
    root.mainloop()
