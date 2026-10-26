"""
Database Initialization Script using SQLAlchemy
Creates all tables (users, predictions, notifications) in Neon PostgreSQL / configured database.
"""
import sys
from pathlib import Path

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import inspect, text
from app.config import settings
from app.db.database import engine, Base, SessionLocal
from app.db.models import User, Prediction, Notification
from app.auth.security import get_password_hash

def init_database(seed_demo_user: bool = True):
    print("=" * 60)
    print(" GALLSCAN AI — SQLALCHEMY DATABASE INITIALIZER ")
    print("=" * 60)
    
    # Redact password in logs for safety
    db_url_display = settings.DATABASE_URL
    if "@" in db_url_display:
        prefix, suffix = db_url_display.split("@", 1)
        db_url_display = f"{prefix.split(':')[0]}://***:***@{suffix}"
    
    print(f"\n[1/4] Connecting to database: {db_url_display}")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
            print(f"      Connected successfully!")
    except Exception as e:
        print(f"\n[ERROR] Connection failed: {e}")
        sys.exit(1)

    print("\n[2/4] Initializing schema and tables with SQLAlchemy...")
    Base.metadata.create_all(bind=engine)
    print("      Base.metadata.create_all() executed.")

    print("\n[3/4] Verifying created tables in database...")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"      Detected tables in database: {tables}")
    for table_name in ["users", "predictions", "notifications"]:
        if table_name in tables:
            columns = [col["name"] for col in inspector.get_columns(table_name)]
            print(f"      [+] Table '{table_name}': {len(columns)} columns ({', '.join(columns[:5])}...)")
        else:
            print(f"      [-] Table '{table_name}' was NOT found!")

    if seed_demo_user:
        print("\n[4/4] Checking / Seeding default demo clinician account...")
        db = SessionLocal()
        try:
            demo_email = "clinician@gallscan.ai"
            existing = db.query(User).filter(User.email == demo_email).first()
            if not existing:
                demo_user = User(
                    name="Dr. Alex Vance, MD",
                    email=demo_email,
                    password_hash=get_password_hash("ClinicianDemo2026!"),
                    role="radiologist"
                )
                db.add(demo_user)
                db.commit()
                db.refresh(demo_user)
                
                # Add welcome notification
                welcome_notif = Notification(
                    user_id=demo_user.id,
                    title="Database Initialized",
                    message="Welcome to GallScan AI. The SQLAlchemy schema and tables are active in Neon PostgreSQL.",
                    type="system"
                )
                db.add(welcome_notif)
                db.commit()
                print(f"      [+] Demo account seeded:")
                print(f"          Email:    {demo_email}")
                print(f"          Password: ClinicianDemo2026!")
            else:
                print(f"      [+] Demo account already exists: {demo_email}")
        except Exception as e:
            print(f"      Warning during seeding: {e}")
            db.rollback()
        finally:
            db.close()

    print("\n" + "=" * 60)
    print(" DATABASE INITIALIZATION COMPLETED SUCCESSFULLY! ")
    print("=" * 60)

if __name__ == "__main__":
    init_database()
