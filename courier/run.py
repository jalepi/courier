from multiprocessing import Process, Pipe
from multiprocessing.connection import Connection
from time import sleep

from courier.web import start

def f(conn: Connection):
    while True:
        conn.send([42, None, 'hello'])
        sleep(5.0)
        
    conn.close()

def monitor_web():
    message = { }
    source, target = Pipe(duplex=True)
    process = Process(target=start, args=(target,))
    process.start()
    while True:
        source.send(message)
        message: dict = source.recv()

def monitor_loop():
    receiver, sender = Pipe(duplex=False)
    process = Process(target=f, args=(sender,))
    process.start()
    while True:
        message = receiver.recv()
        print(message)   # prints "[42, None, 'hello']"

if __name__ == '__main__':
    processes = {
        'monitor_web': Process(target=monitor_web),
        'monitor_loop': Process(target=monitor_loop),
    }
    
    for k, v in processes.items():
        v.start()

    while True:
        print('keep alive...')
        sleep(10.0)