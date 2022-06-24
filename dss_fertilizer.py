import os
import time
import PySimpleGUI as sg
from PySimpleGUI.PySimpleGUI import POPUP_BUTTONS_NO_BUTTONS
from converter import Converter

nplants = 60
grainpp = 20
nitropg = 0.015
nitropkgf = 13
ndvi_file_name = ''
field_limit_file_name = ''
out_folder = ''
area_m2 = 10000
pup_text = ''
intensive_strategy = False;
taskdata_info = {
    "customer_designator":"Ente Parco",
    "farm_designator":"Parco San Rossore",
    "farm_address":"via Cascine vecchie",
    "farm_country":"Italy",
    "worker_designator":"Pasqualetti",
    "field_designator":"Oncinos Field",
    "crop_type": "Sorghum",
    "crop_variety": "Sorghum for Sillage",
    "product_designator":"Dry Blood",
    "product_group":"Fertilizer",
    "task_designator": "Oncinos Field VRA Fert"
}

fert_layout = [
    [
        sg.Text("Select tif file"),
        sg.In(size=(50, 1), enable_events=True, key="-NDVIFILE-"),
        sg.FileBrowse(file_types=(("TIF Files", "*.tif"), ("CSV Files", "*.csv")))
    ],
    [
        sg.Text("Select Field Limits file"),
        sg.In(size=(50, 1), enable_events=True, key="-LIMITFILE-"),
        sg.FileBrowse(file_types=(("CSV Files", "*.csv"), ))
    ],
    [
        sg.Text("Number of plants"),sg.Input('60', size=(25, 1), enable_events=True, key="-NPLANTS-", justification='right')
    ],
    [
        sg.Text("Quantity of grains [g]"),sg.Input('20', size=(25, 1), enable_events=True, key="-GRAINPP-", justification='right')
    ],
    [
        sg.Text("Nitrogen per grain [%]"), sg.Input('1.5', size=(25, 1), enable_events=True, key="-NITROPG-", justification='right')
    ],
    [
        sg.Text("Nitrogen per KG of fertilizer [%]"), sg.Input('13', size=(25, 1), enable_events=True, key="-NITROPKGF-", justification='right')
    ],
    [
        sg.Text("Fertilization strategy"),sg.Combo(["Organic", "Intensive"], default_value="Organic", enable_events=True, key="-STRATEGY-")
    ],
    [
        sg.Text("Select output folder"),sg.In(size=(50, 1), enable_events=True, key="-OUTFILE-"),
        sg.FolderBrowse()
    ],
    [
        sg.Button('Calculate map', key="-CALCBTN-")
    ]
]

data_layout = [
    [sg.Text("Customer",size=(50,1), justification='center')],
    [sg.Text("Name", size=(10,1)), sg.Input(taskdata_info["customer_designator"], size=(40, 1), enable_events=True, key="-CTRDES-", justification='right')],
    [sg.Text("Farm",size=(50,1), justification='center')],
    [sg.Text("Name",size=(10,1)), sg.Input(taskdata_info["farm_designator"], size=(40, 1), enable_events=True, key="-FRMDES-", justification='right')],
    [sg.Text("Address",size=(10,1)), sg.Input(taskdata_info["farm_address"], size=(40, 1), enable_events=True, key="-FRMADDR-", justification='right')],
    [sg.Text("Country",size=(10,1)), sg.Input(taskdata_info["farm_country"], size=(40, 1), enable_events=True, key="-FRMCOUNTRY-", justification='right')],
    [sg.Text("Worker",size=(50,1), justification='center')],
    [sg.Text("Name", size=(10,1)), sg.Input(taskdata_info["worker_designator"], size=(40, 1), enable_events=True, key="-WRKDES-", justification='right')],
    [sg.Text("Field",size=(50,1), justification='center')],
    [sg.Text("Name",size=(10,1)), sg.Input(taskdata_info["field_designator"], size=(40, 1), enable_events=True, key="-PFDDES-", justification='right')],
    [sg.Text("Area [m^2]",size=(10,1)),sg.Input('10000', size=(40, 1), enable_events=True, key="-PFDAREA-", justification='right')],
    [sg.Text("Crop",size=(50,1), justification='center')],
    [sg.Text("Type",size=(10,1)), sg.Input(taskdata_info["crop_type"], size=(40, 1), enable_events=True, key="-CTPDES-", justification='right')],
    [sg.Text("Variety",size=(10,1)),sg.Input(taskdata_info["crop_variety"], size=(40, 1), enable_events=True, key="-CTVDES-", justification='right')],
    [sg.Text("Product",size=(50,1), justification='center')],
    [sg.Text("Name",size=(10,1)), sg.Input(taskdata_info["product_designator"], size=(40, 1), enable_events=True, key="-PDTDES-", justification='right')],
    [sg.Text("Group",size=(10,1)),sg.Input(taskdata_info["product_group"], size=(40, 1), enable_events=True, key="-PGPDES-", justification='right')],
    [sg.Text("Task",size=(50,1), justification='center')],
    [sg.Text("Name",size=(10,1)), sg.Input(taskdata_info["task_designator"], size=(40, 1), enable_events=True, key="-TSKDES-", justification='right')],
]

