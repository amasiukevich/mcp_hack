
from datetime import datetime
from typing import List
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class ShipmentStatus(str, PyEnum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class CourierStatus(str, PyEnum):
    AVAILABLE = "available"
    RESTING = "resting"
    NOT_AVAILABLE = "not_available"

class Shipper(Base):
    __tablename__ = "shippers"

    shipper_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)

    # Relationships
    shipments = relationship("Shipment", back_populates="shipper")
    shipper_process = relationship("ShipperProcess", back_populates="shipper", uselist=False)

    def to_dict(self):
        """Convert the Shipper object to a dictionary."""
        return {
            'shipper_id': self.shipper_id,
            'name': self.name,
            'email': self.email
        }

class Courier(Base):
    __tablename__ = "couriers"

    courier_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    contact_number = Column(String(20), nullable=False)
    status = Column(Enum(CourierStatus), nullable=False)
    email = Column(String(255), nullable=False, unique=True)

    # Relationships
    shipments = relationship("Shipment", back_populates="courier")
    
    def to_dict(self):
        """Convert the Courier object to a dictionary."""
        return {
            'courier_id': self.courier_id,
            'name': self.name,
            'contact_number': self.contact_number,
            'status': self.status.value if self.status else None,
            'email': self.email
        }


class Shipment(Base):
    __tablename__ = "shipments"

    shipment_id = Column(Integer, primary_key=True)
    bol_doc_id = Column(Integer, nullable=False)
    pod_doc_id = Column(Integer, nullable=False)
    shipper_id = Column(Integer, ForeignKey("shippers.shipper_id"), nullable=False)
    courier_id = Column(Integer, ForeignKey("couriers.courier_id"), nullable=True)
    eta = Column(DateTime, nullable=False)
    delivery_date = Column(DateTime, nullable=True)
    shipment_status = Column(Enum(ShipmentStatus), nullable=False)
    shipment_comments = Column(Text, nullable=True)
    dest_address = Column(String(500), nullable=False)
    source_address = Column(String(500), nullable=False)

    # Relationships
    shipper = relationship("Shipper", back_populates="shipments")
    courier = relationship("Courier", back_populates="shipments")

    def to_dict(self):
        """Convert the Shipment object to a dictionary."""
        return {
            'shipment_id': self.shipment_id,
            'bol_doc_id': self.bol_doc_id,
            'pod_doc_id': self.pod_doc_id,
            'shipper_id': self.shipper_id,
            'courier_id': self.courier_id,
            'eta': self.eta.isoformat() if self.eta else None,
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None,
            'shipment_status': self.shipment_status.value if self.shipment_status else None,
            'shipment_comments': self.shipment_comments,
            'dest_address': self.dest_address,
            'source_address': self.source_address,
            'shipper': self.shipper.to_dict() if self.shipper else None,
            'courier': self.courier.to_dict() if self.courier else None
        }


class ShipperProcess(Base):
    __tablename__ = "shipper_processes"

    shipper_id = Column(Integer, ForeignKey("shippers.shipper_id"), primary_key=True)
    email = Column(String(255), nullable=False)
    thread_id = Column(Integer, nullable=False)

    # Relationships
    shipper = relationship("Shipper", back_populates="shipper_process")

    def to_dict(self):
        """Convert the ShipperProcess object to a dictionary."""
        return {
            'shipper_id': self.shipper_id,
            'email': self.email,
            'thread_id': self.thread_id
        }