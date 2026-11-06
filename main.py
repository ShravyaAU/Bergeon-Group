from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="Bergeon Screen Intake API")

@app.get("/")
async def root():
    return {"status": "online", "message": "Bergeon API is running"}

# Allow your Vercel frontend to communicate with this Render backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Security note: Change "*" to your Vercel URL later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to Neon Database using Environment Variables
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# Define the data structure coming from the scanner
class ScreenLog(BaseModel):
    barcode: str
    service_type: str
    emulsion_type: str
    difficulty_rating: int
    estimated_cost: float

@app.post("/api/intake")
async def log_screen(log: ScreenLog):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        insert_query = """
            INSERT INTO screen_logs (barcode, service_type, emulsion_type, difficulty_rating, estimated_cost)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, scanned_at;
        """
        cursor.execute(insert_query, (
            log.barcode, 
            log.service_type, 
            log.emulsion_type, 
            log.difficulty_rating, 
            log.estimated_cost
        ))
        
        result = cursor.fetchone()
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {"status": "success", "message": "Screen logged securely", "data": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs")
async def get_logs():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch the most recent 50 scans for the dashboard
        cursor.execute("SELECT * FROM screen_logs ORDER BY scanned_at DESC LIMIT 50;")
        logs = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {"status": "success", "logs": logs}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))