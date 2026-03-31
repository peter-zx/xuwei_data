from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import os


@dataclass
class FileNode:
    name: str
    path: str
    is_folder: bool
    size: int
    children: List['FileNode']
    selected: bool = False
    extension: str = ""
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "path": self.path,
            "is_folder": self.is_folder,
            "size": self.size,
            "extension": self.extension,
            "selected": self.selected,
            "children": [c.to_dict() for c in self.children]
        }


class FileScanner:
    SUPPORTED_EXTENSIONS = {'.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.txt', '.pdf'}
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.excluded_folders = {'__pycache__', '.git', 'node_modules', '.venv', 'venv'}
    
    def is_valid_file(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUPPORTED_EXTENSIONS
    
    def scan(self) -> Optional[FileNode]:
        if not self.root_path.exists():
            return None
        
        if not self.root_path.is_dir():
            return None
            
        return self._scan_directory(self.root_path)
    
    def _scan_directory(self, dir_path: Path) -> FileNode:
        node = FileNode(
            name=dir_path.name,
            path=str(dir_path),
            is_folder=True,
            size=0,
            children=[]
        )
        
        try:
            items = sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for item in items:
                if item.name in self.excluded_folders:
                    continue
                
                if item.is_dir():
                    child = self._scan_directory(item)
                    if child.children:
                        node.children.append(child)
                        node.size += child.size
                elif item.is_file() and self.is_valid_file(item):
                    ext = item.suffix.lower()
                    size = item.stat().st_size
                    file_node = FileNode(
                        name=item.name,
                        path=str(item),
                        is_folder=False,
                        size=size,
                        children=[],
                        extension=ext
                    )
                    node.children.append(file_node)
                    node.size += size
                    
        except PermissionError:
            pass
        
        return node
    
    def get_all_files(self, node: FileNode) -> List[FileNode]:
        files = []
        if not node.is_folder:
            files.append(node)
        for child in node.children:
            files.extend(self.get_all_files(child))
        return files
    
    def get_file_tree_html(self, node: FileNode, level: int = 0) -> str:
        html = ""
        indent = "    " * level
        
        if node.is_folder:
            for child in node.children:
                html += self.get_file_tree_html(child, level + 1)
        else:
            icon = self._get_file_icon(node.extension)
            size_str = self._format_size(node.size)
            html += f'<li data-path="{node.path}">'
            html += f'<input type="checkbox" data-path="{node.path}">'
            html += f'<span class="file-info">'
            html += f'<span class="file-icon">{icon}</span>'
            html += f'<span class="file-name">{node.name}</span>'
            html += f'<span class="file-size">{size_str}</span>'
            html += f'</span>'
            html += f'</li>\n'
        
        return html
    
    def _get_file_icon(self, ext: str) -> str:
        icons = {
            '.docx': '📄', '.doc': '📄',
            '.xlsx': '📊', '.xls': '📊',
            '.pptx': '📽️', '.ppt': '📽️',
            '.txt': '📝',
            '.pdf': '📕'
        }
        return icons.get(ext, '📁')
    
    def _format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


def count_files(node: FileNode) -> int:
    if not node.is_folder:
        return 1
    return sum(count_files(child) for child in node.children)


def get_selected_files(node: FileNode, selected_paths: set) -> List[FileNode]:
    files = []
    if not node.is_folder:
        if node.path in selected_paths:
            files.append(node)
    else:
        for child in node.children:
            files.extend(get_selected_files(child, selected_paths))
    return files
