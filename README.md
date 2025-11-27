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
- **How to replace:**
    1. Upload your demo video to Google Drive.
    2. Right-click the file → **Get link**.
    3. Change the link access to **Anyone with the link** (or add specific viewers).
    4. Copy the share link and paste it into this README by replacing the placeholder URL.
- **Embed example:**

```markdown
- **Demo video:** [Watch the demo](https://drive.google.com/your-link-here)
```

- **Notes:**
    - Make sure the Drive share settings allow viewing for your audience.
    - For private demos, add viewer email addresses explicitly instead of using public sharing.

```
