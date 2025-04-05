from flask import Flask, render_template, request, jsonify, session, redirect
import os
import json
import re
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
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 


os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


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
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # Use the global resume_analyzer instance
            analysis = resume_analyzer.analyze_resume(file_path)
            questions = resume_analyzer.generate_questions(analysis)
            
            # Store complete analysis in session
            session['resume_analysis'] = analysis
            session['current_questions'] = questions
            session['role'] = analysis.get('role', 'Software Developer')
            session['skills'] = analysis.get('skills', {}).get('technical_skills', [])
            session['experience_level'] = analysis.get('experience_level', 'mid')
            
            return jsonify({
                'success': True,
                'redirect': '/interview'  # Add redirect URL
            })
            
        except Exception as e:
            print(f"Error processing resume: {str(e)}")
            return jsonify({'error': str(e)}), 500
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
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
            
        role = session.get('role', 'Software Developer')
        domain = session.get('domain', 'General')
        skills = session.get('skills', [])
        experience_level = session.get('experience_level', 'mid')
        
        prompt = f"""
        You are an expert technical interviewer. Generate 5 unique technical interview questions.

        Candidate Profile:
        Role: {role}
        Domain: {domain}
        Skills: {', '.join(skills)}
        Level: {experience_level}

        Create questions that:
        1. Test implementation using {skills[0] if skills else 'primary skill'}
        2. Cover system design for {domain}
        3. Test problem-solving with {skills[1] if len(skills) > 1 else 'core technology'}
        4. Test integration of {', '.join(skills[:2])}
        5. Cover best practices in {domain}

        Return ONLY a JSON array in this exact format:
        [
            "Question 1 text here",
            "Question 2 text here",
            "Question 3 text here",
            "Question 4 text here",
            "Question 5 text here"
        ]
        Do not include any other text or formatting.
        """

        # Generate questions using Gemini
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Extract JSON array from response
        json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
        if not json_match:
            raise ValueError("Invalid response format from Gemini")
            
        questions = json.loads(json_match.group())
        
        if not isinstance(questions, list) or len(questions) != 5:
            raise ValueError("Invalid number of questions")
        
        # Store questions in session
        session['current_questions'] = questions
        
        return jsonify({
            'success': True,
            'questions': questions
        })
        
    except Exception as e:
        print(f"Error generating questions: {str(e)}")
        return jsonify({'error': str(e)}), 500
            
    except Exception as e:
        print(f"Error in get_questions: {str(e)}")
        return jsonify({'error': str(e)}), 500
        
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
        is_final = len(session.get('answers', [])) >= 4  # Check if this is the last question
        
        # Define the analysis prompt
        prompt = f"""
        Analyze this technical interview response and provide scores and feedback.
        
        Question: {question}
        Response: {response}
        
        Return the analysis as a JSON object with this exact structure:
        {{
            "technical_score": <0-100>,
            "communication_score": <0-100>,
            "confidence_score": <0-100>,
            "total_score": <0-100>,
            "feedback": ["point1", "point2", "point3"]
        }}
        """
        
        # Get Gemini's analysis
        gemini_response = model.generate_content(prompt)
        response_text = gemini_response.text.strip()
        
        # Clean and parse JSON response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group()
        
        analysis = json.loads(response_text)
        
        # Store only essential data
        answers = session.get('answers', [])
        answers.append({
            'score': {
                'technical_score': analysis['technical_score'],
                'communication_score': analysis['communication_score'],
                'confidence_score': analysis['confidence_score'],
                'total_score': analysis['total_score']
            }
        })
        session['answers'] = answers
        
        if is_final:
            # Calculate final scores
            final_scores = {
                'technical_score': sum(ans['score']['technical_score'] for ans in answers) / len(answers),
                'communication_score': sum(ans['score']['communication_score'] for ans in answers) / len(answers),
                'confidence_score': sum(ans['score']['confidence_score'] for ans in answers) / len(answers),
                'total_score': sum(ans['score']['total_score'] for ans in answers) / len(answers)
            }
            
            # Define feedback prompt for final analysis
            feedback_prompt = f"""
            Analyze the overall interview performance with these scores:
            Technical: {final_scores['technical_score']:.1f}%
            Communication: {final_scores['communication_score']:.1f}%
            Confidence: {final_scores['confidence_score']:.1f}%
            Overall: {final_scores['total_score']:.1f}%

            Return a JSON object with this structure:
            {{
                "strengths": ["strength1", "strength2", "strength3"],
                "areas_for_improvement": ["area1", "area2", "area3"],
                "recommendations": ["rec1", "rec2", "rec3"]
            }}
            """
            
            feedback_response = model.generate_content(feedback_prompt)
            feedback_text = feedback_response.text.strip()
            
            feedback_match = re.search(r'\{.*\}', feedback_text, re.DOTALL)
            if feedback_match:
                feedback_text = feedback_match.group()
            
            overall_feedback = json.loads(feedback_text)
            
            # Store minimal feedback data
            session['final_score'] = final_scores
            session['overall_feedback'] = {
                'strengths': overall_feedback.get('strengths', [])[:3],
                'areas_for_improvement': overall_feedback.get('areas_for_improvement', [])[:3],
                'recommendations': overall_feedback.get('recommendations', [])[:3]
            }
            
            return jsonify({
                'success': True,
                'is_final': True,
                'redirect': '/feedback'
            })
        
        return jsonify({
            'success': True,
            'is_final': False,
            'score': analysis,
            'feedback': analysis['feedback'][:3]  # Limit feedback points
        })
        
    except Exception as e:
        print(f"Error analyzing response: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/feedback')
def feedback():
    if 'final_score' not in session or 'overall_feedback' not in session:
        return redirect('/')
    return render_template('feedback.html')

@app.route('/get_final_feedback')
def get_final_feedback():
    try:
        if 'final_score' not in session or 'overall_feedback' not in session:
            return jsonify({'success': False, 'error': 'No feedback available'}), 404
            
        return jsonify({
            'success': True,
            'final_score': session['final_score'],
            'overall_feedback': session['overall_feedback']
        })
    except Exception as e:
        print(f"Error getting final feedback: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
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

@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html')

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True, port=5501)