import xlrd
from xlwt import *
from models import *
from utility_models import *

def location(filename):
    type_province = LocationType.objects.get(name="Province")
    type_district = LocationType.objects.get(name="District")
    type_constituency = LocationType.objects.get(name="Constituency")
    type_ward = LocationType.objects.get(name="Ward")
    type_polling_district = LocationType.objects.get(name="Polling District")
    type_polling_station = LocationType.objects.get(name="Polling Station")
    type_polling_stream = LocationType.objects.get(name="Polling Stream")
    zambia = Location.objects.get(name="Zambia", type__name="Country")
    stream_name = [1,2,3,4,5,6,7,8,9]
    given_file = xlrd.open_workbook(filename)
    choice_sheet = given_file.sheet_by_index(0)
    for row_num in range(1,choice_sheet.nrows):
        row_vals = choice_sheet.row_values(row_num)
        (province, created) = Location.objects.get_or_create(name=row_vals[0], code=row_vals[0], type=type_province, parent=zambia)
        (district, created) = Location.objects.get_or_create(name=row_vals[1], code=row_vals[1], type=type_district, parent=province)
        (constituency, created) = Location.objects.get_or_create(name=row_vals[3], code=row_vals[3], type=type_constituency, parent=district)
        (ward, created) = Location.objects.get_or_create(name=row_vals[4], code=row_vals[4], type=type_ward, parent=constituency)
        (polling_district, created) = Location.objects.get_or_create(name=row_vals[6], code=row_vals[5], type=type_polling_district, parent=ward)
        (polling_station, created) = Location.objects.get_or_create(name=row_vals[7], code=row_vals[5], type=type_polling_station, parent=polling_district)
        for i in range(int(row_vals[9])):
            (polling_stream, created) = Location.objects.get_or_create(name=stream_name[i], code=stream_name[i], type=type_polling_stream, parent=polling_station)
    return True