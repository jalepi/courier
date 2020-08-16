from argparse import ArgumentParser
from flask import Flask, render_template, request
from multiprocessing import Process, Pipe
from multiprocessing.connection import Connection
from json import loads, dumps
from time import sleep
from datetime import datetime
from os.path import join
from random import random


def execute_instruction(key: str, value: str) -> (dict, dict):
    return {'key': key, 'value': value}, {'value': random()}


def loop_send(name: str, settings: dict):
    configuration: dict = {
    } if 'configuration' not in settings.keys() else settings['configuration']

    folder: str = configuration['folder']

    seconds: int = 60 if 'seconds' not in configuration.keys() else float(
        configuration['seconds'])

    while True:
        now: datetime = datetime.now()
        source_filename: str = 'storage.{0}.{1:04d}-{2:02d}{3:02d}.log'.format(
            name,
            now.year,
            now.month,
            now.day)
        source_filepath: str = join(folder, source_filename)

        target_filename: str = '{0}.{1}'.format(
            "backup",
            source_filename)
        target_filepath: str = join(folder, target_filename)

        with open(source_filepath, mode="r") as source_fh:
            with open(target_filepath, mode="a+") as target_fh:
                pos = target_fh.tell()
                source_fh.seek(pos)
                lines = source_fh.readlines()
                for line in lines:
                    record = loads(line)
                    text_line = dumps(record)
                    target_fh.write(text_line)
                    target_fh.write('\n')

        sleep(seconds)


def loop_collect(name: str, settings: dict):
    configuration: dict = {
    } if 'configuration' not in settings.keys() else settings['configuration']

    folder: str = configuration['folder']

    seconds: int = 60 if 'seconds' not in configuration.keys() else float(
        configuration['seconds'])

    instructions: dict = {
    } if 'instructions' not in settings.keys() else settings['instructions']

    while True:
        now: datetime = datetime.now()
        filename: str = 'storage.{0}.{1:04d}-{2:02d}{3:02d}.log'.format(
            name,
            now.year,
            now.month,
            now.day)
        filepath: str = join(folder, filename)
        with open(filepath, mode="a+") as f:
            for key, value in instructions.items():
                properties, metrics = execute_instruction(key, value)
                record = [key, now.isoformat(), properties, metrics]
                text_line = dumps(record)
                f.write(text_line)
                f.write('\n')

        sleep(seconds)


def start_loop(name: str, conn: Connection):
    processes = [Process]

    while True:
        settings: dict = conn.recv()

        for process in processes:
            try:
                if process is not None and process.is_alive():
                    process.terminate()
            except Exception as ex:
                print(f'Failed to terminate loop process: {ex}')

        collect_process = Process(target=loop_collect, args=(name, settings,))
        collect_process.start()
        processes.append(collect_process)

        send_process = Process(target=loop_send, args=(name, settings,))
        send_process.start()
        processes.append(send_process)


def start_web(name: str, conn: Connection):
    app = Flask(__name__)

    @app.route('/', methods=['GET'])
    def edit():
        settings: dict = {
            'configuration': {},
            'instructions': {},
            **conn.recv(),
        }

        configuration = settings['configuration']
        instructions = settings['instructions']

        return render_template(
            "edit.html",
            configuration_indexes=[i for i, k in enumerate(configuration)],
            configuration_keys=[k for k in configuration.keys()],
            configuration_values=[v for v in configuration.values()],
            instruction_indexes=[i for i, k in enumerate(instructions)],
            instruction_keys=[k for k in instructions.keys()],
            instruction_values=[v for v in instructions.values()],
        )

    @app.route('/', methods=['POST'])
    def view():
        print(request.form)
        configuration_keys = request.form.getlist('configuration_keys')
        configuration_values = request.form.getlist('configuration_values')
        configuration = dict([(k, v) for k, v in zip(
            configuration_keys, configuration_values) if k])

        instruction_keys = request.form.getlist('instruction_keys')
        instruction_values = request.form.getlist('instruction_values')
        instructions = dict([(k, v) for k, v in zip(
            instruction_keys, instruction_values) if k])

        if (conn):
            settings: dict = {
                'configuration': configuration,
                'instructions': instructions,
            }
            conn.send(settings)

        return render_template(
            "view.html",
            configuration_indexes=[i for i, k in enumerate(configuration)],
            configuration_keys=[k for k in configuration.keys()],
            configuration_values=[v for v in configuration.values()],
            instruction_indexes=[i for i, k in enumerate(instructions)],
            instruction_keys=[k for k in instructions.keys()],
            instruction_values=[v for v in instructions.values()],
        )

    _ = (edit, view)
    app.run(debug=False, use_reloader=False)


def main(name: str, host: str, port: int):

    settings_path = join("./", f"settings.{name}.json")

    settings: dict = {}
    try:
        with open(settings_path, mode="r") as f:
            contents = f.read()
            settings = loads(contents)
    except Exception as ex:
        print(f'Failed to open settings file {settings_path}: {ex}')

    settings = {
        'configuration': {
            'folder': "./",
            'seconds': 10,
        },
        'instructions': {},
        **settings,
    }

    print(f'settings loaded: {settings}')

    web_to_here, here_to_web = Pipe(duplex=True)
    web_process = Process(target=start_web, args=(name, web_to_here,))
    web_process.start()

    loop_to_here, here_to_loop = Pipe(duplex=False)
    loop_process = Process(target=start_loop, args=(name, loop_to_here,))
    loop_process.start()

    while True:
        here_to_web.send(settings)
        here_to_loop.send(settings)

        settings: dict = here_to_web.recv()
        print(f'recv: {settings}')
        with open(settings_path, mode="w+") as f:
            contents = dumps(settings)
            f.write(contents)


if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument(
        "--name",
        default="raspberry",
        type=str,
        help="Application name. Default is raspberry")

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        type=str,
        help="Host Address IP or URL. Default value is 127.0.0.1")

    parser.add_argument(
        "--port",
        default=9000,
        type=int,
        help="Port to listen. Default value is 9000")

    args = parser.parse_args()
    main(name=args.name, host=args.host, port=args.port)
