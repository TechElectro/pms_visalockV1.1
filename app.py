import socket
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import datetime

# --- Constantes del Protocolo (Basado en la Documentación) ---
STX = b'\x02' # Tag de inicio de registro de datos [cite: 23]
ETX = b'\x03' # Tag de fin de registro de datos [cite: 24]
RS = b'|'    # Símbolo separador (0x7C) [cite: 24]
# ---

app = Flask(__name__)
CORS(app) # Habilitar CORS para que el HTML pueda llamar al backend

@app.route('/')
def index():
    return render_template('index.html')

def format_datetime_pms(dt_string):
    """
    Convierte un string 'YYYY-MM-DDTHH:MM' de datetime-local
    al formato PMS 'yyyymmddhhnn'[cite: 30].
    """
    try:
        dt_obj = datetime.datetime.fromisoformat(dt_string)
        return dt_obj.strftime('%Y%m%d%H%M')
    except ValueError:
        return None

def send_tcp_command(server_ip, server_port, command):
    """
    Función helper para abrir un socket, enviar un comando y recibir la respuesta.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0) # Timeout recomendado [cite: 57]
            s.connect((server_ip, server_port))
            s.sendall(command)
            response = s.recv(1024) # Esperar respuesta
            return response, None
    except socket.timeout:
        return None, f"Timeout: No se recibió respuesta de {server_ip}:{server_port}"
    except socket.error as e:
        return None, f"Error de Socket: {e}"
    except Exception as e:
        return None, f"Error desconocido: {e}"

# --- ENDPOINT 1: Crear Tarjeta (Check-in 'G') ---
@app.route('/create-card', methods=['POST'])
def create_card():
    data = request.json
    
    try:
        # Formato de Información: <STX>ddssff[data]<ETX> [cite: 25]
        dd = data.get('dest_addr', '01')   # Dirección de destino [cite: 26]
        ss = data.get('src_addr', '03')    # Dirección de origen [cite: 27]
        ff = 'G' # Comando 'G' para Guest Check-in [cite: 28]
        
        # Campos necesarios para 'G': R, N, D, O [cite: 38]
        room = data.get('room_number')
        name = data.get('guest_name')
        check_in = format_datetime_pms(data.get('check_in'))
        check_out = format_datetime_pms(data.get('check_out'))

        if not all([room, name, check_in, check_out]):
             return jsonify({"error": "Faltan campos (R, N, D, O) o el formato de fecha es incorrecto."}), 400

        # Ejemplo de comando G: <STX>0103G|R102|NDu|D200212201200|O200212302100<ETX> [cite: 38]
        data_payload = RS + f"R{room}".encode('ascii') + \
                       RS + f"N{name}".encode('ascii') + \
                       RS + f"D{check_in}".encode('ascii') + \
                       RS + f"O{check_out}".encode('ascii')
        
        command = STX + dd.encode('ascii') + ss.encode('ascii') + ff.encode('ascii') + data_payload + ETX

    except Exception as e:
        return jsonify({"error": f"Error construyendo el comando: {e}"}), 400

    # --- Enviar comando y obtener respuesta ---
    response_data, error = send_tcp_command(data.get('server_ip'), data.get('server_port'), command)
    
    if error:
        return jsonify({"error": error}), 500

    try:
        response_text = response_data.decode('ascii')
    except UnicodeDecodeError:
        response_text = "(Respuesta no decodificable en ASCII)"

    return jsonify({
        "message": "Comando 'G' enviado exitosamente",
        "sent": command.decode('ascii', errors='replace'),
        "received_hex": response_data.hex(),
        "received_text": response_text
    }), 200

# --- ENDPOINT 2: Guest Check-out ('B') ---
@app.route('/checkout-guest', methods=['POST'])
def checkout_guest():
    data = request.json
    
    try:
        # Lógica especial para 'dd' en comando 'B' 
        # dd=00 -> solo checkout en DB [cite: 40]
        # dd=cliente -> checkout en DB Y cancela tarjeta [cite: 41]
        if data.get('cancel_card'):
            dd = data.get('dest_addr', '01')
        else:
            dd = '00' 
            
        ss = data.get('src_addr', '03')    # Dirección de origen [cite: 27]
        ff = 'B' # Comando 'B' para Guest Check-out [cite: 28]
        
        room = data.get('room_number')
        if not room:
            return jsonify({"error": "Falta campo obligatorio: room_number (R)"}), 400
        
        # Campo 'R' es necesario 
        data_payload = RS + f"R{room}".encode('ascii')
        
        # Campo 'N' (Nombre) es opcional para check-out 
        # Si se incluye, solo se hace check-out a ese huésped [cite: 43]
        if data.get('guest_name'):
             data_payload += RS + f"N{data.get('guest_name')}".encode('ascii')

        # Ejemplo comando B: <STX>0000B|R101<ETX> [cite: 44]
        command = STX + dd.encode('ascii') + ss.encode('ascii') + ff.encode('ascii') + data_payload + ETX

    except Exception as e:
        return jsonify({"error": f"Error construyendo el comando 'B': {e}"}), 400

    # --- Enviar comando y obtener respuesta ---
    response_data, error = send_tcp_command(data.get('server_ip'), data.get('server_port'), command)
    
    if error:
        return jsonify({"error": error}), 500

    try:
        response_text = response_data.decode('ascii')
    except UnicodeDecodeError:
        response_text = "(Respuesta no decodificable en ASCII)"

    return jsonify({
        "message": "Comando 'B' enviado exitosamente",
        "sent": command.decode('ascii', errors='replace'),
        "received_hex": response_data.hex(),
        "received_text": response_text
    }), 200

# --- ENDPOINT 3: Leer Tarjeta ('E') ---
@app.route('/read-card', methods=['POST'])
def read_card():
    data = request.json
    
    try:
        dd = data.get('dest_addr', '01')   # Dirección de destino (el lector) [cite: 26]
        ss = data.get('src_addr', '03')    # Dirección de origen [cite: 27]
        ff = 'E' # Comando 'E' para Leer Tarjeta [cite: 28]
        
        # El comando 'E' no lleva región de datos [data] al enviarse 
        # Ejemplo comando E: <STX>0103E<ETX> 
        command = STX + dd.encode('ascii') + ss.encode('ascii') + ff.encode('ascii') + ETX

    except Exception as e:
        return jsonify({"error": f"Error construyendo el comando 'E': {e}"}), 400

    # --- Enviar comando y obtener respuesta ---
    response_data, error = send_tcp_command(data.get('server_ip'), data.get('server_port'), command)
    
    if error:
        return jsonify({"error": error}), 500

    try:
        response_text = response_data.decode('ascii')
    except UnicodeDecodeError:
        response_text = "(Respuesta no decodificable en ASCII)"

    # La respuesta del PMS sí debe contener datos (R, N, D, O) [cite: 46, 47]
    return jsonify({
        "message": "Comando 'E' enviado exitosamente",
        "sent": command.decode('ascii', errors='replace'),
        "received_hex": response_data.hex(),
        "received_text": response_text
    }), 200

if __name__ == '__main__':
    # Ejecuta el servidor Flask en el puerto 5000
    app.run(debug=True, host='0.0.0.0', port=5000)