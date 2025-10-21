import os
import subprocess
from dotenv import load_dotenv
from pyngrok import ngrok

# Load environment variables
load_dotenv()

# Set the port for Streamlit
PORT = 8501

def main():
    """Starts the Streamlit app and exposes it via ngrok."""
    
    # 1. Check for ngrok auth token
    if "NGROK_AUTHTOKEN" not in os.environ:
        print("ERROR: NGROK_AUTHTOKEN not set in .env file.")
        print("Please visit ngrok dashboard to get your token and add it to the .env file.")
        return

    # 2. Authenticate ngrok
    ngrok.set_auth_token(os.environ["NGROK_AUTHTOKEN"])
    
    # 3. Create ngrok tunnel
    try:
        # Use subprocess to run the Streamlit app in the background
        streamlit_process = subprocess.Popen(
            ["streamlit", "run", "app.py", "--server.port", str(PORT), "--server.enableCORS", "false"]
        )
        print(f"✅ Streamlit process started on port {PORT}")
        
        # Connect ngrok to the Streamlit port
        tunnel = ngrok.connect(PORT)
        print(f"🌐 App is live at: {tunnel.public_url}")
        print("\nPress Ctrl+C to stop the application.")
        
        # Keep the main process alive until interrupted
        streamlit_process.wait()
        
    except Exception as e:
        print(f"An error occurred: {e}")
        # Clean up ngrok tunnels if an error occurs
        ngrok.kill()
    except KeyboardInterrupt:
        print("\nStopping application...")
        # Terminate Streamlit and ngrok
        streamlit_process.terminate()
        ngrok.kill()
        print("Application stopped.")

if __name__ == "__main__":
    main()