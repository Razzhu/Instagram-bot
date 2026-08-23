# mystery_generator.py
import random
import json
import re
from datetime import datetime, timedelta
import time

# Fallback mystery templates
MYSTERY_TEMPLATES = [
    {
        "type": "murder",
        "title": "The Locked Room Mystery",
        "setting": "A locked study in an old mansion",
        "incident": "The host was found dead in his study. The door was locked from inside.",
        "suspects": [
            "The Butler",
            "The Wife",
            "The Business Partner",
            "The Secret Lover",
            "The Rival"
        ],
        "clues": [
            "A half-empty glass of wine on the desk",
            "A letter with a threatening message",
            "Footprints leading to the window",
            "A hidden key under the rug",
            "A deleted message on the phone",
            "A torn photograph"
        ],
        "red_herrings": [
            "The wife's suspicious behavior (she was planning a surprise party)",
            "The business partner's secret meeting (it was unrelated)",
            "The butler's missing time (he was getting ice)"
        ],
        "culprit": "The Secret Lover",
        "motive": "Revenge for being betrayed",
        "method": "Poisoned the wine",
        "final_reveal": "The lover had access to the study and poisoned the wine before the host arrived."
    },
    {
        "type": "missing_person",
        "title": "The Vanishing Professor",
        "setting": "A university campus at midnight",
        "incident": "A professor disappeared from his office. His belongings are still there.",
        "suspects": [
            "The Rival Professor",
            "The Student",
            "The Dean",
            "The Caretaker",
            "The Secret Admirer"
        ],
        "clues": [
            "An open window with a torn curtain",
            "A cryptic note on the desk",
            "A campus map with a circled location",
            "A phone call log with an unknown number",
            "A hidden drawer with secret documents"
        ],
        "red_herrings": [
            "The student was there for extra credit (not the professor)",
            "The rival professor was on vacation (confirmed)",
            "The caretaker was cleaning (didn't see anything)"
        ],
        "culprit": "The Student",
        "motive": "The professor discovered the student was cheating",
        "method": "Lured the professor away with a fake meeting",
        "final_reveal": "The student called the professor to meet at the old building, where he confronted him about the cheating."
    },
    {
        "type": "stolen_object",
        "title": "The Missing Masterpiece",
        "setting": "A high-end art gallery",
        "incident": "A priceless painting disappeared from the gallery vault.",
        "suspects": [
            "The Gallery Owner",
            "The Security Guard",
            "The Art Critic",
            "The Wealthy Collector",
            "The Ex-Employee"
        ],
        "clues": [
            "A broken security camera near the vault",
            "An employee badge left behind",
            "A painting replaced with a forgery",
            "A witness who saw a suspicious person",
            "A coded message in the guest book"
        ],
        "red_herrings": [
            "The security guard was asleep (didn't see anything)",
            "The critic was writing a bad review (not the thief)",
            "The collector offered a reward (genuine interest)"
        ],
        "culprit": "The Ex-Employee",
        "motive": "Revenge for being fired",
        "method": "Used old access codes to enter the vault",
        "final_reveal": "The ex-employee never returned their key card and used it to steal the painting."
    },
    {
        "type": "hacker",
        "title": "The Digital Ghost",
        "setting": "A tech company headquarters",
        "incident": "A hacker infiltrated the company's servers and encrypted sensitive data.",
        "suspects": [
            "The IT Manager",
            "The Rival Company",
            "The Disgruntled Employee",
            "The Freelance Hacker",
            "The Corporate Spy"
        ],
        "clues": [
            "A IP address traced to the building",
            "A message demanding a ransom",
            "A hidden file with suspicious code",
            "A USB drive found in the server room",
            "A deleted email from an unknown sender"
        ],
        "red_herrings": [
            "The IT Manager's unusual login times (he was working late)",
            "The rival company's suspicious activity (legitimate business)",
            "The freelance hacker's past history (was hired by another company)"
        ],
        "culprit": "The Disgruntled Employee",
        "motive": "Revenge for being overlooked for promotion",
        "method": "Installed malware on the servers using a USB drive",
        "final_reveal": "The employee was planning to expose the company's secrets after being passed over for promotion."
    }
]

