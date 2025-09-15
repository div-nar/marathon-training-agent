# Marathon Training Agent 🏃‍♂️

AI-powered marathon training agent that analyzes your Strava running history and generates personalized training plans for 16, 12, 8, and 4-week timelines.

## Features

- **Strava Integration**: Automatically pulls your running history from Strava
- **Smart Analysis**: Analyzes pace, distance, consistency, and workout types
- **Personalized Plans**: Generates training plans based on your current fitness level
- **Multiple Timelines**: Supports 16, 12, 8, and 4-week marathon preparation
- **Pace Targets**: Calculates training paces based on your goals
- **Progress Tracking**: Monitors your fitness improvements over time

## Quick Start

### 1. Set Up Strava API

1. Go to [Strava API Settings](https://www.strava.com/settings/api)
2. Create a new application:
   - **Application Name**: "Marathon Training Agent"
   - **Category**: "Training"
   - **Website**: Your GitHub repo URL
   - **Authorization Callback Domain**: "localhost"

3. Get your credentials (Client ID & Client Secret)

4. Get authorization code by visiting:
```
https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost&approval_prompt=force&scope=activity:read_all
```

### 2. Install Dependencies

```bash
pip install requests python-dotenv
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your Strava credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
STRAVA_CLIENT_ID=your_actual_client_id
STRAVA_CLIENT_SECRET=your_actual_client_secret
STRAVA_REFRESH_TOKEN=your_actual_refresh_token
```

### 4. Run the Agent

```python
from marathon_agent import StravaMarathonAgent
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize agent
agent = StravaMarathonAgent()

# Authenticate with Strava
auth_result = agent.authenticate_strava(
    client_id=os.getenv('STRAVA_CLIENT_ID'),
    client_secret=os.getenv('STRAVA_CLIENT_SECRET'),
    refresh_token=os.getenv('STRAVA_REFRESH_TOKEN')
)

if auth_result['success']:
    # Get your running data
    runs = agent.get_strava_activities(days_back=90)
    
    # Analyze fitness
    fitness = agent.analyze_strava_fitness(runs)
    print("Your Current Fitness:", fitness)
    
    # Generate 16-week marathon plan
    plan = agent.generate_training_plan(16, fitness, goal_time="3:45:00")
    print("Your Training Plan:", plan)
```

## Training Plan Features

### Fitness Analysis
- **Weekly Mileage**: Current average weekly distance
- **Pace Analysis**: Average and recent pace trends
- **Consistency Score**: How regularly you run
- **Longest Run**: Current endurance capacity
- **Heart Rate Data**: If available from Strava
- **Workout Distribution**: Types of runs you do

### Training Plans
- **16-Week Plan**: Full marathon preparation with base building
- **12-Week Plan**: Intermediate timeline for experienced runners
- **8-Week Plan**: Short-term plan for maintaining fitness
- **4-Week Plan**: Final preparation and taper

### Plan Components
- **Training Phases**: Base building, speed work, peak, taper
- **Weekly Structure**: Customized based on fitness level
- **Key Workouts**: Long runs, tempo runs, interval training
- **Pace Targets**: Easy, tempo, interval, and race paces
- **Weekly Schedule**: Detailed week-by-week progression

## Fitness Levels

The agent automatically determines your fitness level:

- **Beginner**: <15 miles/week, longest run <8 miles
- **Beginner+**: 15-25 miles/week, longest run 8-12 miles
- **Intermediate**: 25-35 miles/week, longest run 12-16 miles
- **Intermediate+**: 35-50 miles/week, longest run 16-20 miles
- **Advanced**: 50+ miles/week, longest run 20+ miles

## Example Output

```json
{
  "fitness_level": "Intermediate",
  "weekly_mileage": 32.5,
  "consistency_score": "Very Good (5-6 runs/week)",
  "training_recommendations": [
    "Gradually increase long run distance",
    "Add more tempo runs for speed development"
  ],
  "pace_targets": {
    "easy_pace": 9.2,
    "tempo_pace": 8.1,
    "interval_pace": 7.5,
    "goal_marathon_pace": 8.8
  }
}
```

## Configuration

Customize your training preferences in `config.json`:

```json
{
  "training_preferences": {
    "default_timeline_weeks": 16,
    "max_weekly_mileage": 70,
    "preferred_long_run_day": "Sunday",
    "rest_days_per_week": 2
  },
  "runner_profile": {
    "goal_marathon_time": "3:45:00",
    "injury_history": [],
    "preferred_workout_types": ["tempo", "intervals", "long_runs"]
  }
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- Create an issue for bugs or feature requests
- Check existing issues before creating new ones
- Provide detailed information about your setup and error messages

---

**Happy Training! 🏃‍♂️💪**