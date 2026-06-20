import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Ensure env vars are loaded (mainly for local development)
load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
# Accept both SUPABASE_KEY and SUPABASE_SERVICE_KEY
supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

supabase: Client | None = None

if supabase_url and supabase_key:
    # Ensure they are not placeholder values
    if "YOUR_PROJECT" not in supabase_url and "YOUR_SERVICE_ROLE" not in supabase_key:
        try:
            supabase = create_client(supabase_url, supabase_key)
            print("Supabase client initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize Supabase client: {e}")
    else:
        print("Supabase environment variables are placeholders. Supabase integration is disabled.")
else:
    print("Supabase environment variables are missing. Supabase integration is disabled.")
