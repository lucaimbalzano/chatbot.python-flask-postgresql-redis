import json
import logging
import re
import requests
from flask import current_app, jsonify, request

# OpenAI helper
from app.services.openai_service import (
    generate_response,
    client as openai_client,
    OPENAI_ASSISTANT_ID,
    store_thread,            # nuovo: per aggiornare lo shelve
)

# DB / cache helpers
from app.database.connection import (
    get_thread_id, save_thread,
    acquire_lock, release_lock,
    supabase,
)

# ────────────────────────────────────────────────
# UTIL HTTP --------------------------------------
def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def get_text_message_input(recipient, text):
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type":   "individual",
        "to":       recipient,
        "type":     "text",
        "text":     {"preview_url": False, "body": text},
    })


def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }
    url = (
        f"https://graph.facebook.com/"
        f"{current_app.config['VERSION']}/"
        f"{current_app.config['PHONE_NUMBER_ID']}/messages"
    )

    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.Timeout:
        logging.error("Timeout while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except requests.RequestException as e:
        logging.error(f"Request failed: {e}")
        return jsonify({"status": "error", "message": "Failed to send"}), 500
    else:
        log_http_response(response)
        return response


# ────────────────────────────────────────────────
# TEXT FORMATTING --------------------------------
def process_text_for_whatsapp(text: str) -> str:
    # rimuovi 【 … 】
    text = re.sub(r"\【.*?\】", "", text).strip()
    # **bold** → *bold*
    return re.sub(r"\*\*(.*?)\*\*", r"*\1*", text)


# ────────────────────────────────────────────────
# CORE HANDLER -----------------------------------
def process_whatsapp_message(body: dict):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name  = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

    if not acquire_lock(wa_id):
        logging.warning("Double-hit, another worker is processing this user.")
        return

    try:
        msg_text = body["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]

        # ---------- Thread lookup (Redis → Supabase → OpenAI) ----------
        internal_id = get_thread_id(wa_id)         # BIGINT o None

        if internal_id is None:
            # primo messaggio da questo utente → crea thread su OpenAI
            oa_thread = openai_client.beta.threads.create()
            openai_id = oa_thread.id

            # salva in DB e ottieni l'id autoincrementale
            internal_id = save_thread(
                wa_id            = wa_id,
                openai_thread_id = openai_id,
                assistant_id     = OPENAI_ASSISTANT_ID,
            )

            # aggiorna anche lo shelve usato da openai_service
            store_thread(wa_id, openai_id)

        # ---------- Generate reply with OpenAI ----------
        response_raw = generate_response(msg_text, wa_id, name)
        response_txt = process_text_for_whatsapp(response_raw)

        # ---------- Persist i messaggi ----------
        supabase.table("messages").insert({
            "thread_id": internal_id,
            "role":      "user",
            "content":   msg_text,
        }).execute()

        supabase.table("messages").insert({
            "thread_id": internal_id,
            "role":      "assistant",
            "content":   response_raw,
        }).execute()

        # ---------- Send reply to WhatsApp ----------
        payload = get_text_message_input(
            current_app.config["RECIPIENT_WAID"],
            response_txt,
        )
        send_message(payload)

    finally:
        release_lock(wa_id)


# ────────────────────────────────────────────────
# WEBHOOK ROUTING --------------------------------
def is_valid_whatsapp_message(body: dict) -> bool:
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )


def handle_message():
    body = request.get_json()

    # Stato “sent/delivered/read”
    if (
        body.get("entry", [{}])[0]
        .get("changes", [{}])[0]
        .get("value", {})
        .get("statuses")
    ):
        logging.info("Received status update")
        return jsonify({"status": "ok"}), 200

    if not is_valid_whatsapp_message(body):
        return jsonify({"status": "error", "message": "Not a WhatsApp event"}), 404

    try:
        process_whatsapp_message(body)
        return jsonify({"status": "ok"}), 200
    except json.JSONDecodeError:
        logging.error("JSON decode error")
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400


# ────────────────────────────────────────────────
# WEBHOOK VERIFY ---------------------------------
def verify():
    mode       = request.args.get("hub.mode")
    token      = request.args.get("hub.verify_token")
    challenge  = request.args.get("hub.challenge")

    if mode == "subscribe" and token == current_app.config["VERIFY_TOKEN"]:
        logging.info("WEBHOOK_VERIFIED")
        return challenge, 200

    logging.info("VERIFICATION_FAILED")
    return jsonify({"status": "error", "message": "Verification failed"}), 403
