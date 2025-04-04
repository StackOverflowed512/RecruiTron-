import re
import json
import PyPDF2
import spacy
import docx
import os
from typing import Dict, List, Union

class ResumeAnalyzer:
    def __init__(self, gemini_model=None):
        self.model = gemini_model
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            # If model not found, download it
            import subprocess
            subprocess.call(['python', '-m', 'spacy', 'download', 'en_core_web_sm'])
            self.nlp = spacy.load("en_core_web_sm")
            
        # Define common job roles and related keywords
        self.role_keywords = {
            "Software Engineer": ["software engineer", "developer", "programmer", "coder", "software development"],
            "Data Scientist": ["data scientist", "data analyst", "machine learning", "deep learning", "AI"],
            "UX/UI Designer": ["ux", "ui", "user experience", "user interface", "designer"],
            "Product Manager": ["product manager", "product owner", "program manager", "scrum master"],
            "DevOps Engineer": ["devops", "cloud", "aws", "azure", "gcp", "kubernetes"],
            "Financial Analyst": ["financial", "finance", "accounting", "analyst", "investment"],
            "HR Specialist": ["hr", "human resources", "recruiting", "talent", "acquisition"]
        }

    def extract_text(self, file_path: str) -> str:
        """Extract text from resume file (PDF or DOCX)"""
        text = ""
        if file_path.endswith('.pdf'):
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
        elif file_path.endswith('.docx'):
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        return text

    def extract_role_info(self, file_path: str) -> Dict:
        """Extract role information from resume"""
        if self.model:
            return self._extract_role_info_with_gemini(file_path)
        else:
            return self._extract_role_info_with_rules(file_path)

    def _extract_role_info_with_gemini(self, file_path: str) -> Dict:
        """Extract role information using Gemini AI"""
        text = self.extract_text(file_path)
        
        prompt = f"""
        Analyze this resume text and provide a detailed role analysis.
        Focus on:
        1. Primary role/position based on recent experience
        2. Technical domain (e.g., frontend, backend, full-stack, data science, devops)
        3. Experience level based on years and responsibilities
        4. Key technologies and frameworks used

        Return ONLY a JSON object with this exact format:
        {{
            "role": "specific job title",
            "domain": "technical domain",
            "experience_level": "entry/mid/senior",
            "years_of_experience": number,
            "primary_technologies": ["tech1", "tech2", "tech3"],
            "summary": "brief role summary"
        }}

        Resume Text:
        {text[:10000]}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            if isinstance(result, dict):
                return {
                    'role': result.get('role', 'Software Developer'),
                    'experience_level': result.get('experience_level', 'mid'),
                    'domain': result.get('domain', 'General'),
                    'summary': result.get('summary', ''),
                    'technologies': result.get('primary_technologies', [])
                }
            return {
                'role': 'Software Developer',
                'experience_level': 'mid',
                'domain': 'General',
                'summary': 'No specific role identified',
                'technologies': []
            }
        except Exception as e:
            print(f"Error extracting role info: {e}")
            return {
                'role': 'Software Developer',
                'experience_level': 'mid',
                'domain': 'General',
                'summary': 'Error analyzing resume',
                'technologies': []
            }

    def _extract_skills_with_gemini(self, file_path: str) -> List[str]:
        """Extract skills using Gemini AI"""
        text = self.extract_text(file_path)
        
        prompt = f"""
        Analyze this resume and extract ALL technical skills, including:
        1. Programming languages
        2. Frameworks and libraries
        3. Tools and platforms
        4. Methodologies
        5. Domain-specific skills

        Group skills by category and return ONLY a JSON object like this:
        {{
            "programming_languages": ["language1", "language2"],
            "frameworks": ["framework1", "framework2"],
            "tools": ["tool1", "tool2"],
            "platforms": ["platform1", "platform2"],
            "other_skills": ["skill1", "skill2"]
        }}

        Resume Text:
        {text[:10000]}
        """
        
        try:
            response = self.model.generate_content(prompt)
            skills_dict = self._parse_json_response(response.text)
            if isinstance(skills_dict, dict):
                # Flatten and combine all skills
                all_skills = []
                for skill_list in skills_dict.values():
                    if isinstance(skill_list, list):
                        all_skills.extend(skill_list)
                return list(set(all_skills))  # Remove duplicates
            return []
        except Exception as e:
            print(f"Error extracting skills: {e}")
            return []

    def _extract_skills_with_rules(self, file_path: str) -> List[str]:
        """Extract skills using rule-based approach"""
        text = self.extract_text(file_path)
        doc = self.nlp(text)
        
        # Extract skills using NLP
        skills = []
        for ent in doc.ents:
            if ent.label_ in ["PRODUCT", "ORG", "GPE"]:
                skills.append(ent.text)
        
        # Look for skill sections
        skill_sections = re.findall(r'skills[:\s]+(.*?)(?:\n\n|\Z)', text.lower(), re.DOTALL)
        if skill_sections:
            for section in skill_sections:
                items = re.findall(r'(?:•|\*|\-|\d+\.)\s*([^•\*\-\n]+)', section)
                if not items:
                    items = [item.strip() for item in section.split(',')]
                skills.extend([item.strip() for item in items if len(item.strip()) > 2])
        
        return list(set(skills))[:15]  # Return unique skills, limited to top 15

    def _parse_json_response(self, text: str) -> Union[List[str], Dict, str]:
        """Helper to parse JSON from Gemini response"""
        try:
            # Clean and find JSON content
            json_match = re.search(r'(\[|\{).*?(\]|\})', text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            return text
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            return text

    def extract_skills(self, file_path: str) -> List[str]:
        """Extract skills from resume"""
        try:
            if self.model:
                text = self.extract_text(file_path)
                prompt = """
                Extract technical and professional skills from this resume.
                Return ONLY a JSON array of the top 15 most relevant skills.
                
                Resume text:
                {text[:5000]}
                """
                
                response = self.model.generate_content(prompt)
                skills = self._parse_json_response(response.text)
                
                if isinstance(skills, list):
                    return [s.strip() for s in skills if s.strip()][:15]
            
            return self._extract_skills_with_rules(file_path)
        except Exception as e:
            print(f"Error extracting skills: {e}")
            return self._extract_skills_with_rules(file_path)