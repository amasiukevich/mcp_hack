import os
from typing import Any, Dict, Optional

from database.data_schema import Shipment
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

load_dotenv()



def get_shipper_by_email(email: str) -> Optional[Dict[Any, Any]]:
    """
    Retrieve a shipper record from the database by its email.
    """
    pass

def get_shipment_by_id(shipment_id: int) -> Optional[Dict[Any, Any]]:
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
    engine = create_engine(
        os.getenv("DB_PATH"),
        connect_args={"check_same_thread": False},  # Required for SQLite
    )
    SessionClass = sessionmaker(bind=engine)
    db = SessionClass()

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



def get_shipment_by_bol_id(bol_id: int) -> Optional[Dict[Any, Any]]:
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

    engine = create_engine(
        os.getenv("DB_PATH"),
        connect_args={"check_same_thread": False},  # Required for SQLite
    )
    SessionClass = sessionmaker(bind=engine)
    db = SessionClass()

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

def get_all_shipments(shipper_email: str) -> Optional[Dict[Any, Any]]:
    """
    Retrieve all shipments from the database for a given shipper email.

    Args:
        email (str): Email of the shipper

    Returns:
        Optional[Dict[Any, Any]]: List of shipment dictionaries if found, None otherwise

    """
    engine = create_engine(
        os.getenv("DB_PATH"),
        connect_args={"check_same_thread": False},  # Required for SQLite
    )
    SessionClass = sessionmaker(bind=engine)
    db = SessionClass()

    try:
        shipments = db.query(Shipment).filter(Shipment.shipper.email == email).all()
        return [shipment.to_dict() for shipment in shipments]
    except SQLAlchemyError as e:
        raise SQLAlchemyError(f"Error retrieving shipments for email {email}: {str(e)}")


if __name__ == "__main__":
    mcp.run()
