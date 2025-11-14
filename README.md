# Meeting-Insights-and-Follow-up-Automation-Agent-

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32.0-FF4B4B.svg)](https://streamlit.io/)
[![AWS](https://img.shields.io/badge/AWS-FF9900?logo=amazonaws&logoColor=white)](https://aws.amazon.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An AI-powered assistant that automates meeting transcription, summarization, task extraction, and calendar scheduling, boosting productivity by 40%.

##  Features

-  **Automatic Transcription** - Convert meeting audio to text using OpenAI Whisper
-  **AI-Powered Summaries** - Generate concise meeting summaries with key points
-  **Smart Action Items** - Extract tasks with assignees and deadlines
-  **Calendar Integration** - Schedule follow-ups directly to Google Calendar
-  **Cloud Native** - Deploy on AWS with Terraform
-  **Secure Storage** - All data stored securely in AWS S3
-  **Containerized** - Easy deployment with Docker

##  Quick Start

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- AWS Account
- Google Cloud Project with Calendar API enabled

### Local Development

1. **Clone the repository**
   ```bash
   git clone [https://github.com/yourusername/meeting-insights-agent.git](https://github.com/yourusername/meeting-insights-agent.git)
   cd meeting-insights-agent
### Architecture
graph TD
    A[Audio/Text Input] --> B[Whisper Transcription]
    B --> C[GPT-4 Analysis]
    C --> D[Summary & Action Items]
    D --> E[Google Calendar]
    D --> F[AWS S3 Storage]

   
