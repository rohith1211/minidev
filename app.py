import datetime
import requests
from fastapi import FastAPI, Request
from fastapi.responses import Response, JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sentence_transformers import SentenceTransformer
from user_agents import parse
import torch
import chromadb
import google.generativeai as genai  # Import Google Gemini API
import uuid  # Import for unique ID generation
import os
import uvicorn
import csv

# Initialize FastAPI app
app = FastAPI()

# Initialize Chroma client and collection
client = chromadb.PersistentClient(path="db")
collection = client.get_collection("sentence_embeddings_collection")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Set up Gemini API Key
genai.configure(api_key="apitoken")

# Initialize templates (for rendering HTML)
templates = Jinja2Templates(directory="templates")

# Serve static files (JS, CSS, images, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Function to get device information from the user-agent string
def get_device_info(user_agent: str):
    ua = parse(user_agent)
    return f"Device: {ua.device.family} | OS: {ua.os.family} | Browser: {ua.browser.family}"

# Function to get all the details based on the user's IP using ipinfo.io (with token)
def get_user_details(ip_address: str):
    url = f'https://ipinfo.io/{ip_address}?token=5ba236dae40c83'  # Replace with your token
    try:
        response = requests.get(url)
        data = response.json()
        if response.status_code != 200:
            return None  # Returning None in case of failure or invalid status
        return {
            'ip': data.get('ip', 'Unknown'),
            'city': data.get('city', 'Unknown'),
            'region': data.get('region', 'Unknown'),
            'country': data.get('country', 'Unknown'),
            'location': data.get('loc', 'Unknown'),
            'org': data.get('org', 'Unknown'),
            'postal': data.get('postal', 'Unknown'),
            'timezone': data.get('timezone', 'Unknown')
        }
    except Exception as e:
        print(f"Error getting user details: {e}")
        return None

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
def log_to_google_sheet(query, response, device_info, user_details, is_gemini=False):
    # Google Apps Script URL
    script_url = "https://script.google.com/macros/s/AKfycbyV__xHrDS-7ajfeLF0cOFJyUdKgXW84AUS56IP2seRBFWoFAf9qmsUAfN4EhppYUITvg/exec"
    
    # Get the current timestamp in IST
    timestamp = get_ist_timestamp()  # Get the timestamp in IST
    
    # Concatenate the user query with the timestamp and additional details
    concatenated_query = (f"Query: {query} | Timestamp: {timestamp}")

    concatenated_info = (f"Device: {device_info} | "
                      f"IP: {user_details['ip']} | City: {user_details['city']} | Region: {user_details['region']} | "
                      f"Country: {user_details['country']} | Location: {user_details['location']} | "
                      f"Org: {user_details['org']} | Postal: {user_details['postal']} | Timezone: {user_details['timezone']}")


    # Prepare the data to be sent to the Google Apps Script
    data = {
        "entry.1623544729": f"{concatenated_query}",  # Name (you can set this based on your preference)
        "entry.2049655221": f"{response}",  # Email (set this as required)
        "entry.546089960": f"{concatenated_info}"  # Concatenated query and response
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

# Function to log contact form data to Google Sheets
def contactform_sheet(name, email, message, location_info, user_agent):
    script_url = "https://script.google.com/macros/s/AKfycbyV__xHrDS-7ajfeLF0cOFJyUdKgXW84AUS56IP2seRBFWoFAf9qmsUAfN4EhppYUITvg/exec"
    timestamp = get_ist_timestamp()  # Get the timestamp in IST
    
    # Get device information from user-agent
    device_info = get_device_info(user_agent)
    
    # Adding detailed information to name_with_location
    name_with_location = f"{name} | IP: {location_info['ip']} | City: {location_info['city']} | Region: {location_info['region']} | " \
                         f"Country: {location_info['country']} | Location: {location_info['location']} | " \
                         f"Org: {location_info['org']} | Postal: {location_info['postal']} | Timezone: {location_info['timezone']} | " \
                         f"{device_info}"

    # Adding timestamp to email
    email_with_timestamp = f"{email} | Timestamp: {timestamp}"
    
    # Prepare the data to be sent to the Google Apps Script
    data = {
        "entry.1623544729": f"{name_with_location}",  # Name field with detailed location and device info
        "entry.2049655221": f"{email_with_timestamp}",  # Email field with timestamp
        "entry.546089960": f"{message}",  # Message field
    }

    try:
        response = requests.post(script_url, data=data)
        if response.status_code == 200:
            print("Successfully logged contact form data to Google Sheets")
        else:
            print(f"Failed to log data to Google Sheets. Status Code: {response.status_code}")
    except Exception as e:
        print(f"Error sending data to Google Sheets: {e}")

# Contact form endpoint for handling form submissions
@app.post("/contactform")
async def contact_form(request: Request):
    form_data = await request.form()
    
    name = form_data.get("name")
    email = form_data.get("email")
    message = form_data.get("message")
    user_agent = request.headers.get('User-Agent')  # Get the User-Agent from request headers
    ip_address = request.client.host  # Get the IP address of the client
    
    # Get location info using the IP address
    location_info = get_user_details(ip_address)

    if name and email and message and location_info:
        contactform_sheet(name, email, message, location_info, user_agent)
        return JSONResponse(content={"response": "Thank you for reaching out! Your message has been received."})
    else:
        return JSONResponse(content={"response": "Please provide all required fields (Name, Email, Message)."})
    
    
# Serve the main HTML page and capture IP & location when the page is visited
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    ip_address = request.client.host  # Get the IP address of the client
    
    # Get location info using the IP address
    location_info = get_user_details(ip_address)
    user_agent = request.headers.get('User-Agent')  # Get the User-Agent from request headers
    device_info = get_device_info(user_agent)  # Get device info
    
    # Log details (this will log every page visit to Google Sheets)
    if location_info:
        log_to_google_sheet("Page visit", "N/A", device_info, location_info, is_gemini=False)
    
    # Serve the homepage without passing the location and device info to the template
    return templates.TemplateResponse("index.html", {"request": request})

# API endpoint for sending a message
@app.post("/send_message")
async def send_message(data: dict, request: Request):
    user_message = data.get("message")
    user_agent = request.headers.get('user-agent')
    ip_address = request.client.host
    
    if user_message:
        # Query the database for matching context
        results = query_database(user_message, top_k=1, context_range=5)
        if results:
            matched_context = results[0]["context"]
            # Use Gemini API to generate AI response
            bot_response = generate_ai_response(user_message, matched_context, "")
        else:
            bot_response = "Sorry, I couldn't find an answer in the context."  # Default response if no match found
        
        # Get device and user details
        device_info = get_device_info(user_agent)
        user_details = get_user_details(ip_address)

        if user_details:
            # Log data to Google Sheets
            log_to_google_sheet(user_message, bot_response, device_info, user_details, is_gemini=True)

        return JSONResponse(content={"response": bot_response, "context": matched_context, "user_details": user_details})
    
    return JSONResponse(content={"response": "No message received!"})

# Ignore favicon.ico requests by returning a 204 No Content response
@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Default to 8000 if no $PORT is set
    uvicorn.run(app, port=port)  # Gunicorn will handle this
