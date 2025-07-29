import os
import logging
from pathlib import Path
from datetime import datetime
from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler
)
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import inch
from dotenv import load_dotenv
from groq import Groq
import re

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Directories
OUTPUT_DIR = "generated"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# States
MAIN_MENU, CHATTING, SELECTING_TEMPLATE = range(3)

# Document types
DOCUMENT_TYPES = {
    'affidavit': 'Affidavit Document',
    'letter': 'Formal Letter', 
    'contract': 'Contract/Agreement',
    'certificate': 'Certificate',
    'application': 'Application Form',
    'custom': 'Custom Document'
}



class EnhancedDocumentGenerator:
    @staticmethod
    def generate_professional_pdf(text: str, filename: str, title: str, user_data: dict) -> str:
        try:
            filepath = os.path.join(OUTPUT_DIR, f"{filename}.pdf")
            doc = SimpleDocTemplate(filepath, pagesize=A4, 
                                  rightMargin=72, leftMargin=72, 
                                  topMargin=72, bottomMargin=72)
            
            styles = getSampleStyleSheet()
            
            # Enhanced styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold',
                textColor=colors.black
            )
            
            header_style = ParagraphStyle(
                'HeaderStyle',
                parent=styles['Normal'],
                fontSize=12,
                spaceAfter=12,
                fontName='Helvetica-Bold',
                textColor=colors.black
            )
            
            content_style = ParagraphStyle(
                'ContentStyle',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=12,
                leading=16,
                fontName='Helvetica',
                textColor=colors.black,
                alignment=TA_LEFT
            )
            
            signature_style = ParagraphStyle(
                'SignatureStyle',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                fontName='Helvetica',
                alignment=TA_RIGHT
            )
            
            elements = []
            
            # Add title
            elements.append(Paragraph(title.upper(), title_style))
            elements.append(Spacer(1, 20))
            
            # Add user information header if available
            if user_data.get('full_name') or user_data.get('applicant_name'):
                name = user_data.get('full_name') or user_data.get('applicant_name')
                elements.append(Paragraph(f"<b>Name:</b> {name}", header_style))
            
            if user_data.get('address') or user_data.get('applicant_address'):
                address = user_data.get('address') or user_data.get('applicant_address')
                elements.append(Paragraph(f"<b>Address:</b> {address}", header_style))
            
            elements.append(Spacer(1, 20))
            
            # Add date
            current_date = datetime.now().strftime("%d/%m/%Y")
            elements.append(Paragraph(f"<b>Date:</b> {current_date}", header_style))
            elements.append(Spacer(1, 20))
            
            # Process and add main content
            clean_text = str(text).replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
            
            # Split content into paragraphs and format
            paragraphs = clean_text.split('\n')
            for para in paragraphs:
                if para.strip():
                    # Handle different formatting
                    if para.strip().startswith('To:') or para.strip().startswith('From:'):
                        elements.append(Paragraph(para.strip(), header_style))
                    elif para.strip().startswith('Subject:'):
                        elements.append(Paragraph(f"<b>{para.strip()}</b>", header_style))
                    elif para.strip().startswith('Respected') or para.strip().startswith('Dear'):
                        elements.append(Paragraph(para.strip(), content_style))
                    else:
                        elements.append(Paragraph(para.strip(), content_style))
                    elements.append(Spacer(1, 8))
            
            # Add signature section
            elements.append(Spacer(1, 30))
            elements.append(Paragraph("_" * 30, signature_style))
            elements.append(Paragraph("Signature", signature_style))
            
            if user_data.get('full_name') or user_data.get('applicant_name'):
                name = user_data.get('full_name') or user_data.get('applicant_name')
                elements.append(Paragraph(f"({name})", signature_style))
            
            # Add footer (removed AI generation text)
            elements.append(Spacer(1, 20))
            
            doc.build(elements)
            return filepath
            
        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            raise e

def extract_user_data(text: str, document_type: str) -> dict:
    """Extract user data from text using enhanced patterns"""
    data = {}
    
    # Enhanced name patterns
    name_patterns = [
        r"(?:my name is|i am|name:?)\s*([A-Za-z\s]+)",
        r"([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"I,?\s+([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
    ]
    
    # Enhanced address patterns
    address_patterns = [
        r"(?:address|live at|residing at|from):?\s*([^.\n]+(?:\d{6}|\d{3}\s*\d{3})[^.\n]*)",
        r"(\d+[^,\n]+,[^,\n]+,\s*\d{6})",
        r"(?:address|live|residing).*?([^,\n]+,\s*[^,\n]+,\s*\d{6})"
    ]
    
    # Extract name
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and len(match.group(1).strip().split()) >= 2:
            name = match.group(1).strip()
            data['full_name'] = name
            data['applicant_name'] = name
            data['sender_name'] = name
            data['recipient_name'] = name
            break
    
    # Extract address
    for pattern in address_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            address = match.group(1).strip()
            data['address'] = address
            data['applicant_address'] = address
            data['sender_address'] = address
            break
    
    # Extract purpose - be more flexible
    if not data.get('purpose'):
        # If no explicit purpose found, use the entire text as context
        data['purpose'] = text.strip()
    
    return data



async def check_if_needs_more_info(prompt: str, document_type: str) -> str:
    """Check if AI needs more information before generating document"""
    if not groq_client:
        return None
    
    try:
        system_prompt = f"""You are an AI assistant that determines if there's enough information to create a {document_type}. 
        
Analyze the user's request and decide:
        1. If there's enough information to create a complete document, respond with: "GENERATE"
        2. If you need more specific information, respond with: "QUESTION: [ask a specific question]"
        
Be smart - only ask for truly essential information that cannot be reasonably assumed or left as placeholders."""
        
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"User wants to create a {document_type}. Their request: {prompt}"}
            ],
            model="llama3-70b-8192",
            temperature=0.1,
            max_tokens=200
        )
        
        response = chat_completion.choices[0].message.content.strip()
        
        if response.startswith("QUESTION:"):
            return response.replace("QUESTION:", "").strip()
        else:
            return None
            
    except Exception as e:
        logger.error(f"Info check error: {e}")
        return None

async def generate_ai_response(prompt: str, document_type: str, user_data: dict) -> str:
    """Generate AI response using Groq API with smart data extraction"""
    if not groq_client:
        return "AI service not available. Please check configuration."
    
    try:
        system_prompts = {
            'affidavit': "You are an expert legal document writer. Create a complete, professional affidavit with proper legal format. Use the provided information and create a professional document.",
            'letter': "You are a professional business letter writer. Create a complete formal letter with proper Indian format. Use the provided information to create a professional letter.",
            'contract': "You are a contract specialist. Create a comprehensive contract with clear terms. Use the provided information to create a professional contract.",
            'certificate': "You are creating official certificates. Generate a formal certificate with proper formatting using the provided information.",
            'application': "You are an expert in Indian government applications. Create authentic Indian applications with proper format (To, From, Subject structure). Use respectful language and proper Indian format.",
            'general': "You are a professional assistant. Provide helpful, well-structured responses. Be comprehensive and informative."
        }
        
        system_prompt = system_prompts.get(document_type, system_prompts['general'])
        
        # Enhanced user prompt with extracted data
        user_prompt = f"Create a {document_type} based on this request: {prompt}"
        if user_data:
            user_prompt += "\n\nExtracted information:"
            for key, value in user_data.items():
                if value and key != 'purpose':
                    user_prompt += f"\n- {key.replace('_', ' ').title()}: {value}"
        
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama3-70b-8192",
            temperature=0.3,
            max_tokens=2000
        )
        
        return chat_completion.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return f"I'm sorry, I encountered an error with the AI service: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Clear any existing user data
    context.user_data.clear()
    
    keyboard = [
        [InlineKeyboardButton("Chat with AI", callback_data='chat')],
        [InlineKeyboardButton("Generate Document", callback_data='generate')],
        [InlineKeyboardButton("Help", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = (
        "*Welcome to AI Document Assistant!*\n\n"
        "I can help you:\n"
        "• Chat and get AI responses\n"
        "• Generate professional documents\n"
        "• Create properly formatted PDFs\n\n"
        "Choose an option below:"
    )
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    return MAIN_MENU

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == 'chat':
        # Set chat mode in user data
        context.user_data['document_type'] = 'general'
        context.user_data['collected_data'] = {}
        
        await query.edit_message_text(
            "*Chat Mode*\n\n"
            "Ask me anything! I can help with:\n"
            "• General questions and answers\n"
            "• Document advice\n"
            "• Writing assistance\n"
            "• Any other queries\n\n"
            "*Note:* All responses will be provided as text AND PDF format\n\n"
            "Type /menu to return to main menu.",
            parse_mode='Markdown'
        )
        return CHATTING
    
    elif query.data == 'generate':
        keyboard = []
        for key, value in DOCUMENT_TYPES.items():
            keyboard.append([InlineKeyboardButton(f"{value}", callback_data=f'doc_{key}')])
        keyboard.append([InlineKeyboardButton("Back", callback_data='back_menu')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "*Select Document Type*\n\nChoose the type of document:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return SELECTING_TEMPLATE
    
    elif query.data == 'help':
        help_text = (
            "*Help*\n\n"
            "*Commands:*\n"
            "/start - Show main menu\n"
            "/menu - Return to main menu\n\n"
            "*Features:*\n"
            "• Chat with AI\n"
            "• Generate documents with proper formatting\n"
            "• Automatic data collection\n"
            "• Professional PDF generation\n"
        )
        
        keyboard = [[InlineKeyboardButton("Back", callback_data='back_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(help_text, parse_mode='Markdown', reply_markup=reply_markup)
        return MAIN_MENU
    
    elif query.data == 'back_menu':
        return await start_from_callback(query, context)
    
    elif query.data.startswith('doc_'):
        doc_type = query.data.replace('doc_', '')
        context.user_data['document_type'] = doc_type
        context.user_data['collected_data'] = {}
        context.user_data['missing_fields'] = []
        
        await query.edit_message_text(
            f"*Creating {DOCUMENT_TYPES[doc_type]}*\n\nDescribe what you need. I'll create a professional document based on your description.\n\n*Example:* \"I need an affidavit for address proof. My name is John Doe, I live at 123 Main Street, Delhi 110001\"\n\nType /menu to return to main menu.",
            parse_mode='Markdown'
        )
        return CHATTING

async def start_from_callback(query, context):
    keyboard = [
        [InlineKeyboardButton("Chat with AI", callback_data='chat')],
        [InlineKeyboardButton("Generate Document", callback_data='generate')],
        [InlineKeyboardButton("Help", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "*AI Document Assistant*\n\nChoose an option:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    return MAIN_MENU

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        user_message = update.message.text
        user_id = update.effective_user.id
        
        # Show typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action='typing'
        )
        
        document_type = context.user_data.get('document_type', 'general')
        
        # Initialize user data if not exists
        if 'collected_data' not in context.user_data:
            context.user_data['collected_data'] = {}
        
        # Extract data from current message
        extracted_data = extract_user_data(user_message, document_type)
        context.user_data['collected_data'].update(extracted_data)
        
        # Check if AI needs more information
        if document_type != 'general':
            question = await check_if_needs_more_info(user_message, document_type)
            if question:
                await update.message.reply_text(
                    f"I need some more information:\n\n*{question}*",
                    parse_mode='Markdown'
                )
                return CHATTING
        
        # Generate AI response with collected data
        ai_response = await generate_ai_response(user_message, document_type, context.user_data['collected_data'])
        
        # Send text response
        if document_type == 'general':
            await update.message.reply_text(
                f"*AI Assistant Response*\n\n{ai_response}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"*{DOCUMENT_TYPES.get(document_type, 'AI Response')}*\n\n{ai_response}",
                parse_mode='Markdown'
            )
        
        # Generate enhanced PDF
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            user_dir = os.path.join(OUTPUT_DIR, str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            
            doc_generator = EnhancedDocumentGenerator()
            
            if document_type == 'general':
                doc_title = "AI Assistant Response"
                pdf_filename = f"chat_response_{timestamp}"
            else:
                doc_title = DOCUMENT_TYPES.get(document_type, "AI-Generated Document")
                pdf_filename = f"{document_type}_{timestamp}"
            
            pdf_path = doc_generator.generate_professional_pdf(
                ai_response, 
                os.path.join(str(user_id), pdf_filename),
                doc_title,
                context.user_data['collected_data']
            )
            
            with open(pdf_path, 'rb') as pdf_file:
                if document_type == 'general':
                    caption = "AI response in PDF format"
                else:
                    caption = "Professional PDF version with proper formatting"
                    
                await update.message.reply_document(
                    document=pdf_file,
                    filename=f"{pdf_filename}.pdf",
                    caption=caption
                )
            
            # Add menu option after PDF generation
            keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data='back_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "✅ *Document Generated Successfully!*\n\n"
                "Your document has been created and sent as PDF.\n\n"
                "Click below to return to main menu or type /menu",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
                
        except Exception as e:
            logger.error(f"PDF error: {e}")
            await update.message.reply_text("PDF generation failed, but your content is above.")
        
        return CHATTING
        
    except Exception as e:
        logger.error(f"Message handling error: {e}")
        await update.message.reply_text(
            "I encountered an error. Please try again or use /start to restart."
        )
        return CHATTING

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Clear any existing user data
    context.user_data.clear()
    
    keyboard = [
        [InlineKeyboardButton("Chat with AI", callback_data='chat')],
        [InlineKeyboardButton("Generate Document", callback_data='generate')],
        [InlineKeyboardButton("Help", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = (
        "*Welcome to AI Document Assistant!*\n\n"
        "I can help you:\n"
        "• Chat and get AI responses\n"
        "• Generate professional documents\n"
        "• Create properly formatted PDFs\n\n"
        "Choose an option below:"
    )
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    return MAIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Cancelled. Use /start to begin again.')
    context.user_data.clear()
    return ConversationHandler.END

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Error: {context.error}")
    if update and hasattr(update, 'message') and update.message:
        try:
            await update.message.reply_text('Error occurred. Please try /start to restart.')
        except:
            pass

def main() -> None:
    print("TELEGRAM AFFIDAVIT BOT STARTING")
    
    if not BOT_TOKEN:
        print("ERROR: No BOT_TOKEN found!")
        return
    
    if not GROQ_API_KEY:
        print("ERROR: No GROQ_API_KEY found!")
        return
        
    print("Bot token and API key loaded successfully")
    print("Using Groq API for AI responses")
    print("Enhanced PDF generation enabled")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(button_handler),
                CommandHandler('menu', menu_command)
            ],
            CHATTING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message),
                CommandHandler('menu', menu_command)
            ],
            SELECTING_TEMPLATE: [
                CallbackQueryHandler(button_handler)
            ],

        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CommandHandler('menu', menu_command)
        ],
    )
    
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    
    print("Bot is now ONLINE and ready for users!")
    print("Press Ctrl+C to stop")
    
    try:
        application.run_polling()
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Bot crashed: {e}")
    finally:
        print("Bot is now OFFLINE")

if __name__ == '__main__':
    main()
