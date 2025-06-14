import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data_schema import Base, Shipper, Courier, Shipment, ShipperProcess, ShipmentStatus, CourierStatus

# Initialize Faker
fake = Faker()

class DataGenerator:
    def __init__(self, database_url="sqlite:///test_shipments.db"):
        """Initialize the data generator with database connection."""
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
    def generate_shippers(self, count=10):
        """
        Generate fake shipper data.
        """
        shippers = []
        for _ in range(count):
            shipper = Shipper(
                name=fake.company(),
                email=fake.company_email()
            )
            shippers.append(shipper)
        
        self.session.add_all(shippers)
        self.session.commit()
        return shippers
    
    def generate_couriers(self, count=15):
        """Generate fake courier data."""
        couriers = []
        for _ in range(count):
            courier = Courier(
                name=fake.name(),
                contact_number=fake.phone_number(),
                status=random.choice(list(CourierStatus)),
                email=fake.email()
            )
            couriers.append(courier)
        
        self.session.add_all(couriers)
        self.session.commit()
        return couriers
    
    def generate_shipments(self, shippers, couriers, count=50):
        """Generate fake shipment data."""
        shipments = []
        for _ in range(count):
            # Random ETA between now and 30 days from now
            eta = fake.date_time_between(start_date='now', end_date='+30d')
            
            # Delivery date might be None (not delivered yet) or after ETA
            delivery_date = None
            if random.choice([True, False]):  # 50% chance of being delivered
                delivery_date = fake.date_time_between(start_date=eta, end_date='+45d')
            
            # Choose random shipper and courier (courier might be None)
            shipper = random.choice(shippers)
            courier = random.choice(couriers) if random.choice([True, False, True]) else None  # 66% chance of having courier
            
            shipment = Shipment(
                bol_doc_id=fake.random_int(min=100000, max=999999),
                pod_doc_id=fake.random_int(min=100000, max=999999),
                shipper_id=shipper.shipper_id,
                courier_id=courier.courier_id if courier else None,
                eta=eta,
                delivery_date=delivery_date,
                shipment_status=random.choice(list(ShipmentStatus)),
                shipment_comments=fake.text(max_nb_chars=200) if random.choice([True, False]) else None,
                dest_address=fake.address().replace('\n', ', '),
                source_address=fake.address().replace('\n', ', ')
            )
            shipments.append(shipment)
        
        self.session.add_all(shipments)
        self.session.commit()
        return shipments
    
    def generate_shipper_processes(self, shippers):
        """Generate fake shipper process data."""
        shipper_processes = []
        for shipper in shippers:
            shipper_process = ShipperProcess(
                shipper_id=shipper.shipper_id,
                email=fake.email(),  # Single email as per schema
                thread_id=fake.random_int(min=1000, max=9999)
            )
            shipper_processes.append(shipper_process)
        
        self.session.add_all(shipper_processes)
        self.session.commit()
        return shipper_processes
    
    def generate_all_data(self, shipper_count=10, courier_count=15, shipment_count=50):
        """Generate all fake data in the correct order."""
        print("Generating fake data...")
        
        # Generate shippers first (no dependencies)
        print(f"Generating {shipper_count} shippers...")
        shippers = self.generate_shippers(shipper_count)
        
        # Generate couriers (no dependencies)
        print(f"Generating {courier_count} couriers...")
        couriers = self.generate_couriers(courier_count)
        
        # Generate shipments (depends on shippers and couriers)
        print(f"Generating {shipment_count} shipments...")
        shipments = self.generate_shipments(shippers, couriers, shipment_count)
        
        # Generate shipper processes (depends on shippers)
        print(f"Generating shipper processes...")
        shipper_processes = self.generate_shipper_processes(shippers)
        
        print("Data generation completed!")
        return {
            'shippers': shippers,
            'couriers': couriers,
            'shipments': shipments,
            'shipper_processes': shipper_processes
        }
    
    def print_sample_data(self):
        """Print some sample data to verify generation."""
        print("\n=== SAMPLE DATA ===")
        
        # Sample shippers
        shippers = self.session.query(Shipper).limit(3).all()
        print("\nSample Shippers:")
        for shipper in shippers:
            print(f"  ID: {shipper.shipper_id}, Name: {shipper.name}, Email: {shipper.email}")
        
        # Sample couriers
        couriers = self.session.query(Courier).limit(3).all()
        print("\nSample Couriers:")
        for courier in couriers:
            print(f"  ID: {courier.courier_id}, Name: {courier.name}, Status: {courier.status}, Phone: {courier.contact_number}")
        
        # Sample shipments
        shipments = self.session.query(Shipment).limit(3).all()
        print("\nSample Shipments:")
        for shipment in shipments:
            print(f"  ID: {shipment.shipment_id}, Status: {shipment.shipment_status}, ETA: {shipment.eta}")
            print(f"    From: {shipment.source_address[:50]}...")
            print(f"    To: {shipment.dest_address[:50]}...")
        
        # Sample shipper processes
        processes = self.session.query(ShipperProcess).limit(3).all()
        print("\nSample Shipper Processes:")
        for process in processes:
            print(f"  Shipper ID: {process.shipper_id}, Thread ID: {process.thread_id}")
            print(f"    Email: {', '.join(process.email[:2])}...")
    
    def close(self):
        """Close the database session."""
        self.session.close()

def main():
    """Main function to run the data generator."""
    # You can change the database URL here
    # For PostgreSQL: "postgresql://username:password@localhost/dbname"
    # For SQLite: "sqlite:///test_shipments.db"
    
    generator = DataGenerator("sqlite:///test_shipments.db")
    
    try:
        # Generate data
        data = generator.generate_all_data(
            shipper_count=20,
            courier_count=30,
            shipment_count=100
        )
        
        # Print sample data
        generator.print_sample_data()
        
        # Print statistics
        print(f"\n=== STATISTICS ===")
        print(f"Generated {len(data['shippers'])} shippers")
        print(f"Generated {len(data['couriers'])} couriers")
        print(f"Generated {len(data['shipments'])} shipments")
        print(f"Generated {len(data['shipper_processes'])} shipper processes")
        
    finally:
        generator.close()

if __name__ == "__main__":
    main()
