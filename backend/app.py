"""Flask Application for IoT Smart Home Energy Manager"""
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from loguru import logger
from datetime import datetime
import paho.mqtt.client as mqtt
import json
from functools import wraps

# Initialize Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure Logging
logger.add("logs/app.log", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", rotation="500 MB")

# MQTT Configuration
MQTT_BROKER = os.getenv('MQTT_BROKER', 'mosquitto')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_USER = os.getenv('MQTT_USER', '')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')

# MQTT Client
mqtt_client = mqtt.Client()

def on_mqtt_connect(client, userdata, flags, rc):
    """MQTT Connection Callback"""
    if rc == 0:
        logger.info("MQTT connected")
        client.subscribe("home/devices/+/power")
        client.subscribe("home/devices/+/status")
    else:
        logger.error(f"MQTT connection failed: {rc}")

def on_mqtt_message(client, userdata, msg):
    """MQTT Message Callback"""
    try:
        payload = json.loads(msg.payload.decode())
        logger.info(f"MQTT Message: {msg.topic} = {payload}")
        # Emit to WebSocket clients
        socketio.emit('mqtt_message', {'topic': msg.topic, 'payload': payload}, broadcast=True)
    except Exception as e:
        logger.error(f"Error processing MQTT message: {e}")

mqtt_client.on_connect = on_mqtt_connect
mqtt_client.on_message = on_mqtt_message

# Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health Check Endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}), 200

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Get All Registered Devices"""
    logger.info("Fetching all devices")
    return jsonify({'devices': [], 'count': 0}), 200

@app.route('/api/devices', methods=['POST'])
def register_device():
    """Register New Device"""
    try:
        data = request.get_json()
        logger.info(f"Registering new device: {data.get('name')}")
        return jsonify({'message': 'Device registered', 'device_id': '001'}), 201
    except Exception as e:
        logger.error(f"Error registering device: {e}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/energy/live', methods=['GET'])
def get_live_energy():
    """Get Live Energy Consumption Data"""
    logger.info("Fetching live energy data")
    return jsonify({'power': 2500, 'voltage': 230, 'current': 10.87, 'timestamp': datetime.utcnow().isoformat()}), 200

@app.route('/api/energy/forecast', methods=['GET'])
def get_forecast():
    """Get Sales Forecast Data"""
    logger.info("Fetching energy forecast")
    return jsonify({'forecast': [], 'model': 'prophet', 'accuracy': 0.92}), 200

@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    """Get AI Optimization Recommendations"""
    logger.info("Generating recommendations")
    return jsonify({'recommendations': ['Use AC during off-peak hours', 'Optimize water heater schedule']}), 200

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """WebSocket Connection Handler"""
    logger.info("Client connected")
    emit('response', {'data': 'Connected'})

@socketio.on('request_update')
def handle_request_update(data):
    """Handle Client Update Requests"""
    logger.info(f"Update request: {data}")
    emit('update', {'timestamp': datetime.utcnow().isoformat()}, broadcast=True)

if __name__ == '__main__':
    # Connect to MQTT
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        mqtt_client.loop_start()
        logger.info(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as e:
        logger.error(f"Failed to connect to MQTT: {e}")
    
    # Start Flask-SocketIO server
    logger.info("Starting Flask-SocketIO server on port 5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
