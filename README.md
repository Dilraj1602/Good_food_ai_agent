# GoodFoods - Reservation Agent (Prototype)

## Overview
Local prototype of a conversational reservation agent for GoodFoods. Includes:
- Streamlit chat UI
- Seeded restaurants dataset (place `data/restaurants_seed.json`)
- Controller that uses an LLM-like interface (mock by default)
- Tool-calling architecture: LLM suggests actions in JSON, controller executes whitelisted tools.

## Quick start (recommended: Python 3.11)

1. Ensure you have Python 3.11 installed. On Windows use the `py` launcher:

```powershell
py -3.11 --version
```

2. Create and activate a virtual environment from the project root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Upgrade pip tooling and install requirements (prefer binary wheels):

```powershell
python -m pip install --upgrade pip setuptools wheel
pip install --prefer-binary -r requirements.txt
```

4. Run the Streamlit app:

```powershell
streamlit run app/streamlit_app.py

5. If you're using Python 3.13 (system Python) and prefer not to install Python 3.11,
   you can still run the app. Create a venv with your system Python and install
   only the runtime packages to avoid heavy builds (useful when `numpy` may
   require compilation):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install pydantic streamlit
python scripts/check_imports.py
streamlit run app/streamlit_app.py
```

Troubleshooting
- If `pip install -r requirements.txt` fails building a package (e.g. numpy),
  try `pip install --prefer-binary package_name` or install Visual C++ Build
  Tools from Microsoft. Using Python 3.11 is recommended because more
  prebuilt wheels are available.
Using Python 3.11 is recommended because more
prebuilt wheels are available.

## Demo Video

- **Link:** [https://drive.google.com/file/d/1eZ1gttA2bC51ljh5AQmGtIy8i4hHzmTI/view?usp=sharing]

Project Structure

```text
sarvan_ai_assign/
└── goodfoods-agent/
    ├── app/
    │   ├── __pycache__/
    │   │   ├── __init__.cpython-313.pyc
    │   │   ├── controller.cpython-313.pyc
    │   │   ├── llm_client.cpython-313.pyc
    │   │   ├── recommender.cpython-313.pyc
    │   │   ├── schemas.cpython-313.pyc
    │   │   ├── tools.cpython-313.pyc
    │   │   └── utils.cpython-313.pyc
    │   ├── __init__.py
    │   ├── controller.py
    │   ├── llm_client.py
    │   ├── prompts.py
    │   ├── recommender.py
    │   ├── schemas.py
    │   ├── streamlit_app.py
    │   ├── tools.py
    │   └── utils.py
    │
    ├── db/
    │   ├── .gitkeep
    │   └── reservations.db
    │
    ├── scripts/
    │   └── check_imports.py
    │
    ├── .gitignore
    ├── README.md
    └── requirements.txt

```
