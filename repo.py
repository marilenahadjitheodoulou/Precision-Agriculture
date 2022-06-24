#! /bin/python3
import bins
import DDI
import utils

import datetime
import multiprocessing

path=None

TaskData = None
class Factory:
	@staticmethod
	def get_obj( obj, *args, **kwargs):
		assert obj in [
			'Customer', 					#implemented as dict
			'Farm', 						#implemented as dict
			'ProductGroup', 				#implemented as dict
			'Partfield', 					#implemented as dict
			'CropType', 					#implemented as dict
			'CropVariety',					#implemented as dict
			'OperationTechnique',			#implemented as dict
			'OperationTechniqueReference',	#implemented as dict
			'OperTechPractice', 			#implemented as dict
			'Device', 						#implemented as dict
			'Worker', 						#implemented as dict
			'Product', 						#implemented as dict
			'Worker', 						#implemented as dict
			'Position',						#implemented as dict
			'Point',						#implemented as dict
			'Polygon',
			'Linestring',					#implemented as a class inheriting dict
			'TimeSequence', 				#implemented as a class inheriting dict
			'CulturalPractice',				#implemented as a class inheriting dict
			'Grid',							#implemented as a class inheriting dict
			'TimeLog',						#implemented as a class inheriting dict
			'Task',							#implemented as a class inheriting dict
			'DataLogValue',					#implemented as a class inheriting dict
			'TreatmentZone',				#implemented as a class inheriting dict
			'ProcessDataVariable',			#implemented as a class inheriting dict
			], "unidentified object: %s" % obj
		return globals().get(obj, dict)(**(dict(args) if args else kwargs))

	@staticmethod
	def parse_recursive(key, obj):
		try:
			if isinstance(obj, list):
				return [Factory.parse_recursive(key, o) for o in obj]
			elif isinstance(obj,dict):
				return Factory.get_obj(key, **obj)
			else:
				return obj
		except Exception as ex:
			print(str(ex))

class CulturalPractice(dict):
	def __init__(self, **kwargs):
		kwargs["OperationTechniqueReference"]=Factory.parse_recursive("OperationTechniqueReference", kwargs.pop("OperationTechniqueReference"))
		super(CulturalPractice, self).__init__(**kwargs)

class TimeSequence(dict):
	def __init__(self, **kwargs):
		kwargs["DataLogValue"]=Factory.parse_recursive("DataLogValue", kwargs.pop("DataLogValue"))
		super(TimeSequence, self).__init__(**kwargs)

class TreatmentZone(dict):
	def __init__(self,**kwargs):
		kwargs["ProcessDataVariable"]=Factory.parse_recursive("ProcessDataVariable", kwargs.pop("ProcessDataVariable"))
		super(TreatmentZone, self).__init__(**kwargs)

class ProcessDataVariable(dict):
	def __init__(self,**kwargs):
		kwargs["ProcessDataDDI"]="%04x" % int(DDI.get_DDIbyUoM_setpoint(kwargs.pop("UoM")))
		super(ProcessDataVariable, self).__init__(**kwargs)


class Linestring(dict):
	def __init__(self,**kwargs):
		kwargs["Point"]=Factory.parse_recursive("Point", kwargs.pop("Point"))
		super(Linestring, self).__init__(**kwargs)

class Partfield(dict):
	def __init__(self,**kwargs):
		kwargs["Polygon"]=Factory.parse_recursive("Polygon", kwargs.pop("Polygon"))
		super(Partfield, self).__init__(**kwargs)

class Polygon(dict):
	def __init__(self,**kwargs):
		kwargs["Linestring"]=Factory.parse_recursive("Linestring", kwargs.pop("Linestring"))
		super(Polygon, self).__init__(**kwargs)
	

