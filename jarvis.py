import os
import base64
import webbrowser
from datetime import datetime
from google.colab import output
from google import genai
from IPython.display import display, HTML

# Configure Gemini API Key and Client
GOOGLE_API_KEY = "AQ.Ab8RN6KEKh_wl46QhSXnAshhnKiOXhycC-0lvrY5rX42F6j4bA"
os.environ["GEMINI_API_KEY"] = GOOGLE_API_KEY
client = genai.Client(api_key=GOOGLE_API_KEY)

# ==========================================
# 1. TEXT-TO-SPEECH (TTS) SYSTEM
# ==========================================
def speak_out_loud(text):
    """Reads response text out loud using the browser's SpeechSynthesis API"""
    clean_text = text.replace("'", "\\'").replace("\n", " ").strip()
    js_speak = f"""
    <script>
    (function() {{
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance('{clean_text}');
        utterance.rate = 1.05;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
    }})();
    </script>
    """
    display(HTML(js_speak))

# ==========================================
# 2. JARVIS COMMAND PROCESSOR & TOOLS
# ==========================================
def process_command(command):
    """Processes user commands locally and runs system tools if triggered"""
    cmd_lower = command.lower().strip()

    if any(k in cmd_lower for k in ["what time", "current time", "time"]):
        current_time = datetime.now().strftime("%I:%M %p")
        return f"The current time is {current_time}."

    if "open chrome" in cmd_lower or "open google" in cmd_lower:
        webbrowser.open("https://www.google.com")
        return "Opening Google Chrome."

    if "open youtube" in cmd_lower:
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube."

    # Fallback to standard Gemini conversation
    prompt = f"""
    You are JARVIS, a helpful AI voice assistant.
    The user said: \"{command}\"
    Provide a natural, warm, and concise voice reply (no markdown, keep it brief).
    """
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"I encountered an issue generating a response: {str(e)}"

# ==========================================
# 3. NATIVE AUDIO RECORDING BRIDGE (STT)
# ==========================================
RECORD_JS = """
async function recordAudio() {
  const div = document.createElement('div');
  const startButton = document.createElement('button');
  const stopButton = document.createElement('button');
  const status = document.createElement('span');

  startButton.textContent = '🎙️ Start Recording';
  startButton.style.background = '#a6e3a1';
  startButton.style.border = 'none';
  startButton.style.padding = '12px 24px';
  startButton.style.borderRadius = '30px';
  startButton.style.color = '#11111b';
  startButton.style.fontWeight = 'bold';
  startButton.style.cursor = 'pointer';
  startButton.style.fontSize = '14px';
  startButton.style.marginRight = '10px';

  stopButton.textContent = '⏹️ Stop Recording';
  stopButton.style.background = '#f38ba8';
  stopButton.style.border = 'none';
  stopButton.style.padding = '12px 24px';
  stopButton.style.borderRadius = '30px';
  stopButton.style.color = '#11111b';
  stopButton.style.fontWeight = 'bold';
  stopButton.style.cursor = 'pointer';
  stopButton.style.fontSize = '14px';
  stopButton.disabled = true;
  stopButton.style.opacity = '0.5';

  status.textContent = ' Click Start to talk to JARVIS';
  status.style.color = '#ffffff';
  status.style.marginLeft = '15px';

  div.appendChild(startButton);
  div.appendChild(stopButton);
  div.appendChild(status);
  div.style.fontFamily = 'sans-serif';
  div.style.padding = '20px';
  div.style.background = '#1e1e2e';
  div.style.borderRadius = '12px';
  div.style.display = 'flex';
  div.style.alignItems = 'center';
  div.style.maxWidth = '550px';
  div.style.margin = '20px auto';
  document.body.appendChild(div);

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const recorder = new MediaRecorder(stream);
  const chunks = [];

  const recordingReady = new Promise(resolve => {
    recorder.ondataavailable = e => chunks.push(e.data);
    recorder.onstop = async () => {
      const blob = new Blob(chunks);
      const reader = new FileReader();
      reader.readAsDataURL(blob);
      reader.onloadend = () => resolve(reader.result);
    };
  });

  startButton.onclick = () => {
    recorder.start();
    startButton.disabled = true;
    startButton.style.opacity = '0.5';
    stopButton.disabled = false;
    stopButton.style.opacity = '1.0';
    status.textContent = ' Listening...';
  };

  stopButton.onclick = () => {
    recorder.stop();
    stopButton.disabled = true;
    stopButton.style.opacity = '0.5';
    status.textContent = ' Processing voice command...';
  };

  const base64Audio = await recordingReady;
  div.remove();
  return base64Audio;
}
"""

# ==========================================
# 4. EXECUTION PIPELINE
# ==========================================
def run_jarvis():
    try:
        # Greeting
        print("JARVIS: Initializing...")
        speak_out_loud("Hey, this is Jarvis. I am online and ready.")

        # Retrieve Audio from Colab Mic Bridge
        audio_data = output.eval_js(RECORD_JS + "recordAudio()")
        print("Audio capture complete.")

        # Save file locally
        header, encoded = audio_data.split(",", 1)
        audio_bytes = base64.b64decode(encoded)
        file_path = "input_voice.wav"
        with open(file_path, "wb") as f:
            f.write(audio_bytes)

        # Upload and Transcribe utilizing native audio ingestion
        print("Uploading voice input to Gemini...")
        uploaded_file = client.files.upload(file=file_path)

        print("Transcribing audio...")
        transcription = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=[uploaded_file, "Transcribe this voice message verbatim. If there is no speech, output empty."]
        )
        user_query = transcription.text.strip()
        print(f"You said: \"{user_query}\"")

        if user_query:
            # Process custom commands/tools & generate responses
            jarvis_reply = process_command(user_query)
            print(f"\nJARVIS: {jarvis_reply}")
            speak_out_loud(jarvis_reply)
        else:
            print("No speech detected. Please try again.")
            speak_out_loud("I didn't hear anything. Please try speaking again.")

    except Exception as e:
        print("An error occurred in Jarvis Pipeline:", e)
