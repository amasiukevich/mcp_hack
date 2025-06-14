import os
from typing import Any, Dict, Optional

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from database.data_schema import Shipment  # Assuming you have a Shipment model defined

engine = create_engine(
    os.getenv("DB_PATH"),
    connect_args={"check_same_thread": False},  # Required for SQLite
)
SessionClass = sessionmaker(bind=engine)
db = SessionClass()


def get_shipment_by_id(db: Session, shipment_id: int) -> Optional[Dict[Any, Any]]:
    """
    Retrieve a shipment record from the database by its ID.

    Args:
        db (Session): SQLAlchemy database session
        shipment_id (int): Unique identifier of the shipment

    Returns:
        Optional[Dict[Any, Any]]: Dictionary containing shipment details if found, None otherwise

    Raises:
        SQLAlchemyError: If there's any database-related error
    """
    try:
        shipment = (
            db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
        )

        if not shipment:
            return None

        return shipment.to_dict()  # Assuming your model has a to_dict method

    except SQLAlchemyError as e:
        # Log the error here if you have a logging system
        raise SQLAlchemyError(
            f"Error retrieving shipment with ID {shipment_id}: {str(e)}"
        )


def get_shipment_by_bol_id(db: Session, bol_id: int) -> Optional[Dict[Any, Any]]:
    """
    Retrieve a shipment record from the database by its BOL ID.

    Args:
        db (Session): SQLAlchemy database session
        bol_id (str): Unique identifier of the BOL

    Returns:
        Optional[Dict[Any, Any]]: Dictionary containing shipment details if found, None otherwise

    Raises:
        SQLAlchemyError: If there's any database-related error
    """
    try:
        shipment = db.query(Shipment).filter(Shipment.bol_doc_id == bol_id).first()

        if not shipment:
            return None

        return shipment.to_dict()  # Assuming your model has a to_dict method
    except SQLAlchemyError as e:
        # Log the error here if you have a logging system
        raise SQLAlchemyError(
            f"Error retrieving shipment with BOL ID {bol_id}: {str(e)}"
        )


tms_function_descriptions = [
    {
        "type": "function",
        "name": "get_shipment_by_id",
        "description": "Retrieves detailed shipment information including status, tracking details, and associated courier/shipper data by internal shipment ID",
        "parameters": {
            "type": "object",
            "properties": {"shipment_id": {"type": "integer"}},
        },
    },
    {
        "type": "function",
        "name": "get_shipment_by_bol_id",
        "description": "Retrieves a complete shipment record from the database using the Bill of Lading (BOL) document ID. Returns detailed information including shipment status, tracking details, associated courier and shipper data, delivery dates, and any relevant shipment notes. Returns None if no shipment is found with the given BOL ID.",
        "parameters": {"type": "object", "properties": {"bol_id": {"type": "string"}}},
    },
]


class TMSFunctions:

    def __init__(
        self, functions: list[callable], descriptions: list[dict], db: Session
    ):
        self.functions = functions
        self.descriptions = descriptions
        self.db = db

    def execute_function(self, function_name: str, args: dict) -> Any:
        """
        Execute a function with the given arguments.
        """
        for function in self.functions:
            if function.__name__ == function_name:
                return function(db=self.db, **args)


function_handler = TMSFunctions(
    functions=[get_shipment_by_bol_id, get_shipment_by_id],
    descriptions=tms_function_descriptions,
    db=db,
)


# if __name__ == "__main__":

#     engine = create_engine(
#         'sqlite:///database/test_shipments.db',
#         connect_args={"check_same_thread": False} # Required for SQLite
#     )

#     Session = sessionmaker(bind=engine)
#     db = Session()
#     shipment = get_shipment_by_id(db=db, shipment_id=1)
#     print(json.dumps(shipment.to_dict(), indent=4))

#     bol_number = int(input("Enter the BOL number:"))
#     shipment = get_shipment_by_bol_id(db=db, bol_id=bol_number)
#     print(json.dumps(shipment.to_dict(), indent=4))
