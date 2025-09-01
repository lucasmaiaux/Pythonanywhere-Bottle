import pymysql
from pathlib import Path
from bottle import Bottle, template, request, redirect, static_file

ABSOLUTE_APPLICATION_PATH = Path(__file__).parents[0]
app = Bottle()

# Configuration MySQL pour PythonAnywhere
def get_db_connection():
    return pymysql.connect(
        host='Lucas129.mysql.pythonanywhere-services.com',
        user='Lucas129',
        password='mysqlpass',  # Remplacez par votre mot de passe
        database='Lucas129$todo',
        charset='utf8mb4'
    )

@app.route('/')
def index():
    redirect('/todo')

@app.route('/todo')
def todo_list():
    show  = request.query.show or 'open'
    match show:
        case 'open':
            db_query = "SELECT id, task FROM todo WHERE status = 1"
        case 'closed':
            db_query = "SELECT id, task FROM todo WHERE status = 0"
        case 'all':
            db_query = "SELECT id, task FROM todo"
        case _:
            return template('message.tpl',
                message = 'Wrong query parameter: show must be either open, closed or all.')
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(db_query)
        result = cursor.fetchall()
    output = template('show_tasks.tpl', rows=result)
    return output

@app.route('/new', method=['GET', 'POST'])
def new_task():
    if request.POST:
        new_task = request.forms.task.strip()
        with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO todo (task,status) VALUES (%s,%s)", (new_task, 1))
            new_id = cursor.lastrowid
            connection.commit()
        return template('message.tpl',
            message=f'The new task was inserted into the database, the ID is {new_id}')
    else:
        return template('new_task.tpl')

@app.route('/details/<number:int>')
def show_task(number):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT task FROM todo WHERE id = %s", (number,))
        current_data = cursor.fetchall()
    return template('show_tasks', rows=current_data)


@app.route('/edit/<number:int>', method=['GET', 'POST'])
def edit_task(number):
    if request.POST:
        new_data = request.forms.task.strip()
        status = request.forms.status.strip()
        if status == 'open':
            status = 1
        else:
            status = 0
        with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE todo SET task = %s, status = %s WHERE id = %s", (new_data, status, number))
            connection.commit()
        return template('message.tpl',
                        message=f'The task number {number} was successfully updated')
    else:
        with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT task FROM todo WHERE id = %s", (number,))
            current_data = cursor.fetchone()
        return template('edit_task', current_data=current_data, number=number)

@app.route('/as_json/<number:re:[0-9]+>')
def task_as_json(number):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id, task, status FROM todo WHERE id = %s", (number,))
        result = cursor.fetchone()
    if not result:
        return {'task': 'This task ID number does not exist!'}
    else:
        return {'id': result[0], 'task': result[1], 'status': result[2]}

@app.route('/static/<filepath:path>')
def send_static_file(filepath):
    ROOT_PATH = ABSOLUTE_APPLICATION_PATH / 'static'
    return static_file(filepath, root=ROOT_PATH)


@app.error(404)
def error_404(error):
    return 'Sorry, this page does not exist!'

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)