import argparse
from .data import download
from .pipeline import run
from .server import serve

def main():
    parser = argparse.ArgumentParser(description='Lowtide flexible-load scheduling lab')
    sub = parser.add_subparsers(dest='command',required=True)
    p = sub.add_parser('download');p.add_argument('--cache',default='data')
    p = sub.add_parser('run');p.add_argument('--cache',default='data');p.add_argument('--output',default='reports/custom')
    p = sub.add_parser('serve');p.add_argument('--port',type=int,default=8791)
    args = parser.parse_args()
    if args.command == 'download':
        download(args.cache)
    elif args.command == 'run':
        run(args.cache,args.output)
    else:
        serve(args.port)

if __name__ == '__main__':
    main()
