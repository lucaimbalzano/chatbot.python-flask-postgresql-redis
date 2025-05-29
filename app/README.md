# Project Structure Explanation

```
.
├── LICENCE.txt
├── README.md
├── app
│   ├── README.md
│   ├── __init__.py
│   ├── config.py
│   ├── decorators
│   │   └── security.py
│   ├── services
│   │   ├── openai_service.py
│   │   └── whatsapp_service.py
│   └── utils
│       └── __init__.py
├── data
│   └── airbnb-faq.pdf
├── example.env
├── img
│   ├── adding-assets-to-system-user.png
│   ├── assign-role-to-system-user.png
│   └── meta-business-system-user-token.png
├── requirements.txt
├── routes
│   ├── __init__.py
│   └── routes.py
├── run.py
└── threads_db

8 directories, 19 files
```


#  🔹🔹🔹🔹

Welcome to the project!
This structure is based on the Flask framework and use routing "/route" for the endpoint, and "/service" for the business logic.

## Directory Structure:

### `app/` 
This is the main application directory containing all the core files for our Flask application.

- `__init__.py`: Initializes the Flask app using the Flask factory pattern. This allows for creating multiple instances of the app if needed, e.g., for testing.

- `config.py`: Contains configurations/settings for the Flask application. All environment-specific variables and secrets are typically loaded and accessed here.

- `decorators/`: Contains Python decorators that can be used across the application.

- `security.py`: Houses security-related decorators, for example, to check the validity of incoming requests.

- `services/`: Contains service modules that handle the business logic of the application.

  - `whatsapp_service.py`: Handles WhatsApp-related operations, such as processing incoming messages and sending responses via the WhatsApp Cloud API.
  - `openai_service.py`: Integrates with OpenAI's API to generate AI-driven responses.

- `utils/`: Utility functions and helpers to aid different functionalities in the application.


### `routes/`
This directory contains the route definitions for the application.
  - `__init__.py`: Initializes the routes module.
  - `routes.py`: Defines the webhook routes for handling incoming WhatsApp messages and verification requests.

### `data/`
This directory contains any static data files used by the application.
- `airbnb-faq.pdf`: A sample FAQ document for Airbnb hosts.

### `docs/`
This directory contains documentation files for the project.


### `img/`
This directory contains images used in the documentation.
  - `adding-assets-to-system-user.png`: An image showing how to add assets to a system user in Meta Business Manager.
  - `meta-business-system-user-token.png`: An image showing how to generate a system user token in Meta Business Manager.

### `run.py`
This is the entry point to run the Flask application. It sets up and runs the Flask app on a server.

### `requirements.txt`
Lists all the Python packages and libraries required for this project. They can be installed using `pip`.

### `.env`
Contains environment variables for the application, such as API keys and tokens. This file is loaded using `python-dotenv`.

---

## How It Works:

1. **Flask Factory Pattern**: Instead of creating a Flask instance globally, we create it inside a function (`create_app` in `__init__.py`). This function can be configured to different configurations, allowing for better flexibility, especially during testing.

2. **Blueprints**: In larger Flask applications, functionalities can be grouped using blueprints. Here, `routes.py` is a blueprint grouping related routes. It's like a subset of the application, handling a specific functionality (in this case, webhook views).

3. **Flask-RESTx for Swagger**: The project uses Flask-RESTx to define and document the API. Swagger UI is available at `/swagger` to explore and test the API endpoints.

4. **app.config**: Flask uses an object to store its configuration. We can set various properties on `app.config` to control aspects of Flask's behavior. In our `config.py`, we load settings from environment variables and then set them on `app.config`.

5. **Decorators**: These are Python's way of applying a function on top of another, allowing for extensibility and reusability. In the context of Flask, it can be used to apply additional functionality or checks to routes. The `decorators` folder contains such utility functions. For example, `signature_required` in `security.py` ensures that incoming requests are secure and valid.

