import pymysql
from flask import Flask, render_template, request, redirect, url_for, flash, session
# Flask es el framework principal para construir la aplicación web.
import hashlib 
# Hashlib se utiliza para encriptar contraseñas mediante algoritmos de hashing como MD5.

# Configuración para la conexión con la base de datos MySQL
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'Juventus1901.'
MYSQL_DB = 'control_asistencia'

# Inicialización de la aplicación Flask
app = Flask(__name__)

# Clave secreta para habilitar el uso de sesiones y mensajes flash
app.secret_key = 'your_secret_key'

# Función para conectar a la base de datos MySQL
def connect_to_mysql():
    """
    Crea una conexión a la base de datos MySQL utilizando PyMySQL.
    Retorna un objeto de conexión que puede ser usado para ejecutar consultas.
    """
    return pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        db=MYSQL_DB,
        port=3307
    )

# Ruta principal: página de inicio de sesión
@app.route('/')
def login():
    """
    Renderiza la página de inicio de sesión.
    Permite al usuario introducir credenciales y la sede para iniciar sesión.
    """
    return render_template('login.html')

# Ruta para manejar el proceso de inicio de sesión
@app.route('/iniciar_sesion', methods=['POST'])
def iniciar_sesion():
    """
    Procesa el inicio de sesión verificando las credenciales del usuario.
    Si son correctas, inicia sesión; de lo contrario, muestra un mensaje de error.
    """
    usuario = request.form['usuario']
    contrasena = request.form['contrasena']
    sede = request.form['sede']

    # Encripta la contraseña usando MD5 para compararla con la base de datos
    hashed_password = hashlib.md5(contrasena.encode()).hexdigest()

    connection = connect_to_mysql()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM usuarios WHERE nombre_usuario = %s AND contrasena = %s AND sede = %s",
        (usuario, hashed_password, sede)
    )
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if user:
        session['sede'] = sede
        session['usuario'] = usuario
        return redirect(url_for('opciones'))
    else:
        flash('Usuario o contraseña incorrectos')
        return redirect(url_for('login'))

# Ruta para mostrar el menú principal
@app.route('/opciones')
def opciones():
    """
    Renderiza el menú principal con las opciones disponibles.
    Redirige al inicio de sesión si el usuario no ha iniciado sesión.
    """
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('op.html')

# Ruta para la página principal
@app.route('/home')
def home():
    """
    Renderiza la página principal de la aplicación.
    Solo accesible si el usuario ha iniciado sesión.
    """
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

# Ruta para listar los trabajadores
@app.route('/trabajadores')
def index():
    """
    Recupera y muestra una lista de trabajadores desde la base de datos.
    Redirige al inicio de sesión si no hay un usuario autenticado.
    """
    if 'usuario' not in session:
        return redirect(url_for('login'))

    connection = connect_to_mysql()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM trabajadores")
    trabajadores = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('index.html', trabajadores=trabajadores)

# Ruta para agregar un nuevo trabajador
@app.route('/add', methods=['POST'])
def add_trabajador():
    """
    Permite agregar un nuevo trabajador a la base de datos.
    Los datos del trabajador son recibidos desde un formulario HTML.
    """
    if 'usuario' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        nombre = request.form['nombre']
        cc = request.form['cc']
        tema = request.form.get('tema', '')  # Si no se envía, usar cadena vacía
        huella = request.form.get('huella', '')  # Si no se envía, usar cadena vacía

        connection = connect_to_mysql()
        cursor = connection.cursor()
        cursor.execute(
            'INSERT INTO trabajadores (nombre, cc, tema, huella) VALUES (%s, %s, %s, %s)',
            (nombre, cc, tema, huella)
        )
        connection.commit()
        cursor.close()
        connection.close()

        flash('Trabajador registrado exitosamente.')
        return redirect(url_for('index'))

# Ruta para editar un trabajador existente
@app.route('/edit_trabajador/<int:id>', methods=['GET', 'POST'])
def edit_trabajador(id):
    """
    Permite editar la información de un trabajador existente.
    """
    if 'usuario' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        huella = request.form['huella']

        connection = connect_to_mysql()
        cursor = connection.cursor()
        cursor.execute(
            'UPDATE trabajadores SET nombre = %s, apellido = %s, huella = %s WHERE id = %s',
            (nombre, apellido, huella, id)
        )
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('index'))

    connection = connect_to_mysql()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM trabajadores WHERE id = %s', (id,))
    trabajador = cursor.fetchone()
    cursor.close()
    connection.close()
    return render_template('edit.html', trabajador=trabajador)

# Ruta para registrar la entrada de un trabajador
@app.route('/registrar_entrada', methods=['GET', 'POST'])
def registrar_entrada():
    """
    Permite registrar la entrada de un trabajador a la sede.
    """
    if 'usuario' not in session:
        return redirect(url_for('login'))

    connection = connect_to_mysql()
    cursor = connection.cursor()

    if request.method == 'POST':
        id_trabajador = request.form['id_trabajador']
        hora_entrada = request.form['hora_entrada'] + ':00'  # Añade los segundos

        cursor.execute(
            'INSERT INTO entradas (id_trabajador, hora_entrada, fecha_entrada) VALUES (%s, %s, NOW())',
            (id_trabajador, hora_entrada)
        )
        connection.commit()
        cursor.close()
        connection.close()

        flash('Entrada registrada correctamente.')
        return redirect(url_for('home'))

    cursor.execute("SELECT * FROM trabajadores")
    trabajadores = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('registro_entrada.html', trabajadores=trabajadores)

# Ruta para gestionar préstamos de material
@app.route('/prestamo_material')
def prestamo_material():
    """
    Muestra un formulario para registrar préstamos o devoluciones de materiales.
    """
    if 'usuario' not in session:
        return redirect(url_for('login'))

    connection = connect_to_mysql()
    cursor = connection.cursor()
    cursor.execute("SELECT id, nombre FROM trabajadores")
    trabajadores = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('Material.html', trabajadores=trabajadores)

# Ruta para registrar préstamos o devoluciones
@app.route('/registrar_material', methods=['POST'])
def registrar_material():
    """
    Registra el préstamo o devolución de materiales.
    """
    if 'usuario' not in session:
        return redirect(url_for('login'))

    materiales = request.form.getlist('materiales')
    accion = request.form['accion']
    trabajador_id = request.form['trabajador_id']

    connection = connect_to_mysql()
    cursor = connection.cursor()

    for material in materiales:
        if accion == "prestamo":
            cursor.execute(
                """
                INSERT INTO prestamos (material, trabajador_id, fecha_prestamo)
                VALUES (%s, %s, NOW())
                """,
                (material, trabajador_id)
            )
        elif accion == "devolucion":
            cursor.execute(
                """
                UPDATE prestamos
                SET fecha_devolucion = NOW()
                WHERE material = %s AND trabajador_id = %s AND fecha_devolucion IS NULL
                """,
                (material, trabajador_id)
            )

    connection.commit()
    cursor.close()
    connection.close()

    flash(f'Material(es) {accion} registrado(s) correctamente.')
    return redirect(url_for('prestamo_material'))

# Ruta para cerrar la sesión del usuario
@app.route('/cerrar_sesion')
def cerrar_sesion():
    """
    Cierra la sesión actual eliminando las variables de sesión.
    """
    session.pop('sede', None)
    session.pop('usuario', None)
    return redirect(url_for('login'))

# Inicia la aplicación Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

