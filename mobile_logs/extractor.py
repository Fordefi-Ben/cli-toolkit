"""Handle zip file extraction and log file discovery."""

import zipfile
import tempfile
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class LogSource:
    """Represents a source of log files."""
    path: Path
    is_temp: bool
    log_files: list[Path]
    total_size: int
    
    def cleanup(self):
        """Remove temp directory if needed."""
        if self.is_temp and self.path.exists():
            import shutil
            shutil.rmtree(self.path)


def load_logs(source: str, output_dir: Optional[str] = None) -> LogSource:
    """Load logs from a zip file or directory.
    
    Args:
        source: Path to zip file or directory
        output_dir: Optional directory to extract to (for zips)
        
    Returns:
        LogSource with discovered log files
    """
    source_path = Path(source)
    
    if not source_path.exists():
        raise FileNotFoundError(f"Source not found: {source}")
    
    if source_path.is_dir():
        return _load_from_directory(source_path)
    elif zipfile.is_zipfile(source_path):
        return _load_from_zip(source_path, output_dir)
    else:
        raise ValueError(f"Source must be a directory or zip file: {source}")


def _load_from_directory(dir_path: Path) -> LogSource:
    """Load logs from a directory."""
    log_files = sorted(dir_path.glob("flog*.txt"))
    total_size = sum(f.stat().st_size for f in log_files)
    
    return LogSource(
        path=dir_path,
        is_temp=False,
        log_files=log_files,
        total_size=total_size
    )


def _load_from_zip(zip_path: Path, output_dir: Optional[str] = None) -> LogSource:
    """Extract and load logs from a zip file."""
    if output_dir:
        extract_path = Path(output_dir)
        extract_path.mkdir(parents=True, exist_ok=True)
        is_temp = False
    else:
        extract_path = Path(tempfile.mkdtemp(prefix="mobile_logs_"))
        is_temp = True
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_path)
    
    # Find log files - they might be in a subdirectory
    log_files = sorted(extract_path.rglob("flog*.txt"))
    total_size = sum(f.stat().st_size for f in log_files)
    
    return LogSource(
        path=extract_path,
        is_temp=is_temp,
        log_files=log_files,
        total_size=total_size
    )
