import lib.BusAPI as BusAPI

routedata = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data('nj', 'routes', route='87'))

route_list =[]
for i in routedata:
    path_list = []
    for path in i.paths:
        stops_points = []
        for point in path.points:
            if isinstance(point, BusAPI.Route.Stop):
                stops_points.append(point)

        path_list.append(stops_points)

    route_list.append(path_list)

    self.route_stop_list = route_list[0] # keep only a single copy of the services list



# routedata = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(self.source, 'routes', route=self.route))
#
# route_list = []
# for i in routedata:
#     path_list = []
#     for path in i.paths:
#         stops_points = []
#         for point in path.points:
#             if isinstance(point, BusAPI.Route.Stop):
#                 stops_points.append(point)
#
#         path_list.append(stops_points)
#
#     route_list.append(path_list)
#
# # self.route_stop_list = route_list[0]  # chop off the duplicate half
# self.route_stop_list = route_list  # keep the whole thing

