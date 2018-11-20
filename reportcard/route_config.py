# this is where the routes are configured for the homepage, and the dashboard
# 5 and only 5, 6th is TBD


reportcard_routes=[ \
    {'route':'82','grade':'B','services':[('Exchange Place','73012'),('TK','00000')],'schedule_url':'https://www.njtransit.com/pdf/bus/T0082.pdf','moovit_url':'https://moovitapp.com/index/en/public_transit-line-82-NYCNJ-121-516-546379-0',\
    'description_short':'Tracing a long-defunct streetcar line, the 82 connects a corner of The Heights to Downtown Jersey City at Exchange Place.',\
    'description_long':'Following an old streetcar line defunct since 1931, the 82 provides rush-hour only, one-direction commuter service from Summit Avenue to Exchange Place and back in the evening.'},

    {'route': '83', 'grade': 'A', 'services': [('TK', '73012'), ('TK', '00000')],
     'schedule_url': 'https://www.njtransit.com/pdf/bus/T0083.pdf',
     'moovit_url': 'https://moovitapp.com/index/en/public_transit-line-83-NYCNJ-121-516-432984-0', \
     'description_short': 'The 83 links Journal Square and downtown Hackensack via The Heights along an over-extended, infrequent route.', \
     'description_long': 'The 83 links Journal Square and downtown Hackensack along JFK Boulevard in The Heights, making it one of the few inter-county routes served from Jersey City.'},

    {'route':'84','grade':'B','services':[('Journal Square (Via Bergenline Av)','3372'),('North Bergen (Via Bergenline Av)','3373'),('Journal Square (Via Park Av)','3374'),('North Bergen (Via Park Av)','3375')],'schedule_url':'https://www.njtransit.com/pdf/bus/T0084.pdf','moovit_url':'https://moovitapp.com/index/en/public_transit-line-84-NYCNJ-121-516-432985-0',\
     'description_short':'Palisade Avenue local connecting Journal Square, The Heights and Union City and North Bergen every 15-20 minutes throughout the day.',\
     'description_long':'One of the most frequent buses operating along the Palisade Ave corridor, the 84 provides a vital connector between the eastern side of The Heights and Journal Square, as well as points further north along the Palisades in Hudson County.'},\

    {'route': '85', 'grade': 'B','services':[('Secaucus','3379'),('Hoboken','3381')],'schedule_url': 'https://www.njtransit.com/pdf/bus/T0085.pdf','moovit_url': 'https://moovitapp.com/index/en/public_transit-line-86-NYCNJ-121-516-432987-0',\
     'description_short': 'The 85 provides an infrequent but vital link to shopping and jobs in the Secaucus Meadowlands.',\
     'description_long': 'The 85 provides infrequent service every 30-60 minutes providing a vital link to shopping and employment in the Secaucus area.'},\

    {'route':'86', 'grade':'B', 'services':[('Newport Centre Mall','3384'),('Service2','0000'),('Service3','0000')],'schedule_url':'https://www.njtransit.com/pdf/bus/T0086.pdf','moovit_url':'https://moovitapp.com/index/en/public_transit-line-86-NYCNJ-121-516-432987-0',
     'description_short':'This service links The Heights with downtown Jersey City\'s vibrant Grove Street area and the Newport Center Mall.',\
     'description_long':'Running along the Palisade Corridor, the 86(and 86P) link into downtown Jersey City where the bustling Grove Street area and Newport Mall feature lots of dining and entertainment options.'},\

    {'route':'87', 'grade':'D', 'services':[('Jersey City (Gates Av)','3391'),('Hoboken','3392'),('Hoboken','3393'),('Jersey City (Gates Av)','3396')], 'schedule_url':'https://www.njtransit.com/pdf/bus/T0087.pdf','moovit_url':'https://moovitapp.com/index/en/public_transit-line-87-NYCNJ-121-516-432988-0',\
     'description_short':'The Heights\' main bus backbone, providing its most frequent links to rail transit at Journal Square and Hoboken Terminal.',\
     'description_long':'The 87 snakes through The Heights, linking to important rail stations at Journal Square, the 9th Street Light Rail Station, and Hoboken Terminal. It has the worst bunching problems of all NJTransit routes in the area due to heavy traffic, railroad grade crossings, and more.'},\

    {'route': '88', 'grade': 'B', 'services':[('North Bergen','3413'),('Journal Square','3415')],'schedule_url': 'https://www.njtransit.com/pdf/bus/T0088.pdf','moovit_url':'https://moovitapp.com/index/en/public_transit-line-88-NYCNJ-121-516-432989-0',\
     'description_short': 'Links the Western Heights with North Bergen, Union City and Journal Square along JFK Boulevard.',\
     'description_long': 'The 88 provides service throughout the day along JFK Boulevard providing a north-south connection along the western portion of Hudson County.'},\

    {'route':'119', 'grade':'C', 'services':[('Bayonne','117992'),('New York City','38040'),('New York City (limited)','99396')],'schedule_url':'https://www.njtransit.com/pdf/bus/T0119.pdf','moovit_url':'https://moovitapp.com/index/en/public_transit-line-125-NYCNJ-121-516-433013-0',\
     'description_short':'The primary Manhattan commuter service in The Heights, despite recent service increases the 119 is often overcrowded.',\
     'description_long':'The 119 does triple-duty: as a Hudson County north-south connector, a Central Avenue local, and main express commuter line to midtown Manhattan, and fails at all three missions. The 119 is too long, infrequent, and overcrowded.'},

    {'route':'123', 'grade':'B','services':[('Jersey City (Christ Hospital)','1871'),('New York City','1876'),('New York City(limited)s','1877')],'schedule_url':'https://www.njtransit.com/pdf/bus/T0123.pdf','moovit_url':'https://moovitapp.com/index/en/public_transit-line-125-NYCNJ-121-516-433013-0',\
     'description_short':'Alternate Palisade Ave local service to Union City and Manhattan.',\
     'description_long':'The 123 provides local Palisade Avenue service along the length of Union City, before proceeding into Manhattan. A handful of rush-hour runs continue down through The Heights, terminating at Christ Hospital.'},

    {'route': '125', 'grade': 'B','services':[('Journal Square','1885'),('New York City','1886')],'schedule_url': 'https://www.njtransit.com/pdf/bus/T0125.pdf','moovit_url':'https://moovitapp.com/index/en/public_transit-line-125-NYCNJ-121-516-433013-0',\
     'description_short': 'Manhattan commuter line serving the West Side of The Heights along JFK Boulevard.',\
     'description_long': 'The 125 is a primarily rush-hour oriented service providing local scheduled service to and from New York City\'s Port Authority.'}\
    ]

grade_descriptions=[ \
    {'grade':'A', 'description':'Service is provided in line with rider expectations of reliability, capacity, and quality.'},
    {'grade':'B', 'description':'Service is usually good but occaissionaly falls short of rider expectations.'},
    {'grade':'C', 'description':'Service meets the needs of riders some of the time, but suffers from serious shortcomings and gaps. Focused action is required to improve service in the near-term.'},
    {'grade':'D', 'description':'Service frequently fails to meet the needs of riders, and requires substantial effort at improvement.'},
    {'grade':'F', 'description':'Service frequently fails to meeting rider needs and expectations. Immediate action required to achieve minimum level of service.'}\
    ]