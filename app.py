import datetime
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sentence_transformers import SentenceTransformer
import torch
import chromadb
import google.generativeai as genai  # Import Google Gemini API
import uuid  # Import for unique ID generation

import csv
# Initialize FastAPI app
app = FastAPI()

# Initialize Chroma client and collection
client = chromadb.PersistentClient(path="db")
collection = client.get_collection("sentence_embeddings_collection")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Set up Gemini API Key
genai.configure(api_key="AIzaSyBRTJOIZqW5f4Gf0A3Vf_DdSJ1FKn4INAk")

# Initialize templates (for rendering HTML)
templates = Jinja2Templates(directory="templates")

# Serve static files (JS, CSS, images, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Helper function to retrieve context
def get_context(sentence_index, all_sentences, context_range=5):
    start = max(0, sentence_index - context_range)
    end = min(len(all_sentences), sentence_index + context_range + 1)
    return " ".join(all_sentences[start:end])

# Query function to interact with Chroma DB
def query_database(query, top_k=1, context_range=5):
    query_embedding = model.encode(query, convert_to_tensor=True)
    query_embedding = torch.nn.functional.normalize(query_embedding, p=2, dim=0).tolist()
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
    all_sentences = [metadata["sentence"] for metadata in collection.get()["metadatas"]]
    
    matched_sentences = []
    for result in results["metadatas"][0]:
        matched_sentence = result["sentence"]
        sentence_index = all_sentences.index(matched_sentence)
        context = get_context(sentence_index, all_sentences, context_range)
        matched_sentences.append({
            "matched_sentence": matched_sentence,
            "context": context
        })
    return matched_sentences

# Function to get the current timestamp in IST (Indian Standard Time)
def get_ist_timestamp():
    ist_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
    return ist_time.strftime("%Y-%m-%d %H:%M:%S")

# Function to generate AI response based on the context using Gemini API
def generate_ai_response(query, context, chat_history):
    prompt = "You are Mini Rohith, a friendly AI bot here to help users by answering their questions. \
            Your job is to provide kind, clear, and helpful responses based only on the context provided. \
            If the answer to a question is not found within the context, kindly inform the user that the answer is not available. \
            You can also suggest that they ask the same question using the contact form for further assistance. \
            Always maintain a warm, welcoming, and polite tone to make users feel comfortable and valued. \
            You should not use external knowledge, only rely on the provided context to generate your responses."

    if len(chat_history) > 0:
        prompt = prompt + '\n' + "This is the previous exchange you had with the user" + '\n' + chat_history

    prompt = prompt + '\n \n' + f"Context: {context}"
    prompt = prompt + '\n \n' + "Based on the above instructions and context, respond to the below query given by the user."
    prompt = prompt + '\n \n' + f"Query: {query}"
    prompt = prompt + "Your response: "
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")  # Use the desired Gemini model
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating MiniAI Rohith response: {e}")
        return "Unable to generate MiniAI Rohith response at this time."

# Function to log prompts and responses to Google Sheets using the Apps Script endpoint
def log_to_google_sheet(query, response, is_gemini=False):
    # Google Apps Script URL
    script_url = "https://script.google.com/macros/s/AKfycbyV__xHrDS-7ajfeLF0cOFJyUdKgXW84AUS56IP2seRBFWoFAf9qmsUAfN4EhppYUITvg/exec"
    
    # Get the current timestamp in IST
    timestamp = get_ist_timestamp()  # Get the timestamp in IST
    
    # Concatenate the user query with the timestamp
    concatenated_query = f"Query: {query} | Timestamp: {timestamp}"

    # Prepare the data to be sent to the Google Apps Script
    data = {
        "entry.1623544729": f"{concatenated_query}",  # Name (you can set this based on your preference)
        "entry.2049655221": f"{response}",  # Email (set this as required)
        "entry.546089960": "Gemini"  # Concatenated query and response
    }

    # Send the data to the Google Apps Script endpoint
    try:
        response = requests.post(script_url, data=data)
        if response.status_code == 200:
            print("Successfully logged to Google Sheets")
        else:
            print(f"Failed to log data to Google Sheets. Status Code: {response.status_code}")
    except Exception as e:
        print(f"Error sending data to Google Sheets: {e}")


# Serve the main HTML page
@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# API endpoint for sending a message
@app.post("/send_message")
async def send_message(data: dict):
    user_message = data.get("message")

    if user_message:
        # Query the database for matching context
        results = query_database(user_message, top_k=1, context_range=5)
        if results:
            matched_context = results[0]["context"]
            # Use Gemini API to generate AI response
            bot_response = generate_ai_response(user_message, matched_context, "")
        else:
            bot_response = "Sorry, I couldn't find an answer in the context."  # Default response if no match found
        
        # Log data to CSV with Gemini indication
        prompt = f"Query: {user_message} | Context: {matched_context} | Generate a detailed and coherent response..."

        # Log data to Google Sheets
        log_to_google_sheet(user_message, bot_response, is_gemini=True)

        return JSONResponse(content={"response": bot_response, "context": matched_context})
    
    return JSONResponse(content={"response": "No message received!"})

