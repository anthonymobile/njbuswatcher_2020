# cron-able script that doesn nothing but grab the arrival buses for an entire route of stops


import argparse
from reportcard import fetch_arrivals

print 'am i running?'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', dest='source', required=True, default='nj', help='source name')
    parser.add_argument('-r', '--route', dest='route', required=True, help='route # ')
    args = parser.parse_args()

    flag=False

    stoplist = fetch_arrivals(args.source,args.route ,flag)

if __name__ == "__main__":
    main()
