# Meta + Flask + OpenAi
<p align="left">
  <img src="https://skillicons.dev/icons?i=python" height="40" alt="Python" />
<img src="https://external-preview.redd.it/5oUALjI2hLuUySgNHJhh8oJyiA4PY5DQcypeUiLx0MQ.jpg?width=1080&crop=smart&auto=webp&s=b73349a6edb11eb6f2375960d38ae77a488c0f76"
     height="40"
     alt="Flask"
     style="border-radius: 5px;" />
  <img src="https://static.vecteezy.com/system/resources/previews/022/227/364/large_2x/openai-chatgpt-logo-icon-free-png.png" height="40" alt="OpenAI" />
  <img src="https://brandlogos.net/wp-content/uploads/2021/10/meta_platforms_icon-logo_brandlogos.net_f5zqr.png" height="30" alt="Meta" />
</p>


This guide will walk you through the process of creating a WhatsApp bot using the Meta (formerly Facebook) Cloud API with pure Python, and Flask particular. We'll also integrate webhook events to receive messages in real-time and use OpenAI to generate AI responses. For more information on the structure of the Flask application, you can refer to [this documentation](./tree/main/app).

## Youtube Video
[Profile](https://www.youtube.com/@LucasImbalzano)

## Prerequisites

1. A Meta developer account — If you don’t have one, you can [create a Meta developer account here](https://developers.facebook.com/).
2. A business app — If you don't have one, you can [learn to create a business app here](https://developers.facebook.com/docs/development/create-an-app/). If you don't see an option to create a business app, select **Other** > **Next** > **Business**.
3. Familiarity with Python to follow the tutorial.


## Table of Contents

- [Build AI WhatsApp Bots with Pure Python](#build-ai-whatsapp-bots-with-pure-python)
  - [Prerequisites](#prerequisites)
  - [Table of Contents](#table-of-contents)
  - [Get Started](#get-started)
  - [Step 1: Select Phone Numbers](#step-1-select-phone-numbers)
  - [Step 2: Send Messages with the API](#step-2-send-messages-with-the-api)
  - [Step 3: Configure Webhooks to Receive Messages](#step-3-configure-webhooks-to-receive-messages)
      - [Start your app](#start-your-app)
      - [Launch ngrok](#launch-ngrok)
      - [Integrate WhatsApp](#integrate-whatsapp)
      - [Testing the Integration](#testing-the-integration)
  - [Step 4: Understanding Webhook Security](#step-4-understanding-webhook-security)
      - [Verification Requests](#verification-requests)
      - [Validating Verification Requests](#validating-verification-requests)
      - [Validating Payloads](#validating-payloads)
  - [Step 5: Learn about the API and Build Your App](#step-5-learn-about-the-api-and-build-your-app)
  - [Step 6: Integrate AI into the Application](#step-6-integrate-ai-into-the-application)
  - [Step 7: Add a Phone Number](#step-7-add-a-phone-number)
  - [Datalumina](#datalumina)
  - [Tutorials](#tutorials)

## Get Started

1. **Overview & Setup**: Begin your journey [here](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started).
2. **Locate Your Bots**: Your bots can be found [here](https://developers.facebook.com/apps/).
3. **WhatsApp API Documentation**: Familiarize yourself with the [official documentation](https://developers.facebook.com/docs/whatsapp).
4. **Helpful Guide**: Here's a [Python-based guide](https://developers.facebook.com/blog/post/2022/10/24/sending-messages-with-whatsapp-in-your-python-applications/) for sending messages.
5. **API Docs for Sending Messages**: Check out [this documentation](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages).

## Step 1: Select Phone Numbers

- Make sure WhatsApp is added to your App.
- You begin with a test number that you can use to send messages to up to 5 numbers.
- Go to API Setup and locate the test number from which you will be sending messages.
- Here, you can also add numbers to send messages to. Enter your **own WhatsApp number**.
- You will receive a code on your phone via WhatsApp to verify your number.

## Step 2: Send Messages with the API

1. Obtain a 24-hour access token from the API access section.
2. It will show an example of how to send messages using a `curl` command which can be send from the terminal or with a tool like Postman.
3. Let's convert that into a [Python function with the request library](./blob/main/start/whatsapp_quickstart.py).
4. Create a `.env` files based on `example.env` and update the required variables.
   - keep your "secrets" clean and safe
5. You will receive a "Hello World" message (Expect a 60-120 second delay for the message).

Creating an access that works longer then 24 hours
1. Create a [system user at the Meta Business account level](https://business.facebook.com/settings/system-users).
2. On the System Users page, configure the assets for your System User, assigning your WhatsApp app with full control. Don't forget to click the Save Changes button.
   - [See step 1 here](./img/meta-business-system-user-token.png)
   - [See step 2 here](./img/adding-assets-to-system-user.png)
   - [See step 3, if you need to assign a Role for your app, here](./img/assign-role-to-system-user.png)
3. Now click `Generate new token` and select the app, and then choose how long the access token will be valid. You can choose 60 days or never expire.
4. Select all the permissions, as I was running into errors when I only selected the WhatsApp ones.
5. Confirm and copy the access token.

Now we have to find the following information on the **App Dashboard**:

- **APP_ID**: "<YOUR-WHATSAPP-BUSINESS-APP_ID>" (Found at App Dashboard)
- **APP_SECRET**: "<YOUR-WHATSAPP-BUSINESS-APP_SECRET>" (Found at App Dashboard)
- **RECIPIENT_WAID**: "<YOUR-RECIPIENT-TEST-PHONE-NUMBER>" (This is your WhatsApp ID, i.e., phone number. Make sure it is added to the account as shown in the example test message.)
- **VERSION**: "v18.0" (The latest version of the Meta Graph API)
- **ACCESS_TOKEN**: "<YOUR-SYSTEM-USER-ACCESS-TOKEN>" (Created in the previous step)

> You can only send a template type message as your first message to a user. That's why you have to send a reply first before we continue. Took me 2 hours to figure this out.


## Step 3: Configure Webhooks to Receive Messages

> Please note, this is the hardest part of this tutorial.

#### Start your app
- Make you have a python installation or environment and install the requirements: `pip install -r requirements.txt`
- Run your Flask app locally by executing [run.py](./blob/main/run.py)

#### Launch ngrok

The steps below are taken from the [ngrok documentation](https://ngrok.com/docs/integrations/whatsapp/webhooks/).

> You need a static ngrok domain because Meta validates your ngrok domain and certificate!

Once your app is running successfully on localhost, let's get it on the internet securely using ngrok!

1. If you're not an ngrok user yet, just sign up for ngrok for free.
2. Download the ngrok agent.
3. Go to the ngrok dashboard, click Your [Authtoken](https://dashboard.ngrok.com/get-started/your-authtoken), and copy your Authtoken.
4. Follow the instructions to authenticate your ngrok agent. You only have to do this once.
5. On the left menu, expand Cloud Edge and then click Domains.
6. On the Domains page, click + Create Domain or + New Domain. (here everyone can start with [one free domain](https://ngrok.com/blog-post/free-static-domains-ngrok-users))
7. Start ngrok by running the following command in a terminal on your local desktop:
```
ngrok http 8000 --domain your-domain.ngrok-free.app
```
8. ngrok will display a URL where your localhost application is exposed to the internet (copy this URL for use with Meta).


#### Integrate WhatsApp

In the Meta App Dashboard, go to WhatsApp > Configuration, then click the Edit button.
1. In the Edit webhook's callback URL popup, enter the URL provided by the ngrok agent to expose your application to the internet in the Callback URL field, with /webhook at the end (i.e. https://myexample.ngrok-free.app/webhook).
2. Enter a verification token. This string is set up by you when you create your webhook endpoint. You can pick any string you like. Make sure to update this in your `VERIFY_TOKEN` environment variable.
3. After you add a webhook to WhatsApp, WhatsApp will submit a validation post request to your application through ngrok. Confirm your localhost app receives the validation get request and logs `WEBHOOK_VERIFIED` in the terminal.
4. Back to the Configuration page, click Manage.
5. On the Webhook fields popup, click Subscribe to the **messages** field. Tip: You can subscribe to multiple fields.
6. If your Flask app and ngrok are running, you can click on "Test" next to messages to test the subscription. You recieve a test message in upper case. If that is the case, your webhook is set up correctly.


#### Testing the Integration
Use the phone number associated to your WhatsApp product or use the test number you copied before.
1. Add this number to your WhatsApp app contacts and then send a message to this number.
2. Confirm your localhost app receives a message and logs both headers and body in the terminal.
3. Test if the bot replies back to you in upper case.
4. You have now succesfully integrated the bot! 🎉
5. Now it's time to acutally build cool things with this.


## Step 4: Understanding Webhook Security

Below is some information from the Meta Webhooks API docs about verification and security. It is already implemented in the code, but you can reference it to get a better understanding of what's going on in [security.py](./blob/main/app/decorators/security.py)

#### Verification Requests

[Source](https://developers.facebook.com/docs/graph-api/webhooks/getting-started#:~:text=process%20these%20requests.-,Verification%20Requests,-Anytime%20you%20configure)

Anytime you configure the Webhooks product in your App Dashboard, we'll send a GET request to your endpoint URL. Verification requests include the following query string parameters, appended to the end of your endpoint URL. They will look something like this:

```
GET https://www.your-clever-domain-name.com/webhook?
  hub.mode=subscribe&
  hub.challenge=1158201444&
  hub.verify_token=meatyhamhock
```

The verify_token, `meatyhamhock` in the case of this example, is a string that you can pick. It doesn't matter what it is as long as you store in the `VERIFY_TOKEN` environment variable.

#### Validating Verification Requests

[Source](https://developers.facebook.com/docs/graph-api/webhooks/getting-started#:~:text=Validating%20Verification%20Requests)

Whenever your endpoint receives a verification request, it must:
- Verify that the hub.verify_token value matches the string you set in the Verify Token field when you configure the Webhooks product in your App Dashboard (you haven't set up this token string yet).
- Respond with the hub.challenge value.

#### Validating Payloads

[Source](https://developers.facebook.com/docs/graph-api/webhooks/getting-started#:~:text=int-,Validating%20Payloads,-We%20sign%20all)

WhatsApp signs all Event Notification payloads with a SHA256 signature and include the signature in the request's X-Hub-Signature-256 header, preceded with sha256=. You don't have to validate the payload, but you should.

To validate the payload:
- Generate a SHA256 signature using the payload and your app's App Secret.
- Compare your signature to the signature in the X-Hub-Signature-256 header (everything after sha256=). If the signatures match, the payload is genuine.


## Step 5: Learn about the API and Build Your App

Review the developer documentation to learn how to build your app and start sending messages. [See documentation](https://developers.facebook.com/docs/whatsapp/cloud-api).

## Step 6: Integrate AI into the Application

Now that we have an end to end connection, we can make the bot a little more clever then just shouting at us in upper case. All you have to do is come up with your own `generate_response()` function in [whatsapp_utils.py](./blob/main/app/utils/whatsapp_utils.py).

If you want a cookie cutter example to integrate the OpenAI Assistans API with a retrieval tool, then follow these steps.
1. Watch this video: [OpenAI Assistants Tutorial](https://www.youtube.com/watch?v=0h1ry-SqINc)
2. Create your own assistant with OpenAI and update your `OPENAI_API_KEY` and `OPENAI_ASSISTANT_ID` in the environment variables.
3. Provide your assistant with data and instructions
4. Update [openai_service.py](./blob/main/app/services/openai_service.py) to your use case.
5. Import `generate_reponse` into [whatsapp_utils.py](./blob/main/app/utils/)
6. Update `process_whatsapp_message()` with the new `generate_reponse()` function.

## Step 7: Add a Phone Number

When you’re ready to use your app for a production use case, you need to use your own phone number to send messages to your users.

To start sending messages to any WhatsApp number, add a phone number. To manage your account information and phone number, [see the Overview page.](https://business.facebook.com/wa/manage/home/) and the [WhatsApp docs](https://developers.facebook.com/docs/whatsapp/phone-numbers/).

If you want to use a number that is already being used in the WhatsApp customer or business app, you will have to fully migrate that number to the business platform. Once the number is migrated, you will lose access to the WhatsApp customer or business app. [See Migrate Existing WhatsApp Number to a Business Account for information](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started/migrate-existing-whatsapp-number-to-a-business-account).

Once you have chosen your phone number, you have to add it to your WhatsApp Business Account. [See Add a Phone Number](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started/add-a-phone-number).

When dealing with WhatsApp Business API and wanting to experiment without affecting your personal number, you have a few options:

1. Buy a New SIM Card
2. Virtual Phone Numbers
3. Dual SIM Phones
4. Use a Different Device
5. Temporary Number Services
6. Dedicated Devices for Development

**Recommendation**: If this is for a more prolonged or professional purpose, using a virtual phone number service or purchasing a new SIM card for a dedicated device is advisable. For quick tests, a temporary number might suffice, but always be cautious about security and privacy. Remember that once a number is associated with WhatsApp Business API, it cannot be used with regular WhatsApp on a device unless you deactivate it from the Business API and reverify it on the device.



### **Tech Stack**
1. **Backend Framework**: 
   - **Flask**: A lightweight Python web framework used to create the backend API and handle webhook requests.
   
2. **Environment Management**:
   - **python-dotenv**: Used to load environment variables from a `.env` file for configuration.

3. **AI Integration**:
   - **OpenAI**: The project integrates OpenAI's API to generate AI-driven responses, likely using GPT models.

4. **HTTP Requests**:
   - **requests**: Used for synchronous HTTP requests to external APIs (e.g., WhatsApp Cloud API).
   - **aiohttp**: Used for asynchronous HTTP requests.

5. **WhatsApp Integration**:
   - The project uses the **Meta WhatsApp Cloud API** to send and receive WhatsApp messages.

6. **Data Storage**:
   - **shelve**: A lightweight Python library used for thread management (storing and retrieving thread IDs).

7. **Security**:
   - **HMAC**: Used to validate webhook payloads from WhatsApp for authenticity.

8. **Other Tools**:
   - **ngrok**: Mentioned in the documentation for exposing the local Flask app to the internet for webhook testing.

---

### **Business Logic**
The project is designed to create an AI-powered WhatsApp bot for customer interaction. Here's a breakdown of the business logic:

1. **WhatsApp Message Handling**:
   - Incoming messages are received via a webhook endpoint (`/webhook`).
   - Messages are validated for authenticity using HMAC signatures.
   - If valid, the message is processed, and a response is generated.

2. **AI-Powered Responses**:
   - The bot integrates with OpenAI's API to generate intelligent responses.
   - The assistant is configured with specific instructions to act as a helpful and friendly bot for an Airbnb host.

3. **Thread Management**:
   - Each WhatsApp user is associated with a unique thread ID.
   - Threads are stored using `shelve` to maintain conversation context.

4. **WhatsApp API Integration**:
   - The bot sends messages using the WhatsApp Cloud API.
   - It supports both template messages (e.g., "hello_world") and custom text messages.

5. **Webhook Verification**:
   - The webhook endpoint includes a verification mechanism to ensure only legitimate requests from WhatsApp are processed.

6. **Text Processing**:
   - Utility functions are provided to format text for WhatsApp (e.g., converting Markdown-style text to WhatsApp-compatible formatting).

7. **Deployment**:
   - The app is designed to run locally using Flask and can be exposed to the internet using tools like ngrok for testing.

---

### **Use Case**
The bot is tailored for Airbnb hosts to assist guests with queries. It can:
- Provide information about check-in times, lockbox codes, etc.
- Maintain conversation context using threads.
- Respond intelligently using AI, with fallback instructions to contact the host if the bot cannot answer a query.

Let me know if you'd like a deeper dive into any specific part of the project!






1. Create a Virtual Environment
Navigate to your project directory:

Create a virtual environment named venv:
cd /Users/lucas/Documents/Workspaces/ContentCreation/python-whatsapp-bot
python3 -m venv venv

2. Activate the Virtual Environment
Activate the virtual environment:
source venv/bin/activate

3. Install Requirements
Install the dependencies from requirements.txt:
pip install -r requirements.txt

4. Verify Installation
Check that the dependencies are installed:
pip list

5. Set Up Environment Variables
Ensure the .env file is properly configured with your API keys and tokens. The python-dotenv library will load these variables into your application.

6. Deactivate the Virtual Environment
When you're done working, deactivate the virtual environment:
deactivate
