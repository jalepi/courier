from argparse import ArgumentParser

def start(names: [str]):
    print(names)

if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("--name", 
                        default=None, 
                        action='append',
                        type=str)

    args = parser.parse_args()
    start([1])