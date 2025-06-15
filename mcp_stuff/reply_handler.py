TEMPLATE_EMAIL_UPDATE_ETA = """
Dear Supplier,

This is to inform you that the Estimated Time of Arrival (ETA) for shipment ID {shipment_id} has been successfully updated in our system.

Best regards,
Your Logistics Team
"""

TEMPLATE_TG_UPDATE_ETA = """
Hey, the shipment id {shipment_id} ETA update has been successfully updated in the system.
"""



SHIPMENT_SECTION_ONE = """
Shipment ID: {shipment_id}
Shipment Status: {shipment_status}
ETA: {eta}
Delivery Date: {delivery_date}
Source Address: {source_address}
Destination Address: {dest_address}
"""


TEMPLATE_SUPPLIER_SHIPMENT_INFO = """
Dear Supplier,

Please find attached the shipment information of your current shipment.

{shipment_section}

Best regards,
Your Logistics Team
"""


TEMPLATE_ALL_SHIPMENTS_INFO = """
Dear Supplier,

Please find attached the shipment information of your current shipment.

{shipments_sections}

Best regards,
Your Logistics Team
"""


def get_reply_shipper(processed_result: list[dict]) -> str:

    reply = ""
    if len(processed_result) > 1:
        shipment_sections = f"\n{'-'*40}\n".join([SHIPMENT_SECTION_ONE.format(**shipment) for shipment in processed_result])
        reply = TEMPLATE_ALL_SHIPMENTS_INFO.format(shipments_sections=shipment_sections)
    else:
        shipment_section = SHIPMENT_SECTION_ONE.format(**processed_result[0])
        reply = TEMPLATE_SUPPLIER_SHIPMENT_INFO.format(shipment_section=shipment_section)
    
    return reply