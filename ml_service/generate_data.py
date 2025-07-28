# ticketing_system/ml_service/generate_data.py
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

def generate_synthetic_ticket_data(num_records=1000):
    """Generates synthetic data for ticket resolution time estimation."""

    categories = ['Software', 'Hardware', 'Network', 'Account', 'Other']
    priorities = ['Low', 'Medium', 'High', 'Critical']
    
    data = []
    for i in range(num_records):
        ticket_id = i + 1
        category = random.choice(categories)
        priority = random.choice(priorities)
        
        # Base duration in hours (e.g., 2 hours)
        base_duration = random.uniform(1, 10) 

        # Adjust duration based on category
        if category == 'Hardware':
            base_duration += random.uniform(5, 15)
        elif category == 'Network':
            base_duration += random.uniform(3, 10)
        elif category == 'Software':
            base_duration += random.uniform(2, 8)
        elif category == 'Account': # Fixed typo for category
            base_duration += random.uniform(1, 5) 
        elif category == 'Other':
            base_duration += random.uniform(0, 3)

        # Adjust duration based on priority
        if priority == 'Medium':
            base_duration *= 1.5
        elif priority == 'High':
            base_duration *= 2.5
        elif priority == 'Critical':
            base_duration *= 4.0

        num_comments = random.randint(0, 15)
        base_duration += num_comments * 0.5 # Each comment adds 0.5 hours

        is_reopened = random.choice([True, False, False, False]) # More likely to be False
        if is_reopened:
            base_duration *= 1.5 # Reopened tickets take longer

        # Add some randomness (noise)
        resolution_duration_hours = max(0.5, base_duration + random.uniform(-2, 2))
        
        created_at = datetime.now() - timedelta(days=random.randint(1, 365), hours=random.randint(1,24))

        data.append([
            ticket_id,
            f"Ticket {ticket_id}: Issue with {category} system",
            f"Detailed description for {category} problem with priority {priority}.",
            category,
            priority,
            created_at,
            num_comments,
            is_reopened,
            round(resolution_duration_hours, 2)
        ])

    df = pd.DataFrame(data, columns=[
        'ticket_id', 'title', 'description', 'category', 'priority', 
        'created_at', 'num_comments', 'is_reopened', 'resolution_duration_hours'
    ])
    return df

if __name__ == "__main__":
    # Pastikan direktori data ada
    output_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(output_dir, exist_ok=True)
    
    output_file_path = os.path.join(output_dir, 'synthetic_tickets_data.csv')
    
    df = generate_synthetic_ticket_data(num_records=2000) # Generate 2000 sample tickets
    df.to_csv(output_file_path, index=False)
    print(f"Synthetic dataset '{os.path.basename(output_file_path)}' created successfully in {output_dir}/.")