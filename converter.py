from PySimpleGUI.PySimpleGUI import POPUP_BUTTONS_NO_BUTTONS
import fertilization
import field_grid
import json
import os
import repo
import utils
import csv
import collections

class Converter():

    @staticmethod
    def calculate_fertilizer_thread(nplants, grainpp, nitropg, nitropkgf, out_folder, ndvi_file_name, field_limit_file_name, area_m2, intensive_strategy, taskdata_info):
        filepath, f_name = os.path.split(ndvi_file_name)
        filename, file_extension = os.path.splitext(f_name)
        strategy_thresholds = [0.1, 0.2, 0.3, 0.4]
        strategy_gains = [1.0, 2.0, 3.0, 4.0]
        strategy_coeffs = [1.0, 1.0, 1.0]
        cell_dim_x = 0.5 # meters
        cell_dim_y = 0.5 # meters

        fertilization_strategy = fertilization.FertilizationStrategy(intensive_strategy, strategy_thresholds,
                                                                    strategy_gains, strategy_coeffs,
                                                                    nplants, grainpp, nitropg, nitropkgf)

        field_limits = []
        with open(field_limit_file_name, 'r') as field_limit_file:
            for line in field_limit_file:
                if "Latitude" not in line:
                    (lon, lat) = line.split(',', 1)
                    point = {
                            "PointType": 2,
                            "PointNorth": float(lat),
                            "PointEast": float(lon)
                        }
                    field_limits.append(point)
        if len(field_limits) > 0:
            field_limits.append(field_limits[0])
        
        with open("ISOBUS_CONVERTER-PrescriptionMap-Template.json") as template_file:
            iso_json = json.load(template_file)
            iso_json['Partfield']['Polygon']['Linestring']['Point'] = field_limits
            iso_json['Partfield']['PartfieldDesignator'] = taskdata_info['field_designator']
            iso_json['Partfield']['PartfieldArea'] = area_m2
            iso_json['Partfield']['Polygon']['PolygonArea'] = area_m2
            iso_json['Customer']['CustomerDesignator'] = taskdata_info['customer_designator']
            iso_json['Farm']['FarmDesignator'] = taskdata_info['farm_designator']
            iso_json['Farm']['FarmStreet'] = taskdata_info['farm_address']
            iso_json['Farm']['FarmCountry'] = taskdata_info['farm_country']
            iso_json['ProductGroup'][0]['ProductGroupDesignator'] = taskdata_info['product_group']
            iso_json['Product'][0]['ProductDesignator'] = taskdata_info['product_designator']
            iso_json['CropType'][0]['CropTypeDesignator'] = taskdata_info['crop_type']
            iso_json['CropType'][0]['CropVariety'][0]['CropVarietyDesignator'] = taskdata_info['crop_variety']
            iso_json['Worker']['WorkerDesignator'] = taskdata_info['worker_designator']
            iso_json['Task'][0]['TaskDesignator'] = taskdata_info['task_designator']
        
        #tif path starting from tif
        tif_path  = ndvi_file_name
        if file_extension == '.csv':
            #add field limits to shape file
            csv_fl_file = out_folder+filename+"_fl.csv"
            with open(ndvi_file_name) as csv_file, open(csv_fl_file, "w") as csv_out:
                csv_reader = csv.DictReader(csv_file, fieldnames=["ID", "Longitude", "Latitude", "Value"], delimiter=';')
                pt_list = [row for row in csv_reader]
                new_id = len(pt_list)
                for index, fl in enumerate(field_limits[:-1]):
                    pt = d = collections.OrderedDict()
                    pt['ID'] = str(new_id + index)
                    pt["Longitude"] = str(fl["PointNorth"])
                    pt["Latitude"] = str(fl["PointEast"])
                    pt["Value"] = str(-1)
                    pt_list.append(pt)
                for row in pt_list:
                    line = row['ID']+";"+row["Longitude"]+";"+row["Latitude"]+";"+row["Value"]+"\n"
                    csv_out.write(line)

            # create grid from points
            f_grid = field_grid.FieldGrid(csv_fl_file, out_folder=out_folder, cell_width=cell_dim_x,
                                            cell_height=cell_dim_y)

            # grow borders thickness to avoid jagged edges
            f_grid.grow(niter=2, cell_radius=1)

            # fill holes with values based on context
            f_grid.fill_holes()

            f_grid.update_tiff()

            # File name for GeoTIFF file is the same as CSV file
            #tif path starting from CSV
            tif_path = out_folder + f_grid.filename + '.tif'

        #####
        #####
        #####
        # Read data file from tif previously created

        fert_grid = field_grid.FieldGrid(tif_path, out_folder=out_folder)

        # apply fertilization strategy
        fert_grid.write_geo_tiff(filename +'_fertilization', calc_function=fertilization_strategy.get_fertilization_value,
                                 out_folder=out_folder)

        grid = fert_grid.get_json(fertilization_strategy.get_fertilization_value)

        # create json to convert
        gridMod = [x*100 if x >= 0 else 0 for x in grid['Grid']["GridCell"]]
        grid['Grid']["GridCell"] = gridMod
        print(max(gridMod))
        iso_json['Task'][0]['Grid'] = grid['Grid']
        
        with open (out_folder + filename + '.json', 'w') as json_file:
            json.dump(iso_json, json_file, indent=2) 

        # create TASKDATA.XML
        try:
            res, body_json= utils.validate_json(iso_json, utils.PMAP_JSON_SCHEMA_PATH)
            assert res, body_json
            repo.path=out_folder
            res, body_xml = utils.to_xml({k:repo.Factory.parse_recursive(k,v) for k,v in body_json.items()})
            assert res, body_xml
            with open(os.path.join(out_folder,'taskdata.xml'), 'w') as f:
                f.write(body_xml)
                return "MAP succesfully created. Average ammount of fertilizer: "+str(fertilization_strategy.fiso)+ " kg/ha"         
        except Exception as ex:
            return "MAP creation failed " + str(ex)
