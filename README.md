# humblePhlipperNet
Java frontend · Python backend

## Overview

**Java (Frontend)**  
Uses a client like DreamBot to interact with the Grand Exchange. Each bot gathers its portfolio state (offers, inventory) and communicates with the backend.

**Python (Backend)**  
A Flask server that runs the centralised trading logic. It receives portfolio snapshots from bots over HTTP and responds with instructions (e.g., BID, ASK, CANCEL).

**Why?**  
Java is a pain for coding trading algorithms with concurrent bot synchronisation - Python is easy to tweak on the fly.

## Installation

1. **Start the server**

```bash
cd python-server
pip install -r requirements.txt
python -m humblePhlipperPython.app.server
```

2. **Run your bot**

Compile Java code and run your bots - Dreambot example, https://dreambot.org/guides/scripter-guide/starting/
