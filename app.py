from flask import Flask, render_template, request, jsonify, session
import os
import json
from werkzeug.utils import secure_filename
from models.resume_analyzer import ResumeAnalyzer
from models.sentiment_analyzer import SentimentAnalyzer
from models.video_analyzer import VideoAnalyzer
from models.voice_analyzer import VoiceAnalyzer
import uuid
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize components with Gemini model
resume_analyzer = ResumeAnalyzer(model)
sentiment_analyzer = SentimentAnalyzer(model)
video_analyzer = VideoAnalyzer()
voice_analyzer = VoiceAnalyzer()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        # Create unique session ID for this interview
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        
        # Save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{filename}")
        file.save(file_path)
        
        try:
            # Extract role and skills from resume
            role_info = resume_analyzer.extract_role_info(file_path)
            skills = resume_analyzer.extract_skills(file_path)
            
            # Store in session
            session['role'] = role_info.get('role', 'General')
            session['experience_level'] = role_info.get('experience_level', 'mid')
            session['skills'] = skills
            session['resume_path'] = file_path
            
            return jsonify({
                'success': True,
                'redirect': '/interview',
                'role': session['role'],
                'skills': skills
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/interview')
def interview():
    if 'role' not in session or 'skills' not in session:
        return render_template('index.html', error="Please upload your resume first")
    
    return render_template('interview.html', 
                          role=session.get('role'),
                          skills=session.get('skills'))

@app.route('/get_questions', methods=['POST'])
def get_questions():
    try:
        if 'role' not in session or 'skills' not in session:
            return jsonify({'error': 'Session expired'}), 400
            
        role = session.get('role', 'General')
        skills = session.get('skills', [])
        
        # Generate questions using Gemini
        prompt = f"""
        Generate 5 technical interview questions for a {role} position.
        Required skills: {', '.join(skills)}

        Format your response EXACTLY as a JSON array like this:
        [
            "Question 1: What is your experience with {skills[0] if skills else 'programming'}?",
            "Question 2: Describe a technical challenge you faced with {skills[1] if len(skills) > 1 else 'your main technology'}.",
            "Question 3: How would you implement...",
            "Question 4: Explain the concept of...",
            "Question 5: What are the best practices for..."
        ]

        Make questions specific to the role and skills. Return ONLY the JSON array, no other text.
        """
        
        try:
            response = model.generate_content(prompt)
            # Clean the response text to ensure it's valid JSON
            response_text = response.text.strip()
            if not response_text.startswith('['):
                # Extract JSON array if it's wrapped in other text
                import re
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group()
                else:
                    raise ValueError("Invalid response format")
            
            questions = json.loads(response_text)
            
            # Validate questions format
            if not isinstance(questions, list) or len(questions) != 5:
                raise ValueError("Invalid questions format")
            
            # Store questions in session
            session['current_questions'] = questions
            
            return jsonify({
                'success': True,
                'questions': questions
            })
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Response text: {response_text}")
            return jsonify({
                'success': False,
                'error': 'Failed to parse questions'
            }), 500
            
    except Exception as e:
        print(f"Error in get_questions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
        
        prompt = f"""
        You are an expert technical interviewer for {role} position.
        Generate 5 unique and specific interview questions based on these requirements:

        Role: {role}
        Skills: {', '.join(skills)}

        Requirements:
        1. First question should be about their experience with {skills[0] if skills else 'their main technology'}
        2. Second question should be a technical problem-solving scenario
        3. Third question should test their knowledge of {skills[1] if len(skills) > 1 else 'relevant technologies'}
        4. Fourth question should be about system design or architecture
        5. Fifth question should be about their biggest technical achievement

        Make questions very specific to the role and skills.
        Return as JSON array with objects containing:
        - question: detailed interview question
        - expected_answer: specific points that should be covered in a good answer
        - difficulty: easy/medium/hard
        - score_criteria: specific points to evaluate the answer (0-100)

        Ensure questions are detailed and technical.
        """
        
        response = model.generate_content(prompt)
        questions_data = json.loads(response.text)
        
        session['current_questions'] = questions_data
        session['answers'] = []
        session['scores'] = []
        
        return jsonify({
            'success': True,
            'questions': [q['question'] for q in questions_data]
        })
        
    except Exception as e:
        print(f"Error generating questions: {e}")
        return jsonify({
            'success': True,
            'questions': [
                f"Describe your experience with {skills[0] if skills else 'your main technology'}.",
                "Explain a challenging technical problem you solved recently.",
                f"How would you implement a system using {', '.join(skills[:2])}?",
                "Design a scalable architecture for a real-time application.",
                "What's your most significant technical achievement?"
            ]
        })

@app.route('/analyze_response', methods=['POST'])
def analyze_response():
    try:
        data = request.json
        question = data.get('question', '')
        response = data.get('response', '')
        
        # Generate analysis prompt for Gemini
        prompt = f"""
        Analyze this interview response for a technical interview.
        Question: {question}
        Answer: {response}
        
        Provide evaluation in this exact JSON format:
        {{
            "technical_score": <score between 0-100>,
            "communication_score": <score between 0-100>,
            "confidence_score": <score between 0-100>,
            "total_score": <average of all scores>,
            "feedback": [
                "specific feedback point 1",
                "specific feedback point 2",
                "specific feedback point 3"
            ]
        }}
        
        Base the scores on:
        - Technical accuracy and depth
        - Communication clarity
        - Confidence in delivery
        """
        
        # Get Gemini's analysis
        gemini_response = model.generate_content(prompt)
        response_text = gemini_response.text.strip()
        
        # Clean and parse JSON response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group()
        
        analysis = json.loads(response_text)
        
        # Validate analysis format
        required_keys = ['technical_score', 'communication_score', 'confidence_score', 'total_score', 'feedback']
        if not all(key in analysis for key in required_keys):
            raise ValueError("Invalid response format from Gemini")
        
        # Store the response and score
        answers = session.get('answers', [])
        answers.append({
            'question': question,
            'response': response,
            'score': analysis
        })
        session['answers'] = answers
        
        # Check if this was the last question
        current_questions = session.get('current_questions', [])
        is_final = len(answers) >= len(current_questions)
        
        if is_final:
            # Calculate final score
            scores = [ans['score']['total_score'] for ans in answers]
            final_score = {
                'total_score': sum(scores) / len(scores),
                'technical_score': sum(ans['score']['technical_score'] for ans in answers) / len(answers),
                'communication_score': sum(ans['score']['communication_score'] for ans in answers) / len(answers),
                'overall_score': sum(scores) / len(scores)
            }
            session['final_score'] = final_score
        
        return jsonify({
            'success': True,
            'score': analysis,
            'feedback': analysis['feedback'],
            'is_final': is_final,
            'final_score': final_score if is_final else None
        })
        
    except Exception as e:
        print(f"Error analyzing response: {e}")
        print(f"Response text: {response_text if 'response_text' in locals() else 'Not available'}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/get_final_score')
def get_final_score():
    try:
        final_score = session.get('final_score')
        answers = session.get('answers', [])
        
        if not final_score:
            final_score = score_calculator.calculate_final_score({
                'questions': answers
            })
            session['final_score'] = final_score
        
        return jsonify({
            'success': True,
            'score': final_score,
            'answers': answers
        })
        
    except Exception as e:
        print(f"Error getting final score: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    video_data = data.get('videoData', '')
    audio_data = data.get('audioData', '')
    
    try:
        # Analyze different aspects of the response
        sentiment_score = sentiment_analyzer.analyze(response)
        video_analysis = video_analyzer.analyze(video_data)
        voice_analysis = voice_analyzer.analyze(audio_data)
        
        # Calculate comprehensive score
        score = score_calculator.calculate_score(
            question=question,
            response=response,
            sentiment=sentiment_score,
            video_analysis=video_analysis,
            voice_analysis=voice_analysis
        )
        
        # Update interview context
        context = session.get('interview_context', {})
        context['last_score'] = score
        context['question_history'] = context.get('question_history', []) + [question]
        session['interview_context'] = context
        
        # Adjust difficulty based on performance
        session['current_difficulty'] = 'hard' if score > 80 else 'medium' if score > 50 else 'easy'
        
        # Generate follow-up question or end interview
        if len(context['question_history']) < 5:
            follow_up = question_generator.generate_follow_up(
                response, score, session.get('current_difficulty')
            )
        else:
            follow_up = None
        
        return jsonify({
            'success': True,
            'score': score,
            'feedback': [
                f"Content Score: {score['technical_score']}%",
                f"Communication Score: {score['communication_score']}%",
                f"Confidence Score: {score['confidence_score']}%"
            ],
            'follow_up': follow_up
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/submit_interview', methods=['POST'])
def submit_interview():
    interview_data = request.json.get('interview_data', {})
    final_score = score_calculator.calculate_final_score(interview_data)
    
    # Save to leaderboard if name provided
    candidate_name = request.json.get('name', '')
    if candidate_name:
        try:
            with open('data/leaderboard.json', 'r') as f:
                leaderboard = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            leaderboard = []
        
        leaderboard.append({
            'name': candidate_name,
            'role': session.get('role', 'General'),
            'score': final_score['total_score'],
            'date': interview_data.get('date', '')
        })
        
        # Sort by score
        leaderboard = sorted(leaderboard, key=lambda x: x['score'], reverse=True)
        
        # Save back
        with open('data/leaderboard.json', 'w') as f:
            json.dump(leaderboard, f)
    
    return jsonify({
        'success': True,
        'redirect': '/feedback',
        'score': final_score
    })

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html')

if __name__ == '__main__':
    app.run(debug=True, port=5501)