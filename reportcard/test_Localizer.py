# testing lib.Localizer
# -- dump to console
import lib.Localizer as Localizer
import lib.BusAPI as BusAPI
print (Localizer.infer_stops(BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data('nj', 'buses_for_route',route='87')),'87'))


