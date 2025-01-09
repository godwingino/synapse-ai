import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import google.generativeai as genai
from .models import PDFDocument, Chat
from .forms import PDFUploadForm
import PyPDF2

# Configure the Generative AI SDK
GENAI_API_KEY = "AIzaSyAeKZigfAIdTDe3NByjY6D8seo3PDjJyqw"
genai.configure(api_key=GENAI_API_KEY)

def extract_text_from_pdf(pdf_file):
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            text += page_text if page_text else "\n[Page contains no extractable text]\n"
        return text.strip() if text else "No extractable text found."
    except Exception as e:
        return f"Error extracting text: {e}"

def home(request):
    if request.method == 'POST':
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            pdf = form.save(commit=False)
            pdf.name = request.FILES['file'].name
            pdf.save()
            return redirect('home')
    else:
        form = PDFUploadForm()
    documents = PDFDocument.objects.all()
    return render(request, 'home.html', {'form': form, 'documents': documents})

def pdf_detail(request, pk):
    document = get_object_or_404(PDFDocument, pk=pk)
    extracted_text = None
    chat_reply = None
    with document.file.open() as pdf_file:
        extracted_text = extract_text_from_pdf(pdf_file)
    
    # Retrieve previous chats for this document
    chats = Chat.objects.filter(document=document).order_by('-created_at')
    
    if request.method == 'POST':
        user_input = request.POST.get('user_input', '')
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(f"Context: {extracted_text}\nUser: {user_input}")
            chat_reply = response.text if response and hasattr(response, 'text') else "Sorry, I could not understand that."

            # Save the chat to the database
            Chat.objects.create(
                document=document,
                user_input=user_input,
                chat_reply=chat_reply
            )
        except Exception as e:
            chat_reply = f"Error generating chatbot response: {e}"
    
    return render(request, 'pdf_detail.html', {
        'document': document,
        'extracted_text': extracted_text,
        'chat_reply': chat_reply,
        'chats': chats
    })

@csrf_exempt
def chat_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '')
            document_id = data.get('document_id', None)
            document = get_object_or_404(PDFDocument, pk=document_id)
            with document.file.open() as pdf_file:
                context = extract_text_from_pdf(pdf_file)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(f"Context: {context}\nUser: {message}")
            reply = response.text if response and hasattr(response, 'text') else "Sorry, I could not understand that."
            
            # Save the chat to the database
            Chat.objects.create(
                document=document,
                user_input=message,
                chat_reply=reply
            )

            return JsonResponse({'reply': reply})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)
