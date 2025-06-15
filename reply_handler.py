TEMPLATE_EMAIL_UPDATE_ETA = """
Dear Supplier,

This is to inform you that the Estimated Time of Arrival (ETA) for shipment ID {shipment_id} has been successfully updated in our system.

Best regards,
Your Logistics Team
"""

TEMPLATE_TG_UPDATE_ETA = """
Hey, the shipment id {shipment_id} ETA update has been successfully updated in the system.
"""


TEMPLATE_SUPPLIER_SHIPMENT_INFO = """
Dear Supplier,

Please find attached the shipment information of your current shipment.

Shipment ID: {shipment_id}
Shipment Status: {shipment_status}
ETA: {eta}
Delivery Date: {delivery_date}
Source Address: {source_address}
Destination Address: {dest_address}

Best regards,
Your Logistics Team
"""