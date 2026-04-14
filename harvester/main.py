import os
import argparse
import logging
from dotenv import load_dotenv

from clickup.client import ClickUpClient
from github.client import GitHubClient
from orchestrator import Orchestrator
from utils.state import StateStore

def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Klippy Data Harvester")
    parser.add_argument("--clickup", action="store_true", help="Run ClickUp harvester")
    parser.add_argument("--github", action="store_true", help="Run GitHub harvester")
    parser.add_argument("--all", action="store_true", help="Run all harvesters")
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger("harvester")

    # Configuration from .env
    clickup_api_key = os.getenv("CLICKUP_API_KEY")
    clickup_workspace_id = os.getenv("CLICKUP_WORKSPACE_ID")
    clickup_list_ids = os.getenv("CLICKUP_LIST_IDS", "").split(",")
    
    github_token = os.getenv("GITHUB_TOKEN")
    github_orgs = os.getenv("GITHUB_ORGS", "").split(",")
    github_users = os.getenv("GITHUB_USERS", "").split(",")
    
    data_dir = os.getenv("DATA_DIR", "./data")
    state_file = os.getenv("STATE_FILE", "state.json")

    # Initialize Clients
    clickup_client = ClickUpClient(api_key=clickup_api_key) if clickup_api_key else None
    github_client = GitHubClient(token=github_token) if github_token else None
    state_store = StateStore(state_file)
    
    orchestrator = Orchestrator(
        clickup_client=clickup_client,
        github_client=github_client,
        state_store=state_store,
        data_dir=data_dir
    )

    if args.all or args.clickup:
        if clickup_client and clickup_workspace_id:
            logger.info("Starting ClickUp harvesting...")
            orchestrator.run_clickup(list_ids=clickup_list_ids, workspace_id=clickup_workspace_id)
        else:
            logger.warning("ClickUp configuration missing.")

    if args.all or args.github:
        if github_client:
            logger.info("Starting GitHub harvesting...")
            # Filter out empty strings from split
            orgs = [o for o in github_orgs if o]
            users = [u for u in github_users if u]
            orchestrator.run_github(org_names=orgs, user_names=users)
        else:
            logger.warning("GitHub configuration missing.")

    logger.info("Harvesting complete.")

if __name__ == "__main__":
    main()
