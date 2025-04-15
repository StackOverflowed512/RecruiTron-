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
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models.user import db, User
from models.interview_feedback import InterviewFeedback
from sqlalchemy import func, desc

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

# Add these configurations after creating the Flask app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recruittron.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Update the index route to require login
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect('/')
        return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            return render_template('signup.html', error='Username already exists')
        if User.query.filter_by(email=email).first():
            return render_template('signup.html', error='Email already registered')
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # Redirect to login page with a success message
        return render_template('login.html', message='Registration successful! Please login.')
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

# Add @login_required to all other routes that should be protected
@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        try:
            # Save file temporarily
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Analyze resume
            analysis = resume_analyzer.analyze_resume(file_path)
            resume_text = resume_analyzer.extract_text(file_path)
            
            # Store complete analysis in session
            session['resume_analysis'] = analysis
            session['resume_text'] = resume_text
            session['role'] = analysis.get('role', 'Software Developer')
            session['domain'] = analysis.get('domain', 'General')
            session['skills'] = analysis.get('skills', {}).get('technical_skills', [])
            session['experience_level'] = analysis.get('experience_level', 'mid')
            session['projects'] = analysis.get('projects', [])
            session['experience'] = analysis.get('experience', [])
            
            return jsonify({
                'success': True,
                'redirect': '/interview'
            })
            
        except Exception as e:
            print(f"Error processing resume: {str(e)}")
            return jsonify({'error': str(e)}), 500
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

