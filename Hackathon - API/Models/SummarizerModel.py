#!/usr/bin/env python
# coding: utf-8

# In[19]:


import pandas as pd
import os
import pyodbc
from transformers import pipeline,BartTokenizer


# In[15]:


def get_data_from_sql(NOTE_IDs):
    
    server = os.getenv("MY_HOST")
    database = os.getenv("MY_DB")
    username = os.getenv("MY_UID")
    password = os.getenv("MY_PWD")

    conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    conn = pyodbc.connect(conn_str)

    cursor = conn.cursor()
    query = f"SELECT CreatedDate as created_date, Comments as note_comment FROM Notes_Master WHERE NOTEID IN ({', '.join(NOTE_IDs)})"
    cursor.execute(query)
    
    data = []
    for row in cursor.fetchall():
        created_date, note_comment = row
        data.append({"Note Date": created_date, "Note Comment": note_comment})

    conn.close()
    df = pd.DataFrame(data)
    return df


# In[8]:


def add_ordinal_indicator(date):
    if pd.isna(date):
        return "Invalid Date"
    day = date.day
    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][day % 10 - 1]
    return f"Update On:{day}{suffix} {date.strftime('%b %Y')}, "


# In[9]:


## some pre-processing
def preprocessing(NOTE_IDs):
    Client_Notes = {}
    df = get_data_from_sql(NOTE_IDs)
    #df = df.sort_values(by=['Client ID', 'Note Date'], ascending=[True, True])
    for index, row in df.iterrows():
        Client = 'C1'
        #Invoice = row['Invoice Number']
        # If this is the first note for this client, create a new list for them
        if Client not in Client_Notes:
            Client_Notes[Client] = ''
    
        #Siddesh - Added this check as empty note was giving summarizing issues. 
        if row['Note Comment'] is not None:
            # Format the date and prepend it to the note
            note_date = add_ordinal_indicator(row['Note Date'])
            note_with_date = note_date + row['Note Comment'].strip()
        
            if note_with_date[-1] !='.':
                note_with_date = note_with_date + '.'
            if note_with_date[0] =='.':
                note_with_date = note_with_date[1:]
        
            Client_Notes[Client] += note_with_date
    return Client_Notes


# In[10]:


def BART(Client_Notes):
    fine_tuned_bart = pipeline("summarization", model="./fine_tuned_bart")
    fine_bart_tokenizer = BartTokenizer.from_pretrained("./fine_tuned_bart")
    summaries = []
    for client, notes in Client_Notes.items():
        fine_bart_summary = fine_tuned_bart(notes, max_length=250, min_length=40, length_penalty=2, num_beams=6)[0]['summary_text']
 
    return fine_bart_summary


# In[21]:


def generative_summary_for_note(NOTE_IDs):
    Client_Notes = preprocessing(NOTE_IDs)
    summary_df=BART(Client_Notes)
    return summary_df



