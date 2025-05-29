import logging
from flask import current_app, jsonify, request
import json
import requests
import re
from app.services.openai_service import generate_response
from app.database.connection import (
    get_thread_id, save_thread,
    acquire_lock, release_lock
)
from app.database.connection import supabase

def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def get_text_message_input(recipient, text):
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    })


# def generate_response(response):
#     # Return text in uppercase
#     return response.upper()


def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }
    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"

    print(f"URL:: {url}")
    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)
        print(f"DATAJSON:: {json.dumps(data, indent=2)}")
        print(f"RESPONSE.TEXT:: {response.text}")
        response.raise_for_status()
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except (
        requests.RequestException
    ) as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        # Process the response as normal
        log_http_response(response)
        return response

def process_text_for_whatsapp(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    # Substitute the pattern with an empty string
    text = re.sub(pattern, "", text).strip()

    # Pattern to find double asterisks including the word(s) in between
    pattern = r"\*\*(.*?)\*\*"

    # Replacement pattern with single asterisks
    replacement = r"*\1*"

    # Substitute occurrences of the pattern with the replacement
    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text



def process_whatsapp_message(body):
    """
    Here we process the message request and persist the conversation
    """
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name  = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

    if not acquire_lock(wa_id):
        logging.warning("Double-hit, worker already processing this user.")
        return                      # Drop or queue later

    try:
        msg_text = body["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]

        # -----------------------------------------
        # Thread lookup (Redis → Supabase → OpenAI)
        # -----------------------------------------
        thread_id = get_thread_id(wa_id)
        if thread_id is None:
            # First time we see this user ‒ create new thread via OpenAI
            thread   = current_app.openai_client.beta.threads.create()
            thread_id = thread.id
            save_thread(wa_id, thread_id, current_app.config["OPENAI_ASSISTANT_ID"])

        # -----------------------------------------
        # Generate reply with OpenAI
        # -----------------------------------------
        response_raw = generate_response(msg_text, wa_id, name)   # unchanged
        response     = process_text_for_whatsapp(response_raw)

        supabase.table("messages").insert({
        "thread_id": thread_id,
        "wa_id":     wa_id,
        "role":      "user",
        "content":   msg_text,
        }).execute()

        supabase.table("messages").insert({
            "thread_id": thread_id,
            "wa_id":     wa_id,
            "role":      "assistant",
            "content":   response_raw,
        }).execute()


        # -----------------------------------------
        # Send back to WhatsApp
        # -----------------------------------------
        data = get_text_message_input(current_app.config["RECIPIENT_WAID"], response)
        send_message(data)

    finally:
        release_lock(wa_id)



def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )


def handle_message():
    """
    Handle incoming webhook events from the WhatsApp API.

    This function processes incoming WhatsApp messages and other events,
    such as delivery statuses. If the event is a valid message, it gets
    processed. If the incoming payload is not a recognized WhatsApp event,
    an error is returned.

    Every message send will trigger 4 HTTP requests to your webhook: message, sent, delivered, read.

    Returns:
        response: A tuple containing a JSON response and an HTTP status code.
    """
    body = request.get_json()
    # logging.info(f"request body: {body}")

    # Check if it's a WhatsApp status update
    if (
        body.get("entry", [{}])[0]
        .get("changes", [{}])[0]
        .get("value", {})
        .get("statuses")
    ):
        logging.info("Received a WhatsApp status update.")
        return jsonify({"status": "ok"}), 200

    try:
        if is_valid_whatsapp_message(body):
            process_whatsapp_message(body)
            return jsonify({"status": "ok"}), 200
        else:
            # if the request is not a WhatsApp API event, return an error
            return (
                jsonify({"status": "error", "message": "Not a WhatsApp API event"}),
                404,
            )
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON")
        return jsonify({"status": "error", "message": "Invalid JSON provided"}), 400


# Required webhook verifictaion for WhatsApp
def verify():
    # Parse params from the webhook verification request
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    # Check if a token and mode were sent
    if mode and token:
        # Check the mode and token sent are correct
        if mode == "subscribe" and token == current_app.config["VERIFY_TOKEN"]:
            # Respond with 200 OK and challenge token from the request
            logging.info("WEBHOOK_VERIFIED")
            return challenge, 200
        else:
            # Responds with '403 Forbidden' if verify tokens do not match
            logging.info("VERIFICATION_FAILED")
            return jsonify({"status": "error", "message": "Verification failed"}), 403
    else:
        # Responds with '400 Bad Request' if verify tokens do not match
        logging.info("MISSING_PARAMETER")
        return jsonify({"status": "error", "message": "Missing parameters"}), 400