@app.route('/get_questions', methods=['POST'])
def get_questions():
    try:
        if 'resume_analysis' not in session:
            return jsonify({'error': 'Session expired'}), 400
            
        analysis = session.get('resume_analysis', {})
        resume_text = session.get('resume_text', '')
        
        # Check if we have specific project/experience data
        if not analysis.get('projects') and not analysis.get('experience'):
            # Fall back to simpler question generation
            role = session.get('role', 'Software Developer')
            domain = session.get('domain', 'General')
            skills = session.get('skills', [])
            experience_level = session.get('experience_level', 'mid')

            prompt = f"""
            You are an expert technical interviewer. Generate 5 technical interview questions.
            
            Role: {role}
            Domain: {domain}
            Skills: {', '.join(skills)}
            Level: {experience_level}
            
            Resume Text:
            {resume_text}

            Return ONLY a JSON array in this exact format, with no additional text:
            [
                "Question 1 text",
                "Question 2 text",
                "Question 3 text",
                "Question 4 text",
                "Question 5 text"
            ]
            """
        else:
            # Use detailed question generation with project/experience references
            prompt = f"""
            You are an expert technical interviewer. Generate 5 highly specific technical interview questions based on this candidate's actual experience.

            Resume Analysis:
            Role: {analysis.get('role', 'Software Developer')}
            Experience Level: {analysis.get('experience_level', 'mid')}
            Years of Experience: {analysis.get('years_of_experience', 0)}
            Technical Skills: {', '.join(analysis.get('skills', {}).get('technical_skills', []))}
            
            Projects: {json.dumps(analysis.get('projects', []))}
            Work Experience: {json.dumps(analysis.get('experience', []))}
            
            Complete Resume Text:
            {resume_text}

            Requirements:
            1. Each question MUST reference specific projects or work experience from their resume
            2. Questions should focus on technologies they've actually used
            3. Include scenario-based questions based on their real projects
            4. Match the difficulty to their experience level
            5. Ask about specific technical challenges they've mentioned

            Return ONLY a JSON array with exactly 5 questions, each referencing specific details from their resume.
            Format: [
                "Regarding your project X, explain how you implemented Y using Z technology...",
                "In your role at Company A, you worked on B. How would you...",
                "You mentioned experience with Technology C in Project D. Describe...",
                "Based on your work at Company E, design a solution for...",
                "Considering your implementation of Feature F, explain the technical challenges..."
            ]
            """

        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Parse and validate response
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if not json_match:
            return jsonify({'error': 'Invalid response format from AI'}), 500
            
        questions = json.loads(json_match.group())
        if not isinstance(questions, list) or len(questions) < 5:
            return jsonify({'error': 'Invalid questions format'}), 500
            
        session['questions'] = questions
        return jsonify({
            'success': True,
            'questions': questions
        })

    except Exception as e:
        print(f"Error generating questions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/interview')
def interview():
    if 'role' not in session or 'skills' not in session:
        return render_template('index.html', error="Please upload your resume first")
    
    return render_template('interview.html', 
                          role=session.get('role'),
                          skills=session.get('skills'))

# Remove the duplicate @app.route('/analyze_response') and keep only one version
@app.route('/analyze_response', methods=['POST'])
@login_required
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
            
            # Save feedback to database
            feedback = InterviewFeedback(
                user_id=current_user.id,
                technical_score=final_scores['technical_score'],
                communication_score=final_scores['communication_score'],
                confidence_score=final_scores['confidence_score'],
                total_score=final_scores['total_score'],
                strengths=overall_feedback.get('strengths', [])[:3],
                improvements=overall_feedback.get('areas_for_improvement', [])[:3],
                recommendations=overall_feedback.get('recommendations', [])[:3],
                role=session.get('role', 'Software Developer')
            )
            db.session.add(feedback)
            db.session.commit()
            
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
    # Get top 5 users based on average interview scores
    top_users = db.session.query(
        User,
        func.avg(InterviewFeedback.total_score).label('avg_score'),
        func.count(InterviewFeedback.id).label('interview_count')
    ).join(InterviewFeedback)\
    .group_by(User.id)\
    .order_by(desc('avg_score'))\
    .limit(5)\
    .all()

    leaderboard_data = [{
        'rank': idx + 1,
        'name': user.username,
        'avg_score': float("%.1f" % avg_score),
        'interviews': interview_count
    } for idx, (user, avg_score, interview_count) in enumerate(top_users)]

    return render_template('leaderboard.html', leaderboard_data=leaderboard_data)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/ats-analyzer')
@login_required
def ats_analyzer():
    return render_template('ats_analyzer.html')

@app.route('/analyze-ats', methods=['POST'])
@login_required
def analyze_ats():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Extract text from resume
            resume_text = resume_analyzer.extract_text(file_path)
            
            # Create ATS analysis prompt
            prompt = f"""
            Analyze this resume for ATS (Applicant Tracking System) optimization.
            Return the analysis in JSON format.
            
            Resume Text:
            {resume_text}
            
            {{"ats_score": 0, "keyword_match_score": 0, "format_score": 0, "readability_score": 0, "missing_keywords": [], "improvement_suggestions": [], "format_suggestions": [], "keyword_suggestions": []}}
            
            Analyze and provide scores (0-100) and suggestions for:
            1. Overall ATS compatibility score
            2. Keyword matching with industry standards
            3. Format and structure
            4. Readability
            5. Missing important keywords
            6. Specific improvement suggestions
            7. Format optimization tips
            8. Recommended keywords to add
            """
            
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean and parse JSON response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group()
            
            try:
                analysis = json.loads(response_text)
            except json.JSONDecodeError:
                # Fallback response if JSON parsing fails
                analysis = {
                    "ats_score": 70,
                    "keyword_match_score": 65,
                    "format_score": 75,
                    "readability_score": 70,
                    "missing_keywords": ["relevant skill 1", "relevant skill 2"],
                    "improvement_suggestions": [
                        "Consider adding more specific technical skills",
                        "Quantify your achievements with metrics"
                    ],
                    "format_suggestions": [
                        "Use standard section headings",
                        "Ensure consistent formatting"
                    ],
                    "keyword_suggestions": [
                        "industry-specific term 1",
                        "industry-specific term 2"
                    ]
                }
            
            return jsonify({
                'success': True,
                'analysis': analysis
            })
            
        except Exception as e:
            print(f"Error analyzing resume: {str(e)}")
            return jsonify({
                'error': 'Failed to analyze resume. Please try again.',
                'details': str(e)
            }), 500
        finally:
            # Clean up the uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)

@app.route('/past-interviews')
@login_required
def past_interviews():
    # Get all interviews for the current user, ordered by date (newest first)
    interviews = InterviewFeedback.query.filter_by(user_id=current_user.id)\
        .order_by(InterviewFeedback.date.desc()).all()
    return render_template('past_interviews.html', interviews=interviews)

@app.route('/interview-details/<int:interview_id>')
@login_required
def interview_details(interview_id):
    # Get the specific interview for the current user
    interview = InterviewFeedback.query.filter_by(
        id=interview_id, 
        user_id=current_user.id
    ).first_or_404()
    
    return render_template('interview_details.html', interview=interview)

if __name__ == '__main__':
    app.run(debug=True, port=5501)