import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from database.data_schema import Courier, Shipment

load_dotenv()


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


def get_shipments_by_courier_contact(contact_number: str) -> list[Shipment]:
    """
    Retrieve a courier from the database by their contact number.

    Args:
        contact_number (str): Contact number of the courier

    Returns:
        Courier: Courier object if found, None otherwise
    """

    engine = create_engine(
        os.getenv("DB_PATH"),
        connect_args={"check_same_thread": False},  # Required for SQLite
    )
    SessionClass = sessionmaker(bind=engine)
    db = SessionClass()

    courier = db.query(Courier).filter_by(contact_number=contact_number).first()
    if courier:
        shipments = db.query(Shipment).filter_by(courier_id=courier.courier_id).all()
        return shipments
    else:
        return []


def update_shipment_eta(shipment_id: int, seconds: int) -> Shipment:
    """
    Takes the shipment id and the number of seconds to add to the eta.
    Returns the updated shipment.
    Args:
        shipment_id (int): The id of the shipment to update
        seconds (int): The number of seconds to add to the eta

    Returns:
        Shipment: The updated shipment
    """
    engine = create_engine(
        os.getenv("DB_PATH"),
        connect_args={"check_same_thread": False},  # Required for SQLite
    )
    SessionClass = sessionmaker(bind=engine)
    db = SessionClass()

    if seconds > 0:
        shipment = db.query(Shipment).filter_by(shipment_id=shipment_id).first()
        if not shipment.eta:
            shipment.eta = datetime.now() + timedelta(seconds=seconds)
        else:
            shipment.eta = shipment.eta + timedelta(seconds=seconds)
        db.commit()
        return shipment.to_dict()
    else:
        raise ValueError("Seconds must be greater than 0")


def reset_shipment_eta(shipment_id: int, datetime: datetime) -> Shipment:
    """
    Reset the eta of a shipment in the database.
    """
    engine = create_engine(
        os.getenv("DB_PATH"),
        connect_args={"check_same_thread": False},  # Required for SQLite
    )
    SessionClass = sessionmaker(bind=engine)
    db = SessionClass()

    shipment = db.query(Shipment).filter_by(shipment_id=shipment_id).first()
    shipment.eta = datetime
    db.commit()
    return shipment.to_dict()


if __name__ == "__main__":

    SHIPMENT_ID = 7
    SECONDS = 3 * 3600
    OG_ETA = "2025-06-27 18:24:32.121214"

    # OG_ETA = datetime.strptime(MY_DATE, '%Y-%m-%dT%H:%M:%S.%f')

    print(f"Original shipment eta: {OG_ETA}")
    print("--------------------------------")

    shipment = update_shipment_eta(SHIPMENT_ID, SECONDS)
    print(f"Updated shipment eta: {shipment['eta']}")
    print("--------------------------------")

    shipment = reset_shipment_eta(
        SHIPMENT_ID, datetime.strptime(OG_ETA, "%Y-%m-%d %H:%M:%S.%f")
    )
    print(f"Reset shipment eta: {shipment['eta']}")
    print("--------------------------------")
