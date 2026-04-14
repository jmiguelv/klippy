import os
import argparse
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import threading

from clickup.client import ClickUpClient
from github.client import GitHubClient
from orchestrator import Orchestrator
from utils.state import StateStore

def setup_logging(level=logging.INFO, log_file="harvester.log"):
    # Root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    if log_file:
        file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Klippy Data Harvester")
    parser.add_argument("--clickup", action="store_true", help="Run ClickUp harvester")
    parser.add_argument("--github", action="store_true", help="Run GitHub harvester")
    parser.add_argument("--all", action="store_true", help="Run all harvesters")
    args = parser.parse_args()

    # Configuration from .env
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    data_dir = os.getenv("DATA_DIR", "./data/raw")
    log_file = os.path.join(os.path.dirname(data_dir), "harvester.log") # Save log in data/harvester.log
    
    setup_logging(level=log_level, log_file=log_file)
    logger = logging.getLogger("harvester")

    clickup_api_key = os.getenv("CLICKUP_API_KEY")
    clickup_workspace_id = os.getenv("CLICKUP_WORKSPACE_ID")
    clickup_ignore_spaces = os.getenv("CLICKUP_IGNORE_SPACES", "").split(",")
    
    github_token = os.getenv("GITHUB_TOKEN")
    github_orgs = os.getenv("GITHUB_ORGS", "").split(",")
    github_users = os.getenv("GITHUB_USERS", "").split(",")
    
    state_file = os.getenv("STATE_FILE", "./data/state.json")

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

    threads = []

    if args.all or args.clickup:
        if clickup_client and clickup_workspace_id:
            ignore_spaces = [s for s in clickup_ignore_spaces if s]
            def run_cu():
                logger.info("Thread: Starting ClickUp harvesting...")
                orchestrator.run_clickup(workspace_id=clickup_workspace_id, ignore_spaces=ignore_spaces)
            
            t = threading.Thread(target=run_cu, name="ClickUpThread")
            threads.append(t)
            t.start()
        else:
            logger.warning("ClickUp configuration missing.")

    if args.all or args.github:
        if github_client:
            orgs = [o for o in github_orgs if o]
            users = [u for u in github_users if u]
            def run_gh():
                logger.info("Thread: Starting GitHub harvesting...")
                orchestrator.run_github(org_names=orgs, user_names=users)
            
            t = threading.Thread(target=run_gh, name="GitHubThread")
            threads.append(t)
            t.start()
        else:
            logger.warning("GitHub configuration missing.")

    for t in threads:
        t.join()

    logger.info("All harvesting tasks complete.")

if __name__ == "__main__":
    main()
