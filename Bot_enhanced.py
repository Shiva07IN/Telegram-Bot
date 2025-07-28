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
MAIN_MENU, CHATTING, SELECTING_TEMPLATE, COLLECTING_DATA = range(4)

# Document types
DOCUMENT_TYPES = {
    'affidavit': 'Affidavit Document',
    'letter': 'Formal Letter', 
    'contract': 'Contract/Agreement',
    'certificate': 'Certificate',
    'application': 'Application Form',
    'custom': 'Custom Document'
}

# Required fields for each document type
REQUIRED_FIELDS = {
    'affidavit': ['full_name', 'address', 'purpose', 'facts'],
    'letter': ['sender_name', 'sender_address', 'recipient_name', 'recipient_address', 'subject', 'purpose'],
    'contract': ['party1_name', 'party1_address', 'party2_name', 'party2_address', 'subject_matter', 'terms'],
    'certificate': ['recipient_name', 'achievement', 'issuing_authority', 'date'],
    'application': ['applicant_name', 'applicant_address', 'organization', 'purpose', 'details'],
    'custom': ['purpose', 'details']
}

# Field questions
FIELD_QUESTIONS = {
    'full_name': "What is your full name?",
    'address': "What is your complete address with pin code?",
    'purpose': "What is the purpose of this document?",
    'facts': "What are the key facts or statements to include?",
    'sender_name': "What is the sender's name?",
    'sender_address': "What is the sender's address?",
    'recipient_name': "Who is the recipient?",
    'recipient_address': "What is the recipient's address?",
    'subject': "What is the subject of the letter?",
    'party1_name': "What is the first party's name?",
    'party1_address': "What is the first party's address?",
    'party2_name': "What is the second party's name?",
    'party2_address': "What is the second party's address?",
    'subject_matter': "What is the subject matter of the contract?",
    'terms': "What are the key terms and conditions?",
    'recipient_name': "Who is receiving the certificate?",
    'achievement': "What achievement or completion is being certified?",
    'issuing_authority': "What is the issuing authority/organization?",
    'date': "What is the date for the certificate?",
    'applicant_name': "What is the applicant's name?",
    'applicant_address': "What is the applicant's address?",
    'organization': "Which organization/department is this for?",
    'details': "Please provide specific details:"
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
    """Extract user data from text using regex patterns"""
    data = {}
    
    # Common patterns
    name_patterns = [
        r"(?:my name is|i am|name:)\s*([A-Za-z\s]+)",
        r"([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
    ]
    
    address_patterns = [
        r"(?:address|live at|residing at):?\s*([^.]+)",
        r"(\d+[^,]+,[^,]+,\s*\d{6})"
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and not data.get('full_name'):
            data['full_name'] = match.group(1).strip()
            data['applicant_name'] = match.group(1).strip()
            break
    
    for pattern in address_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and not data.get('address'):
            data['address'] = match.group(1).strip()
            data['applicant_address'] = match.group(1).strip()
            break
    
    # Extract purpose
    purpose_patterns = [
        r"(?:purpose|for|need|want):?\s*([^.]+)",
        r"(?:application for|request for):?\s*([^.]+)"
    ]
    
    for pattern in purpose_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and not data.get('purpose'):
            data['purpose'] = match.group(1).strip()
            break
    
    return data

def get_missing_fields(user_data: dict, document_type: str) -> list:
    """Get list of missing required fields"""
    required = REQUIRED_FIELDS.get(document_type, [])
    missing = []
    
    for field in required:
        if not user_data.get(field):
            missing.append(field)
    
    return missing

async def generate_ai_response(prompt: str, document_type: str, user_data: dict) -> str:
    """Generate AI response using Groq API with user data"""
    if not groq_client:
        return "AI service not available. Please check configuration."
    
    try:
        # Create context from user data
        context = ""
        if user_data:
            context = "User Information:\n"
            for key, value in user_data.items():
                if value:
                    context += f"- {key.replace('_', ' ').title()}: {value}\n"
            context += "\n"
        
        system_prompts = {
            'affidavit': f"You are an expert legal document writer. Create a complete, professional affidavit with proper legal format. Use the provided user information. {context}",
            'letter': f"You are a professional business letter writer. Create a complete formal letter with proper Indian format. Use the provided user information. {context}",
            'contract': f"You are a contract specialist. Create a comprehensive contract with clear terms. Use the provided user information. {context}",
            'certificate': f"You are creating official certificates. Generate a formal certificate with proper formatting. Use the provided user information. {context}",
            'application': f"You are an expert in Indian government applications. Create authentic Indian applications with proper format (To, From, Subject structure). Use respectful language and proper Indian format. {context}",
            'general': f"You are a professional document assistant. Create high-quality, well-structured content. Use the provided user information. {context}"
        }
        
        system_prompt = system_prompts.get(document_type, system_prompts['general'])
        
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a {document_type} based on: {prompt}"}
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
            f"*Creating {DOCUMENT_TYPES[doc_type]}*\n\nPlease describe what you need. Include as much detail as possible (name, address, purpose, etc.).\n\nType /menu to return to main menu.",
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
        
        # Check for missing fields
        missing_fields = get_missing_fields(context.user_data['collected_data'], document_type)
        
        # If we're in data collection mode
        if context.user_data.get('collecting_field'):
            field = context.user_data['collecting_field']
            context.user_data['collected_data'][field] = user_message
            context.user_data.pop('collecting_field')
            missing_fields = get_missing_fields(context.user_data['collected_data'], document_type)
        
        # If there are missing critical fields, ask for them
        if missing_fields and document_type != 'general':
            field_to_ask = missing_fields[0]
            context.user_data['collecting_field'] = field_to_ask
            
            question = FIELD_QUESTIONS.get(field_to_ask, f"Please provide {field_to_ask.replace('_', ' ')}:")
            
            await update.message.reply_text(
                f"I need some additional information:\n\n*{question}*",
                parse_mode='Markdown'
            )
            return COLLECTING_DATA
        
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
    context.user_data.clear()
    return await start(update, context)

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
            COLLECTING_DATA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message),
                CommandHandler('menu', menu_command)
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