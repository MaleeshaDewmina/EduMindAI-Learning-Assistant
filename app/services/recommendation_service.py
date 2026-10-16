"""Rule-based learning recommendations derived from *recorded app behaviour*.

No claim is made that these rules diagnose or measure psychological motivation.
"""


def generate_recommendation(metrics, motivation):
    total = metrics["total_tasks"]
    completed = metrics["completed_tasks"]
    completion_rate = metrics["completion_rate"]
    pending = metrics["pending_tasks"]
    overdue = metrics["overdue_tasks"]
    engagement = motivation["engagement_score"]
    consistency = motivation["consistency_score"]

    if total == 0:
        return {
            "feedback_type": "GettingStarted",
            "message": "You have not created any study tasks yet.",
            "recommendation": (
                "Set one small, achievable study goal with a deadline. "
                "After completing it, reflect on the approach that worked for you."
            ),
        }

    if overdue > 0:
        return {
            "feedback_type": "Deadline",
            "message": f"You have {overdue} overdue task(s) in your study planner.",
            "recommendation": (
                "Review the deadlines and break one overdue task into manageable steps. "
                "Adjust the deadline if appropriate, and restart with a clear next action."
            ),
        }

    if completed == total:
        return {
            "feedback_type": "Progress",
            "message": "All of your currently recorded study tasks have been completed.",
            "recommendation": (
                "Recognise the strategies that helped you finish them. "
                "When ready, set a new, realistic goal to build on your progress."
            ),
        }

    if completion_rate < 40 and pending > 0:
        return {
            "feedback_type": "Progress",
            "message": (
                f"You have completed {completed} of {total} tasks. "
                "There is room to make progress on your remaining plan."
            ),
            "recommendation": (
                "Choose one pending task and work on a small part of it today. "
                "Small, consistent steps are more manageable than trying to finish everything at once."
            ),
        }

    if engagement < 40:
        return {
            "feedback_type": "Engagement",
            "message": "There have been relatively few recorded EduMind AI interactions recently.",
            "recommendation": (
                "You can use the planner to record study milestones when useful. "
                "Limited app activity does not necessarily mean limited studying or motivation."
            ),
        }

    if consistency < 40:
        return {
            "feedback_type": "Consistency",
            "message": "Recorded EduMind AI activity was spread across relatively few recent days.",
            "recommendation": (
                "Consider a sustainable routine for updating your study plan. "
                "This indicator reflects app use rather than all of your study activity."
            ),
        }

    return {
        "feedback_type": "Progress",
        "message": "Your recorded tasks show continued progress on your study plan.",
        "recommendation": (
            "Keep adjusting your next steps as you learn. Reflect on challenges, "
            "useful strategies, and improvements you can try."
        ),
    }
