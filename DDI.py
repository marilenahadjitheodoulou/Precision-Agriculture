import requests
import requests_cache

requests_cache.install_cache('DDI_cache', backend='sqlite', expire_after=int(1.577e7), allowable_codes=(200, 404))#expires after 6months
DDI_URL='https://www.isobus.net/isobus/dDEntity/detailjson/%d'
DDI_MAX=632

def get_DDIbyUoM_setpoint(uom):
    for num in range(1,DDI_MAX,5):#caselli docet lo step di 5
        ddi=DDI(num)
        if ddi.sysUnit == uom:
            return ddi.DDIdentifier
    raise ValueError("UoM not found in any setpoint")

class DDI:
    def __init__(self, num):
        r = requests.get(DDI_URL % num) #cached
        assert r.status_code == 200, "Proprietary DDI: %d"%num
        self.sysUnit = self.DDIdentifier = self.DDEName = None #to tame the lint
        self.__dict__ = r.json()
        self.__dict__['sysUnit'] = self.__dict__['sysUnit'].replace(u'³','3').replace(u'²','2')

"""
EXAMPLE OF A DDI
{
  "DDIdentifier": "397",
  "DDEName": "Actual Speed",
  "Definition": "The actual speed as measured on or used by a device for the execution of task based data, e.g. to convert a setpoint rate expressed per area to device specific control data that is expressed as a rate per time. The actual speed can be measured by the device itself or it can be a speed value that is obtained from one of the speed parameter groups that are broadcasted on the ISO11783 network and defined in ISO11783-7. Examples of broadcasted speed parameter groups are wheel based speed, ground based speed and machine selected speed. The source of the actual speed can be specified by a Speed Source DDI that is present in the same device element as the speed DDI.  A positive value will represent forward direction and a negative value will represent reverse direction.",
  "sysUnitReadable": "Speed - mm/s",
  "sysUnit": "mm/s",
  "Comment": "This DDI has been added to the data dictionary to support logging of the speed that the device uses for processing and for generation of task data. The addition of a DDI for actual speed allows speed values to be added to the default data set that devices present to a task controller or a data logger.",
  "SAESPN": "",
  "SubmitDate": "2015-04-24",
  "SubmitBy": "Hans van Zadelhoff",
  "SubmitCompany": "Grimme Landmaschinenfabrik GmbH & Co. KG",
  "BitResolution": "1",
  "MinimumValue": "-2147483648",
  "MinimumDisplayValue": "-2147483648",
  "MaximumValue": "2147483647",
  "MaximumDisplayValue": "2147483647",
  "Type": "Entity",
  "SAEOption": "No SAE SPN",
  "SubIdentifier": null,
  "isDraft": "0",
  "isForRevision": "0",
  "RevisionNumber": "1",
  "DeviceClasses": [
    "0 - Non-specific system",
    "1 - Tractor",
    "2 - Primary Soil Tillage",
    "3 - Secondary Soil Tillage",
    "4 - Planters /Seeders",
    "5 - Fertilizer",
    "6 - Sprayers",
    "7 - Harvesters",
    "8 - Root Harvester",
    "9 - Forage harvester",
    "10 - Irrigation",
    "11 - Transport / Trailers",
    "12 - Farmyard Work",
    "13 - Powered Auxilary Units",
    "14 - Special Crops"
  ]
}"""

if __name__ == '__main__':
    ddi=DDI(397)
    print(ddi.sysUnit)
    print(get_DDIbyUoM_setpoint(u'mm3/m2'))