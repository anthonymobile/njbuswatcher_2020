import lib.ReportCard as ReportCard
import lib.BusAPI as BusAPI
import lib.WebAPI as WebAPI

from route_config import reportcard_routes,grade_descriptions


# hardcode transit system
source = 'nj'

# hardcode period
period = 'weekly'

# loop over all routes
for rt_no in reportcard_routes:

    # create base RouteReport instance
    routereport=ReportCard.RouteReport(source,rt_no['route'],reportcard_routes,grade_descriptions)

    # generate individual reports
    # every report in lib.ReportCard should have an easy_cache decorator or else we are wasting time

    # generate bunching leaderboard
    routereport.get_bunching_leaderboard(route=rt_no['route'],period=period)

    # generate other reports
    # routereport.get_bunching_leaderboard()

