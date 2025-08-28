# Finance-bot

A finance bot that answers questions about finance and uses LiveKit for hosting the voice agent.

---

##  Overview

**Finance-bot** is a Python-based chatbot designed to respond intelligently to finance-related queries. 
The bot leverages **LiveKit**, a real-time media platform, to handle hosting and interaction.

---

##  Features

- Responds to finance-related questions.
- Hosted and managed using LiveKit for seamless real-time interactions.
- Modular code structure with agents, prompts, and tools.

---

##  Repository Structure

```text
.
├── agent1.py           # Core logic for your finance bot agents
├── prompt1.py          # Prompt definitions and interactions
├── tools1.py           # Utility functions and support tools
├── requirements.txt    # Python dependencies
├── .gitignore          # Specifies files and folders to ignore
└── .env                # Environment variables

## To run the bot:
Make sure you have the following installed:

python3.9+     # Recommended Python version
pip            # Python package manager

Clone the Repository
git clone https://github.com/aura-autumn/Finance-bot.git
cd Finance-bot

Install Dependencies
pip install -r requirements.txt

Setup LiveKit

Finance-bot uses LiveKit for real-time hosting and streaming.

1. Create a LiveKit Account

Go to https://livekit.io
 and sign up.

Create a project in the LiveKit Cloud Console.

2. Get API Keys

In the project settings, generate an API Key and API Secret.

Copy them somewhere safe.

3. Configure Environment

Add these keys to a .env file in your project root:

LIVEKIT_API_KEY=your_livekit_api_key_here
LIVEKIT_API_SECRET=your_livekit_api_secret_here
LIVEKIT_URL=wss://<your-livekit-domain>.livekit.cloud

Launch the bot with:

python agent1.py console

The bot will connect to LiveKit and begin responding to finance-related prompts defined in prompt1.py, with supporting utilities in tools1.py.
