import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from loguru import logger

from llmops_datacollection.domain.documents import RepositoryDocument
from llmops_datacollection.domain.exceptions import CrawlerError
from llmops_datacollection.settings import settings
from .base import BaseCrawler

class GithubCrawler(BaseCrawler):
    """GitHub repository crawler."""
    
    model = RepositoryDocument

    def __init__(
        self, 
        ignore=(".git", ".toml", ".lock", ".png", "venv", "__pycache__", "node_modules")
    ):
        self._ignore = ignore

    def extract(self, link: str, **kwargs) -> None:
        """Extract repository content from GitHub."""
        if self.model.find(link=link):
            logger.info(f"Repository already exists: {link}")
            return

        logger.info(f"Extracting repository: {link}")

        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        try:
            # Clone repository
            os.chdir(temp_dir)
            self._clone_repository(link)

            # Get repository name and path
            repo_name = link.rstrip("/").split("/")[-1]
            repo_path = Path(temp_dir) / repo_name

            # Process repository files
            tree = self._process_repository(repo_path)
            
            # Extract repository metadata
            metadata = self._extract_metadata(repo_path)

            # Save repository
            user = kwargs["user"]
            repo = self.model(
                content=tree,
                name=repo_name,
                link=link,
                platform="github",
                author_id=user.id,
                author_full_name=user.full_name,
                metadata=metadata
            )
            repo.save()

            logger.info("Successfully extracted repository")

        except Exception as e:
            logger.error(f"Failed to extract repository: {str(e)}")
            raise CrawlerError(f"Repository extraction failed: {str(e)}")
        finally:
            shutil.rmtree(temp_dir)

    def _clone_repository(self, link: str) -> None:
        """Clone repository using git."""
        cmd = ["git", "clone"]
        
        # Add token if available (for private repos)
        if settings.GITHUB_TOKEN:
            auth_link = link.replace(
                "https://", 
                f"https://{settings.GITHUB_TOKEN}@"
            )
            cmd.append(auth_link)
        else:
            cmd.append(link)

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise CrawlerError(
                f"Failed to clone repository: {e.stderr.decode()}"
            )

    def _process_repository(self, repo_path: Path) -> dict:
        """Process repository files."""
        tree = {}
        
        for root, _, files in os.walk(repo_path):
            dir_path = Path(root).relative_to(repo_path)
            
            # Skip ignored directories
            if any(i in str(dir_path) for i in self._ignore):
                continue

            for file in files:
                # Skip ignored files
                if any(file.endswith(i) for i in self._ignore):
                    continue
                    
                file_path = dir_path / file
                try:
                    with open(repo_path / file_path, "r", encoding="utf-8") as f:
                        tree[str(file_path)] = f.read()
                except (UnicodeDecodeError, IOError):
                    continue

        return tree

    def _extract_metadata(self, repo_path: Path) -> dict:
        """Extract repository metadata."""
        metadata = {
            "num_files": 0,
            "languages": set(),
            "has_readme": False,
            "has_license": False,
            "has_tests": False
        }

        for root, _, files in os.walk(repo_path):
            metadata["num_files"] += len(files)
            
            for file in files:
                # Check for important files
                lower_file = file.lower()
                if lower_file.startswith("readme"):
                    metadata["has_readme"] = True
                elif lower_file.startswith("license"):
                    metadata["has_license"] = True
                elif "test" in lower_file:
                    metadata["has_tests"] = True
                    
                # Detect language from extension
                ext = Path(file).suffix.lower()
                if ext in {".py", ".js", ".java", ".cpp", ".go", ".rs"}:
                    metadata["languages"].add(ext[1:])  # Remove dot

        metadata["languages"] = list(metadata["languages"])
        return metadata