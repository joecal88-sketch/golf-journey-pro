"""High-level summary used by the dashboard."""
import pandas as pd
from cloud_storage import load_data


def get_summary() -> dict:
    data = load_data()
    rounds_list = data.get("rounds", [])
    practice_list = data.get("practice", [])
    speed_list = data.get("speed", [])

    result = {
        "rounds_count": 0,
        "best_score": None,
        "avg_score": None,
        "improvement": None,
        "focus_area": "Start logging rounds to get personalized recommendations.",
        "top_club": None,
        "practice_count": len(practice_list),
        "speed_sessions": len(speed_list),
        "latest_espeed": None,
    }

    if rounds_list:
        df = pd.DataFrame(rounds_list)
        if "score" in df.columns:
            df["score"] = pd.to_numeric(df["score"], errors="coerce")
            df["par"] = pd.to_numeric(df.get("par", pd.Series([70] * len(df))), errors="coerce")
            full = df[df["par"] >= 65].dropna(subset=["score"])
            if len(full):
                result["rounds_count"] = len(full)
                result["best_score"] = int(full["score"].min())
                result["avg_score"] = round(full["score"].mean(), 1)
                if len(full) >= 2:
                    result["improvement"] = round(
                        float(full["score"].iloc[-1]) - float(full["score"].iloc[0]), 1
                    )
                gir = next((c for c in full.columns if "gir" in c.lower()), None)
                putts = next((c for c in full.columns if "putt" in c.lower()), None)
                if gir and pd.to_numeric(full[gir], errors="coerce").mean() < 5:
                    result["focus_area"] = "Approach shots — your GIR is below 5/round. Wedge ladder drill (75-105 yds) will save 2 strokes."
                elif putts and pd.to_numeric(full[putts], errors="coerce").mean() > 32:
                    result["focus_area"] = "Putting — averaging over 32 putts/round. Lag drill (10/20/30/40 ft) will cut 3-putts."
                else:
                    result["focus_area"] = "Driver accuracy — your scoring shots are sharp. Lock in fairway position with the gate drill."

    if speed_list:
        sdf = pd.DataFrame(speed_list)
        if "driver_speed" in sdf.columns:
            vals = pd.to_numeric(sdf["driver_speed"], errors="coerce").dropna()
            if len(vals):
                result["latest_espeed"] = float(vals.iloc[-1])

    if practice_list:
        pdf = pd.DataFrame(practice_list)
        cc = next((c for c in pdf.columns if "club" in c.lower()), None)
        if cc and len(pdf):
            result["top_club"] = pdf[cc].value_counts().index[0]

    return result
