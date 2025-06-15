import os
from typing import Any, Dict, Optional

from mcp_stuff.functions import (
    get_all_shipments as get_all_shipments_func,
    get_shipment_by_bol_id as get_shipment_by_bol_id_func,
    get_shipment_by_id as get_shipment_by_id_func,
    get_shipper_by_email as get_shipper_by_email_func,
)

from database.data_schema import Shipment
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

load_dotenv()

mcp = FastMCP("TMS MCP")


@mcp.tool()
def get_shipper_by_email(email: str) -> Optional[Dict[Any, Any]]:
    """
    Retrieve a shipper record from the database by its email.
    """
    return get_shipper_by_email_func(email)

@mcp.tool()
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
    return get_shipment_by_id_func(shipment_id)


@mcp.tool()
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
    return get_shipment_by_bol_id_func(bol_id)

@mcp.tool()
def get_all_shipments(shipper_email: str) -> Optional[Dict[Any, Any]]:
    """
    Retrieve all shipments from the database for a given shipper email.

    Args:
        email (str): Email of the shipper

    Returns:
        Optional[Dict[Any, Any]]: List of shipment dictionaries if found, None otherwise

    """
    return get_all_shipments_func(shipper_email)


if __name__ == "__main__":
    mcp.run()
