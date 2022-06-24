import geopy.distance
from osgeo import gdal
import math
import copy
import csv
import os
# --
import filler


class FieldGrid:
    def __init__(self, filename, out_folder='', cell_width=0.5, cell_height=0.5):
        self.filepath, f_name = os.path.split(filename)
        self.filename, self.file_ext = os.path.splitext(f_name)
        self.out_folder = out_folder
        self.n_field_grid = {}
        self.field_grid = []
        self.earth_r = 6371e3  # metres
        self.ndvi_mean = 0
        self.bounds = {'latF': {'max': -1000.0, 'min': 1000.0},
                       'lonF': {'max': -1000.0, 'min': 1000.0},
                       'ndviF': {'max': -1000.0, 'min': 1000.0}
                       }
        self.cellX = cell_width  # default 0.5 meters
        self.cellY = cell_height  # default 0.5 meters
        self.east_size = 0
        self.north_size = 0
        self.dimY = 0
        self.dimX = 0
        self.nc_x = 1
        self.nc_y = 1

        if self.file_ext == '.tif':
            self.__from_tif()
        else:
            self.__from_csv()

    def __from_tif(self):

        ds = gdal.Open(self.filepath+'/'+self.filename+self.file_ext)
        self.field_grid = ds.GetRasterBand(1).ReadAsArray()

        geo_transform = ds.GetGeoTransform()
        if geo_transform:
            self.east_size = geo_transform[1]
            self.north_size = abs(geo_transform[5])

            c = gdal.ApplyGeoTransform(geo_transform, ds.RasterXSize, ds.RasterYSize)
            self.bounds['latF']['max'] = c[1]
            self.bounds['lonF']['max'] = c[0]
            self.bounds['latF']['min'] = geo_transform[3]
            self.bounds['lonF']['min'] = geo_transform[0]

            self.dimY = self.gps_dist({'lat': self.bounds['latF']['min'], 'lon': self.bounds['lonF']['min']},
                                      {'lat': self.bounds['latF']['max'], 'lon': self.bounds['lonF']['min']})

            self.dimX = self.gps_dist({'lat': self.bounds['latF']['min'], 'lon': self.bounds['lonF']['min']},
                                      {'lat': self.bounds['latF']['min'], 'lon': self.bounds['lonF']['max']})

            evm_y = self.gps_dist({'lat': geo_transform[3], 'lon': geo_transform[0]},
                                  {'lat': float(geo_transform[3]) + float(geo_transform[5]), 'lon': geo_transform[0]})

            evm_x = self.gps_dist({'lat': geo_transform[3], 'lon': geo_transform[0] + float(geo_transform[1])},
                                  {'lat': float(geo_transform[3]), 'lon': geo_transform[0]})

            self.cellX = round(evm_x, 6)
            self.cellY = round(evm_y, 6)

            self.nc_x = ds.RasterXSize
            self.nc_y = ds.RasterYSize

        self.update_ndvi_mean()
        ds = None

    def __from_csv(self):
        p = []
        with open(self.filepath+'/'+self.filename+self.file_ext, 'r') as csv_file:
            for line in csv_file:
                (lid, lat, lon, ndvi) = line.split(';', 4)
                el = {'id': float(lid.replace(',', '.')),
                      'lat': float(lat.replace(',', '.')),
                      'lon': float(lon.replace(',', '.')),
                      'ndvi': float(ndvi.strip().replace(',', '.').replace("\r", ''))
                      }

                p.append(el)
                for k in ('lat', 'lon', 'ndvi'):
                    if el[k] < self.bounds[k + 'F']['min']:
                        self.bounds[k + 'F']['min'] = el[k]

                    if el[k] > self.bounds[k + 'F']['max']:
                        self.bounds[k + 'F']['max'] = el[k]

        self.set_geometry()
        p = sorted(p, key=lambda i: (i['lat'], i['lon']))

        # sparse matrix
        field_grid_ns = {}

        for row in range(0, self.nc_y + 2):
            for col in range(0, self.nc_x + 2):
                if row not in self.n_field_grid:
                    self.n_field_grid[row] = {}
                self.n_field_grid[row][col] = -1

        self.write_csv(self.out_folder+'temp', self.get_actual_value)
        if os.path.exists(self.out_folder+"temp.vrt"):
            os.remove(self.out_folder+"temp.vrt")

        f = open(self.out_folder+"temp.vrt", "w")
        f.write("<OGRVRTDataSource>\n\
            <OGRVRTLayer name=\"temp\">\n\
                <SrcDataSource>"+self.out_folder+"temp.csv</SrcDataSource>\n\
                <GeometryType>wkbPoint</GeometryType>\n\
                <GeometryField encoding=\"PointFromColumns\" x=\"x\" y=\"y\" z=\"value\"/>\n\
            </OGRVRTLayer>\n\
        </OGRVRTDataSource>")

        f.close()

        gdal.Rasterize(self.out_folder+self.filename+".tif", self.out_folder+"temp.vrt", outputSRS="EPSG:4326",
                       xRes=self.east_size, yRes=-self.north_size,
                       attribute="value", noData=-1, targetAlignedPixels=True)

        ds = gdal.Open(self.out_folder+self.filename+".tif", gdal.GA_Update)
        field_grid = ds.GetRasterBand(1).ReadAsArray()

        geo_transform = ds.GetGeoTransform()
        if geo_transform:
            self.east_size = geo_transform[1]
            self.north_size = abs(geo_transform[5])

            c = gdal.ApplyGeoTransform(geo_transform, ds.RasterXSize, ds.RasterYSize)
            self.bounds['latF']['max'] = c[1]
            self.bounds['lonF']['max'] = c[0]
            self.bounds['latF']['min'] = geo_transform[3]
            self.bounds['lonF']['min'] = geo_transform[0]

            self.dimY = self.gps_dist({'lat': self.bounds['latF']['min'], 'lon': self.bounds['lonF']['min']},
                                      {'lat': self.bounds['latF']['max'], 'lon': self.bounds['lonF']['min']})

            self.dimX = self.gps_dist({'lat': self.bounds['latF']['min'], 'lon': self.bounds['lonF']['min']},
                                      {'lat': self.bounds['latF']['min'], 'lon': self.bounds['lonF']['max']})

            evm_y = self.gps_dist({'lat': geo_transform[3], 'lon': geo_transform[0]},
                                  {'lat': float(geo_transform[3]) + float(geo_transform[5]), 'lon': geo_transform[0]})

            evm_x = self.gps_dist({'lat': geo_transform[3], 'lon': geo_transform[0] + float(geo_transform[1])},
                                  {'lat': float(geo_transform[3]), 'lon': geo_transform[0]})

            self.cellX = round(evm_x, 6)
            self.cellY = round(evm_y, 6)

            self.nc_x = ds.RasterXSize
            self.nc_y = ds.RasterYSize

        yval = {}
        xval = {}
        for row in range(0, ds.RasterYSize + 2):
            c = gdal.ApplyGeoTransform(geo_transform, 0, row)
            yval[row] = c[1]

        for col in range(0, ds.RasterXSize + 2):
            c = gdal.ApplyGeoTransform(geo_transform, col, 0)
            xval[col] = c[0]

        for point in p:
            cx = 0
            cy = ds.RasterYSize + 1
            while point['lat'] > yval[cy - 1]:
                cy = cy - 1

            while point['lon'] > xval[cx + 1]:
                cx = cx + 1

            cy = cy - 1

            try:
                field_grid_ns[cy][cx] += 1
                # average on iteration -> m[n] = m[n-1] + (v - m[n-1]) / n;
                field_grid[cy][cx] += (point['ndvi'] - field_grid[cy][cx]) / field_grid_ns[cy][cx]
            except KeyError:
                try:
                    field_grid_ns[cy][cx] = 1
                except KeyError:
                    field_grid_ns[cy] = {}
                    field_grid_ns[cy][cx] = 1

                try:
                    field_grid[cy][cx] = point['ndvi']
                except KeyError:
                    field_grid[cy] = {}
                    field_grid[cy][cx] = point['ndvi']

        self.field_grid = field_grid
        self.update_ndvi_mean()

        ds.GetRasterBand(1).WriteArray(self.field_grid)
        ds.FlushCache()
        ds = None

        if os.path.exists(self.out_folder+"temp.vrt"):
            os.remove(self.out_folder+"temp.vrt")

        if os.path.exists(self.out_folder+"temp.csv"):
            os.remove(self.out_folder+"temp.csv")

    def update_tiff(self):
        ds = gdal.Open(self.out_folder + self.filename + ".tif", gdal.GA_Update)
        ds.GetRasterBand(1).WriteArray(self.field_grid)
        ds.FlushCache()
        ds = None

    def set_geometry(self):
        c1 = self.gps_new_pos({'lat': self.bounds['latF']['max'],
                               'lon': self.bounds['lonF']['min']}, self.cellY, 180)
        c2 = self.gps_new_pos({'lat': self.bounds['latF']['max'],
                               'lon': self.bounds['lonF']['min']}, self.cellX, 90)

        self.east_size = c2['lon'] - self.bounds['lonF']['min']
        self.north_size = - c1['lat'] + self.bounds['latF']['max']

        self.dimY = self.gps_dist({'lat': self.bounds['latF']['min'], 'lon': self.bounds['lonF']['min']},
                                  {'lat': self.bounds['latF']['max'], 'lon': self.bounds['lonF']['min']})

        self.dimX = self.gps_dist({'lat': self.bounds['latF']['min'], 'lon': self.bounds['lonF']['min']},
                                  {'lat': self.bounds['latF']['min'], 'lon': self.bounds['lonF']['max']})

        self.nc_x = math.floor(self.dimX / self.cellX)
        self.nc_y = math.floor(self.dimY / self.cellY)

    def update_ndvi_mean(self):
        n = 0
        self.bounds['ndviF'] = {'max': -1000.0, 'min': 1000.0}
        self.ndvi_mean = 0
        for row in range(0, self.nc_y):
            for col in range(0, self.nc_x):
                if self.field_grid[row][col] > 0:
                    n += 1
                    self.ndvi_mean += (self.field_grid[row][col] - self.ndvi_mean) / n
                    if self.bounds['ndviF']['max'] is None \
                            or self.field_grid[row][col] > self.bounds['ndviF']['max']:
                        self.bounds['ndviF']['max'] = self.field_grid[row][col]
                    if self.bounds['ndviF']['min'] is None \
                            or self.field_grid[row][col] > self.bounds['ndviF']['min']:
                        self.bounds['ndviF']['min'] = self.field_grid[row][col]

    def grow(self, niter, cell_radius):
        for _ in range(niter):
            nn_field_grid = copy.deepcopy(self.field_grid)

            for row in range(0, self.nc_y):
                for col in range(0, self.nc_x):
                    if nn_field_grid[row][col] == -1:
                        self.field_grid[row][col] = self.n_circle(nn_field_grid, self.nc_y, self.nc_x,
                                                                  row, col, cell_radius)
            del nn_field_grid

    def fill_holes(self):
        filler.fill_holes(self.field_grid)

    @staticmethod
    def n_circle(init, r, c, x, y, radius):
        s = 0
        n = 0
        for i in range(-radius, radius):
            if 0 <= x + i < r:
                for j in range(-radius, radius):
                    if 0 <= y + j < c:
                        if init[x + i][y + j] > -1:
                            s += init[x + i][y + j]
                            n += 1
        if s == 0:
            return -1
        return s / n

    def gps_new_pos(self, gps1, d, brng):
        try:
            x = geopy.distance.distance(meters=d).destination((gps1['lat'], gps1['lon']), bearing=brng)
            r_val = {'lat': x.latitude, 'lon': x.longitude}
        except NameError:

            f1 = gps1['lat'] * math.pi / 180  # f, l in radians
            l1 = gps1['lon'] * math.pi / 180
            brng = brng * math.pi / 180

            f2 = math.asin(math.sin(f1) * math.cos(d / self.earth_r) +
                           math.cos(f1) * math.sin(d / self.earth_r) * math.cos(brng))

            l2 = l1 + math.atan2(math.sin(brng) * math.sin(d / self.earth_r) * math.cos(f1),
                                 math.cos(d / self.earth_r) - math.sin(f1) * math.sin(f2))
            r_val = {'lat': f2 * 180 / math.pi, 'lon': l2 * 180 / math.pi}

        return r_val

    def gps_dist(self, gps1, gps2):
        if not gps1 or not gps2:
            return -1

        try:
            distance = geopy.distance.distance((gps1['lat'], gps1['lon']), (gps2['lat'], gps2['lon'])).m
        except NameError:

            f1 = gps1['lat'] * math.pi / 180  # f, l in radians
            f2 = gps2['lat'] * math.pi / 180
            ddf = (gps2['lat'] - gps1['lat']) * math.pi / 180
            ddl = (gps2['lon'] - gps1['lon']) * math.pi / 180

            a = math.sin(ddf / 2) * math.sin(ddf / 2) \
                + math.cos(f1) * math.cos(f2) * math.sin(ddl / 2) * math.sin(ddl / 2)

            distance = self.earth_r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))  # in meters

        return distance

    @staticmethod
    def get_actual_value(value, _):
        return value

    def write_csv(self, filename, calc_function=None):
        if calc_function is None:
            calc_function = self.get_actual_value
        csv_columns = ['x', 'y', 'value', 'cx', 'cy']
        csv_file = filename + ".csv"
        try:
            with open(csv_file, 'w', newline='') as actual_file:
                writer = csv.DictWriter(actual_file, fieldnames=csv_columns)
                writer.writeheader()

                yval = {}
                xval = {}
                for row in sorted(self.n_field_grid.keys()):
                    yval[row] = self.gps_new_pos({'lat': self.bounds['latF']['max'],
                                                  'lon': self.bounds['lonF']['min']},
                                                 (float(row) + 0.0) * float(self.cellY), 180)

                for col in sorted(self.n_field_grid[0].keys()):
                    xval[col] = self.gps_new_pos({'lat': self.bounds['latF']['max'],
                                                  'lon': self.bounds['lonF']['min']},
                                                 (float(col) + 0.0) * float(self.cellX), 90)

                for row in sorted(self.n_field_grid.keys()):
                    for col in sorted(self.n_field_grid[row].keys()):
                        data = {'x': str(xval[col]['lon']), 'y': str(yval[row]['lat']),
                                'value': str(calc_function(self.n_field_grid[row][col], self.ndvi_mean)),
                                'cx': str(col),
                                'cy': str(row)}
                        writer.writerow(data)
        except IOError:
            print("I/O error")

    def __apply_transform(self, calc_function):
        nn_field_grid = copy.deepcopy(self.field_grid)
        for row in range(0, self.nc_y):
            for col in range(0, self.nc_x):
                if self.field_grid[row][col] != -1:
                    nn_field_grid[row][col] = calc_function(self.field_grid[row][col], self.ndvi_mean)
        return nn_field_grid

    def write_geo_tiff(self, filename, out_folder='', calc_function=None):
        if calc_function is None:
            calc_function = self.get_actual_value

        transformed_grid = self.__apply_transform(calc_function)

        ds = gdal.Open(self.out_folder + self.filename + ".tif")

        file_format = "GTiff"
        driver = gdal.GetDriverByName(file_format)
        clone_file_ds = driver.CreateCopy(out_folder+filename+'.tif', ds, strict=0)
        clone_file_ds.GetRasterBand(1).WriteArray(transformed_grid)
        clone_file_ds.FlushCache()
        clone_file_ds = None
        ds = None

    def get_json(self, calc_function=None):
        if calc_function is None:
            calc_function = self.get_actual_value

        self.update_ndvi_mean()

        values_list = []
        for row in reversed(range(0, self.nc_y)):
            for col in range(0, self.nc_x):
                values_list.append(int(calc_function(self.field_grid[row][col], self.ndvi_mean)))

        data = {
            "Grid": {
                "GridMinimumNorthPosition": self.bounds['latF']['max'],
                "GridMinimumEastPosition": self.bounds['lonF']['min'],
                "GridCellNorthSize": self.north_size, #"{:.19f}".format(self.north_size).strip('"'),
                "GridCellEastSize": self.east_size, #"{:.19f}".format(self.east_size).strip('"'),
                "GridMaximumColumn": self.nc_x,
                "GridMaximumRow": self.nc_y,
                "GridCell": values_list,
                "Filelength": len(values_list)*4
                    }
        }

        return data