tab_list = [
    [sg.Tab("Fertilization",fert_layout, tooltip='Fertilization configuration', element_justification= 'left')],
    [sg.Tab("Data",data_layout, tooltip='Task data', element_justification= 'left')]
]
layout = [
    [sg.TabGroup(tab_list)],
]

window = sg.Window("DSS Fertilizer v1.0.0", layout)

while True:
    event, values = window.read()
    if event == "-NPLANTS-":
        nplants = int(values["-NPLANTS-"])
    elif event == "-PFDAREA-":
        area_m2 = int(values["-PFDAREA-"])
    elif event == "-GRAINPP-":
        grainpp = float(values["-GRAINPP-"])
    elif event == "-NITROPG-":
        nitropg = float(values["-NITROPG-"])/100
    elif event == "-NITROPKGF-":
        nitropkgf = float(values["-NITROPKGF-"])
    elif event == "-CALCBTN-":
        if not os.path.isfile(ndvi_file_name):
            sg.Popup("Please select a valid NDVI file")
        elif not os.path.isfile(field_limit_file_name):
            sg.Popup("Please select a valid field limit file")
        elif not os.path.isdir(out_folder):
            sg.Popup("Please select a valid out folder")
        else:
            msg = Converter.calculate_fertilizer_thread(nplants, grainpp, nitropg, nitropkgf, out_folder, ndvi_file_name, field_limit_file_name, area_m2, intensive_strategy, taskdata_info)
            sg.Popup(msg)
    elif event == "-NDVIFILE-":
        ndvi_file_name = values["-NDVIFILE-"]
    elif event == "-LIMITFILE-":
        field_limit_file_name = values["-LIMITFILE-"]
    elif event == "-OUTFILE-":
        out_folder = values["-OUTFILE-"]+'/'
    elif event == "-STRATEGY-":
        if "Intensive" == values["-STRATEGY-"]:
            intensive_strategy = True
            print('Intensive')
        else:
            intensive_strategy = False
            print('Organic')
    elif event == "-CTRDES-":
        taskdata_info["customer_designator"] = values["-CTRDES-"]
    elif event == "-FRMDES-":
        taskdata_info["farm_designator"] = values["-FRMDES-"]
    elif event == "-FRMADDR-":
        taskdata_info["farm_address"] = values["-FRMADDR-"]
    elif event == "-FRMCOUNTRY-":
        taskdata_info["farm_country"] = values["-FRMCOUNTRY-"]
    elif event == "-WRKDES-":
        taskdata_info["worker_designator"] = values["-WRKDES-"]
    elif event == "-PFDDES-":
        taskdata_info["field_designator"] = values["-PFDDES-"]
    elif event == "-CTPDES-":
        taskdata_info["crop_type"] = values["-CTPDES-"]
    elif event == "-CTVDES-":
        taskdata_info["crop_variety"] = values["-CTVDES-"]
    elif event == "-PDTDES-":
        taskdata_info["product_designator"] = values["-PDTDES-"]
    elif event == "-PGPDES-":
        taskdata_info["product_group"] = values["-PGPDES-"]
    elif event == "-TSKDES-":
        taskdata_info["task_designator"] = values["-TSKDES-"]
    elif event == "Exit" or event == sg.WIN_CLOSED:
        break

window.close()

