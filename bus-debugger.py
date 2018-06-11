# for debugging Buses parse_route_xml

import lib.Buses as Buses
routes=Buses.parse_route_xml(Buses.get_xml_data('nj', 'routes', route=119))
