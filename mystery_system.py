# mystery_system.py
import random
import time
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading

from mystery_database import *
from mystery_generator import MysteryGenerator

# Configuration
MYSTERY_CONFIG = {
    'enabled': True,
    'event_chance': 0.01,  # 1% chance per message check
    'cooldown': 3600,  # 1 hour between events
    'min_members': 4,
    'max_active_events': 1,
    'default_difficulty': 'hard',
    'time_limits': {
        'easy': 600,  # 10 minutes
        'medium': 1200,  # 20 minutes
        'hard': 1800,  # 30 minutes
        'insane': 3600  # 1 hour
    }
}

class MysterySystem:
    def __init__(self, bot, groq_api_key):
        self.bot = bot
        self.groq_api_key = groq_api_key
        self.generator = MysteryGenerator(groq_api_key)
        self.active_events = {}  # thread_id -> event data
        self.event_cooldowns = {}  # thread_id -> timestamp
        self.pending_actions = {}  # thread_id -> pending actions
        self.mystery_contexts = defaultdict(lambda: deque(maxlen=50))
        
        # Load active events from database on startup
        self._recover_events()
    
    def _recover_events(self):
        """Recover active mystery events from database"""
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT thread_id, state_json FROM mystery_events 
                WHERE active = 1 AND datetime(expires_at) > datetime('now')
            ''')
            rows = c.fetchall()
            for row in rows:
                try:
                    event_data = json.loads(row['state_json'])
                    thread_id = row['thread_id']
                    self.active_events[thread_id] = event_data
                    print(f"[MYSTERY] Recovered active event for thread {thread_id}")
                except Exception as e:
                    print(f"[MYSTERY] Recovery error: {e}")
    
    def should_start_mystery(self, thread_id, members_count):
        """Determine if a mystery should start"""
        if not MYSTERY_CONFIG['enabled']:
            return False
        
        # Check if thread already has active mystery
        if thread_id in self.active_events:
            return False
        
        # Check cooldown
        if thread_id in self.event_cooldowns:
            if time.time() - self.event_cooldowns[thread_id] < MYSTERY_CONFIG['cooldown']:
                return False
        
        # Check minimum members
        if members_count < MYSTERY_CONFIG['min_members']:
            return False
        
        # Random chance
        if random.random() > MYSTERY_CONFIG['event_chance']:
            return False
        
        return True
    
    def start_mystery(self, thread_id, members, difficulty="hard", manual=False):
        """Start a new mystery event"""
        if thread_id in self.active_events:
            return "❌ A mystery is already active in this group!"
        
        # Generate mystery
        mystery_data = self.generator.generate_mystery(thread_id, members, difficulty)
        if not mystery_data:
            return "❌ Failed to generate mystery. Try again."
        
        # Add event metadata
        event_id = f"mystery_{int(time.time())}_{thread_id[-6:]}"
        now = datetime.now().isoformat()
        time_limit = MYSTERY_CONFIG['time_limits'].get(difficulty, 1800)
        expires_at = (datetime.now() + timedelta(seconds=time_limit)).isoformat()
        
        event_data = {
            'event_id': event_id,
            'type': mystery_data.get('type', 'unknown'),
            'title': mystery_data['title'],
            'phase': 'investigation',
            'started_at': now,
            'expires_at': expires_at,
            'difficulty': difficulty,
            'suspects': mystery_data['suspects'],
            'motives': mystery_data.get('motives', []),
            'timeline': mystery_data.get('timeline', []),
            'clues': mystery_data['clues'],
            'red_herrings': mystery_data.get('red_herrings', []),
            'discovered_clues': [],
            'culprit': mystery_data['culprit'],
            'motive': mystery_data['motive'],
            'method': mystery_data['method'],
            'final_reveal': mystery_data['final_reveal'],
            'players': {},
            'accusations': {},
            'theories': {},
            'interrogations': {},
            'setting': mystery_data.get('setting', 'Unknown location'),
            'incident': mystery_data.get('incident', 'An incident occurred.'),
            'timer_start': time.time(),
            'time_limit': time_limit
        }
        
        # Save to database
        save_mystery_event(thread_id, event_data)
        
        # Store in memory
        self.active_events[thread_id] = event_data
        
        # Announce the mystery
        announcement = self._format_announcement(event_data)
        return announcement
    
    def _format_announcement(self, event_data):
        """Format the mystery announcement"""
        suspects_text = "\n".join([f"🔹 @{suspect} - {role}" for suspect, role in event_data['suspects'].items()])
        
        announcement = f"""
🕵️ **MYSTERY EVENT STARTED!**

━━━━━━━━━━━━━━━━━━
📖 **{event_data['title']}**
━━━━━━━━━━━━━━━━━━

📍 **Setting:** {event_data['setting']}

📌 **Incident:**
{event_data['incident']}

🎯 **Suspects:**
{suspects_text}

⏰ **Time Limit:** {event_data['time_limit']//60} minutes
📊 **Difficulty:** {event_data['difficulty'].upper()}

━━━━━━━━━━━━━━━━━━

**🔍 Commands:**
.mystery investigate - Search for clues
.mystery suspects - View suspects
.mystery evidence - Check evidence board
.mystery timeline - View timeline
.mystery interrogate @user - Question a suspect
.mystery theory [text] - Submit a theory
.mystery accuse @user - Make an accusation
.mystery hint - Get a hint (costs coins)

**💡 Tip:** Pay attention to contradictions and timelines!

Good luck, detectives! 🕵️
"""
        return announcement
    
    def handle_mystery_command(self, thread_id, user_id, username, command, args):
        """Handle mystery-related commands"""
        # Check if it's a start command
        if args and len(args) > 0 and args[0].lower() == 'start':
            # Check if user is admin
            if not self.bot.is_admin(username):
                return f"❌ @{username} Only admins can start mysteries!"
            
            # Check if already active
            if thread_id in self.active_events:
                return "❌ A mystery is already active!"
            
            # Get difficulty from args
            difficulty = "hard"
            if len(args) > 1 and args[1].lower() in ['easy', 'medium', 'hard', 'insane']:
                difficulty = args[1].lower()
            
            members = self.bot._get_thread_members(thread_id)
            result = self.start_mystery(thread_id, members, difficulty, manual=True)
            if result:
                # Set cooldown
                self.event_cooldowns[thread_id] = time.time()
                return result
            return "❌ Failed to start mystery."
        
        # Check if mystery is active for other commands
        if thread_id not in self.active_events:
            if command == '.mystery':
                return "❌ No active mystery in this group. Use `.mystery start` to begin one (admin only)."
            return "❌ No active mystery in this group."
        
        event = self.active_events[thread_id]
        
        # Check if mystery has expired
        if time.time() - event['timer_start'] > event['time_limit']:
            return self._handle_timeout(thread_id)
        
        # Handle subcommands
        if not args:
            return self._format_status(event)
        
        subcommand = args[0].lower()
        subargs = args[1:] if len(args) > 1 else []
        
        if subcommand == 'status':
            return self._format_status(event)
        
        elif subcommand == 'investigate':
            return self._investigate(thread_id, user_id, username, event)
        
        elif subcommand == 'suspects':
            return self._list_suspects(event)
        
        elif subcommand == 'evidence':
            return self._show_evidence(event)
        
        elif subcommand == 'timeline':
            return self._show_timeline(event)
        
        elif subcommand == 'interrogate':
            if not subargs:
                return "❌ Usage: .mystery interrogate @username"
            target = subargs[0].replace('@', '')
            return self._interrogate(thread_id, user_id, username, target, event)
        
        elif subcommand == 'theory':
            if not subargs:
                return "❌ Usage: .mystery theory [your theory]"
            theory = ' '.join(subargs)
            return self._submit_theory(thread_id, user_id, username, theory, event)
        
        elif subcommand == 'accuse':
            if not subargs:
                return "❌ Usage: .mystery accuse @username"
            target = subargs[0].replace('@', '')
            return self._accuse(thread_id, user_id, username, target, event)
        
        elif subcommand == 'hint':
            return self._give_hint(thread_id, user_id, event)
        
        elif subcommand == 'leaderboard':
            return self._get_leaderboard(thread_id)
        
        elif subcommand == 'stats':
            return self._get_stats(thread_id, user_id, username)
        
        elif subcommand == 'theories':
            return self._list_theories(event)
        
        elif subcommand == 'stop':
            if not self.bot.is_admin(username):
                return f"❌ @{username} Only admins can stop mysteries!"
            # Close the mystery
            close_mystery(thread_id, event['event_id'], solved=False)
            del self.active_events[thread_id]
            return "🛑 Mystery stopped."
        
        else:
            return f"❌ Unknown mystery command: {subcommand}\nUse `.mystery` for status or `.mystery start` to begin."
    
    def _format_status(self, event):
        """Format current mystery status"""
        elapsed = int(time.time() - event['timer_start'])
        remaining = max(0, event['time_limit'] - elapsed)
        minutes = remaining // 60
        seconds = remaining % 60
        
        discovered = len(event['discovered_clues'])
        total = len(event['clues'])
        
        status = f"""
🕵️ **MYSTERY STATUS**

━━━━━━━━━━━━━━━━━━
📖 {event['title']}
━━━━━━━━━━━━━━━━━━

📍 **Setting:** {event['setting']}
📊 **Difficulty:** {event['difficulty'].upper()}
⏰ **Time Remaining:** {minutes:02d}:{seconds:02d}
🔍 **Clues Found:** {discovered}/{total}
📌 **Phase:** {event['phase'].upper()}

**Players:** {len(event['players'])} investigators active

**Commands:**
.mystery investigate
.mystery suspects
.mystery evidence
.mystery timeline
.mystery interrogate @user
.mystery theory [text]
.mystery accuse @user
.mystery hint
"""
        return status
    
    def _investigate(self, thread_id, user_id, username, event):
        """Investigate for clues"""
        # Check if user has already investigated recently
        player_key = f"{thread_id}_{user_id}"
        if hasattr(self, '_last_investigation'):
            if player_key in self._last_investigation:
                elapsed = time.time() - self._last_investigation[player_key]
                if elapsed < 10:
                    return "⏳ Wait 10 seconds before investigating again!"
        
        # Store last investigation time
        if not hasattr(self, '_last_investigation'):
            self._last_investigation = {}
        self._last_investigation[player_key] = time.time()
        
        # Check if there are undiscovered clues
        undiscovered = [c for c in event['clues'] if c not in event['discovered_clues']]
        
        if not undiscovered:
            return "🔍 You've searched everywhere! No more clues to find."
        
        # Randomly find a clue (70% chance)
        if random.random() < 0.7:
            clue = random.choice(undiscovered)
            event['discovered_clues'].append(clue)
            
            # Track player stats
            update_mystery_player_stats(thread_id, user_id, event['event_id'], xp=5, clues=1)
            
            # Check if it's a red herring
            is_red_herring = clue in event['red_herrings']
            
            responses = [
                f"🔎 You found something!",
                f"📋 You discovered a clue!",
                f"🧐 Your investigation paid off!"
            ]
            
            response = f"{random.choice(responses)}\n\n🔹 **Clue Found:**\n{clue}"
            
            if is_red_herring:
                response += "\n\n⚠️ *This might be a red herring...*"
            
            # Save event state
            save_mystery_event(thread_id, event)
            return response
        else:
            # No clue found
            no_clue_responses = [
                "🔎 You searched thoroughly but found nothing.",
                "🤔 This place is clean... too clean?",
                "🧹 You found only dust and cobwebs.",
                "📸 You took photos for evidence, but nothing useful."
            ]
            return random.choice(no_clue_responses)
    
    def _list_suspects(self, event):
        """List suspects with their roles"""
        suspects_text = "\n".join([f"🔹 @{suspect} — {role}" for suspect, role in event['suspects'].items()])
        
        return f"""
🎯 **SUSPECTS**

{suspects_text}

**Tip:** Use `.mystery interrogate @username` to question a suspect.
"""
    
    def _show_evidence(self, event):
        """Show the evidence board"""
        if not event['discovered_clues']:
            return "📭 No evidence discovered yet. Use `.mystery investigate` to search for clues."
        
        evidence_text = "\n".join([f"🔹 {clue}" for clue in event['discovered_clues']])
        
        # Calculate unknown information
        total_clues = len(event['clues'])
        found_clues = len(event['discovered_clues'])
        remaining = total_clues - found_clues
        
        board = f"""
🗂️ **EVIDENCE BOARD**

**Discovered Evidence:**
{evidence_text}

**Clues Remaining:** {remaining}

**Unknown Questions:**
❓ Who had the opportunity?
❓ What was the motive?
❓ How was it done?

*Keep investigating to find more evidence!*
"""
        return board
    
    def _show_timeline(self, event):
        """Show the timeline"""
        if not event['timeline']:
            return "⏰ No timeline information available yet."
        
        timeline_text = "\n".join([f"⏱️ {item}" for item in event['timeline']])
        
        return f"""
⏰ **TIMELINE**

{timeline_text}

*Check for inconsistencies in the timeline!*
"""
    
    def _interrogate(self, thread_id, user_id, username, target, event):
        """Interrogate a suspect"""
        # Check if target is a suspect
        if target not in event['suspects']:
            return f"❌ @{target} is not a suspect in this mystery."
        
        # Check cooldown
        interrogate_key = f"{thread_id}_{target}"
        if hasattr(self, '_last_interrogation'):
            if interrogate_key in self._last_interrogation:
                elapsed = time.time() - self._last_interrogation[interrogate_key]
                if elapsed < 30:
                    return f"⏳ @{target} has already been questioned recently. Wait {30 - int(elapsed)}s."
        
        if not hasattr(self, '_last_interrogation'):
            self._last_interrogation = {}
        self._last_interrogation[interrogate_key] = time.time()
        
        # Generate interrogation response
        role = event['suspects'][target]
        is_culprit = target == event['culprit']
        
        interrogation_texts = [
            f"🕵️ **Interrogating @{target}**\n\nDetective: \"Where were you at the time of the incident?\"\n\n@{target}: \"I was... {random.choice(['in my room', 'at the office', 'with a friend', 'sleeping', 'working out'])}.\"\n\n*Suspicious? You decide.*",
            f"🕵️ **Interrogating @{target}**\n\nDetective: \"Did you know the victim?\"\n\n@{target} ({role}): \"{random.choice(['I barely knew them.', 'We were colleagues.', 'We were friends.', 'We had our differences.', 'I\'d rather not say.'])}\"",
            f"🕵️ **Interrogating @{target}**\n\nDetective: \"Can anyone confirm your alibi?\"\n\n@{target}: \"{random.choice(['Yes, I was with someone.', 'No, I was alone.', 'I don\'t remember.', 'Maybe...', 'That\'s none of your business!'])}\""
        ]
        
        if is_culprit:
            culprit_responses = [
                f"🕵️ **Interrogating @{target}**\n\nDetective: \"I have evidence against you.\"\n\n@{target}: \"{random.choice(['You can\'t prove anything!', 'I... I need a lawyer.', 'Okay, you caught me.', 'It wasn\'t me!', 'You\'re making a mistake.'])}\"",
                f"🕵️ **Interrogating @{target}**\n\nDetective: \"Your story doesn\'t add up.\"\n\n@{target}: *{random.choice(['looks nervous', 'avoids eye contact', 'sweats', 'starts fidgeting', 'stays silent'])}*"
            ]
            response = random.choice(culprit_responses)
        else:
            response = random.choice(interrogation_texts)
        
        # Track interrogation
        event['interrogations'][f"{target}_{int(time.time())}"] = {
            'interrogator': username,
            'question': 'Standard interrogation',
            'response': response
        }
        
        return response
    
    def _submit_theory(self, thread_id, user_id, username, theory, event):
        """Submit a theory about the mystery"""
        # Save theory
        theory_key = f"{thread_id}_{int(time.time())}"
        event['theories'][theory_key] = {
            'user': username,
            'theory': theory,
            'timestamp': time.time()
        }
        
        # Evaluate theory (simple check - does it mention the culprit?)
        is_correct = False
        if event['culprit'].lower() in theory.lower():
            is_correct = True
            # Award XP
            update_mystery_player_stats(thread_id, user_id, event['event_id'], xp=20, correct_theories=1)
        
        # Save event state
        save_mystery_event(thread_id, event)
        
        responses = [
            "🧠 Theory noted! Interesting perspective...",
            "📝 Your theory has been recorded.",
            "💭 That's a possibility...",
            "🔍 Good thinking!"
        ]
        
        response = random.choice(responses)
        if is_correct:
            response += "\n\n⚠️ *You're onto something...*"
        
        return f"{response}\n\n**Your Theory:**\n{theory}"
    
    def _accuse(self, thread_id, user_id, username, target, event):
        """Accuse a suspect"""
        if target not in event['suspects']:
            return f"❌ @{target} is not a suspect."
        
        # Check if already accused
        if f"{thread_id}_{user_id}" in event['accusations']:
            return "⚠️ You've already made an accusation!"
        
        # Check if it's the culprit
        is_correct = target == event['culprit']
        
        # Get evidence count
        evidence_found = len(event['discovered_clues'])
        total_evidence = len(event['clues'])
        
        # Calculate evidence percentage
        evidence_percentage = (evidence_found / total_evidence) * 100 if total_evidence > 0 else 0
        
        # Determine confidence based on evidence
        if evidence_percentage < 30:
            confidence = "low"
            message = "You don't have enough evidence yet!"
        elif evidence_percentage < 60:
            confidence = "medium"
            message = "You have some evidence, but more is needed!"
        else:
            confidence = "high"
            message = "You have strong evidence!"
        
        if is_correct:
            # Case solved!
            event['phase'] = 'solved'
            update_mystery_player_stats(thread_id, user_id, event['event_id'], xp=100, correct_accusations=1)
            
            # Update overall stats
            with get_db() as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO mystery_stats (thread_id, user_id, total_mystery_xp, cases_solved, correct_accusations)
                    VALUES (?, ?, 100, 1, 1)
                    ON CONFLICT(thread_id, user_id) DO UPDATE SET
                        total_mystery_xp = total_mystery_xp + 100,
                        cases_solved = cases_solved + 1,
                        correct_accusations = correct_accusations + 1
                ''', (thread_id, user_id))
                conn.commit()
            
            # Close the mystery
            close_mystery(thread_id, event['event_id'], solved=True, culprit=target, solution=event['final_reveal'])
            
            return self._format_final_reveal(event, username, target)
        else:
            # Wrong accusation
            update_mystery_player_stats(thread_id, user_id, event['event_id'], wrong_accusations=1)
            
            # Penalty
            penalties = [
                "❌ **WRONG ACCUSATION!**\n\nThe evidence doesn't support your claim.",
                "❌ **MISTAKEN IDENTITY!**\n\nYour accusation was incorrect.",
                "❌ **FALSE ACCUSATION!**\n\nYou've accused the wrong person."
            ]
            
            response = random.choice(penalties)
            response += f"\n\n@{target} is NOT the culprit."
            response += f"\n\n**Evidence Confidence:** {evidence_percentage:.0f}%"
            response += f"\n**Status:** {message}"
            response += "\n\n*Continue investigating...*"
            
            # Save the accusation
            event['accusations'][f"{thread_id}_{user_id}"] = {
                'accuser': username,
                'accused': target,
                'correct': False,
                'timestamp': time.time()
            }
            
            return response
    
    def _format_final_reveal(self, event, username, target):
        """Format the final reveal"""
        reveal = f"""
━━━━━━━━━━━━━━━━━━
🕵️ **CASE CLOSED!**
━━━━━━━━━━━━━━━━━━

🏆 **The mystery has been solved!**

**Solved by:** @{username}

**CULPRIT:** @{target}

**MOTIVE:**
{event['motive']}

**METHOD:**
{event['method']}

**THE TRUTH:**
{event['final_reveal']}

━━━━━━━━━━━━━━━━━━

**Key Evidence:**
"""
        # Add key evidence
        for clue in event['discovered_clues'][:5]:
            reveal += f"\n🔹 {clue}"
        
        reveal += f"""

**Congratulations, Detective! 🎉**

*The case is now closed.*
"""
        return reveal
    
    def _give_hint(self, thread_id, user_id, event):
        """Give a hint (costs coins)"""
        # Check if user has enough coins
        from database import get_user_data, add_coins
        user_data = get_user_data(user_id, thread_id)
        
        if user_data['coins'] < 50:
            return "❌ You need 50 coins for a hint!"
        
        # Deduct coins
        add_coins(user_id, thread_id, -50)
        
        # Generate hint based on progress
        discovered = len(event['discovered_clues'])
        total = len(event['clues'])
        
        if discovered < total * 0.3:
            hint = "💡 **Hint:** Start by investigating all the suspects. Use `.mystery investigate` to search for clues."
        elif discovered < total * 0.6:
            hint = f"💡 **Hint:** You've found {discovered}/{total} clues. Focus on the timeline and look for inconsistencies."
        else:
            hint = "💡 **Hint:** You're close! Think about who had the opportunity and motive. The culprit is among the suspects."
            # If they've found most clues, give a stronger hint
            if discovered > total * 0.8:
                hint += f"\n\n🔍 **Strong Hint:** Look closely at @{event['culprit']}'s story."
        
        return f"💡 **Hint Unlocked!**\n\n{hint}\n\n*Cost: 50 coins*"
    
    def _handle_timeout(self, thread_id):
        """Handle mystery timeout"""
        if thread_id not in self.active_events:
            return "No active mystery found."
        
        event = self.active_events[thread_id]
        
        # Close the mystery
        close_mystery(thread_id, event['event_id'], solved=False)
        
        reveal = f"""
⏰ **TIME'S UP!**

The mystery has expired.

**CULPRIT:** @{event['culprit']}

**MOTIVE:**
{event['motive']}

**METHOD:**
{event['method']}

**THE TRUTH:**
{event['final_reveal']}

*Better luck next time, detectives!*
"""
        # Remove from active events
        del self.active_events[thread_id]
        
        return reveal
    
    def _get_leaderboard(self, thread_id):
        """Get mystery leaderboard"""
        results = get_mystery_leaderboard(thread_id)
        
        if not results:
            return "📭 No mystery stats available yet. Start a mystery to earn XP!"
        
        board = "🏆 **MYSTERY LEADERBOARD**\n\n"
        for i, row in enumerate(results, 1):
            # Get username
            username = self.bot.get_username_cached(row['user_id']) or f"User{row['user_id'][:8]}"
            
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            board += f"{emoji} @{username} — {row['total_mystery_xp']} Mystery XP\n"
            board += f"   🏅 {row['best_rank']} | Solved: {row['cases_solved']}\n\n"
        
        return board
    
    def _get_stats(self, thread_id, user_id, username):
        """Get player mystery stats"""
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT * FROM mystery_stats
                WHERE thread_id = ? AND user_id = ?
            ''', (thread_id, user_id))
            row = c.fetchone()
        
        if not row:
            return f"📊 **@{username}**\n\nNo mystery stats yet. Join a mystery to earn XP!"
        
        stats = f"""
🕵️ **MYSTERY STATS**
**@{username}**

**Rank:** {row['best_rank']}
**Mystery XP:** {row['total_mystery_xp']}
**Cases Solved:** {row['cases_solved']}
**Clues Found:** {row['clues_found']}
**Correct Accusations:** {row['correct_accusations']}
**Wrong Accusations:** {row['wrong_accusations']}

**🏅 Ranks:**
0-100: Rookie
101-300: Investigator
301-600: Detective
601-1000: Senior Detective
1001-2000: Master Detective
2001+: Sherlock
"""
        return stats
    
    def _list_theories(self, event):
        """List all theories submitted"""
        if not event['theories']:
            return "📭 No theories submitted yet."
        
        theories_text = ""
        for key, data in list(event['theories'].items())[-5:]:  # Show last 5
            theories_text += f"🔹 @{data['user']}: {data['theory']}\n\n"
        
        return f"🧠 **THEORIES**\n\n{theories_text}"
    
    def handle_natural_query(self, thread_id, user_id, username, message):
        """Handle natural language mystery queries"""
        if thread_id not in self.active_events:
            return None
        
        event = self.active_events[thread_id]
        
        # Check for mystery-related natural language
        mystery_keywords = ['mystery', 'case', 'clue', 'suspect', 'investigate', 'interrogate', 
                           'evidence', 'timeline', 'theory', 'accuse', 'murder', 'crime', 
                           'detective', 'investigation', 'who', 'what happened', 'kisne', 'kaun']
        
        if not any(keyword in message.lower() for keyword in mystery_keywords):
            return None
        
        # Check for specific queries
        if 'interrogate' in message.lower() or 'puch' in message.lower() or 'ask' in message.lower():
            # Try to extract a name
            words = message.split()
            for word in words:
                if word.startswith('@'):
                    target = word[1:]
                    if target in event['suspects']:
                        return self._interrogate(thread_id, user_id, username, target, event)
        
        if 'clue' in message.lower() or 'evidence' in message.lower() or 'search' in message.lower():
            return self._investigate(thread_id, user_id, username, event)
        
        if 'suspect' in message.lower() or 'who' in message.lower():
            return self._list_suspects(event)
        
        if 'timeline' in message.lower():
            return self._show_timeline(event)
        
        # Default response for mystery-related queries
        responses = [
            "🕵️ Keep investigating! Use `.mystery investigate` to search for clues.",
            "🔍 Every clue matters. Check the evidence board with `.mystery evidence`.",
            "💡 The truth is somewhere. Try interrogating suspects with `.mystery interrogate @user`."
        ]
        return random.choice(responses)
    
    def on_message(self, thread_id, user_id, username, message):
        """Called when a message is received"""
        # Handle natural queries
        response = self.handle_natural_query(thread_id, user_id, username, message)
        if response:
            return response
        
        return None

# Create global mystery system instance (will be initialized by bot)
mystery_system = None
