todo ASAP
- fix mysql.connector issue on Macbook here
- implement new period routing for stop pages (is this what's borking the caching?)
- verify caching actually working on buswatcher.code4jc.org
- Look at 87 xml response getrotepoints to fix parser - flatten nested it?

todo NEXT
- hourly frequency table
- reliability rating / grade - % on time (based on how long average it is taking buses to run the whole route end to end -- looking at routereport?)

todo FUTURE
- convert to python 3
- bigger/better maps
- import dump.gz --> process 2prune_ tables by keeping only records with pt='APPROACHING' and migrate to current tables
- setup daily mysqldb backup

todo BRYAN comments

Homepage:

- TELL PEOPLE HOW SMART YOU ARE: explain it right up front on the homepage in 1 paragraph. Tell people why it’s currently hard to evaluate bus service, what you did to make it easy, and why it matters.

- LANGUAGE: Not sure about the “opportunities and challenges” language. I think your language can be more pointed: We made this site so you can tell how well the busses actually work. Knowing the status quo is critical to having a constructive discussion about how to improve service for all JC residents.” Or whatever.

- Clicking “check out the report cards” does nothing.

- Nine bus routes on bottom of page are ambiguous - are they buttons or not? Consider adding text above to the effect of “Click your route to see our analysis”

- Can you indicate on the homepage what the general grade is for each route? For instance, can you make the lines with best service green and the one with worst service red, and all the shades in between for the others? Or give each a red/yellow/green icon or something?

Route page (e.g. http://buswatcher.code4jc.org/nj/119):

- The route grades will help a lot. I think you want the grade to be the most obvious thing on the page so it’s clear WTF you’re looking at. The description of the route is nice but less important, especially since I think you already know about the route if you care enough to use the site.

- Can you compare today to historical trends? TODAY IS TYPICAL. TODAY IS WORSE THAN USUAL.

- "What are the trouble spots slowing service on the 119?" language is distracting.

- I like the Bottlenecks list. Put the focus on the stops that need the most help. This should take precedence over “Choose Direction…” which I might consider replacing with a list of all of the stops do you don’t have to go through two drop downs to get to a stop page. Alternatively, replace the whole thing with a map interface that has RED icons for the bottleneck stops and GREEN ones for the good service stops, or some variation thereof.

Stop page (e.g. http://buswatcher.code4jc.org/nj/119/stop/20393):

- Would be nice to have an overall assessment at the top. THIS STATION USUALLY HAS DECENT SERVICE or THIS STATION HAS GOOD SERVICE TODAY or something like that.

- Not sure how to read the Arriving Soon and Arrival History columns together. Presumably since this is a report card I don’t really care about the arriving soon times… I just care whether the service is good or not. If that’s the case, I would ditch arriving soon altogether, or perhaps put all arrivals (past and future) in one single list that’s organized ascending (past first).

- Can you show the delta between planned arrival time and actual arrival? I understand the bunching concern, but it seems like the avg rider would also be concerned about late arrivals. For instance, when I see a bus that usually has headways of 12-25 minutes, but has one instance of a 35 min headway, that seems like it should be called out similarly to how the bunching incidents are called out.

- I see a 3 min interval as bunching but not a 0 minute one as bunching… seems counter intuitive?

