import csv
import json
from models import Challenge, Badge
CHALLENGES_FILE = "C:\\Users\\ANIRBAN\\Desktop\\wellness challenge\\data\\exercises.csv"
QUOTES_FILE = "C:\\Users\\ANIRBAN\\Desktop\\wellness challenge\\data\\quotes.csv"
def load_challenges(filename):
    challenges = []
    with open(filename, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            challenges.append(row)
    return challenges

def load_quotes(filename):
    quotes = []
    with open(filename, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            quotes.append(row)
    return quotes

def load_badges(filename):
    with open(filename, encoding='utf-8') as f:
        return json.load(f)

def export_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def import_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_challenges(challenge_rows):
    fieldnames = ["title", "description", "difficulty", "equipment", "body_part"]
    with open(CHALLENGES_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(challenge_rows)

def save_quotes(quotes_rows):
    fieldnames = ["text", "author", "category"]
    with open(QUOTES_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(quotes_rows)