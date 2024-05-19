#!/usr/bin/env python
# coding: utf-8

# In[29]:


import requests
import pyodbc
import os

from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient

endpoint = os.environ["LANGUAGE_ENDPOINT"]
key = os.environ["LANGUAGE_KEY"]

# Create the Text Analytics client
text_analytics_client = TextAnalyticsClient(endpoint, AzureKeyCredential(key))

def get_data_from_sql(NOTE_IDs):
    # Replace with your actual SQL connection details
    server = "gcollect.database.windows.net"
    database = "gCollectDB"
    username = "sqladmin"
    password = "pwd@123456"

    # Establish a connection
    conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    conn = pyodbc.connect(conn_str)

    # Execute your SQL query to retrieve data
    cursor = conn.cursor()
    query = f"SELECT CreatedDate as created_date, Comments as note_comment FROM Notes_Master WHERE NOTEID IN ({', '.join(NOTE_IDs)})"
    cursor.execute(query)

    # Fetch all rows
    data = []
    for row in cursor.fetchall():
        created_date, note_comment = row
        data.append({"created_date": created_date, "note_comment": note_comment})

    conn.close()
    return data

def concatenate_data(data):
    # Concatenate 'created_date' with 'note_comment' in the desired format
    formatted_data = []
    for row in data:
        formatted_row = f"On {row['created_date'].strftime('%d %B')}, {row['note_comment']}"
        formatted_data.append(formatted_row)
    return formatted_data

def generate_abstractive_summary(text_data):
    poller = text_analytics_client.begin_abstract_summary(text_data)
    abstract_summary_results = poller.result()
    for result in abstract_summary_results:
        print()
        if result.kind == "AbstractiveSummarization":
            return result.summaries[0].text
        elif result.is_error is True:
            print("...Is an error with code '{}' and message '{}'".format(
                result.error.code, result.error.message
            ))


def generative_summary_for_note(NOTE_IDs):
    data = get_data_from_sql(NOTE_IDs)
    formatted_data = concatenate_data(data)
    summary = generate_abstractive_summary(formatted_data)
    return summary


# In[ ]:




