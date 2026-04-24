import os
import logging
import easyocr
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import google.generativeai as genai
from PIL import Image
from tavily import TavilyClient
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Setup Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Environment Variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not all([BOT_TOKEN, GEMINI_API_KEY, TAVILY_API_KEY]):
    logger.error("MISSING CORE API KEYS! Check your .env file.")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Configure Tavily
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# Initialize OCR
logger.info("Loading OCR Model...")
reader = easyocr.Reader(['en'], gpu=False)

# STATE TRACKER: Remembers who asked for an AI Check
AWAITING_AI_CHECK = set()

# ==========================================
# LAYER 0: Fast Python Sanity Check
# ==========================================
def sanity_check_passed(text: str) -> tuple[bool, str]:
    text_lower = text.lower().strip()
    junk_phrases = {
        "hi", "hello", "hey", "sup", "yo", "morning", "good morning", 
        "thanks", "thank you", "ok", "okay", "cool", "bye", "yes", "no",
        "ping", "test", "how are you", "who are you", "what do you do", "help"
    }
    if text_lower in junk_phrases:
        return False, "Hello! 👋 I am TruthGuard. Send me a news headline or image to fact-check, or use /ai to detect AI images."
    if len(text_lower.split()) < 3:
        return False, "That's a bit too short for me to fact-check. Can you provide a full sentence or a specific claim?"
    return True, ""

# ==========================================
# LAYER 1 & 2: Search and Reasoning
# ==========================================
def search_web_evidence(claim: str) -> str:
    try:
        response = tavily_client.search(query=claim, search_depth="basic", max_results=3)
        results = response.get("results", [])
        if not results:
            return "No search results found."
        context = ""
        for i, r in enumerate(results):
            context += f"Source {i+1}: {r.get('title', '')} - {r.get('content', '')}\n\n"
        return context
    except Exception as e:
        logger.error(f"Tavily Search Error: {e}")
        return "Search failed."

def analyze_with_llm(claim: str, context: str) -> str:
    prompt = f"""
    You are an elite, highly accurate fact-checking AI. Analyze the CLAIM strictly based on the WEB SEARCH EVIDENCE.
    CLAIM: "{claim}"
    WEB SEARCH EVIDENCE:\n{context}
    RULES:
    1. Strong support = TRUE
    2. Strong contradiction = FALSE
    3. Mix of both = PARTIALLY TRUE
    4. Insufficient/unrelated = UNVERIFIED
    5. Be extremely concise.
    Respond EXACTLY in this format:
    VERDICT: [TRUE/FALSE/PARTIALLY TRUE/UNVERIFIED]
    REASON: [One clear, factual sentence explaining why based on the evidence.]
    """
    try:
        return model.generate_content(prompt).text.strip()
    except Exception as e:
        logger.error(f"Gemini Error: {e}")
        return "VERDICT: ERROR\nREASON: Could not connect to reasoning engine."

# ==========================================
# LAYER 3: AI Image Detection (Ultimate Gemini Fix)
# ==========================================
def detect_ai_image(file_path: str) -> str:
    try:
        img = Image.open(file_path)
        prompt = """
        Analyze this image carefully. Is it AI-generated or a real photograph? 
        Look for AI artifacts like distorted hands, unnatural lighting, overly smooth textures, weird background text, or impossible geometry.
        
        Respond EXACTLY in this format (and nothing else):
        **[🤖 AI GENERATED or 📸 REAL/HUMAN]**
        *Reason:* [One short sentence explaining the visual evidence you found.]
        """
        response = model.generate_content([prompt, img])
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini Vision API Error: {e}")
        return "⚠️ Detection failed. Could not analyze image."

# ==========================================
# TELEGRAM HANDLERS
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "🛡️ **TruthGuard Active**\n\n"
        "🔍 Send me a news headline or screenshot to fact-check.\n"
        "🤖 Send `/ai` to enter AI Image Detection Mode.\n\n"
        "⚠️ *Disclaimer: I am an AI fact-checking assistant. My verdicts are based on live web retrieval and visual analysis models. I am highly capable, but not infallible. Always use critical thinking!*"
    )
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def cmd_ai_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    AWAITING_AI_CHECK.add(user_id)
    await update.message.reply_text("🤖 **AI Detection Mode ON**\n\nPlease send me the image you want to check. (This mode will turn off after one image).", parse_mode='Markdown')

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in AWAITING_AI_CHECK:
        AWAITING_AI_CHECK.remove(user_id)

    claim = update.message.text
    is_valid, reply_message = sanity_check_passed(claim)
    if not is_valid:
        await update.message.reply_text(reply_message)
        return
        
    processing_msg = await update.message.reply_text(f"🔍 Searching the web via Tavily for: '{claim}'...")
    evidence = search_web_evidence(claim)
    
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=processing_msg.message_id, text="🧠 Evidence found. Reasoning with Gemini...")
    verdict = analyze_with_llm(claim, evidence)
    
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=processing_msg.message_id, text=f"🛡️ **TruthGuard Analysis**\n\n**Claim:** {claim}\n\n{verdict}", parse_mode='Markdown')

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_path = "temp_image.jpg"
    await file.download_to_drive(file_path)

    if user_id in AWAITING_AI_CHECK:
        AWAITING_AI_CHECK.remove(user_id)
        processing_msg = await update.message.reply_text("🤖 Analyzing image details with Gemini Vision...")
        try:
            ai_verdict = detect_ai_image(file_path)
            await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=processing_msg.message_id, text=f"🔍 **AI Image Detection Result**\n\n{ai_verdict}", parse_mode='Markdown')
        except Exception as e:
            await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=processing_msg.message_id, text=f"Error: {e}")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
        return

    processing_msg = await update.message.reply_text("🖼️ Running OCR on image...")
    try:
        results = reader.readtext(file_path, detail=0)
        claim = " ".join(results)
        
        if not claim.strip():
            await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=processing_msg.message_id, text="❌ Could not extract any text from the image.")
            return

        is_valid, reply_message = sanity_check_passed(claim)
        if not is_valid:
            await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=processing_msg.message_id, text=f"📝 Extracted: '{claim}'\n\n❌ {reply_message}")
            return

        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=processing_msg.message_id, text=f"📝 Extracted: '{claim[:50]}...'\n🔍 Searching web via Tavily...")
        evidence = search_web_evidence(claim)
        
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=processing_msg.message_id, text="🧠 Reasoning with Gemini...")
        verdict = analyze_with_llm(claim, evidence)
        
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=processing_msg.message_id, text=f"🖼️ **Extracted Claim:** {claim}\n\n🛡️ **TruthGuard Analysis**\n\n{verdict}", parse_mode='Markdown')
    except Exception as e:
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=processing_msg.message_id, text=f"Error: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# ==========================================
# RENDER.COM HEALTH CHECK SERVER
# ==========================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"TruthGuard Bot is Alive and Running!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is missing!")
        return
        
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ai", cmd_ai_mode))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    
    logger.info("TruthGuard Bot v7.2 Deployment Ready...")
    app.run_polling()

if __name__ == '__main__':
    main()
