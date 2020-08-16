from flask import Flask, render_template, request
from multiprocessing import Process, Pipe
from multiprocessing.connection import Connection
from json import loads, dumps
from time import sleep

settings_path = "./courier/settings.json"


def loop(settings: dict):
    while True:
        configuration = {
        } if 'configuration' not in settings else settings['configuration']
        interval = 90 if 'interval' not in configuration else int(
            configuration['interval'])

        sleep(interval)


def start_loop(conn: Connection):
    processes = []

    while True:
        settings: dict = conn.recv

        for process in processes:
            process.terminate()

        loop_process = Process(target=loop, args=(settings,))
        loop_process.start()
        processes.append(loop_process)


def start_web(conn: Connection):
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

    app.run(debug=True, use_reloader=True)


def main():
    settings = {
        'configuration': {},
        'instructions': {},
    }
    with open(settings_path, mode="r") as f:
        contents = f.read()
        settings = loads(contents)

    web_to_here, here_to_web = Pipe(duplex=True)
    web_process = Process(target=start_web, args=(web_to_here,))
    web_process.start()

    loop_to_here, here_to_loop = Pipe(duplex=False)
    loop_process = Process(target=start_loop, args=(loop_to_here,))
    loop_process.start()

    while True:
        here_to_web.send(settings)
        here_to_loop.send(settings)

        settings: dict = here_to_web.recv()
        print(f'recv: {settings}')
        with open(settings_path, mode="w") as f:
            contents = dumps(settings)
            f.write(contents)


if __name__ == '__main__':
    main()
