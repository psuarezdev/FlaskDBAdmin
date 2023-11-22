from flask import Flask, render_template, request, redirect, session
from mysql.connector import connect
from json import loads, dumps
from functools import wraps
from secrets import token_hex

# Crear una instancia de la aplicación Flask
app = Flask(__name__)
# Generar una clave secreta para la sesión de la aplicación
app.secret_key = token_hex(16)

# Establecer variables de conexión y base de datos como None al principio
conn = None
db = None

# Decorador para requerir autenticación antes de acceder a ciertas rutas
def auth_required(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    if not session.get('logged_in'):
      return redirect('/login')
    return f(*args, **kwargs)
  return decorated

# Ruta principal para mostrar las tablas y sus registros
@app.route("/")
@auth_required
def index():
  # Ejecutar una consulta para obtener todas las tablas en la base de datos para posteriormente listarlas
  db.execute("SHOW TABLES")
  tables = db.fetchall()

  data = { "tables": tables }
  
  # Obtener el parámetro 'table' de la solicitud HTTP
  table = request.args.get('table')

  if(table):
    data["selected_table"] = table
    
    # Obtener los campos de la tabla seleccionada
    db.execute(f"DESCRIBE {table}")
    fields = db.fetchall()

    data["fields"] = fields

    # Obtener todos los regisros de la tabla seleccionada
    db.execute(f"SELECT * FROM {table}")
    rows = db.fetchall()

    data["rows"] = rows
  
  return render_template("index.html", data=data)
 
# Ruta para insertar datos en la base de datos
@app.route("/insert", methods=["POST"])
@auth_required
def insert():
  try:
    # Obtener los datos de la solicitud y cargarlos como un diccionario
    table = request.form.get('table')
    data = request.form.get('data')

    data_dict = loads(data)

    # Crear strings para la consulta de inserción
    columns = ', '.join(data_dict.keys())
    values = ', '.join([f"'{value}'" for value in data_dict.values()])

    query = f"INSERT INTO {table} ({columns}) VALUES ({values})"

    # Ejecutar la consulta y confirmar los cambios
    db.execute(query)
    conn.commit()

    return dumps({'message': 'Data successfully inserted'}), 200, {'Content-Type': 'application/json'}
  except Exception as e:
    # Devolver un mensaje de error si algo sale mal
    return dumps({'error': f"An error occurred: {e}"}), 500, {'Content-Type': 'application/json'}
 
# Ruta para actualizar datos en la base de datos
@app.route("/update", methods=["POST"]) 
@auth_required
def update():
  try:
    # Obtener los datos de la solicitud para la actualización
    table = request.form.get('table')
    row_id = request.form.get('row_id')
    data = request.form.get('data')

    data_dict = loads(data)
    query = f"UPDATE {table} SET "

    # Construir la consulta de actualización
    for key, value in data_dict.items():
      query += f"{key} = '{value}', "
      
    query = query[:-2]
    query += f" WHERE id = {row_id}"

    # Ejecutar la consulta y confirmar los cambios
    db.execute(query)
    conn.commit()

    return dumps({'message': 'Data successfully updated'}), 200, {'Content-Type': 'application/json'}
  except Exception as e:
    # Devolver un mensaje de error si algo sale mal
    return dumps({'error': str(e)}), 500, {'Content-Type': 'application/json'}

# Ruta para eliminar datos de la base de datos
@app.route("/delete", methods=["POST"])
@auth_required
def delete():
  try:
    # Obtener los datos de la solicitud para eliminar una fila
    table = request.form.get('table')
    row_id = request.form.get('row_id')
  
    # Ejecutar la consulta de eliminación y confirmar los cambios
    db.execute(f"DELETE FROM {table} WHERE id = {row_id}")
    conn.commit()

    return dumps({'message': 'Row deleted successfully'}), 200, {'Content-Type': 'application/json'}
  except Exception as e:
    # Devolver un mensaje de error si algo sale mal
    return dumps({'error': f"An error occurred: {e}"}), 500, {'Content-Type': 'application/json'}

# Ruta para ejecutar consultas personalizadas en la base de datos
@app.route("/query", methods=["POST"])
@auth_required
def query():
  try:
    # Obtener la consulta de la solicitud y ejecutarla
    query = request.form.get('query').strip().lower().replace('\t', '')
    # Ejecutar la consulta SELECT y obtener los resultados
    if(query.startswith('select')):
      db.execute(query)
      rows = db.fetchall()

      # Obtener los campos de la tabla seleccionada en la consulta
      db.execute(f"DESCRIBE {query.split(' ')[3]}")
      fields = db.fetchall()

      return dumps({'fields': fields, 'rows': rows}), 200, {'Content-Type': 'application/json'}
    else:
      # Ejecutar la consulta y confirmar los cambios -> INSERT, UPDATE, DELETE, etc.
      db.execute(query)
      conn.commit()

      return dumps({'message': 'Query executed successfully'}), 200, {'Content-Type': 'application/json'}
  except Exception as e:
    # Devolver un mensaje de error si algo sale mal
    return dumps({'error': f"An error occurred: {e}"}), 500, {'Content-Type': 'application/json'}

# Ruta para el inicio de sesión
@app.route("/login", methods=["GET", "POST"])
def login():
  if(request.method == "POST"):
    # Obtener los datos de inicio de sesión de la solicitud y establecer la conexión
    host = request.form.get("host")
    username = request.form.get("username")
    password = request.form.get("password")
    database = request.form.get("database")
    
    if not password:
      password = ""

    global conn, db

    try:
      # Intentar establecer la conexión y el cursor de la base de datos
      conn = connect(
        host=host.strip(),
        user=username.strip(),
        password=password.strip(),
        database=database.strip()
      )
      
      db = conn.cursor()
      
      # Establecer la sesión como iniciada si la conexión es exitosa
      session['logged_in'] = True
      
      # Obtener una tabla de la base de datos para redirigir al usuario a la página principal y que cargue una tabla directamente
      db.execute("SHOW TABLES")
      tables = db.fetchall()      

      return redirect(f"/?table={tables[0][0]}")
    except Exception as e:
      return render_template("login.html")
  else:
    if session.get('logged_in'):
      db.execute("SHOW TABLES")
      tables = db.fetchall()      

      return redirect(f"/?table={tables[0][0]}")
    
    # Volver a la página de inicio de sesión si hay algún error
    return render_template("login.html")

# Ruta para cerrar la sesión actual
@app.route("/logout")
def logout():
  session['logged_in'] = False
  return redirect("/login")

if __name__ == '__main__':
  # Ejecutar la aplicación Flask
  app.run()