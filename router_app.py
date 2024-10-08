import logging
import uuid
import requests
from flask import jsonify, Request
from flask_jwt_extended import jwt_required
from data_models import EventRequestModel
from database import MongoHandler
from typing import Any, List, Dict
from pydantic import ValidationError

logger = logging.getLogger(__name__)

class RouterApp:
    def __init__(self, mongo_handler: MongoHandler):
        self.mongo_handler = mongo_handler

    @jwt_required()
    def route_event(self, request: Request) -> Any:
        request_id = str(uuid.uuid4())
        logger.info(f"Handling request {request_id}")

        try:
            data = EventRequestModel(**request.json)
            logger.info(f"Request {request_id}: Parsed request data successfully")
        except ValidationError as e:
            logger.error(f"Request {request_id}: Validation error: {e.json()}")
            return jsonify({"error": e.errors()}), 400

        strategy = custom_strategy if (custom_strategy := data.strategy) else self.mongo_handler.get_default_strategy()
        logger.info(f"Request {request_id}: Using strategy {strategy}")

        destinations = self.mongo_handler.get_destinations()
        logger.info(f"Request {request_id}: Evaluating routing intents")
        selected_intents = self.evaluate_strategy(strategy, data.routingIntents)
        response: Dict[str, bool] = {}

        for intent in data.routingIntents:
            dest_name = intent.destinationName
            logger.info(f"Request {request_id}: Processing intent for destination [{dest_name}]")
            dest_info = next((dest for dest in destinations if dest['destinationName'] == dest_name), None)
            if not dest_info:
                response[dest_name] = False
                logger.error(f"UnknownDestinationError ({dest_name}) for request {request_id}")
                continue

            if intent in selected_intents:
                response[dest_name] = True
                logger.info(f"Request {request_id}: Distributing to [{dest_name}]")
                self._distribute_request(request_id, dest_name, dest_info, data.payload)
            else:
                response[dest_name] = False
                logger.info(f"Request {request_id}: Skipped destination [{dest_name}]")

        self.mongo_handler.log_request(request_id, data.dict(), response)
        logger.info(f"Completed handling request {request_id}")
        return jsonify(response)

    def evaluate_strategy(self, strategy: str, routing_intents: List[RoutingIntentModel]) -> List[RoutingIntentModel]:
        logger.info(f"Evaluating strategy: {strategy}")
        if strategy == "ALL":
            return routing_intents
        elif strategy == "IMPORTANT":
            return [intent for intent in routing_intents if intent.important]
        elif strategy == "SMALL":
            return [intent for intent in routing_intents if intent.bytes < 1024]
        logger.warning(f"Unknown strategy type: {strategy}, returning empty list")
        return []

    def _distribute_request(self, request_id: str, dest_name: str, dest_info: Dict[str, Any], payload: Dict[str, Any]) -> None:
        logger.info(f"Request {request_id}: Distributing request to [{dest_name}] with transport [{dest_info['transport']}]")
        transport = dest_info['transport']
        if transport.startswith('http.'):
            self._http_distribute_request(request_id, dest_name, dest_info, payload)
        elif transport.startswith('log.'):
            self._log_distribute_request(request_id, dest_name, dest_info)
        else:
            logger.error(f"Request {request_id}: Unknown transport type [{transport}] for [{dest_name}]")

    def _http_distribute_request(self, request_id: str, dest_name: str, dest_info: Dict[str, Any], payload: Dict[str, Any]) -> None:
        logger.info(f"Request {request_id}: Preparing to send HTTP request to [{dest_name}] with payload {payload}")
        try:
            method = dest_info['transport'].split('.')[1]
            response = requests.request(method, dest_info['url'], json=payload)
            response.raise_for_status()
            logger.info(f"Request {request_id}: payload sent to [{dest_name}] via [{dest_info['transport']}] transport, response: {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Request {request_id}: Failed to send payload to [{dest_name}] via [{dest_info['transport']}] transport, error: {str(e)}")

    def _log_distribute_request(self, request_id: str, dest_name: str, dest_info: Dict[str, Any]) -> None:
        log_level = dest_info['transport'].split('.')[1]
        log_message = f"Request {request_id}: payload sent to [{dest_name}] via [log.{log_level}] transport"
        logger.info(f"Request {request_id}: Preparing to log with level [{log_level}] for [{dest_name}]")
        {
            'info': logger.info,
            'warn': logger.warning,
            'error': logger.error,
            'debug': logger.debug
        }.get(log_level, lambda msg: logger.error(f"Request {request_id}: Unsupported log level [{log_level}] for [{dest_name}]"))(log_message)