#!/usr/bin/env python
# coding: utf-8

# In[1]:


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from Models.SummarizerModel import generative_summary_for_note
import os

my_uid = os.getenv("MY_UID")
my_pwd = os.getenv("MY_PWD")
my_host = os.getenv("MY_HOST")
my_db = os.getenv("MY_DB")


my_odbc_driver = "ODBC Driver 17 for SQL Server"


app = FastAPI()

# Define a list of allowed origins
origins = [
    "https://calm-river-0fec61600.5.azurestaticapps.net",
    "http://localhost:3000",
    "https://localhost:3000"
]

connection_url = URL.create(
    "mssql+pyodbc",
    username=my_uid,
    password=my_pwd,
    host=my_host,
    database=my_db,
    query={"driver": my_odbc_driver},
)

engine = create_engine(str(connection_url))

# Add CORSMiddleware to the application instance
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows only the specified origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class ClientCode(BaseModel):
    ClientCode: str

class NoteForClient(BaseModel):
    ClientCode: str
    Invoices: str
    NoteComment: str

@app.get("/getClients")
async def get_clients():
    with engine.connect() as connection:
        result = connection.execute(text("EXEC usp_getClients"))
        return result.fetchall()

@app.get("/getInvoiceDetailsByClient")
#@app.api_route("/getInvoiceDetailsByClient", methods=["GET", "POST"])
async def get_invoice_details_by_client(ClientCode: str):
    with engine.connect() as connection:
        result = connection.execute(text("EXEC usp_getInvoiceDetailsByClient :client_code"), client_code=ClientCode)
        return result.fetchall()

@app.get("/getNotesByClient")
#@app.api_route("/getNotesByClient", methods=["GET", "POST"])
async def get_notes_by_client(ClientCode: str):
    with engine.connect() as connection:
        result = connection.execute(text("EXEC usp_getNotesByClient :client_code"), client_code=ClientCode)
        return result.fetchall()

@app.post("/saveNoteForClient")
async def save_note_for_client(note: NoteForClient):
    try:
        with engine.connect() as connection:
            # Explicitly begin the transaction
            transaction = connection.begin()

            try:
                result = connection.execute(
                    text("EXEC usp_saveNoteForClient :client_code, :invoices, :note_comment"),
                    client_code=note.ClientCode,
                    invoices=note.Invoices,
                    note_comment=note.NoteComment,
                )

                # Check if the result set contains rows
                if result.rowcount > 0:
                    # Commit the transaction
                    transaction.commit()
                    return "Success"
                else:
                    # Roll back the transaction
                    transaction.rollback()
                    return {"message": "No rows found."}
            except Exception as e:
                # Roll back the transaction on error
                transaction.rollback()
                return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


@app.get("/getSummaryForNotes/")
def get_summary_for_notes(Noteids: str):
    try:
        # Convert comma-separated Noteids to a list
        note_ids_list = Noteids.split(",")

        # Call your generative_summary_for_note function
        summary,inputnotes = generative_summary_for_note(note_ids_list)

        # Return the summary as a string
        return {"inputtext":inputnotes,"summary": summary}
    except Exception as e:
        return {"error": str(e)}

@app.get("/getSummaryForNotesTest/")
def get_summary_for_notes_test(Noteids: str):
    return {"inputtext":"My Input","summary":"My Output"}
