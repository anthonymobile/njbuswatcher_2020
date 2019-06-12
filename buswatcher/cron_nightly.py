# todo 1 dump this into a decorator in www.py so it runs everytime a page is triggered, and it checks the TTL on the config/route_descriptions.json file

import buswatcher.lib.wwwAPI as wwwAPI
import buswatcher.lib.RouteConfig as RouteConfig

# hardcode transit system
source = 'nj'

# hardcode period
period = 'weekly'

# loop over all routes
for rt_no in reportcard_routes: # todo 3 fix this

    # create base RouteReport instance
    routereport=wwwAPI.RouteReport(source,rt_no['route'])

    # generate individual reports to a pickle file

    # generate bunching leaderboard
    routereport.generate_bunching_leaderboard(route=rt_no['route'],period=period)

    # generate other reports
    # e.g. routereport.get_bunching_leaderboard()


# todo RouteConfig.fetch_update_route_metadata

# check ttl then run it






###################################################
#  old cron_nightly.py
#  generates bunching reports
###################################################

# import lib.ReportCard as ReportCard
#
# from route_config import reportcard_routes,grade_descriptions
#
#
# # hardcode transit system
# source = 'nj'
#
# # hardcode period
# period = 'weekly'
#
# # loop over all routes
# for rt_no in reportcard_routes:
#
#     # create base RouteReport instance
#     routereport=ReportCard.RouteReport(source,rt_no['route'],reportcard_routes,grade_descriptions)
#
#     # generate individual reports to a pickle file
#
#     # every report in lib.ReportCard should have an easy_cache decorator or else we are wasting time
#
#     # generate bunching leaderboard
#     routereport.generate_bunching_leaderboard(route=rt_no['route'],period=period)
#
#     # generate other reports
#     # routereport.get_bunching_leaderboard()
#
# a