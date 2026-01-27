"""vault - SQLite Database Management.

Provides SQLite database utilities with automatic directory management,
CRUD operations, and wickit integration.

Example:
    >>> from wickit import vault
    >>> db = vault.VaultDatabase("jobforge")
    >>> job = db.create_job({"title": "Engineer", "company": "TechCorp"})
    >>> jobs = db.get_jobs()

Classes:
    VaultDatabase: Main database class with CRUD operations.
    WickitSQLite: Low-level SQLite wrapper.

Functions:
    get_database: Get database instance for a product.
    init_database: Initialize database schema.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from contextlib import contextmanager

from .hideaway import get_data_dir


@dataclass
class BaseRecord:
    """Base record with common fields."""
    id: str
    created_at: str
    updated_at: str
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


class DatabaseError(Exception):
    """Database operation error."""
    pass


class WickitSQLite:
    """SQLite database wrapper with automatic path management."""
    
    def __init__(self, product_name: str, db_name: str = "database.db"):
        self.product_name = product_name
        self.db_name = db_name
        self.db_path = get_data_dir(product_name) / db_name
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise DatabaseError(f"Database error: {e}")
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute a SELECT query and return results."""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def execute_command(self, command: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE command and return affected rows."""
        with self.get_connection() as conn:
            cursor = conn.execute(command, params)
            conn.commit()
            return cursor.rowcount
    
    def execute_many(self, command: str, params_list: List[tuple]) -> int:
        """Execute a command with multiple parameter sets."""
        with self.get_connection() as conn:
            cursor = conn.executemany(command, params_list)
            conn.commit()
            return cursor.rowcount


class VaultDatabase:
    """Vault database with job tracking operations."""
    
    def __init__(self, product_name: str = "jobforge"):
        self.db = WickitSQLite(product_name, "jobforge.db")
        self._init_schema()
    
    def _init_schema(self):
        """Initialize database schema."""
        schema = """
        -- Jobs table
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            url TEXT,
            description TEXT,
            location TEXT,
            salary TEXT,
            requirements TEXT, -- JSON array
            stage TEXT DEFAULT 'saved',
            notes TEXT DEFAULT '',
            tags TEXT, -- JSON array
            applied_date TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        
        -- Companies table
        CREATE TABLE IF NOT EXISTS companies (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            domain TEXT,
            industry TEXT,
            size TEXT,
            funding_stage TEXT,
            rating REAL,
            location TEXT,
            website TEXT,
            notes TEXT,
            last_updated TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Contacts table
        CREATE TABLE IF NOT EXISTS contacts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            company TEXT NOT NULL,
            position TEXT,
            linkedin_url TEXT,
            relationship TEXT,
            connection_type TEXT,
            warm_intro_potential TEXT,
            last_contact TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Offers table
        CREATE TABLE IF NOT EXISTS offers (
            id TEXT PRIMARY KEY,
            job_id TEXT,
            company TEXT NOT NULL,
            base_salary INTEGER,
            bonus TEXT,
            equity TEXT,
            benefits TEXT,
            start_date TEXT,
            negotiation_notes TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Job Alerts table
        CREATE TABLE IF NOT EXISTS job_alerts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            keywords TEXT NOT NULL,
            location TEXT,
            frequency TEXT DEFAULT 'daily',
            is_active BOOLEAN DEFAULT 1,
            last_run TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Interview Sessions table
        CREATE TABLE IF NOT EXISTS interview_sessions (
            id TEXT PRIMARY KEY,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            category TEXT DEFAULT 'behavioral',
            questions TEXT, -- JSON array
            answers TEXT, -- JSON array
            feedback TEXT,
            score INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
        CREATE INDEX IF NOT EXISTS idx_jobs_stage ON jobs(stage);
        CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);
        CREATE INDEX IF NOT EXISTS idx_offers_company ON offers(company);
        """
        
        with self.db.get_connection() as conn:
            conn.executescript(schema)
    
    # Job operations
    def create_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new job entry."""
        import uuid
        
        job_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        record = {
            "id": job_id,
            "title": job_data.get("title", ""),
            "company": job_data.get("company", ""),
            "url": job_data.get("url"),
            "description": job_data.get("description"),
            "location": job_data.get("location"),
            "salary": job_data.get("salary"),
            "requirements": json.dumps(job_data.get("requirements", [])),
            "stage": job_data.get("stage", "saved"),
            "notes": job_data.get("notes", ""),
            "tags": json.dumps(job_data.get("tags", [])),
            "applied_date": job_data.get("applied_date"),
            "created_at": now,
            "updated_at": now
        }
        
        query = """
        INSERT INTO jobs (id, title, company, url, description, location, salary, 
                         requirements, stage, notes, tags, applied_date, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            record["id"], record["title"], record["company"], record["url"],
            record["description"], record["location"], record["salary"],
            record["requirements"], record["stage"], record["notes"],
            record["tags"], record["applied_date"], record["created_at"], record["updated_at"]
        )
        
        self.db.execute_command(query, params)
        return self.get_job(job_id)
    
    def get_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs."""
        query = "SELECT * FROM jobs ORDER BY created_at DESC"
        jobs = self.db.execute_query(query)
        
        # Parse JSON fields
        for job in jobs:
            job["requirements"] = json.loads(job["requirements"] or "[]")
            job["tags"] = json.loads(job["tags"] or "[]")
        
        return jobs
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific job by ID."""
        query = "SELECT * FROM jobs WHERE id = ?"
        jobs = self.db.execute_query(query, (job_id,))
        
        if not jobs:
            return None
        
        job = jobs[0]
        job["requirements"] = json.loads(job["requirements"] or "[]")
        job["tags"] = json.loads(job["tags"] or "[]")
        
        return job
    
    def update_job(self, job_id: str, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a job entry."""
        job_data["updated_at"] = datetime.now().isoformat()
        
        # Build dynamic update query
        fields = []
        params = []
        for key, value in job_data.items():
            if key != "id":
                if key in ["requirements", "tags"]:
                    value = json.dumps(value or [])
                fields.append(f"{key} = ?")
                params.append(value)
        
        params.append(job_id)
        
        query = f"UPDATE jobs SET {', '.join(fields)} WHERE id = ?"
        
        rows_affected = self.db.execute_command(query, tuple(params))
        
        if rows_affected > 0:
            return self.get_job(job_id)
        return None
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job entry."""
        query = "DELETE FROM jobs WHERE id = ?"
        rows_affected = self.db.execute_command(query, (job_id,))
        return rows_affected > 0
    
    # Company operations
    def create_company(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new company."""
        import uuid
        
        company_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        record = {
            "id": company_id,
            "name": company_data.get("name", ""),
            "domain": company_data.get("domain"),
            "industry": company_data.get("industry"),
            "size": company_data.get("size"),
            "funding_stage": company_data.get("funding_stage"),
            "rating": company_data.get("rating"),
            "location": company_data.get("location"),
            "website": company_data.get("website"),
            "notes": company_data.get("notes", ""),
            "last_updated": now,
            "created_at": now
        }
        
        query = """
        INSERT INTO companies (id, name, domain, industry, size, funding_stage, 
                              rating, location, website, notes, last_updated, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            record["id"], record["name"], record["domain"], record["industry"],
            record["size"], record["funding_stage"], record["rating"],
            record["location"], record["website"], record["notes"],
            record["last_updated"], record["created_at"]
        )
        
        self.db.execute_command(query, params)
        return self.get_company(company_id)
    
    def get_companies(self) -> List[Dict[str, Any]]:
        """Get all companies."""
        query = "SELECT * FROM companies ORDER BY name ASC"
        return self.db.execute_query(query)
    
    def get_company(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific company by ID."""
        query = "SELECT * FROM companies WHERE id = ?"
        companies = self.db.execute_query(query, (company_id,))
        return companies[0] if companies else None
    
    # Contact operations
    def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new contact."""
        import uuid
        
        contact_id = str(uuid.uuid4())
        
        record = {
            "id": contact_id,
            "name": contact_data.get("name", ""),
            "company": contact_data.get("company", ""),
            "position": contact_data.get("position"),
            "linkedin_url": contact_data.get("linkedin_url"),
            "relationship": contact_data.get("relationship"),
            "connection_type": contact_data.get("connection_type"),
            "warm_intro_potential": contact_data.get("warm_intro_potential"),
            "last_contact": contact_data.get("last_contact"),
            "notes": contact_data.get("notes", "")
        }
        
        query = """
        INSERT INTO contacts (id, name, company, position, linkedin_url, 
                            relationship, connection_type, warm_intro_potential, last_contact, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            record["id"], record["name"], record["company"], record["position"],
            record["linkedin_url"], record["relationship"], record["connection_type"],
            record["warm_intro_potential"], record["last_contact"], record["notes"]
        )
        
        self.db.execute_command(query, params)
        return self.get_contact(contact_id)
    
    def get_contacts(self) -> List[Dict[str, Any]]:
        """Get all contacts."""
        query = "SELECT * FROM contacts ORDER BY name ASC"
        return self.db.execute_query(query)
    
    def get_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific contact by ID."""
        query = "SELECT * FROM contacts WHERE id = ?"
        contacts = self.db.execute_query(query, (contact_id,))
        return contacts[0] if contacts else None
    
    def delete_contact(self, contact_id: str) -> bool:
        """Delete a contact."""
        query = "DELETE FROM contacts WHERE id = ?"
        rows_affected = self.db.execute_command(query, (contact_id,))
        return rows_affected > 0
    
    # Job Alert operations
    def create_job_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new job alert."""
        import uuid
        
        alert_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        record = {
            "id": alert_id,
            "name": alert_data.get("name", ""),
            "keywords": alert_data.get("keywords", ""),
            "location": alert_data.get("location", ""),
            "frequency": alert_data.get("frequency", "daily"),
            "is_active": alert_data.get("is_active", True),
            "last_run": alert_data.get("last_run"),
            "created_at": now,
            "updated_at": now
        }
        
        query = """
        INSERT INTO job_alerts (id, name, keywords, location, frequency, is_active, 
                               last_run, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            record["id"], record["name"], record["keywords"], record["location"],
            record["frequency"], record["is_active"], record["last_run"],
            record["created_at"], record["updated_at"]
        )
        
        self.db.execute_command(query, params)
        return self.get_job_alert(alert_id)
    
    def get_job_alerts(self) -> List[Dict[str, Any]]:
        """Get all job alerts."""
        query = "SELECT * FROM job_alerts ORDER BY created_at DESC"
        return self.db.execute_query(query)
    
    def get_job_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific job alert by ID."""
        query = "SELECT * FROM job_alerts WHERE id = ?"
        alerts = self.db.execute_query(query, (alert_id,))
        return alerts[0] if alerts else None
    
    def toggle_job_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Toggle job alert active/inactive status."""
        query = """
        UPDATE job_alerts 
        SET is_active = NOT is_active, updated_at = ?
        WHERE id = ?
        """
        self.db.execute_command(query, (datetime.now().isoformat(), alert_id))
        return self.get_job_alert(alert_id)
    
    def run_job_alert(self, alert_id: str) -> Dict[str, Any]:
        """Mark job alert as run and return results."""
        query = """
        UPDATE job_alerts 
        SET last_run = ?, updated_at = ?
        WHERE id = ?
        """
        self.db.execute_command(query, (datetime.now().isoformat(), datetime.now().isoformat(), alert_id))
        
        alert = self.get_job_alert(alert_id)
        return {
            "alert": alert,
            "jobs_found": [],  # Would integrate with job search APIs
            "message": "Job alert executed (demo mode)"
        }
    
    # Interview Session operations
    def create_interview_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new interview session."""
        import uuid
        
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        record = {
            "id": session_id,
            "company": session_data.get("company", ""),
            "role": session_data.get("role", ""),
            "category": session_data.get("category", "behavioral"),
            "questions": json.dumps(session_data.get("questions", [])),
            "answers": json.dumps(session_data.get("answers", [])),
            "feedback": session_data.get("feedback", ""),
            "score": session_data.get("score"),
            "created_at": now,
            "updated_at": now
        }
        
        query = """
        INSERT INTO interview_sessions (id, company, role, category, questions, answers, 
                                     feedback, score, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            record["id"], record["company"], record["role"], record["category"],
            record["questions"], record["answers"], record["feedback"],
            record["score"], record["created_at"], record["updated_at"]
        )
        
        self.db.execute_command(query, params)
        return self.get_interview_session(session_id)
    
    def get_interview_sessions(self) -> List[Dict[str, Any]]:
        """Get all interview sessions."""
        query = "SELECT * FROM interview_sessions ORDER BY created_at DESC"
        sessions = self.db.execute_query(query)
        
        # Parse JSON fields
        for session in sessions:
            session["questions"] = json.loads(session["questions"] or "[]")
            session["answers"] = json.loads(session["answers"] or "[]")
        
        return sessions
    
    def get_interview_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific interview session by ID."""
        query = "SELECT * FROM interview_sessions WHERE id = ?"
        sessions = self.db.execute_query(query, (session_id,))
        
        if not sessions:
            return None
        
        session = sessions[0]
        session["questions"] = json.loads(session["questions"] or "[]")
        session["answers"] = json.loads(session["answers"] or "[]")
        
        return session
    
    # Offer operations
    def create_offer(self, offer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new offer."""
        import uuid
        
        offer_id = str(uuid.uuid4())
        
        record = {
            "id": offer_id,
            "job_id": offer_data.get("job_id"),
            "company": offer_data.get("company", ""),
            "base_salary": offer_data.get("base_salary"),
            "bonus": offer_data.get("bonus", ""),
            "equity": offer_data.get("equity", ""),
            "benefits": offer_data.get("benefits", ""),
            "start_date": offer_data.get("start_date"),
            "negotiation_notes": offer_data.get("negotiation_notes", ""),
            "status": offer_data.get("status", "pending")
        }
        
        query = """
        INSERT INTO offers (id, job_id, company, base_salary, bonus, equity, benefits, 
                          start_date, negotiation_notes, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            record["id"], record["job_id"], record["company"], record["base_salary"],
            record["bonus"], record["equity"], record["benefits"],
            record["start_date"], record["negotiation_notes"], record["status"]
        )
        
        self.db.execute_command(query, params)
        return self.get_offer(offer_id)
    
    def get_offers(self) -> List[Dict[str, Any]]:
        """Get all offers."""
        query = "SELECT * FROM offers ORDER BY created_at DESC"
        return self.db.execute_query(query)
    
    def get_offer(self, offer_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific offer by ID."""
        query = "SELECT * FROM offers WHERE id = ?"
        offers = self.db.execute_query(query, (offer_id,))
        return offers[0] if offers else None
    
    def calculate_offer_value(self, offer_id: str) -> Dict[str, Any]:
        """Calculate total offer value."""
        offer = self.get_offer(offer_id)
        if not offer:
            raise DatabaseError("Offer not found")
        
        base_salary = offer.get("base_salary", 0) or 0
        # Simple calculation - would be more complex in real implementation
        total_value = base_salary * 1.2  # Assume 20% additional value from benefits
        
        return {
            "offer_id": offer_id,
            "base_salary": base_salary,
            "estimated_total_value": total_value,
            "calculation_note": "Estimated total value including benefits"
        }


# Convenience functions
def get_database(product_name: str = "jobforge") -> VaultDatabase:
    """Get a database instance for a product."""
    return VaultDatabase(product_name)


def init_database(product_name: str = "jobforge") -> VaultDatabase:
    """Initialize database for a product."""
    return VaultDatabase(product_name)


# Export main classes and functions
__all__ = [
    "WickitSQLite",
    "VaultDatabase", 
    "DatabaseError",
    "get_database",
    "init_database"
]