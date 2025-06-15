from database.data_schema import Courier, Shipment, ShipmentStatus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

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

# def update_shipment_status(shipment_id: int, status: str) -> None:
#     """
#     Update the status of a shipment in the database.
#     """
#     engine = create_engine(
#         os.getenv("DB_PATH"),
#         connect_args={"check_same_thread": False},  # Required for SQLite
#     )
#     SessionClass = sessionmaker(bind=engine)
#     db = SessionClass()

#     shipment = db.query(Shipment).filter_by(shipment_id=shipment_id).first()
#     shipment.shipment_status = status
#     db.commit()
#     return shipment



### HELPER FUNCTION
def reset_status(shipment_id: int) -> None:
    """
    Reset the status of a shipment in the database.
    """
    engine = create_engine(
        os.getenv("DB_PATH"),
        connect_args={"check_same_thread": False},  # Required for SQLite   
    )
    SessionClass = sessionmaker(bind=engine)
    db = SessionClass()

    shipment = db.query(Shipment).filter_by(shipment_id=shipment_id).first()
    shipment.shipment_status = ShipmentStatus.IN_TRANSIT
    db.commit()
    return shipment

# if __name__ == "__main__":

#     # for more than one shipment
#     number = "(974)583-4681"

#     # shipments = get_shipments_by_courier_contact(number)
#     # for shipment in shipments:
#     #     print(shipment.shipment_id)

#     shipment_id = 7
#     reset_status(shipment_id)
    