import re
import json
import PyPDF2
import spacy
import docx
import os
from typing import Dict, List, Union

class ResumeAnalyzer:
    def __init__(self, model):
        self.model = model

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

    def analyze_resume(self, file_path: str) -> Dict:
        """Complete resume analysis"""
        resume_text = self.extract_text(file_path)
        
        prompt = f"""
        Analyze this resume in detail and extract all relevant information.
        
        Resume Text:
        {resume_text}
        
        Provide a detailed analysis in JSON format with the following structure:
        {{
            "personal_info": {{
                "name": "candidate name",
                "email": "email if present",
                "location": "location if present"
            }},
            "professional_summary": "detailed summary of career",
            "role": "current or target role",
            "experience_level": "entry/mid/senior",
            "years_of_experience": number,
            "skills": {{
                "technical_skills": ["list of technical skills"],
                "frameworks": ["list of frameworks"],
                "tools": ["list of tools"],
                "soft_skills": ["list of soft skills"]
            }},
            "experience": [
                {{
                    "title": "job title",
                    "company": "company name",
                    "duration": "duration",
                    "responsibilities": ["key responsibilities"],
                    "technologies": ["technologies used"]
                }}
            ],
            "education": [
                {{
                    "degree": "degree name",
                    "institution": "institution name",
                    "year": "completion year"
                }}
            ],
            "projects": [
                {{
                    "name": "project name",
                    "description": "brief description",
                    "technologies": ["technologies used"]
                }}
            ]
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            analysis = json.loads(response.text)
            return analysis
        except Exception as e:
            print(f"Error analyzing resume: {e}")
            return {}

    def generate_questions(self, analysis: Dict) -> List[Dict]:
        """Generate tailored interview questions based on complete analysis"""
        prompt = f"""
        You are an expert technical interviewer. Generate detailed technical interview questions based on this candidate's profile:

        Role: {analysis.get('role', 'Software Developer')}
        Experience: {analysis.get('years_of_experience', 0)} years
        Technical Skills: {', '.join(analysis.get('skills', {}).get('technical_skills', []))}
        Projects: {json.dumps(analysis.get('projects', []))}
        Experience: {json.dumps(analysis.get('experience', []))}

        Generate 5 technical questions that:
        1. Test their strongest technical skill
        2. Validate their project experience
        3. Challenge their problem-solving abilities
        4. Assess their system design knowledge
        5. Evaluate their best practices understanding

        For each question:
        1. Make it specific to their background
        2. Reference their actual projects or experience
        3. Focus on technologies they've used
        4. Include follow-up points to probe deeper

        Return as JSON array with objects containing:
        {{
            "question": "detailed question text",
            "context": "why this question is relevant to their background",
            "expected_points": ["key points to look for in answer"],
            "follow_ups": ["follow-up questions"],
            "difficulty": "easy/medium/hard",
            "category": "technical/design/problem-solving",
            "related_skills": ["skills being tested"]
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            questions = json.loads(response.text)
            return questions
        except Exception as e:
            print(f"Error generating questions: {e}")
            return []

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