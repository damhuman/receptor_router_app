from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from router_app import RouterApp
from database import MongoHandler
import logging

# App Initialization
app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/router_db"
app.config['JWT_SECRET_KEY'] = 'secret'
mongo = PyMongo(app)
jwt = JWTManager(app)

# Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mongo_handler = MongoHandler(mongo)
router_app = RouterApp(mongo_handler)

# Route to Handle Events
@app.route('/api/events', methods=['POST'])
@jwt_required()
def route_event():
    return router_app.route_event(request)

if __name__ == '__main__':
    app.run(debug=True)