class Task(dict):
	def __init__(self, **kwargs):
		if int(kwargs["TaskStatus"]) == 1: #it's a prescription map file
			kwargs["TreatmentZone"]=Factory.parse_recursive("TreatmentZone", kwargs.pop("TreatmentZone"))
			kwargs["Grid"]["id"]=abs(int(kwargs["TaskId"][3:]))
			kwargs["Grid"]=Factory.parse_recursive("Grid", kwargs.pop("Grid"))
			kwargs["DataLogTrigger"]={"DataLogDDI":"DFFF", "DataLogMethod":31}
			if "OperTechPractice" in kwargs:
				kwargs["OperTechPractice"]=Factory.parse_recursive("OperTechPractice", kwargs.pop("OperTechPractice"))
		else: #it's a log map file
			assert "TimeLog" in kwargs or "TimeSequence" in kwargs, "Task must have either a TimeLog or TimeSequence object"
			obj_type = "TimeLog" if "TimeLog" in kwargs else "TimeSequence" #FIXME not sure of this: multiple timelogs and timesequence could be present
			arg="Timelog"
			kwargs["TaskStatus"]=int(kwargs["TaskStatus"])
			kwargs[arg]=Factory.parse_recursive(obj_type, kwargs.pop(obj_type))
			for arg in ["Grid","TreatmentZone","DeviceAllocation", "Time"]:
				del kwargs[arg]
			
		super(Task, self).__init__(**kwargs)

class Grid(dict):
	def __init__(self, **kwargs):
		assert "id" in kwargs, "Grid object needs id argument"
		kwargs["GridType"]=2 if "GridType" not in kwargs else kwargs["GridType"]
		kwargs["TreatmentZoneCode"]=0 if "TreatmentZoneCode" not in kwargs else kwargs["TreatmentZoneCode"]
		kwargs["Filename"]=bins.write_bin_grd(kwargs.pop("id"),kwargs.pop("GridCell"), path)
		super(Grid, self).__init__(**kwargs)

class DataLogValue(dict):
	def __init__(self, **kwargs):
		try:
			ddi = DDI.DDI(int(kwargs["ProcessDataDDI"],16))
			self["UoM"] = ddi.sysUnit
			self["DataValueDesignator"] = ddi.DDEName
		except Exception:
			self["UoM"] = self["DataValueDesignator"] = 'n/a'
		self["DataValue"] = float(kwargs["ProcessDataValue"])
		super(DataLogValue, self).__init__(**self)

class TimeLog(dict):
	def __init__(self, **kwargs):
		assert "Device" in TaskData, 'TimeLog object definition needs "Device" object' #shouldn't fail, the xml should be validated first
		def find_Device(dev_el):
			for dev in TaskData["Device"]:
				if dev_el in [d_e["DeviceElementId"] for d_e in dev["DeviceElement"]]:
					return dev["DeviceDesignator"], dev["DeviceStructureLabel"]
		
		self["TimeSequence"] = bins.read_bin_tlg(kwargs['Filename'], path) #TODO infer xsd from xml
		self["DeviceDesignator"] = self["DeviceStructureLabel"] = None
		if self["TimeSequence"]:
			#INFO only one implement is handled in a timelog, we take the first reference to that
			self["DeviceDesignator"], self["DeviceStructureLabel"] = find_Device(self["TimeSequence"][0]["DataLogValue"][0]["DeviceElementIdRef"]) 
			self["TimeSequence"]= Factory.parse_recursive("TimeSequence", self["TimeSequence"])
			l=sorted([i["Start"] for i in self["TimeSequence"]])#time series may not be ordered
			self["Start"] = int(datetime.datetime.fromisoformat(l[0]).timestamp())
			self["Stop"] = int(datetime.datetime.fromisoformat(l[-1]).timestamp())
			self["Duration"] = self["Stop"] - self["Start"]
		super(TimeLog, self).__init__(**self)

#test unit
if __name__ == '__main__':
	import json
	from pprint import pprint
	res, TaskData = utils.validate_json('/home/tony/Progetti/ISOBUSConverter-tony/test/TASKDATA-PMAP/ISOBUS_CONVERTER-PrescriptionMap-examplev2.1.json',utils.PMAP_JSON_SCHEMA_PATH)
	assert res, TaskData
	TaskData['Task']=Factory.parse_recursive('Task',TaskData['Task'])

	print(json.dumps(TaskData))