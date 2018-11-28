# this is where the routes are configured for the homepage, and the dashboard
# 5 and only 5, 6th is TBD


reportcard_routes=[ \

    {'route':'1','grade':'B','services':[('TK','00000'),('TK','00000')],
     'schedule_url':'https://www.njtransit.com/pdf/bus/T0001.pdf',
     'moovit_url':'https://moovitapp.com/',\
     'prettyname':'Route 1',\
     'description_short':'Coming soon.',\
     'description_long':'Coming soon.'},
                   
    {'route':'27','grade':'B','services':[('TK','00000'),('TK','00000')],
     'schedule_url':'https://www.njtransit.com/pdf/bus/T0027.pdf',
     'moovit_url':'https://moovitapp.com/',\
     'prettyname':'Route 27',\
     'description_short':'Coming soon.',\
     'description_long':'Coming soon.'},
                   
    {'route':'28','grade':'B','services':[('TK','00000'),('TK','00000')],
     'schedule_url':'https://www.njtransit.com/pdf/bus/T0028.pdf',
     'moovit_url':'https://moovitapp.com/',\
     'prettyname':'Route 28',\
     'description_short':'Coming soon.',\
     'description_long':'Coming soon.'}\
    ]


grade_descriptions=[ \
    {'grade':'A', 'description':'Service is provided in line with rider expectations of reliability, capacity, and quality.'},
    {'grade':'B', 'description':'Service is usually good but occaissionaly falls short of rider expectations.'},
    {'grade':'C', 'description':'Service meets the needs of riders some of the time, but suffers from serious shortcomings and gaps. Focused action is required to improve service in the near-term.'},
    {'grade':'D', 'description':'Service frequently fails to meet the needs of riders, and requires substantial effort at improvement.'},
    {'grade':'F', 'description':'Service frequently fails to meeting rider needs and expectations. Immediate action required to achieve minimum level of service.'}\
    ]
