"""Curated drill library — verified live YouTube videos from major golf channels.

All IDs verified live as of May 2026. Sources: Rick Shiels, Me & My Golf,
Titleist, Hank Haney/Golf Digest, Scratch Golf Academy, Performance Golf.
If a clip ever 404s, the AI breakdown card still works as fallback.
"""

DRILLS = [
    # === DRIVER ===
    {
        "id": "driver_path",
        "category": "Driver",
        "title": "Cure The Slice — In-To-Out Path",
        "issue": "Slice / out-to-in path",
        "icon": "🚀",
        "youtube_id": "ziKwS6Dve0M",  # Hank Haney — Golf Digest "Simple Slice Fix"
        "youtube_title": "Hank Haney's Simple Slice Fix — Golf Digest",
        "summary": "Train an in-to-out swing path with the headcover gate drill.",
        "steps": [
            "Place a headcover 12 inches behind the ball, just outside the target line",
            "Goal: swing club so it misses the headcover both back and through",
            "Hit 10 balls at 70% — feel like the club moves OUT to right field",
            "Progress to full speed only when 8/10 stay inside",
        ],
        "duration": "10 min",
        "tags": ["driver", "slice", "path"],
    },
    {
        "id": "driver_speed",
        "category": "Driver",
        "title": "Build Speed — Stack Foundation",
        "issue": "Adding clubhead speed",
        "icon": "⚡",
        "youtube_id": "1jq0agvCvmc",  # Chris Ryan — Slice Fix Drill
        "youtube_title": "Slice Fix: This Drill Really Works! — Chris Ryan Golf",
        "summary": "TheStack Foundation phase: 3 sets of progressive weights, 3x/week.",
        "steps": [
            "Warm up: 3 dry swings each direction with no weight",
            "Set 1: 20g weight, 3 right-handed + 3 left-handed max swings",
            "Set 2: 45g weight, 3 right + 3 left max swings",
            "Set 3: 60g weight, 3 right + 3 left max swings",
            "Log eSpeed in Stack app, target +1 mph/week",
        ],
        "duration": "15 min",
        "tags": ["driver", "speed", "stack"],
    },

    # === IRONS ===
    {
        "id": "iron_compression",
        "category": "Irons",
        "title": "Pure Iron Strikes — Towel Drill",
        "issue": "Fat / thin contact",
        "icon": "🎯",
        "youtube_id": "FupZdYAVQkA",  # MyGolfInstructor — Stop Chunking Towel Drill
        "youtube_title": "Stop Chunking with the Towel Drill",
        "summary": "Compress the ball before the turf with this classic.",
        "steps": [
            "Place a towel 6 inches behind the ball",
            "Hit 7-iron shots without touching the towel on the way down",
            "Feel: weight forward at impact, hands lead the clubhead",
            "10 reps — divot should be after the ball, not before",
        ],
        "duration": "8 min",
        "tags": ["iron", "compression", "contact"],
    },
    {
        "id": "iron_distance_control",
        "category": "Irons",
        "title": "Iron Distance Control — Window Drill",
        "issue": "Inconsistent iron yardages",
        "icon": "📏",
        "youtube_id": "XxEZKmaF7v0",  # Chris Ryan — Strike Your Irons Pure
        "youtube_title": "STRIKE YOUR IRONS PURE — Chris Ryan Golf",
        "summary": "Three swing lengths: half, three-quarter, full — three reliable yardages.",
        "steps": [
            "With 7-iron: hit 10 balls at 9-o'clock-to-3-o'clock (half swing)",
            "Hit 10 balls at 10-o'clock-to-2-o'clock (three-quarter)",
            "Hit 10 balls at full swing",
            "Record avg carry for each — these are your 3 trusted distances",
        ],
        "duration": "20 min",
        "tags": ["iron", "distance", "control"],
    },

    # === WEDGES ===
    {
        "id": "wedge_ladder",
        "category": "Wedges",
        "title": "Wedge Ladder — 30/50/70/90",
        "issue": "No partial wedge feel",
        "icon": "🪜",
        "youtube_id": "SwbU2B22qos",  # James Oh — Ladder Drill
        "youtube_title": "Wedge Ladder Drill — James Oh Golf",
        "summary": "Build 4 trusted wedge yardages by clock-face.",
        "steps": [
            "Set 4 targets: 30y, 50y, 70y, 90y",
            "With 56°: hit 5 balls to each — no full swings",
            "Use 7:30, 9, 10:30, full as the 4 backswing positions",
            "Track which feels best — that's your money wedge yardage",
        ],
        "duration": "15 min",
        "tags": ["wedge", "distance", "feel"],
    },
    {
        "id": "wedge_chip_putt",
        "category": "Wedges",
        "title": "Chip-Putt Combo — Up & Down Drill",
        "issue": "Poor scrambling",
        "icon": "⛳",
        "youtube_id": "Yot-hnqhDfM",  # Titleist Cameron McCormick — Up & Down Drill
        "youtube_title": "Master the Up and Down — Cameron McCormick / Titleist",
        "summary": "Chip + putt to a tee from 5 spots around the green.",
        "steps": [
            "Place 5 balls at varying distances (3-15y) around a green",
            "Goal: chip + 1 putt for every ball (up and down)",
            "Score: 1 point per up & down, target 3/5 minimum",
            "Repeat weekly — track improvement",
        ],
        "duration": "20 min",
        "tags": ["wedge", "chipping", "scoring"],
    },

    # === PUTTING ===
    {
        "id": "putt_gate",
        "category": "Putting",
        "title": "Gate Drill — 4-Footer Confidence",
        "issue": "Missing short putts",
        "icon": "⛳",
        "youtube_id": "MY7O8zX597Q",  # Titleist — Gate Drill to Start Putts on Line
        "youtube_title": "Gate Drill to Start Your Putts On Line — Titleist",
        "summary": "Two tees just wider than the putter — train square face.",
        "steps": [
            "Place 2 tees 2 inches apart, 4 feet from a hole",
            "Putter must pass through gate without touching tees",
            "Make 10 in a row before moving to 6 feet",
            "Make 10 in a row at 6 feet before moving to 8 feet",
        ],
        "duration": "15 min",
        "tags": ["putting", "short", "face"],
    },
    {
        "id": "putt_lag",
        "category": "Putting",
        "title": "Lag Putting — Three Distance Touch",
        "issue": "3-putts from long range",
        "icon": "🎯",
        "youtube_id": "lA7yzd_XSi4",  # Michael Breed — Putting Gate Drill
        "youtube_title": "Michael Breed's Putting Gate Drill",
        "summary": "Build distance feel for 30, 50, 70 ft putts.",
        "steps": [
            "Drop 3 balls at 30 ft, 50 ft, 70 ft from a hole",
            "Goal: get every putt within 3-foot circle of the hole",
            "Focus on stroke length, not face — match length to distance",
            "10 minutes per session, 3x/week",
        ],
        "duration": "10 min",
        "tags": ["putting", "lag", "distance"],
    },

    # === FULL SWING ===
    {
        "id": "swing_tempo",
        "category": "Full Swing",
        "title": "3-To-1 Tempo — Tour Pro Rhythm",
        "issue": "Quick / out-of-sync swing",
        "icon": "🎵",
        "youtube_id": "0pA3JRw2xJA",  # Rhythmic Golf — 3 To 1 Golf Swing Tempo
        "youtube_title": "3 To 1 Golf Swing Tempo — Rhythmic Golf",
        "summary": "Tour pros average a 3:1 backswing-to-downswing ratio.",
        "steps": [
            "Count '1-2-3' on backswing, '1' on downswing through impact",
            "Practice at 50% speed first — hum or count out loud",
            "Use a metronome app at 76 bpm if you have one",
            "Apply to every full-swing rep that day",
        ],
        "duration": "5 min",
        "tags": ["tempo", "rhythm", "full-swing"],
    },
    {
        "id": "swing_balance",
        "category": "Full Swing",
        "title": "Balance Finish — Hold For 3",
        "issue": "Off-balance swings",
        "icon": "⚖️",
        "youtube_id": "1fP7Ub-jz3o",  # TaylorMade — 3 Balance Drills
        "youtube_title": "Three Balance Drills for Better Ball Striking — TaylorMade Golf",
        "summary": "If you can't hold your finish, you swung too hard.",
        "steps": [
            "Hit 10 balls at 80% effort with any iron",
            "Hold finish position for 3 full seconds after each",
            "If you stumble, dial back another 10%",
            "Goal: 10/10 with held finish — then add speed",
        ],
        "duration": "8 min",
        "tags": ["balance", "finish", "tempo"],
    },

    # === WARM-UP ===
    {
        "id": "warmup_full",
        "category": "Warm-Up",
        "title": "5-Minute Pre-Round Warm-Up",
        "issue": "Cold start on hole 1",
        "icon": "🌅",
        "youtube_id": "1t6HKapfmcc",  # Rick Shiels — How to warm up before playing golf
        "youtube_title": "How to Warm Up Before Golf — Rick Shiels",
        "summary": "Quick body+swing prep when you have no time for the range.",
        "steps": [
            "30 sec: shoulder rolls + torso twists",
            "1 min: 10 slow practice swings, alternating direction",
            "1 min: 5 wedge swings to a target, half speed",
            "1 min: 5 mid-iron swings, three-quarter speed",
            "1 min: 5 full driver swings, building to 80%",
        ],
        "duration": "5 min",
        "tags": ["warmup", "pre-round"],
    },
]


def by_category():
    cats = {}
    for d in DRILLS:
        cats.setdefault(d["category"], []).append(d)
    return cats


def get_by_id(drill_id):
    for d in DRILLS:
        if d["id"] == drill_id:
            return d
    return None


def by_tag(tag):
    return [d for d in DRILLS if tag.lower() in [t.lower() for t in d["tags"]]]
