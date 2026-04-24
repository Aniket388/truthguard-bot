import os, logging, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from google import genai
from PIL import Image
from tavily import TavilyClient
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Environment Variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# ==========================================
# FINAL OPTIMIZED CONFIGURATION
# ==========================================
MODEL_ID = 'gemini-2.5-flash-lite'
client = genai.Client(api_key=GEMINI_API_KEY)
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
AWAITING_AI_CHECK = set()

# ==========================================
# CORE FORENSIC & FACT-CHECK LOGIC
# ==========================================

def search_web_evidence(claim: str) -> str:
    try:
        response = tavily_client.search(query=claim, search_depth="basic", max_results=3)
        return "".join([f"Source: {r.get('content', '')}\n\n" for r in response.get("results", [])])
    except: return "Search failed."

def analyze_with_llm(claim: str, context: str) -> str:
    prompt = f"Expert Fact-Check: '{claim}' using: {context}. Format: VERDICT: [STATUS] REASON: [WHY]."
    try:
        response = client.models.generate_content(model=MODEL_ID, contents=prompt)
        return response.text.strip()
    except Exception as e: return f"Reasoning Error: {str(e)}"

def detect_ai_image(file_path: str) -> str:
    """Forensic Investigator prompt for historical and visual analysis."""
    try:
        img = Image.open(file_path)
        prompt = """
        Analyze this image as an expert forensic investigator:
        1. IDENTIFY: Who are the people or what are the objects?
        2. HISTORICAL CHECK: Is it historically possible for these people to be together?
        3. VISUAL CHECK: Look for AI artifacts like weird hands or physics errors.
        
        Respond in this format:
        VERDICT: [AI GENERATED or REAL/HUMAN]
        REASON: [Short explanation of visual and historical evidence.]
        """
        response = client.models.generate_content(model=MODEL_ID, contents=[img, prompt])
        return response.text.strip()
    except Exception as e: return f"Detection Error: {str(e)}"

def extract_text(file_path: str) -> str:
    try:
        img = Image.open(file_path)
        prompt = "Extract all text from this image. If none, reply 'NONE'."
        response = client.models.generate_content(model=MODEL_ID, contents=[img, prompt])
        t = response.text.strip()
        return "" if t == "NONE" else t
    except Exception as e: return f"OCR_ERROR: {str(e)}"

# ==========================================
# TELEGRAM HANDLERS
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🛡️ **TruthGuard v12.0 Active**\nModel: {MODEL_ID}\nStatus: Ready.", parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    claim = update.message.text
    msg = await update.message.reply_text("🔍 Analyzing claim...")
    evidence = search_web_evidence(claim)
    verdict = analyze_with_llm(claim, evidence)
    await msg.edit_text(f"🛡️ **Analysis**\n\n{verdict}")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_path = "temp.jpg"
    await file.download_to_drive(file_path)

    if user_id in AWAITING_AI_CHECK:
        AWAITING_AI_CHECK.remove(user_id)
        msg = await update.message.reply_text("🤖 Running Forensic AI Analysis...")
        result = detect_ai_image(file_path)
        await msg.edit_text(f"🔍 **Forensic Result**\n\n{result}")
    else:
        msg = await update.message.reply_text("🖼️ Extracting & Checking image content...")
        claim = extract_text(file_path)
        if "OCR_ERROR" in claim or not claim:
            await msg.edit_text("❌ No clear text found in image for fact-checking.")
        else:
            evidence = search_web_evidence(claim)
            verdict = analyze_with_llm(claim, evidence)
            await msg.edit_text(f"🛡️ **Analysis**\n\n{verdict}")
    
    if os.path.exists(file_path): os.remove(file_path)

# ==========================================
# DEPLOYMENT SETUP
# ==========================================

class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"OK")

def main():
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 8080))), HealthCheck).serve_forever(), daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ai", lambda u, c: AWAITING_AI_CHECK.add(u.effective_user.id) or u.message.reply_text("🤖 AI Detection Mode ON")))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == '__main__':
    main()
