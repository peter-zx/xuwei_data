from pathlib import Path
from typing import List, Dict, Optional
import os


class FileNode:
    def __init__(self, name: str, path: str, is_folder: bool, size: int = 0, children: List['FileNode'] = None):
        self.name = name
        self.path = path
        self.is_folder = is_folder
        self.size = size
        self.children = children or []
        self.extension = "" if is_folder else Path(path).suffix.lower()


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
    
    def get_file_tree_html(self, node: FileNode) -> str:
        html = '<ul class="file-tree" style="list-style:none; margin:0; padding:0;">'
        html += self._render_node(node, 0)
        html += '</ul>'
        return html
    
    def _render_node(self, node: FileNode, level: int) -> str:
        html = ""
        
        if node.is_folder:
            for child in node.children:
                html += self._render_node(child, level)
        else:
            icon = self._get_file_icon(node.extension)
            size_str = self._format_size(node.size)
            html += f'<li style="padding:6px 8px; border-radius:6px; margin-bottom:2px; display:flex; align-items:center; gap:8px;" onmouseover="this.style.background=\'#f3f4f6\'" onmouseout="this.style.background=\'transparent\'">'
            html += f'<input type="checkbox" data-path="{node.path}" style="width:16px; height:16px; cursor:pointer;">'
            html += f'<span style="flex:1; display:flex; align-items:center; gap:6px;">'
            html += f'<span>{icon}</span>'
            html += f'<span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{node.name}</span>'
            html += f'</span>'
            html += f'<span style="color:#9ca3af; font-size:0.85rem; white-space:nowrap;">{size_str}</span>'
            html += f'</li>'
        
        return html
    
    def _get_file_icon(self, ext: str) -> str:
        icons = {
            '.docx': 'DOCX', '.doc': 'DOC',
            '.xlsx': 'XLSX', '.xls': 'XLS',
            '.pptx': 'PPTX', '.ppt': 'PPT',
            '.txt': 'TXT',
            '.pdf': 'PDF'
        }
        return icons.get(ext, 'FILE')
    
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
