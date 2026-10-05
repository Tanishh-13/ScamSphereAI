# 🛡️ ScamSphere AI

### AI-Powered Fraud Campaign Intelligence Platform

ScamSphere AI is an evidence-driven fraud intelligence platform that analyzes suspicious messages and screenshots, extracts structured threat intelligence, assigns a deterministic risk score, correlates cases with historical complaints, and visualizes potential fraud campaigns.

> **ScamSphere AI doesn't just detect scams — it uncovers fraud campaigns.**

---

## 🚀 Live Demo

🌐 **[Try ScamSphere AI](https://scamsphereai.streamlit.app/)**

The deployed application is hosted on Streamlit Community Cloud.

---

## ✨ Features

### 📸 Screenshot & Text Analysis

- Upload suspicious screenshots or provide suspicious text.
- Extract text from screenshots using OCR.
- Analyze extracted content for scam indicators.

### 🎯 Scam & Entity Detection

Extracts structured threat intelligence including:

- 📞 Phone numbers
- 💳 UPI IDs
- 🔗 URLs
- 🏛️ Authorities / organizations mentioned
- 💰 Monetary amounts
- 🎯 Scam type
- 📝 Case summary

Concrete identifiers such as phone numbers, UPI IDs, and URLs are validated using deterministic extraction rather than relying solely on the LLM.

### 🚨 Evidence-Based Risk Scoring

ScamSphere evaluates multiple evidence signals to generate a risk score and severity assessment.

Signals include:

- Authority impersonation
- Urgency and pressure tactics
- Banking / KYC indicators
- Digital-arrest / law-enforcement pressure
- Extracted identifiers
- Historical complaint connections

### 🕸️ Fraud Campaign Intelligence

ScamSphere stores analyzed complaints and compares new cases against historical evidence.

It can identify relationships between cases based on shared evidence such as:

- Phone numbers
- UPI IDs
- URLs
- Authorities
- Scam characteristics
- Other extracted indicators

This allows individual complaints to be viewed as part of a larger potential fraud campaign.

### 📊 Fraud Network Visualization

The platform visualizes relationships between complaints as an interactive network graph.

This helps investigators identify:

- Connected complaints
- Repeated scam infrastructure
- Shared identifiers
- Potential campaign clusters

### 🤖 AI Cybercrime Copilot

The AI Copilot provides an investigative interface for reasoning about suspicious activity and the evidence collected by ScamSphere.

---

## 🏗️ System Workflow

```text
                 Suspicious Message
                         │
                         ▼
              Screenshot / Text Input
                         │
                         ▼
                        OCR
                         │
                         ▼
                Entity Extraction
                         │
                         ▼
              Evidence Validation
                         │
                         ▼
                Threat Assessment
                         │
                         ▼
              Historical Correlation
                         │
                         ▼
              Fraud Network Analysis
                         │
                         ▼
                AI Cyber Copilot
```

---

## 🧠 Intelligence Pipeline

ScamSphere follows an evidence-first approach:

```text
Raw Evidence
     │
     ├── OCR Text
     │
     ├── Phone Numbers
     │
     ├── UPI IDs
     │
     ├── URLs
     │
     ├── Authorities
     │
     └── Monetary Amounts
             │
             ▼
      Structured Evidence
             │
             ▼
       Risk Assessment
             │
             ▼
      Historical Database
             │
             ▼
     Case Correlation
             │
             ▼
      Fraud Campaign Graph
```

The goal is to move beyond isolated scam classification and provide **case-level and campaign-level intelligence**.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Streamlit | Web application |
| Groq | LLM-powered analysis |
| EasyOCR | Screenshot text extraction |
| PostgreSQL / Supabase | Historical complaint database |
| Plotly | Interactive visualizations |
| NetworkX | Fraud network analysis |
| Pandas | Data processing |
| OpenCV | Image processing |

---

## 📂 Project Structure

```text
ScamSphereAI/
│
├── agents/
│   ├── extraction_agent.py
│   ├── risk_agent.py
│   ├── cluster_agent.py
│   └── ...
│
├── utils/
│   ├── ocr.py
│   ├── db.py
│   ├── groq_client.py
│   └── ...
│
├── data/
│
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

## ⚙️ Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Tanishh-13/ScamSphereAI.git
cd ScamSphereAI
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
DATABASE_URL=your_postgresql_connection_string
```

### 4. Run the application

```bash
streamlit run app.py
```

The application will then be available locally through Streamlit.

---

## 🔐 Security

API keys and database credentials should **never be committed to the repository**.

Use environment variables locally and Streamlit Secrets when deploying to Streamlit Community Cloud.

Example:

```env
GROQ_API_KEY=your_api_key
DATABASE_URL=your_database_url
```

---

## 🎯 Why ScamSphere AI?

Traditional scam detection systems often treat every complaint as an isolated event.

ScamSphere takes a different approach.

Instead of asking only:

> **"Is this message a scam?"**

ScamSphere also asks:

> **"Have we seen similar evidence before?"**

and:

> **"Could these complaints be part of the same fraud campaign?"**

By combining structured evidence extraction, historical intelligence, risk assessment, and graph-based correlation, ScamSphere provides a foundation for investigating organized scam activity.

---

## 🌍 Real-World Applications

ScamSphere can serve as a prototype intelligence layer for:

- Cybercrime investigation teams
- Fraud analysis teams
- Banking security teams
- Digital safety organizations
- Scam reporting platforms
- Security researchers
- Fraud prevention systems

It can help investigators move from individual complaints toward identifying **patterns, repeated infrastructure, and potential coordinated campaigns**.

---

## 🔮 Future Scope

Potential extensions include:

- 🌐 Real-time complaint databases
- 📞 Voice-call analysis
- 🗣️ Multi-language scam detection
- 🎥 Video and social-media evidence analysis
- 📱 WhatsApp / Instagram / Facebook evidence ingestion
- 🔎 Large-scale fraud campaign clustering
- 🏛️ Cybercrime portal integration
- 🚨 Real-time campaign monitoring
- 🧠 Advanced graph-based community detection
- 📈 Investigator dashboards and case management

---

## ⚠️ Disclaimer

ScamSphere AI is an experimental fraud-intelligence platform and should be treated as an investigative aid rather than a definitive authority.

Risk scores and campaign connections should be reviewed by qualified investigators before taking enforcement or legal action.

---

## 🏆 Impact

ScamSphere AI combines:

**OCR + AI + Structured Evidence + Historical Intelligence + Graph Analysis**

to transform isolated suspicious messages into connected fraud intelligence.

> **Detect the scam. Connect the evidence. Uncover the campaign.**

---

## 🌐 Links

- 🚀 **Live Demo:** https://scamsphereai.streamlit.app/
- 💻 **GitHub:** https://github.com/Tanishh-13/ScamSphereAI
