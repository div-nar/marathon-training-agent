# Enhanced Marathon Training Agent with Strava Integration
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

class StravaMarathonAgent:
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        self.base_url = "https://www.strava.com/api/v3"
        self.headers = {
            'Authorization': f'Bearer {access_token}' if access_token else None
        }
        
        # Training zones (percentage of race pace)
        self.training_zones = {
            'easy': 0.65,
            'tempo': 0.88,
            'threshold': 0.92,
            'interval': 1.05,
            'recovery': 0.60
        }
    
    def authenticate_strava(self, client_id: str, client_secret: str, refresh_token: str) -> Dict:
        """Refresh Strava access token"""
        auth_url = "https://www.strava.com/oauth/token"
        payload = {
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        
        try:
            response = requests.post(auth_url, data=payload)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                self.headers['Authorization'] = f'Bearer {self.access_token}'
                return {
                    'success': True,
                    'access_token': token_data['access_token'],
                    'expires_at': token_data['expires_at']
                }
            else:
                return {'success': False, 'error': f'Auth failed: {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_strava_activities(self, days_back: int = 90, activity_type: str = 'Run') -> List[Dict]:
        """Fetch running activities from Strava"""
        if not self.access_token:
            return {'error': 'No Strava access token provided'}
        
        # Calculate date range
        after_date = datetime.now() - timedelta(days=days_back)
        after_timestamp = int(after_date.timestamp())
        
        url = f"{self.base_url}/athlete/activities"
        params = {
            'after': after_timestamp,
            'per_page': 200,  # Max activities per request
            'page': 1
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                activities = response.json()
                
                # Filter for running activities and extract relevant data
                runs = []
                for activity in activities:
                    if activity.get('type') == activity_type and activity.get('distance', 0) > 0:
                        # Convert meters to miles and seconds to pace per mile
                        distance_miles = activity['distance'] * 0.000621371
                        moving_time_seconds = activity.get('moving_time', 0)
                        
                        if moving_time_seconds > 0 and distance_miles > 0:
                            pace_per_mile = (moving_time_seconds / distance_miles) / 60  # minutes per mile
                            
                            run_data = {
                                'id': activity['id'],
                                'name': activity['name'],
                                'date': activity['start_date'][:10],
                                'distance': round(distance_miles, 2),
                                'moving_time': moving_time_seconds,
                                'pace_per_mile': round(pace_per_mile, 2),
                                'elevation_gain': activity.get('total_elevation_gain', 0) * 3.28084,  # meters to feet
                                'average_heartrate': activity.get('average_heartrate'),
                                'max_heartrate': activity.get('max_heartrate'),
                                'suffer_score': activity.get('suffer_score'),
                                'workout_type': activity.get('workout_type')
                            }
                            runs.append(run_data)
                
                return runs
            else:
                return {'error': f'Strava API error: {response.status_code}'}
                
        except Exception as e:
            return {'error': f'Failed to fetch Strava data: {str(e)}'}
    
    def analyze_strava_fitness(self, runs_data: List[Dict]) -> Dict:
        """Enhanced fitness analysis with Strava data"""
        if not runs_data or 'error' in runs_data:
            return {"error": "No valid running data available"}
        
        # Basic metrics
        total_distance = sum(run['distance'] for run in runs_data)
        total_runs = len(runs_data)
        avg_pace = sum(run['pace_per_mile'] for run in runs_data) / total_runs
        
        # Weekly analysis
        weeks_of_data = len(set(run['date'][:7] for run in runs_data))  # Unique year-month combinations
        weekly_mileage = total_distance / max(weeks_of_data, 1)
        
        # Find longest run and recent performance
        longest_run = max(runs_data, key=lambda x: x['distance'])
        recent_runs = sorted(runs_data, key=lambda x: x['date'], reverse=True)[:10]
        recent_avg_pace = sum(run['pace_per_mile'] for run in recent_runs) / len(recent_runs)
        
        # Workout type analysis
        workout_types = {}
        for run in runs_data:
            wtype = run.get('workout_type', 'Easy')
            workout_types[wtype] = workout_types.get(wtype, 0) + 1
        
        # Heart rate analysis (if available)
        hr_runs = [run for run in runs_data if run.get('average_heartrate')]
        avg_hr = sum(run['average_heartrate'] for run in hr_runs) / len(hr_runs) if hr_runs else None
        
        # Consistency analysis
        run_dates = [datetime.strptime(run['date'], '%Y-%m-%d') for run in runs_data]
        run_dates.sort()
        gaps = [(run_dates[i] - run_dates[i-1]).days for i in range(1, len(run_dates))]
        avg_gap = sum(gaps) / len(gaps) if gaps else 0
        
        fitness_level = self._determine_fitness_level(weekly_mileage, longest_run['distance'], avg_pace)
        
        return {
            'data_period_days': (max(run_dates) - min(run_dates)).days if run_dates else 0,
            'total_runs': total_runs,
            'total_distance': round(total_distance, 1),
            'weekly_mileage': round(weekly_mileage, 1),
            'average_pace': round(avg_pace, 2),
            'recent_pace_trend': round(recent_avg_pace, 2),
            'longest_run': {
                'distance': longest_run['distance'],
                'pace': longest_run['pace_per_mile'],
                'date': longest_run['date']
            },
            'fitness_level': fitness_level,
            'consistency_score': self._calculate_consistency_score(avg_gap),
            'workout_distribution': workout_types,
            'average_heartrate': round(avg_hr, 0) if avg_hr else None,
            'training_recommendations': self._generate_recommendations(weekly_mileage, longest_run['distance'], avg_gap)
        }
    
    def generate_training_plan(self, weeks: int, fitness_data: Dict, goal_time: Optional[str] = None) -> Dict:
        """Generate personalized marathon training plan based on Strava data"""
        
        weekly_mileage = fitness_data.get('weekly_mileage', 20)
        fitness_level = fitness_data.get('fitness_level', 'Beginner')
        longest_run = fitness_data.get('longest_run', {}).get('distance', 8)
        
        # Calculate peak mileage based on timeline and current fitness
        peak_multipliers = {16: 1.8, 12: 1.6, 8: 1.4, 4: 1.2}
        max_safe_mileage = min(weekly_mileage * peak_multipliers.get(weeks, 1.5), 70)
        
        # Adjust based on fitness level
        if fitness_level == 'Beginner':
            max_safe_mileage = min(max_safe_mileage, 40)
        elif fitness_level == 'Beginner+':
            max_safe_mileage = min(max_safe_mileage, 50)
        
        plan = {
            'timeline_weeks': weeks,
            'fitness_level': fitness_level,
            'current_weekly_mileage': weekly_mileage,
            'peak_weekly_mileage': round(max_safe_mileage, 1),
            'goal_marathon_time': goal_time,
            'training_phases': self._create_training_phases(weeks, weekly_mileage, max_safe_mileage),
            'weekly_structure': self._create_weekly_structure(fitness_level),
            'key_workouts': self._generate_key_workouts(weeks, fitness_level, longest_run),
            'pace_targets': self._calculate_pace_targets(fitness_data, goal_time),
            'weekly_schedule': self._generate_weekly_schedule(weeks, weekly_mileage, max_safe_mileage, fitness_level)
        }
        
        return plan
    
    def _calculate_consistency_score(self, avg_gap_days: float) -> str:
        """Calculate training consistency score"""
        if avg_gap_days <= 1.5:
            return "Excellent (Daily runner)"
        elif avg_gap_days <= 2.5:
            return "Very Good (5-6 runs/week)"
        elif avg_gap_days <= 3.5:
            return "Good (4-5 runs/week)"
        elif avg_gap_days <= 5:
            return "Fair (3-4 runs/week)"
        else:
            return "Needs Improvement (Inconsistent)"
    
    def _generate_recommendations(self, weekly_mileage: float, longest_run: float, avg_gap: float) -> List[str]:
        """Generate training recommendations based on current fitness"""
        recommendations = []
        
        if weekly_mileage < 20:
            recommendations.append("Focus on building base mileage gradually (10% rule)")
        
        if longest_run < 10:
            recommendations.append("Gradually increase long run distance")
        
        if avg_gap > 3:
            recommendations.append("Improve consistency - aim for at least 4 runs per week")
        
        if weekly_mileage > 50 and longest_run < 16:
            recommendations.append("Add more long runs to match your weekly volume")
        
        return recommendations
    
    def _determine_fitness_level(self, weekly_mileage: float, longest_run: float, avg_pace: float) -> str:
        """Enhanced fitness level determination"""
        # Base level on mileage and long run
        if weekly_mileage >= 50 and longest_run >= 20:
            base_level = "Advanced"
        elif weekly_mileage >= 35 and longest_run >= 16:
            base_level = "Intermediate+"
        elif weekly_mileage >= 25 and longest_run >= 12:
            base_level = "Intermediate"
        elif weekly_mileage >= 15 and longest_run >= 8:
            base_level = "Beginner+"
        else:
            base_level = "Beginner"
        
        # Adjust based on pace (rough estimates)
        if avg_pace < 7.0:  # Sub-7 minute miles
            if base_level in ["Beginner", "Beginner+"]:
                base_level = "Intermediate"
        elif avg_pace > 10.0:  # Slower than 10 min/mile
            if base_level in ["Advanced", "Intermediate+"]:
                base_level = "Intermediate"
        
        return base_level
    
    def _create_training_phases(self, weeks: int, base: float, peak: float) -> List[Dict]:
        """Create training phases with mileage progression"""
        if weeks == 16:
            return [
                {'phase': 'Base Building', 'weeks': '1-6', 'focus': 'Aerobic development', 'mileage_range': f"{base:.0f}-{base*1.3:.0f}"},
                {'phase': 'Build Up', 'weeks': '7-12', 'focus': 'Speed & strength', 'mileage_range': f"{base*1.3:.0f}-{peak:.0f}"},
                {'phase': 'Peak', 'weeks': '13-14', 'focus': 'Race pace practice', 'mileage_range': f"{peak:.0f}"},
                {'phase': 'Taper', 'weeks': '15-16', 'focus': 'Recovery & race prep', 'mileage_range': f"{base*0.6:.0f}-{base*0.8:.0f}"}
            ]
        elif weeks == 12:
            return [
                {'phase': 'Base Building', 'weeks': '1-4', 'focus': 'Aerobic development', 'mileage_range': f"{base:.0f}-{base*1.2:.0f}"},
                {'phase': 'Build Up', 'weeks': '5-9', 'focus': 'Speed & strength', 'mileage_range': f"{base*1.2:.0f}-{peak:.0f}"},
                {'phase': 'Peak', 'weeks': '10', 'focus': 'Race pace practice', 'mileage_range': f"{peak:.0f}"},
                {'phase': 'Taper', 'weeks': '11-12', 'focus': 'Recovery & race prep', 'mileage_range': f"{base*0.7:.0f}-{base*0.8:.0f}"}
            ]
        elif weeks == 8:
            return [
                {'phase': 'Build Up', 'weeks': '1-5', 'focus': 'Maintain & improve', 'mileage_range': f"{base:.0f}-{peak:.0f}"},
                {'phase': 'Peak', 'weeks': '6', 'focus': 'Race pace practice', 'mileage_range': f"{peak:.0f}"},
                {'phase': 'Taper', 'weeks': '7-8', 'focus': 'Recovery & race prep', 'mileage_range': f"{base*0.8:.0f}"}
            ]
        else:  # 4 weeks
            return [
                {'phase': 'Maintain', 'weeks': '1-2', 'focus': 'Maintain fitness', 'mileage_range': f"{base:.0f}"},
                {'phase': 'Taper', 'weeks': '3-4', 'focus': 'Recovery & race prep', 'mileage_range': f"{base*0.7:.0f}"}
            ]
    
    def _create_weekly_structure(self, fitness_level: str) -> Dict:
        """Define weekly training structure based on fitness level"""
        structures = {
            'Beginner': {
                'runs_per_week': 4,
                'structure': ['Easy Run', 'Rest', 'Easy Run', 'Rest', 'Tempo/Speed', 'Rest', 'Long Run']
            },
            'Beginner+': {
                'runs_per_week': 5,
                'structure': ['Easy Run', 'Tempo/Speed', 'Easy Run', 'Rest', 'Easy Run', 'Rest', 'Long Run']
            },
            'Intermediate': {
                'runs_per_week': 5,
                'structure': ['Easy Run', 'Speed Work', 'Easy Run', 'Tempo Run', 'Easy Run', 'Rest', 'Long Run']
            },
            'Intermediate+': {
                'runs_per_week': 6,
                'structure': ['Easy Run', 'Speed Work', 'Easy Run', 'Tempo Run', 'Easy Run', 'Recovery Run', 'Long Run']
            },
            'Advanced': {
                'runs_per_week': 6,
                'structure': ['Easy Run', 'Speed Work', 'Easy Run', 'Tempo Run', 'Easy Run', 'Recovery Run', 'Long Run']
            }
        }
        return structures.get(fitness_level, structures['Beginner'])
    
    def _generate_key_workouts(self, weeks: int, fitness_level: str, current_longest: float) -> List[Dict]:
        """Generate key workout progressions"""
        workouts = []
        
        # Long run progression - start from current longest run
        start_long = max(current_longest, 8)
        if weeks >= 12:
            long_runs = []
            current = start_long
            for i in range(weeks - 4):  # Leave 4 weeks for taper
                if i % 2 == 0 and current < 20:  # Increase every other week
                    current += 2
                long_runs.append(min(current, 22))
            long_runs.extend([18, 12, 8, 6])  # Taper weeks
        else:
            # Shorter timeline - more conservative
            long_runs = [start_long + i for i in range(0, min(weeks-2, 6), 2)]
            long_runs.extend([12, 8])
            
        workouts.append({
            'type': 'Long Runs',
            'progression': long_runs[:weeks],
            'notes': 'Build endurance gradually, practice race nutrition'
        })
        
        # Speed work progression based on fitness level
        if fitness_level in ['Beginner']:
            speed_workouts = [
                '4x400m @ 5K pace',
                '3x800m @ 5K pace', 
                '6x400m @ 5K pace',
                '4x800m @ 5K pace'
            ]
        elif fitness_level in ['Beginner+', 'Intermediate']:
            speed_workouts = [
                '4x800m @ 5K pace',
                '6x800m @ 5K pace', 
                '3x1600m @ 10K pace',
                '5x1000m @ 5K pace',
                '8x400m @ Mile pace'
            ]
        else:  # Advanced
            speed_workouts = [
                '6x800m @ 5K pace',
                '4x1200m @ 5K pace', 
                '3x1600m @ 10K pace',
                '8x400m @ Mile pace',
                '5x1000m @ 5K pace',
                '2x3200m @ 10K pace'
            ]
        
        workouts.append({
            'type': 'Speed Work',
            'examples': speed_workouts,
            'notes': 'Improve VO2 max and running economy'
        })
        
        return workouts
    
    def _calculate_pace_targets(self, fitness_data: Dict, goal_time: Optional[str] = None) -> Dict:
        """Calculate training pace targets"""
        current_pace = fitness_data.get('average_pace', 9.0)
        
        if goal_time:
            # Parse goal time (e.g., "3:30:00" -> 3.5 hours)
            time_parts = goal_time.split(':')
            goal_hours = float(time_parts[0]) + float(time_parts[1])/60 + float(time_parts[2])/3600
            goal_pace = (goal_hours * 60) / 26.2  # minutes per mile
        else:
            # Estimate based on current fitness
            goal_pace = current_pace * 0.95  # Assume 5% improvement
        
        return {
            'current_average_pace': current_pace,
            'goal_marathon_pace': round(goal_pace, 2),
            'easy_pace': round(goal_pace * 1.15, 2),
            'tempo_pace': round(goal_pace * 0.92, 2),
            'interval_pace': round(goal_pace * 0.85, 2),
            'long_run_pace': round(goal_pace * 1.10, 2)
        }
    
    def _generate_weekly_schedule(self, weeks: int, base_mileage: float, peak_mileage: float, fitness_level: str) -> List[Dict]:
        """Generate detailed weekly schedule"""
        schedule = []
        
        # Calculate weekly mileage progression
        mileage_progression = []
        if weeks >= 12:
            # Gradual build-up
            build_weeks = weeks - 4
            increment = (peak_mileage - base_mileage) / build_weeks
            
            for week in range(build_weeks):
                weekly_miles = base_mileage + (increment * week)
                mileage_progression.append(round(weekly_miles, 1))
            
            # Add taper weeks
            mileage_progression.extend([
                round(peak_mileage * 0.8, 1),
                round(peak_mileage * 0.6, 1),
                round(peak_mileage * 0.4, 1),
                round(peak_mileage * 0.3, 1)
            ])
        else:
            # Shorter timeline - maintain current fitness
            for week in range(weeks - 2):
                mileage_progression.append(base_mileage)
            mileage_progression.extend([
                round(base_mileage * 0.7, 1),
                round(base_mileage * 0.5, 1)
            ])
        
        # Generate weekly details
        for week_num in range(1, weeks + 1):
            weekly_miles = mileage_progression[week_num - 1] if week_num <= len(mileage_progression) else base_mileage
            
            schedule.append({
                'week': week_num,
                'total_miles': weekly_miles,
                'focus': self._get_week_focus(week_num, weeks),
                'key_workout': self._get_key_workout(week_num, weeks, fitness_level)
            })
        
        return schedule
    
    def _get_week_focus(self, week_num: int, total_weeks: int) -> str:
        """Determine weekly focus based on training phase"""
        if total_weeks >= 12:
            if week_num <= 6:
                return "Base building"
            elif week_num <= total_weeks - 4:
                return "Speed & strength"
            elif week_num <= total_weeks - 2:
                return "Race pace"
            else:
                return "Taper & recovery"
        else:
            if week_num <= total_weeks - 2:
                return "Maintain fitness"
            else:
                return "Taper & recovery"
    
    def _get_key_workout(self, week_num: int, total_weeks: int, fitness_level: str) -> str:
        """Get key workout for the week"""
        if week_num > total_weeks - 2:
            return "Easy pace runs only"
        
        workout_cycle = (week_num - 1) % 3
        
        if fitness_level in ['Beginner']:
            workouts = ["Tempo run", "Fartlek", "Hill repeats"]
        else:
            workouts = ["Interval training", "Tempo run", "Long run with pickups"]
        
        return workouts[workout_cycle]


if __name__ == "__main__":
    # Example usage
    agent = StravaMarathonAgent()
    
    # This would be replaced with actual Strava data
    sample_data = {
        'weekly_mileage': 35,
        'fitness_level': 'Intermediate',
        'longest_run': {'distance': 14}
    }
    
    plan = agent.generate_training_plan(16, sample_data, "3:45:00")
    print(json.dumps(plan, indent=2))