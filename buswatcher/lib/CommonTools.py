import time

def timeit(f):

    def timed(*args, **kw):

        ts = time.time()
        result = f(*args, **kw)
        te = time.time()

        print ('func:%r took: %2.4f sec' % \
          (f.__name__, te-ts))
        # print ('func:%r args:[%r, %r] took: %2.4f sec' % \
        #   (f.__name__, args, kw, te-ts))
        return result

    return timed

# gets all stops on all active routes
def get_stoplist(route):
    routes, coordinate_bundle = BusAPI.parse_xml_getRoutePoints(RouteConfig.get_route_geometry(route))
    # routes, coordinate_bundle = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(self.source, 'routes', route=route))
    route_stop_list = []
    for r in routes:
        path_list = []
        for path in r.paths:
            stops_points = RouteReport.Path()
            for point in path.points:
                if isinstance(point, BusAPI.Route.Stop):
                    stops_points.stops.append(point)
            stops_points.id = path.id
            stops_points.d = path.d
            stops_points.dd = path.dd
            path_list.append(
                stops_points)  # path_list is now a couple of Path instances, plus the metadata id,d,dd fields
        route_stop_list.append(path_list)
    return route_stop_list[0]  # transpose a single copy since the others are all repeats (can be verified by path ids)
