import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class MongoHandler:
    def __init__(self, mongo: Any):
        self.mongo = mongo

    def get_destinations(self, filter_by_name: Optional[str] = None) -> List[Dict[str, Any]]:
        logger.info(f"Fetching destinations with filter: {filter_by_name}")
        query = {"destinationName": filter_by_name} if filter_by_name else {}
        destinations = list(self.mongo.db.destinations.find(query))
        logger.info(f"Fetched {len(destinations)} destinations")
        return destinations

    def get_default_strategy(self) -> str:
        logger.info("Fetching default strategy from settings")
        strategy_doc = self.mongo.db.settings.find_one({"key": "default_strategy"})
        strategy = strategy_doc.get("value") if strategy_doc else "ALL"
        logger.info(f"Default strategy fetched: {strategy}")
        return strategy

    def log_request(self, request_id: str, request_data: Dict[str, Any], response_data: Dict[str, Any]) -> None:
        logger.info(f"Logging request {request_id} to database")
        log_entry = {
            "request_id": request_id,
            "request": request_data,
            "response": response_data
        }
        self.mongo.db.logs.insert_one(log_entry)
        logger.info(f"Logged request {request_id}")
