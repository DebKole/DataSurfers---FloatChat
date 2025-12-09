import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from groq import Groq
except ImportError:
    print("❌ 'groq' library not found. Please install it with: pip install groq")
    sys.exit(1)

def list_models():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY not found in environment variables.")
        print("   Please add it to your .env file or set it in your environment.")
        return

    try:
        client = Groq(api_key=api_key)
        print("CONNECTING TO GROQ...")
        models = client.models.list()
        
        print("\n✅ AVAILABLE GROQ MODELS:")
        print("=" * 40)
        found_gpt_oss = False
        
        for model in models.data:
            print(f"- {model.id}")
            if "gpt" in model.id.lower() or "oss" in model.id.lower():
                print(f"  *** POTENTIAL MATCH: {model.id} ***")
                found_gpt_oss = True
        
        print("=" * 40)
        
        if found_gpt_oss:
             print("\n✨ Found models that might match 'GPT-OSS'.")
        else:
             print("\n⚠️ No obvious 'GPT-OSS' named models found. Using best alternative might be necessary.")

    except Exception as e:
        print(f"\n❌ Error connecting to Groq API: {e}")

if __name__ == "__main__":
    # Redirect stdout to a file to capture output reliably
    with open("groq_models_output.txt", "w", encoding="utf-8") as f:
        # Create a helper to print to both console and file
        def log(msg=""):
            print(msg)
            f.write(msg + "\n")
            
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            log("❌ GROQ_API_KEY not found in environment variables.")
        else:
            try:
                client = Groq(api_key=api_key)
                log("CONNECTING TO GROQ...")
                models = client.models.list()
                
                log("\n✅ AVAILABLE GROQ MODELS:")
                log("=" * 40)
                found_gpt_oss = False
                
                for model in models.data:
                    log(f"- {model.id}")
                    if "gpt" in model.id.lower() or "oss" in model.id.lower():
                        log(f"  *** POTENTIAL MATCH: {model.id} ***")
                        found_gpt_oss = True
                
                log("=" * 40)
                
                if found_gpt_oss:
                     log("\n✨ Found models that might match 'GPT-OSS'.")
                else:
                     log("\n⚠️ No obvious 'GPT-OSS' named models found.")

            except Exception as e:
                log(f"\n❌ Error connecting to Groq API: {e}")
