"""Drill library — curated drills with embedded video links."""

DRILLS = [
    {
        "id": "slice_fix",
        "title": "Slice Fix — Headcover Drill",
        "category": "Driver",
        "level": "Beginner",
        "duration": "10 min",
        "description": "Place a headcover under your right armpit (lead arm for lefties). Hit 20 half-swings keeping the headcover pinned. Trains connection between arms and body.",
        "video": "https://www.youtube.com/watch?v=vY7kjWFDBdg",
        "tags": ["slice", "right miss", "driver", "path"],
        "reps": "20 swings × 2 sets",
    },
    {
        "id": "gate_drill",
        "title": "Gate Drill — Strike Center",
        "category": "Driver / Irons",
        "level": "Beginner",
        "duration": "10 min",
        "description": "Place two tees just outside the heel and toe of your clubhead at address. Make swings without hitting the tees. Builds center-face contact and consistent path.",
        "video": "https://www.youtube.com/watch?v=4M8YtYUZ-A0",
        "tags": ["contact", "smash factor", "driver"],
        "reps": "15 reps",
    },
    {
        "id": "lag_putt",
        "title": "Lag Putting — Ladder Drill",
        "category": "Putting",
        "level": "All",
        "duration": "15 min",
        "description": "Place tees at 10/20/30/40 ft. Hit 3 balls from each. Goal: each ball stops within 3 ft of the next tee. Trains distance control.",
        "video": "https://www.youtube.com/watch?v=oKWE2pHX4Hc",
        "tags": ["putting", "3-putt", "lag", "distance"],
        "reps": "3 balls × 4 distances",
    },
    {
        "id": "gate_putt",
        "title": "Putting Gate — Make 25 Straight",
        "category": "Putting",
        "level": "All",
        "duration": "10 min",
        "description": "Two tees barely wider than the ball, 4 ft from cup. Make 25 in a row without touching a tee. Resets tempo and start line.",
        "video": "https://www.youtube.com/watch?v=q-XQ-ZHYHbE",
        "tags": ["putting", "short", "make percentage"],
        "reps": "25 in a row",
    },
    {
        "id": "wedge_ladder",
        "title": "Wedge Ladder — 75/85/95/105",
        "category": "Wedges",
        "level": "Intermediate",
        "duration": "20 min",
        "description": "Hit 5 wedges at each yardage: 75, 85, 95, 105 yards. Track which lands within 10 ft. Builds scoring distance control.",
        "video": "https://www.youtube.com/watch?v=oVH06p-K8Ek",
        "tags": ["wedge", "scoring", "approach", "GIR"],
        "reps": "5 shots × 4 distances",
    },
    {
        "id": "stack_overspeed",
        "title": "TheStack — Overspeed Set (20g)",
        "category": "Speed",
        "level": "All",
        "duration": "8 min",
        "description": "Use the 20g (Green) Stack weight. 8 max-effort swings, 30s rest between. Trains your nervous system to swing faster.",
        "video": "https://www.youtube.com/watch?v=gB5_1l-BnEk",
        "tags": ["speed", "stack", "distance"],
        "reps": "8 swings",
    },
    {
        "id": "tempo_18",
        "title": "Tempo Drill — 1-2-3 Count",
        "category": "Full Swing",
        "level": "All",
        "duration": "10 min",
        "description": "Count '1-2' going back and '3' on downswing. 3:1 ratio. Use a metronome at 76 BPM (tour avg). Smooths transition and rhythm.",
        "video": "https://www.youtube.com/watch?v=yPVx-Em6_W0",
        "tags": ["tempo", "consistency", "transition"],
        "reps": "20 swings",
    },
    {
        "id": "warmup_5",
        "title": "5-Minute Pre-Round Warm-Up",
        "category": "Warm-Up",
        "level": "All",
        "duration": "5 min",
        "description": "10 putts (3 ft, 6 ft, lag). 5 wedges (50 yds). 3 mid-irons (7i). 3 hybrids/3W. 3 drivers. Stretch in between. Walk to first tee.",
        "video": "https://www.youtube.com/watch?v=LQ8C5UpJJpQ",
        "tags": ["warm-up", "pre-round"],
        "reps": "Once, before round",
    },
    {
        "id": "footwork_balance",
        "title": "Feet-Together Half Swings",
        "category": "Full Swing",
        "level": "Beginner",
        "duration": "10 min",
        "description": "Stand with feet together. Hit 7-iron half swings 50 yds. Forces center-pivot and balance. Cures over-the-top moves and lateral sway.",
        "video": "https://www.youtube.com/watch?v=qF8NfxJgfPs",
        "tags": ["balance", "consistency", "left miss"],
        "reps": "20 swings",
    },
    {
        "id": "bunker_basic",
        "title": "Bunker — Splash Drill",
        "category": "Short Game",
        "level": "Intermediate",
        "duration": "15 min",
        "description": "Draw a line in the sand. Splash sand 1 inch behind the line every time, no ball. Then add ball on the line. Trains entry point.",
        "video": "https://www.youtube.com/watch?v=tA8OIyvzc8c",
        "tags": ["bunker", "sand", "short game"],
        "reps": "15 swings",
    },
]


def find_drills_for(tags: list) -> list:
    """Return drills matching any of the provided tags."""
    tags_lower = {t.lower() for t in tags}
    return [d for d in DRILLS if any(t in tags_lower for t in d["tags"])]


def by_category(cat: str) -> list:
    return [d for d in DRILLS if d["category"].lower() == cat.lower()]
