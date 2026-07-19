# gitgaze.py
import re
import sys
from typing import Dict, List, Any

class GitGazeAnalyzer:
    def __init__(self):
        # Risk weights for different code operational footprints
        self.risk_keywords = {
            r"db\..*": 3,           # Database operations (High Risk)
            r"threading\..*": 4,   # Concurrency/Parallelism (Very High Risk)
            r"requests\..*": 2,     # Network calls (Medium Risk)
            r"open\(.*\)": 2        # File system operations (Medium Risk)
        }

    def analyze_diff(self, diff_content: str) -> Dict[str, Any]:
        """
        Parses a git diff/patch text input and assesses architectural risk metrics.
        """
        lines = diff_content.split('\n')
        added_lines = []
        removed_lines = []
        
        for line in lines:
            if line.startswith('+') and not line.startswith('+++'):
                added_lines.append(line[1:])
            elif line.startswith('-') and not line.startswith('---'):
                removed_lines.append(line[1:])

        total_risk_score = 0
        risk_triggers = []
        
        # Scan changes for high-risk system operations
        for line in added_lines:
            for pattern, weight in self.risk_keywords.items():
                if re.search(pattern, line):
                    total_risk_score += weight
                    risk_triggers.append(f"Detected operation matching '{pattern}' (Risk Weight: {weight})")

        # Basic code churn logic
        churn_ratio = len(added_lines) / max(len(removed_lines), 1)
        
        # Architectural classification based on risk score metrics
        if total_risk_score >= 6:
            status = "CRITICAL RISK: Requires Immediate Senior Architect Review."
        elif total_risk_score >= 3:
            status = "MEDIUM RISK: Review for side-effects recommended."
        else:
            status = "LOW RISK: Standard code modifications."

        return {
            "metrics": {
                "lines_added": len(added_lines),
                "lines_removed": len(removed_lines),
                "churn_ratio": round(churn_ratio, 2),
                "calculated_risk_score": total_risk_score
            },
            "status": status,
            "system_triggers": risk_triggers
        }

if __name__ == "__main__":
    # Simulate a raw Git diff payload passed to the tool
    mock_git_diff = """
--- a/src/user_service.py
+++ b/src/user_service.py
@@ -10,4 +10,8 @@
 def update_profile(user_id, data):
-    print("Updating database metadata locally")
+    import threading
+    db.users.update_one({"id": user_id}, {"$set": data})
+    threading.Thread(target=sync_logs).start()
+    return {"status": "success"}
     """
     
     analyzer = GitGazeAnalyzer()
     report = analyzer.analyze_diff(mock_git_diff)
     
     print("======= GITGAZE METRIC ANALYSIS =======")
     print(f"Status: {report['status']}")
     print(f"Risk Score: {report['metrics']['calculated_risk_score']}")
     print("Triggers:")
     for trigger in report['system_triggers']:
         print(f"  - {trigger}")
