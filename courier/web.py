from flask import Flask, render_template, request
from multiprocessing.connection import Connection

def start(conn: Connection):
    app = Flask(__name__)
    @app.route('/', methods = ['GET'])
    def edit():
        fields: dict = conn.recv()

        keys = [k for k in fields.keys()]
        values = [v for v in fields.values()]
        indexes = [i for i, k in enumerate(fields)]
        print(f'indexes: {indexes}')
        print(f'keys: {keys}')
        print(f'values: {values}')
        print(f'fields: {fields}')

        return render_template("edit.html", indexes=indexes, keys=keys, values=values)

    @app.route('/', methods = ['POST'])
    def view():
        keys = request.form.getlist('key')
        values = request.form.getlist('value')
        fields = dict([(k, v) for k, v in zip(keys, values) if k])

        if (conn):
            conn.send(fields)

        keys = [k for k in fields.keys()]
        values = [v for v in fields.values()]
        indexes = [i for i, k in enumerate(fields)]

        return render_template("view.html", indexes=indexes, keys=keys, values=values)


    app.run(debug=True, use_reloader=True)

    if conn:
        conn.close()

if __name__ == "__main__":
    start(None)