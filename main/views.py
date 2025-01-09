from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from transformers import pipeline
from .models import PDFDocument
from .forms import PDFUploadForm
import PyPDF2
import json

# Hugging Face pipelines
chatbot_pipeline = pipeline("text2text-generation", model="facebook/blenderbot-400M-distill")

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
    if request.method == 'POST':
        user_input = request.POST.get('user_input', '')
        try:
            chat_response = chatbot_pipeline(f"Context: {extracted_text}\nUser: {user_input}", max_length=200)
            chat_reply = chat_response[0]['generated_text']
        except Exception as e:
            chat_reply = f"Error generating chatbot response: {e}"
    return render(request, 'pdf_detail.html', {'document': document, 'extracted_text': extracted_text, 'chat_reply': chat_reply})

def chat_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '')
            document_id = data.get('document_id', None)
            document = get_object_or_404(PDFDocument, pk=document_id)
            with document.file.open() as pdf_file:
                context = extract_text_from_pdf(pdf_file)
            response = chatbot_pipeline(f"Context: {context}\nUser: {message}", max_length=200)
            reply = response[0]['generated_text']
            return JsonResponse({'reply': reply})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)
