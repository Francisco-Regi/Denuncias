
from flask import Flask, request, jsonify, render_template, redirect, session
import sqlite3
import os
from datetime import datetime
import requests

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "denuncias.db")
app.secret_key = "clave-secreta-segura"  # Necesario para usar sesiones

# Páginas principales
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/anonimo")
def formulario_anonimo():
    return render_template("anonimo.html")

@app.route("/digital")
def formulario_digital():
    return render_template("digital.html")

@app.route("/consulta")
def consulta():
    return render_template("consulta.html")

@app.route("/registro")
def registro():
    return render_template("registrarse.html")

@app.route("/login")
def login():
    return render_template("iniciosesion.html")

# Generar folio automáticamente
@app.route("/api/ultimo_folio")
def ultimo_folio():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT MAX(id_denuncia) FROM denuncias")
    ultimo_id = cur.fetchone()[0] or 0
    nuevo_folio = f"DV{datetime.now().strftime('%Y%m%d')}{ultimo_id + 1:04d}"
    return jsonify({"folio": nuevo_folio})

# Registro de usuario
@app.route("/api/registro", methods=["POST"])
def api_registro():
    
    data = request.form
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO usuarios (nombre, apellidos, correo, contrasena, telefono, curp, acepta_terminos)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("nombre"),
            data.get("apellidos"),
            data.get("correo"),
            data.get("contrasena"),
            data.get("telefono"),
            data.get("curp"),
            1 if data.get("terminos") == "on" else 0
        ))
        conn.commit()
        return redirect("/login")
    except Exception as e:
        conn.rollback()
        return f"Error en registro: {e}"
    finally:
        conn.close()

# Validación de login
@app.route("/api/login", methods=["POST"])
def api_login():
    correo = request.form.get("correo")
    contrasena = request.form.get("contrasena")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT nombre, telefono FROM usuarios WHERE correo=? AND contrasena=?", (correo, contrasena))
    user = cur.fetchone()
    conn.close()

    if user:
        session["nombre"] = user[0]
        session["telefono"] = user[1]
        return redirect("/digital")
    else:
        return "Correo o contraseña incorrectos"

#cerrar sesion
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# Denuncia anónima
@app.route("/api/anonima", methods=["POST"])
def denuncia_anonima():
    data = request.form
    archivos = request.files.getlist("evidencias")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT MAX(id_denuncia) FROM denuncias")
    ultimo_id = cur.fetchone()[0] or 0
    folio = f"DV{datetime.now().strftime('%Y%m%d')}{ultimo_id + 1:04d}"

    cur.execute("""
        INSERT INTO denuncias (
            tipo_denuncia, categoria, latitud, longitud, direccion,
            fecha_hora, placa_vehiculo, descripcion, folio
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "anonima", data.get("categoria"), data.get("latitud"), data.get("longitud"),
        data.get("direccion"), data.get("fecha_hora"), data.get("placa_vehiculo"),
        data.get("descripcion"), folio
    ))
    id_denuncia = cur.lastrowid

    # Asegurarse de que la carpeta exista
    os.makedirs("static/uploads", exist_ok=True)

    for archivo in archivos:
        if archivo:
            nombre = archivo.filename
            archivo.save(os.path.join("static/uploads", nombre))
            cur.execute("INSERT INTO evidencias (id_denuncia, archivo, tipo) VALUES (?, ?, ?)",
                        (id_denuncia, nombre, "imagen"))

    conn.commit()
    conn.close()
    return redirect("/")



# Denuncia digital
@app.route("/api/digital", methods=["POST"])
def denuncia_digital():
    data = request.form
    archivos = request.files.getlist("evidencias")
    nombre = data.get("nombre")
    telefono = data.get("telefono")

    # ✅ Crear carpeta de destino si no existe
    os.makedirs("static/uploads", exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id_usuario FROM usuarios WHERE nombre=? AND telefono=?", (nombre, telefono))
    user = cur.fetchone()
    if not user:
        return "Usuario no encontrado", 400
    id_usuario = user[0]

    cur.execute("SELECT MAX(id_denuncia) FROM denuncias")
    ultimo_id = cur.fetchone()[0] or 0
    folio = f"DV{datetime.now().strftime('%Y%m%d')}{ultimo_id + 1:04d}"

    cur.execute("""
        INSERT INTO denuncias (
            id_usuario, tipo_denuncia, categoria, latitud, longitud, direccion,
            fecha_hora, placa_vehiculo, descripcion, folio
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        id_usuario, "digital", data.get("categoria"), data.get("latitud"), data.get("longitud"),
        data.get("direccion"), data.get("fecha_hora"), data.get("placa_vehiculo"),
        data.get("descripcion"), folio
    ))
    id_denuncia = cur.lastrowid

    # Asegurarse de que la carpeta exista
    os.makedirs("static/uploads", exist_ok=True)

    for archivo in archivos:
        if archivo:
            nombre = archivo.filename
            archivo.save(os.path.join("static/uploads", nombre))
            cur.execute("INSERT INTO evidencias (id_denuncia, archivo, tipo) VALUES (?, ?, ?)",
                        (id_denuncia, nombre, "imagen"))
    conn.commit()
    conn.close()
    # Enviar mensaje de WhatsApp
    mensaje = (
        f"📄 *Denuncia Registrada*\n\n"
        f"🆔 Folio: {folio}\n"
        f"📂 Categoría: {data.get('categoria')}\n"
        f"📅 Fecha: {data.get('fecha_hora')}\n\n"
        f"✅ Muchas gracias por su colaboración. Estaremos en comunicación con usted."
    )

    url_api = "https://api.wali.chat/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "Token": "d076d11b5867519589de94b1341c8773bd992e80319d5cc5c0c71fdc3e7bc6d0f85f1d9159530ca0"  # Reemplaza con tu token real
    }
    payload = {
        "phone": f"+52{telefono}",  # Asegúrate de incluir el código de país
        "message": mensaje
    }

    try:
        response = requests.post(url_api, json=payload, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar el mensaje de WhatsApp: {e}")

    return jsonify({"status": "ok"})



# Consulta de denuncias
@app.route("/api/consulta/<folio>")
def consulta_folio(folio):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT estado, descripcion_seguimiento, atendido_por, cargo FROM denuncias WHERE folio = ?", (folio,))
    row = cur.fetchone()
    conn.close()
    if row:
        return jsonify({
            "estado": row[0],
            "descripcion": row[1],
            "atendido_por": row[2],
            "cargo": row[3]
        })
    else:
        return jsonify({"error": "No encontrado"}), 404

if __name__ == "__main__":
    app.run(debug=True)
