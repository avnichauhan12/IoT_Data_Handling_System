from flask import Flask, request, jsonify
from flask_cors import CORS
import pika
import json
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

# Queue Name
RABBITMQ_QUEUE = 'iot_queue'

# MongoDB configuration
MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017
MONGODB_DB = 'iot_system'
MONGODB_COLLECTION = 'user_data'

# Connect to MongoDB
client = MongoClient(MONGODB_HOST, MONGODB_PORT)
db = client[MONGODB_DB]
collection = db[MONGODB_COLLECTION]

active=False
# Sending message to Queue
def send_rabbitmq(message):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE)
    channel.basic_publish(exchange='', routing_key=RABBITMQ_QUEUE, body=json.dumps(message))
    connection.close()

def process_message(body):
    # Process the incoming MQTT message
    try:
        data = json.loads(body)
        # Perform validation, transformation, etc. as needed
        # For simplicity, we'll just insert the message into MongoDB
        collection.insert_one(data)
        print("Message processed and inserted into MongoDB:", data)
    except Exception as e:
        print("Error processing message:", e)

def callback(ch, method, properties, body):
    # Callback function to handle incoming MQTT messages
    process_message(body)

def receive_rabbitmq():
    global active
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declare the RabbitMQ queue
    channel.queue_declare(queue=RABBITMQ_QUEUE)

    # Set up consumer to receive messages
    for method_frame, properties, body in channel.consume(RABBITMQ_QUEUE, auto_ack=True):
        # Process the message
        process_message(body)
        # If receiving_active is False, cancel consuming
        if not active:
            break

    # Close the connection
    connection.close()
    # Reset receiving_active flag
    active = False

@app.route('/')
def index():
    return "Welocme to IOT_SYTEM"

@app.route('/send', methods=['POST'])
def send_message():
    data = request.get_json()
    send_rabbitmq(data)
    return jsonify({'message': 'Message sent successfully'}), 200

@app.route('/receive', methods=['GET'])
def receive_message():
    global active 
    if not active:
        active = True
        receive_rabbitmq()
    return "Message receive Succesfully and stored in the database."

if __name__ == '__main__':
    app.run(debug=True)