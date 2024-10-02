from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
import spacy
import re

from docx import Document
import PyPDF2


class ResumeUploadAPI(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        resume_file = request.FILES['file']
        text_content = self.extract_text(resume_file)
        if resume_file:
            summary = self.summarize_resume(text_content)
            return Response({'summary': summary})
        else:
            return Response({"error": "No file uploaded"}, status=400)
       

    def extract_text(self, resume_file):
        if resume_file.name.endswith('.docx'):
            doc = Document(resume_file)
            return '\n'.join([para.text for para in doc.paragraphs])
        elif resume_file.name.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(resume_file)
            return '\n'.join([page.extract_text() for page in pdf_reader.pages])
        else:
            return ""

    # def summarize_resume(self, text_content):
    #     nlp = spacy.load('en_core_web_sm')
    #     doc = nlp(text_content)
    #     # NLP or keyword-based summarization logic here
    #     return "Summarized text"

    def summarize_resume(self, text_content):
         # Load the spaCy model for English language processing
        nlp = spacy.load('en_core_web_sm')
    
        # Process the text content using the NLP pipeline
        doc = nlp(text_content)
    
        # Initialize the summary dictionary
        summary = {
                "Name": None,
                "Email": None,
                "Phone": None,
                "Education": [],
                "Experience": [],
                "Skills": []
            }

        # Extract name from the first few lines
        lines = text_content.split('\n')
        for line in lines[:5]:  # Check only the first few lines for a name
                if len(line.split()) > 1 and not line.startswith('http'):
                    summary['Name'] = line
                    break

        # Use regex to extract email and phone number
        email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        phone_regex = r'\+?\d[\d -]{8,12}\d'
    
        email_match = re.search(email_regex, text_content)
        phone_match = re.search(phone_regex, text_content)
    
        summary["Email"] = email_match.group() if email_match else None
        summary["Phone"] = phone_match.group() if phone_match else None
    
        # Extract entities and classify them
        for ent in doc.ents:
            if ent.label_ == "ORG" and any(keyword in ent.text.lower() for keyword in ['college', 'university']):
                summary["Education"].append(ent.text)
            elif ent.label_ == "ORG" and not any(keyword in ent.text.lower() for keyword in ['college',     'university']):
                summary["Experience"].append(ent.text)

        # A keyword-based approach to skill extraction
        skill_keywords = ['java', 'python', 'html', 'css', 'javascript', 'sql', 'springboot']
    
        # Token-based analysis for skill extraction
        tokens = [token.text.lower() for token in doc if not token.is_stop and not token.is_punct]
        for skill in skill_keywords:
            if skill in tokens:
                summary["Skills"].append(skill.capitalize())
    
        # Remove duplicates and clean up
        summary["Education"] = list(set(summary["Education"]))
        summary["Experience"] = list(set(summary["Experience"]))
        summary["Skills"] = list(set(summary["Skills"]))
    
        # Return the refined summary
        return summary

class JobDescriptionCompareAPI(APIView):
    def post(self, request, *args, **kwargs):
        summary = request.data.get('summary')
        job_description = request.data.get('jobDescription')

        if not summary or not job_description:
            return Response({"error": "Both summary and job description are required"}, status=400)

        # Extract skills from the summary for comparison
        skills = summary.get("Skills", [])
        
        # Calculate match percentage based on skills
        match_count = sum(1 for skill in skills if skill.lower() in job_description.lower())
        match_percentage = (match_count / len(skills)) * 100 if skills else 0
        
        match_percentage = round(match_percentage, 2)

        return Response({'matchPercentage': match_percentage})
