from fpdf import FPDF
import os
from datetime import datetime

class InterviewReportGenerator:
    def __init__(self):
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=15)
        # Remove the font addition since FPDF2 has built-in fonts
        
    def generate_report(self, interview, user):
        # Add title page
        self.pdf.add_page()
        self.pdf.set_font('Helvetica', size=24)
        self.pdf.cell(0, 20, 'Interview Report', ln=True, align='C')
        
        # Add basic information
        self.pdf.set_font('Helvetica', size=12)
        self.pdf.ln(20)
        self.pdf.cell(0, 10, f'Candidate: {user.username}', ln=True)
        self.pdf.cell(0, 10, f'Role: {interview.role}', ln=True)
        self.pdf.cell(0, 10, f'Date: {interview.date.strftime("%B %d, %Y")}', ln=True)
        
        # Add scores section
        self.pdf.ln(10)
        self.pdf.set_font('Helvetica', size=16)
        self.pdf.cell(0, 10, 'Performance Scores', ln=True)
        self.pdf.set_font('Helvetica', size=12)
        
        scores = [
            ('Technical Score', interview.technical_score),
            ('Communication Score', interview.communication_score),
            ('Confidence Score', interview.confidence_score),
            ('Overall Score', interview.total_score)
        ]
        
        for label, score in scores:
            self.pdf.cell(0, 10, f'{label}: {score:.1f}%', ln=True)
        
        # Add feedback sections
        sections = [
            ('Key Strengths', interview.strengths),
            ('Areas for Improvement', interview.improvements),
            ('Recommendations', interview.recommendations)
        ]
        
        for title, items in sections:
            self.pdf.ln(10)
            self.pdf.set_font('Helvetica', size=16)
            self.pdf.cell(0, 10, title, ln=True)
            self.pdf.set_font('Helvetica', size=12)
            
            for item in items:
                self.pdf.cell(0, 10, f'• {item}', ln=True)
        
        # Save the report
        filename = f'interview_report_{interview.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        filepath = os.path.join('static', 'reports', filename)
        os.makedirs(os.path.join('static', 'reports'), exist_ok=True)
        self.pdf.output(filepath)
        
        return filename