class MysteryGenerator:
    def __init__(self, groq_api_key=None):
        self.groq_api_key = groq_api_key
        self.fallback_templates = MYSTERY_TEMPLATES
    
    def generate_mystery(self, thread_id, members, difficulty="hard"):
        """Generate a complete mystery event"""
        # Try Groq first
        if self.groq_api_key:
            try:
                mystery = self._generate_with_groq(members, difficulty)
                if mystery:
                    return mystery
            except Exception as e:
                print(f"[MYSTERY] Groq generation failed: {e}")
        
        # Use fallback
        return self._generate_fallback(members, difficulty)
    
    def _generate_with_groq(self, members, difficulty):
        """Generate mystery using Groq AI"""
        # Import here to avoid circular import
        import requests
        
        # Select random real members for suspects
        suspect_count = min(5, len(members))
        selected_members = random.sample(members, suspect_count)
        
        prompt = f"""Generate a detailed interactive mystery for an Instagram group chat.

Members of the GC: {', '.join(selected_members)}

Difficulty: {difficulty.upper()}

Generate a mystery where these members are the suspects. Create fictional roles around them.

Format EXACTLY as follows:

TITLE: [Mystery title]
TYPE: [murder/missing_person/stolen_object/hacker/secret_identity]
SETTING: [Location description]
INCIDENT: [What happened]
DIFFICULTY: [easy/medium/hard/insane]

SUSPECTS:
[For each member, create a fictional role]
[member1] - [role]
[member2] - [role]
[member3] - [role]
[member4] - [role]
[member5] - [role]

MOTIVES:
[List of possible motives]

TIMELINE:
[Key timeline events]

CLUES (8-12):
[Clue descriptions]

RED_HERRINGS (3-5):
[Red herring descriptions]

TRUE_SOLUTION:
CULPRIT: [the member who is actually guilty]
MOTIVE: [why they did it]
METHOD: [how they did it]
FINAL_REVEAL: [detailed explanation]

IMPORTANT: The culprit must be ONE of the suspects listed above. Make the story complex but solvable.

Return ONLY the formatted data, no other text."""

        try:
            response = self._call_groq(prompt)
            if response:
                return self._parse_mystery_response(response, selected_members)
        except Exception as e:
            print(f"[MYSTERY] Groq error: {e}")
        
        return None
    
    def _call_groq(self, prompt):
        """Call Groq API"""
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
                "max_tokens": 800
            }
            response = requests.post(url, headers=headers, json=data, timeout=45)
            if response.status_code == 200:
                result = response.json()
                return result.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            print(f"[MYSTERY] API error: {e}")
        return None
    
    def _parse_mystery_response(self, response, members):
        """Parse Groq response into mystery data"""
        try:
            lines = response.split('\n')
            mystery = {
                'title': '',
                'type': 'murder',
                'setting': '',
                'incident': '',
                'difficulty': 'hard',
                'suspects': {},
                'motives': [],
                'timeline': [],
                'clues': [],
                'red_herrings': [],
                'culprit': '',
                'motive': '',
                'method': '',
                'final_reveal': ''
            }
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('TITLE:'):
                    mystery['title'] = line[6:].strip()
                elif line.startswith('TYPE:'):
                    mystery['type'] = line[5:].strip().lower()
                elif line.startswith('SETTING:'):
                    mystery['setting'] = line[8:].strip()
                elif line.startswith('INCIDENT:'):
                    mystery['incident'] = line[9:].strip()
                elif line.startswith('DIFFICULTY:'):
                    mystery['difficulty'] = line[11:].strip().lower()
                elif line.startswith('SUSPECTS:'):
                    current_section = 'suspects'
                elif line.startswith('MOTIVES:'):
                    current_section = 'motives'
                elif line.startswith('TIMELINE:'):
                    current_section = 'timeline'
                elif line.startswith('CLUES:'):
                    current_section = 'clues'
                elif line.startswith('RED_HERRINGS:'):
                    current_section = 'red_herrings'
                elif line.startswith('TRUE_SOLUTION:'):
                    current_section = 'solution'
                elif line.startswith('CULPRIT:'):
                    mystery['culprit'] = line[9:].strip()
                elif line.startswith('MOTIVE:'):
                    mystery['motive'] = line[7:].strip()
                elif line.startswith('METHOD:'):
                    mystery['method'] = line[7:].strip()
                elif line.startswith('FINAL_REVEAL:'):
                    mystery['final_reveal'] = line[13:].strip()
                elif line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    # List items
                    item = line.lstrip('-•* ').strip()
                    if current_section == 'suspects':
                        # Parse suspect format: "username - role"
                        if ' - ' in item:
                            name, role = item.split(' - ', 1)
                            mystery['suspects'][name.strip()] = role.strip()
                    elif current_section == 'motives':
                        mystery['motives'].append(item)
                    elif current_section == 'timeline':
                        mystery['timeline'].append(item)
                    elif current_section == 'clues':
                        mystery['clues'].append(item)
                    elif current_section == 'red_herrings':
                        mystery['red_herrings'].append(item)
            
            # Validate we have what we need
            if not mystery['title'] or not mystery['suspects']:
                return None
            
            # Ensure enough clues
            if len(mystery['clues']) < 5:
                mystery['clues'] = self._generate_fallback_clues(mystery['type'])
            
            return mystery
        except Exception as e:
            print(f"[MYSTERY] Parse error: {e}")
            return None
    
    def _generate_fallback_clues(self, mystery_type):
        """Generate fallback clues for a mystery type"""
        clue_sets = {
            'murder': [
                "A bloodstained handkerchief was found",
                "The victim had a secret meeting scheduled",
                "A witness heard an argument earlier",
                "A mysterious phone call was traced",
                "A note with a threat was discovered",
                "The victim's last meal was poisoned"
            ],
            'missing_person': [
                "A broken phone was found",
                "A car was seen leaving late",
                "A secret meeting was planned",
                "A voicemail was deleted",
                "A mysterious note was left",
                "A camera captured a shadow"
            ],
            'stolen_object': [
                "A broken lock was found",
                "A security video went blank",
                "A strange item was left behind",
                "A known thief was in the area",
                "A key was found missing",
                "A coded message was discovered"
            ],
            'hacker': [
                "A suspicious file was downloaded",
                "A server log showed unauthorized access",
                "A hidden program was installed",
                "A message was sent anonymously",
                "A backdoor was created",
                "A password was compromised"
            ]
        }
        return clue_sets.get(mystery_type, clue_sets['murder'])
    
    def _generate_fallback(self, members, difficulty):
        """Generate a fallback mystery from templates"""
        template = random.choice(self.fallback_templates)
        
        # Use real members for suspects
        suspect_count = min(5, len(members))
        selected_members = random.sample(members, suspect_count)
        
        # Create roles for real members
        role_templates = [
            "The Butler", "The Wife", "The Business Partner", 
            "The Secret Lover", "The Rival", "The Assistant",
            "The Witness", "The Journalist", "The Investigator",
            "The Caretaker", "The Student", "The Teacher"
        ]
        
        suspects = {}
        for i, member in enumerate(selected_members):
            role = role_templates[i % len(role_templates)]
            # Make it clear this is a fictional role
            suspects[member] = f"Fictional character: {role}"
        
        # Adjust difficulty
        clue_count = {
            'easy': 5,
            'medium': 8,
            'hard': 12,
            'insane': 15
        }.get(difficulty, 8)
        
        red_herring_count = {
            'easy': 1,
            'medium': 2,
            'hard': 3,
            'insane': 5
        }.get(difficulty, 2)
        
        # Generate clues
        clues = random.sample(template.get('clues', []), min(clue_count, len(template.get('clues', []))))
        while len(clues) < clue_count:
            clues.append(f"Additional clue #{len(clues)+1}")
        
        red_herrings = random.sample(template.get('red_herrings', []), min(red_herring_count, len(template.get('red_herrings', []))))
        while len(red_herrings) < red_herring_count:
            red_herrings.append(f"Red herring #{len(red_herrings)+1}")
        
        # Select culprit from suspects
        culprit = random.choice(list(suspects.keys()))
        
        return {
            'title': template['title'],
            'type': template['type'],
            'setting': template['setting'],
            'incident': template['incident'],
            'difficulty': difficulty,
            'suspects': suspects,
            'motives': template.get('motives', ['Unknown motive']),
            'timeline': template.get('timeline', ['Timeline unavailable']),
            'clues': clues,
            'red_herrings': red_herrings,
            'culprit': culprit,
            'motive': template.get('motive', 'Unknown motive'),
            'method': template.get('method', 'Unknown method'),
            'final_reveal': template.get('final_reveal', 'The mystery remains unsolved...')
              }
