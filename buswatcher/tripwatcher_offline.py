# tool for working with offline archived data
# todo data needs to be migrated to new db format first

from lib.TransitSystem import load_system_map
from lib.BusProcessor import BusProcessor

system_map = load_system_map()
BusProcessor(system_map, mode='offline')

