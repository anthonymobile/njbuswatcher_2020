import lib.wwwAPI as wwwAPI

from route_config import reportcard_routes,grade_descriptions

# hardcode transit system
source = 'nj'

# hardcode period
period = 'weekly'

# loop over all routes
for rt_no in reportcard_routes:

    # create base RouteReport instance
    routereport=wwwAPI.RouteReport(source,rt_no['route'],reportcard_routes,grade_descriptions)

    # generate individual reports to a pickle file

    # generate bunching leaderboard
    routereport.generate_bunching_leaderboard(route=rt_no['route'],period=period)

    # generate other reports
    # e.g. routereport.get_bunching_leaderboard()
