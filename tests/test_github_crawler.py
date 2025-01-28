import os
import tempfile
import uuid
from pathlib import Path
from unittest.mock import Mock, patch

import click
import pytest
from click.testing import CliRunner

from llmops_datacollection.application.crawlers.github import GithubCrawler
from llmops_datacollection.domain.documents import RepositoryDocument, UserDocument

@pytest.fixture
def mock_user():
    return UserDocument(
        first_name="John",
        last_name="Doe",
        id=str(uuid.uuid4())
    )

@pytest.fixture
def github_crawler():
    return GithubCrawler(ignore=(".git", ".toml", ".lock", ".png"))

@pytest.fixture
def mock_repo_content():
    return {
        "app.py": "from fastapi import FastAPI\n",
        "requirements.txt": "fastapi==0.68.0\n",
        "setup.py": "from setuptools import setup\n",
        "README.md": "# Money-Laundering Prevention\n",
        "notebook/EDA.ipynb": "# Exploratory Data Analysis\n"
    }

@pytest.fixture
def test_repo_url():
    return "https://github.com/SuyodhanJ6/Money-Laundering-Prevention"

def create_mock_repo_structure(temp_dir: Path, files: dict) -> None:
    """Helper function to create mock repository structure"""
    for file_path, content in files.items():
        full_path = temp_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

def test_extract_repo_already_exists(github_crawler, mock_user):
    """Test that crawler exits early when repo already exists"""
    test_url = "https://github.com/user/test-repo"
    
    with patch('llmops_datacollection.domain.documents.RepositoryDocument.find', return_value=Mock()):
        github_crawler.extract(test_url, user=mock_user)
        # Should exit early without cloning repo

@pytest.mark.integration
def test_extract_new_repo(github_crawler, mock_user, mock_repo_content, test_repo_url):
    """Test successful extraction of a new repository"""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        with patch('tempfile.mkdtemp', return_value=str(temp_dir)), \
             patch('subprocess.run') as mock_git_clone, \
             patch('llmops_datacollection.domain.documents.RepositoryDocument.find', return_value=None), \
             patch('llmops_datacollection.domain.documents.RepositoryDocument.save') as mock_save:
            
            # Create mock repository structure
            repo_dir = temp_dir / "Money-Laundering-Prevention"
            repo_dir.mkdir(parents=True)
            create_mock_repo_structure(repo_dir, mock_repo_content)
            
            # Execute crawler
            github_crawler.extract(test_repo_url, user=mock_user)
            
            # Verify git clone was called correctly
            mock_git_clone.assert_called_once_with(["git", "clone", test_repo_url])
            
            # Verify repository document was saved
            mock_save.assert_called()
            args, _ = mock_save.call_args
            saved_doc = args[0]
            assert isinstance(saved_doc, RepositoryDocument)
            assert saved_doc.name == "Money-Laundering-Prevention"
            assert saved_doc.link == test_repo_url
            assert saved_doc.platform == "github"
            assert saved_doc.author_id == mock_user.id
            assert isinstance(saved_doc.content, dict)
    finally:
        # Cleanup temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

def test_extract_with_ignored_files(github_crawler, mock_user, test_repo_url):
    """Test that ignored files are properly excluded"""
    mock_files = {
        "app.py": "from fastapi import FastAPI\n",
        "requirements.txt": "fastapi==0.68.0\n",
        ".git/config": "should be ignored",
        "test.png": "should be ignored",
        "poetry.lock": "should be ignored"
    }
    
    temp_dir = Path(tempfile.mkdtemp())
    try:
        repo_dir = temp_dir / "Money-Laundering-Prevention"
        repo_dir.mkdir(parents=True)
        create_mock_repo_structure(repo_dir, mock_files)
        
        with patch('tempfile.mkdtemp', return_value=str(temp_dir)), \
             patch('subprocess.run', return_value=Mock(returncode=0)), \
             patch('llmops_datacollection.domain.documents.RepositoryDocument.find', return_value=None), \
             patch('llmops_datacollection.domain.documents.RepositoryDocument.save') as mock_save:
            
            github_crawler.extract(test_repo_url, user=mock_user)
            
            # Verify saved content
            args, _ = mock_save.call_args
            saved_doc = args[0]
            assert isinstance(saved_doc, RepositoryDocument)
            
            # Check included/excluded files
            assert "app.py" in saved_doc.content
            assert "requirements.txt" in saved_doc.content
            assert not any(k.startswith(".git/") for k in saved_doc.content.keys())
            assert not any(k.endswith(".png") for k in saved_doc.content.keys())
            assert not any(k.endswith(".lock") for k in saved_doc.content.keys())
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

def test_extract_clone_failure(github_crawler, mock_user, test_repo_url):
    """Test handling of git clone failures"""
    with patch('subprocess.run', side_effect=Exception("Git clone failed")), \
         patch('llmops_datacollection.domain.documents.RepositoryDocument.find', return_value=None):
        
        with pytest.raises(Exception) as exc_info:
            github_crawler.extract(test_repo_url, user=mock_user)
        assert str(exc_info.value) == "Git clone failed"

@pytest.mark.cli
def test_cli_crawl_command(test_repo_url):
    """Test the CLI interface"""
    @click.command()
    @click.option("--user-name", required=True)
    @click.option("--repo-url", required=True)
    def cli(user_name: str, repo_url: str):
        try:
            first_name, last_name = user_name.split(" ", 1)
            user = UserDocument(
                first_name=first_name,
                last_name=last_name,
                id=str(uuid.uuid4())
            )
            crawler = GithubCrawler()
            crawler.extract(repo_url, user=user)
        except Exception as e:
            raise click.ClickException(str(e))

    runner = CliRunner()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        with patch('tempfile.mkdtemp', return_value=str(temp_path)), \
             patch('subprocess.run', return_value=Mock(returncode=0)), \
             patch('llmops_datacollection.domain.documents.RepositoryDocument.find', return_value=None), \
             patch('llmops_datacollection.domain.documents.RepositoryDocument.save'):
            
            # Create necessary directory structure
            repo_dir = temp_path / "Money-Laundering-Prevention"
            repo_dir.mkdir(parents=True)
            
            result = runner.invoke(cli, [
                '--user-name', 'Suyodhan J', 
                '--repo-url', test_repo_url
            ])
            
            assert result.exit_code == 0

def test_cleanup_after_extraction(github_crawler, mock_user, test_repo_url):
    """Test proper cleanup of temporary directories"""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        with patch('tempfile.mkdtemp', return_value=str(temp_dir)), \
             patch('subprocess.run', return_value=Mock(returncode=0)), \
             patch('llmops_datacollection.domain.documents.RepositoryDocument.find', return_value=None), \
             patch('llmops_datacollection.domain.documents.RepositoryDocument.save'):
            
            # Create the repository directory
            repo_dir = temp_dir / "Money-Laundering-Prevention"
            repo_dir.mkdir(parents=True)
            
            # Execute the crawler
            github_crawler.extract(test_repo_url, user=mock_user)
            
            # Verify directory was cleaned up
            assert not temp_dir.exists()
    finally:
        # Ensure cleanup in case of test failure
        if temp_dir.exists():
            shutil.rmtree(temp_dir)