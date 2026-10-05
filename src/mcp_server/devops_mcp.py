"""
FastMCP Tool Server — Azure DevOps Sprint Data

Exposes Azure DevOps sprint data via the Model Context Protocol (MCP).
In a real environment, these tools would call the Azure DevOps REST API
(free tier). Here they serve from local mock JSON exports.

Tools:
  - get_sprint_status(project_id) — Current sprint metrics for a project
  - get_all_sprint_statuses() — Sprint metrics for all active projects
  - get_work_items(project_id) — Work items in the current sprint
  - get_sprint_burndown(project_id) — Burndown data for the sprint
  - get_team_members(project_id) — Team members assigned to a project

STEP UP: Replace local JSON reads with Azure DevOps REST API calls:
  GET https://dev.azure.com/{org}/{project}/_apis/work/teamsettings/iterations?api-version=7.0
  GET https://dev.azure.com/{org}/{project}/_apis/wit/workitems?api-version=7.0
"""
from fastmcp import FastMCP
import json
import os
import logging

logger = logging.getLogger("IntelligentDeliveryAgent")

# Create FastMCP server
mcp = FastMCP("DevOpsServer")

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "mock_devops.json")


def load_devops_data():
    """Load DevOps sprint data from local JSON export."""
    if not os.path.exists(DATA_PATH):
        logger.warning(f"[MCP] DevOps data file not found: {DATA_PATH}")
        return []
    with open(DATA_PATH, "r") as f:
        return json.load(f)


@mcp.tool()
def get_sprint_status(project_id: str) -> str:
    """
    Get the current sprint status for a given project ID.
    Returns sprint velocity, bug counts, blocker count, and story point completion.

    STEP UP: In production, calls Azure DevOps REST API:
    GET https://dev.azure.com/{org}/{project}/_apis/work/teamsettings/iterations?$timeframe=current
    """
    logger.info(f"[MCP Tool] get_sprint_status called for project_id={project_id}")
    data = load_devops_data()
    for item in data:
        if item.get("projectId") == project_id:
            # Return sprint summary without work items (use get_work_items for details)
            summary = {k: v for k, v in item.items() if k != "workItems"}
            return json.dumps(summary)
    return json.dumps({"error": f"Project {project_id} not found in DevOps data."})


@mcp.tool()
def get_all_sprint_statuses() -> str:
    """
    Get sprint status for all active projects.
    Returns an array of sprint summaries (without work item details).
    """
    logger.info("[MCP Tool] get_all_sprint_statuses called")
    data = load_devops_data()
    summaries = []
    for item in data:
        summary = {k: v for k, v in item.items() if k != "workItems"}
        summaries.append(summary)
    return json.dumps(summaries)


@mcp.tool()
def get_work_items(project_id: str) -> str:
    """
    Get the work items (user stories, bugs, tasks) for the current sprint of a project.
    Returns detailed work item data including title, type, state, and assignee.

    STEP UP: In production, calls Azure DevOps REST API:
    GET https://dev.azure.com/{org}/{project}/_apis/wit/workitems?ids={ids}&api-version=7.0
    """
    logger.info(f"[MCP Tool] get_work_items called for project_id={project_id}")
    data = load_devops_data()
    for item in data:
        if item.get("projectId") == project_id:
            work_items = item.get("workItems", [])
            return json.dumps({
                "projectId": project_id,
                "sprint": item.get("sprint", "N/A"),
                "workItemCount": len(work_items),
                "workItems": work_items
            })
    return json.dumps({"error": f"Project {project_id} not found in DevOps data."})


@mcp.tool()
def get_sprint_burndown(project_id: str) -> str:
    """
    Get sprint burndown data for a project.
    Returns total vs completed story points and a completion percentage.

    STEP UP: In production, calls Azure DevOps Analytics API for burndown charts.
    """
    logger.info(f"[MCP Tool] get_sprint_burndown called for project_id={project_id}")
    data = load_devops_data()
    for item in data:
        if item.get("projectId") == project_id:
            total = item.get("totalStoryPoints", 0)
            completed = item.get("completedStoryPoints", 0)
            remaining = total - completed
            completion_pct = round((completed / max(1, total)) * 100, 1)
            return json.dumps({
                "projectId": project_id,
                "sprint": item.get("sprint", "N/A"),
                "totalStoryPoints": total,
                "completedStoryPoints": completed,
                "remainingStoryPoints": remaining,
                "completionPercentage": completion_pct,
                "sprintStartDate": item.get("sprintStartDate", "N/A"),
                "sprintEndDate": item.get("sprintEndDate", "N/A")
            })
    return json.dumps({"error": f"Project {project_id} not found in DevOps data."})


@mcp.tool()
def get_team_members(project_id: str) -> str:
    """
    Get team members assigned to work items in the current sprint of a project.
    Extracted from work item assignees.

    STEP UP: In production, calls Azure DevOps REST API:
    GET https://dev.azure.com/{org}/_apis/projects/{project}/teams?api-version=7.0
    """
    logger.info(f"[MCP Tool] get_team_members called for project_id={project_id}")
    data = load_devops_data()
    for item in data:
        if item.get("projectId") == project_id:
            work_items = item.get("workItems", [])
            members = set()
            for wi in work_items:
                assignee = wi.get("assignedTo")
                if assignee:
                    members.add(assignee)
            return json.dumps({
                "projectId": project_id,
                "sprint": item.get("sprint", "N/A"),
                "teamMembers": sorted(list(members)),
                "teamSize": len(members)
            })
    return json.dumps({"error": f"Project {project_id} not found in DevOps data."})


if __name__ == "__main__":
    # Start the server (usually via stdio for MCP clients)
    mcp.run()
