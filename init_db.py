from flask import Flask
from models.database import db
from models.badge import Badge
import os

app = Flask(__name__)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recruittron.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

def init_database():
    with app.app_context():
        db.create_all()
        
        # Initialize default badges if they don't exist
        if not Badge.query.first():
            default_badges = [
                Badge(
                    name='First Interview',
                    description='Completed your first technical interview',
                    icon='🎯',
                    criteria='Complete first interview'
                ),
                Badge(
                    name='High Scorer',
                    description='Achieved 90% or higher in an interview',
                    icon='🏆',
                    criteria='Score 90% or higher'
                ),
                Badge(
                    name='Weekly Warrior',
                    description='Completed 3 interviews in a week',
                    icon='⚔️',
                    criteria='Complete 3 interviews in 7 days'
                ),
                Badge(
                    name='Perfect Score',
                    description='Achieved 100% in an interview',
                    icon='🌟',
                    criteria='Score 100%'
                ),
                Badge(
                    name='Consistency King',
                    description='Maintained 85%+ score for 5 interviews',
                    icon='👑',
                    criteria='Score 85%+ in 5 interviews'
                ),
                Badge(
                    name='Speed Demon',
                    description='Completed interview in record time',
                    icon='⚡',
                    criteria='Complete interview under 15 minutes'
                )
            ]
            
            for badge in default_badges:
                db.session.add(badge)
            
            db.session.commit()
            print("Default badges created successfully!")
        
        print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()