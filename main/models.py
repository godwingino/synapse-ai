from django.db import models

class PDFDocument(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='pdfs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Chat(models.Model):
    document = models.ForeignKey(PDFDocument, related_name='chats', on_delete=models.CASCADE)
    user_input = models.TextField()
    chat_reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat with document {self.document.name} at {self.created_at}"
