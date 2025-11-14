import os
import streamlit as st
import whisper
import openai
from datetime import datetime, timedelta
import boto3
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import tempfile
from dateparser import parse
import re
import uuid

# AWS Configuration
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET = os.getenv('S3_BUCKET', 'meeting-insights-bucket')

# Google Calendar API Scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

class MeetingAgent:
    def __init__(self):
        self.whisper_model = whisper.load_model("base")
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION
        )
        self.openai_client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION
        )

    def transcribe_audio(self, audio_file):
        """Transcribe audio file using Whisper."""
        try:
            result = self.whisper_model.transcribe(audio_file.name)
            return result["text"]
        except Exception as e:
            st.error(f"Error during transcription: {str(e)}")
            return None

    def generate_summary(self, text):
        """Generate meeting summary and extract action items using GPT-4."""
        try:
            prompt = f"""
            Analyze the following meeting transcript and provide:
            1. A concise summary of key points
            2. Action items in the format [Task] [Assignee] [Deadline]
            3. Important decisions made
            
            Transcript: {text}
            """
            
            response = self.openai_client.invoke_model(
                modelId='anthropic.claude-v2',
                body=json.dumps({
                    'prompt': f"\n\nHuman:{prompt}\n\nAssistant:",
                    'max_tokens_to_sample': 1000,
                    'temperature': 0.5,
                    'top_p': 0.9,
                })
            )
            
            result = json.loads(response['body'].read().decode())
            return result['completion']
            
        except Exception as e:
            st.error(f"Error generating summary: {str(e)}")
            return None

    def parse_action_items(self, summary):
        """Parse action items from the summary text."""
        action_items = []
        lines = summary.split('\n')
        
        for line in lines:
            if '[' in line and ']' in line:
                try:
                    task = re.search(r'\[(.*?)\]', line).group(1)
                    assignee = re.search(r'\[(.*?)\]', line[line.find(']')+1:]).group(1)
                    deadline = re.search(r'\[(.*?)\]', line[line.rfind('['):]).group(1)
                    
                    action_items.append({
                        'task': task.strip(),
                        'assignee': assignee.strip(),
                        'deadline': parse(deadline).strftime('%Y-%m-%d')
                    })
                except Exception:
                    continue
        
        return action_items

    def create_calendar_event(self, action_item, calendar_service):
        """Create a calendar event for an action item."""
        try:
            event = {
                'summary': f'[Action] {action_item["task"]}',
                'description': f'Assigned to: {action_item["assignee"]}\n\n{action_item.get("description", "")}',
                'start': {
                    'dateTime': f"{action_item['deadline']}T09:00:00-07:00",
                    'timeZone': 'America/Los_Angeles',
                },
                'end': {
                    'dateTime': f"{action_item['deadline']}T10:00:00-07:00",
                    'timeZone': 'America/Los_Angeles',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 30},
                    ],
                },
            }
            
            event = calendar_service.events().insert(calendarId='primary', body=event).execute()
            return event.get('htmlLink')
            
        except Exception as e:
            st.error(f"Error creating calendar event: {str(e)}")
            return None

def get_google_calendar_service():
    """Get Google Calendar API service with OAuth2."""
    creds = None
    token_file = 'token.pickle'
    
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('calendar', 'v3', credentials=creds)

def main():
    st.title("🤖 Meeting Insights and Follow-up Agent")
    st.write("Upload your meeting recording or paste the transcript to get started.")
    
    agent = MeetingAgent()
    
    # File uploader for audio
    audio_file = st.file_uploader("Upload Meeting Recording", type=["mp3", "wav", "m4a"])
    
    # Text area for direct transcript input
    transcript_text = st.text_area("Or paste meeting transcript here:", height=150)
    
    if st.button("Process Meeting") and (audio_file or transcript_text):
        with st.spinner("Processing meeting..."):
            if audio_file:
                # Save uploaded file to temp
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.name)[1]) as tmp_file:
                    tmp_file.write(audio_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                # Transcribe audio
                transcript = agent.transcribe_audio(open(tmp_file_path, 'rb'))
                os.unlink(tmp_file_path)
                
                if not transcript:
                    st.error("Failed to transcribe audio. Please try again.")
                    return
            else:
                transcript = transcript_text
            
            # Generate summary
            summary = agent.generate_summary(transcript)
            
            if summary:
                st.subheader("📝 Meeting Summary")
                st.write(summary)
                
                # Extract and display action items
                action_items = agent.parse_action_items(summary)
                
                if action_items:
                    st.subheader("✅ Action Items")
                    for idx, item in enumerate(action_items, 1):
                        with st.expander(f"Action {idx}: {item['task']}"):
                            st.write(f"👤 **Assignee:** {item['assignee']}")
                            st.write(f"📅 **Deadline:** {item['deadline']}")
                            
                            # Add to Google Calendar
                            if st.button(f"Add to Calendar - Action {idx}"):
                                try:
                                    calendar_service = get_google_calendar_service()
                                    event_link = agent.create_calendar_event(item, calendar_service)
                                    if event_link:
                                        st.success(f"✅ Added to calendar! [View Event]({event_link})")
                                except Exception as e:
                                    st.error(f"Failed to add to calendar: {str(e)}")
                else:
                    st.info("No action items found in the meeting summary.")
                
                # Save to S3
                try:
                    meeting_id = str(uuid.uuid4())
                    s3_key = f"meetings/{meeting_id}.json"
                    
                    meeting_data = {
                        'transcript': transcript,
                        'summary': summary,
                        'action_items': action_items,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    agent.s3_client.put_object(
                        Bucket=S3_BUCKET,
                        Key=s3_key,
                        Body=json.dumps(meeting_data),
                        ContentType='application/json'
                    )
                    
                    st.success("Meeting data saved successfully!")
                    
                except Exception as e:
                    st.warning(f"Meeting processed, but failed to save to S3: {str(e)}")

if __name__ == "__main__":
    main()
