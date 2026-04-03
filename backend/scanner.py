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
        html = '<div class="tree-container">'
        
        if node.is_folder:
            html += self._render_tree(node, 0)
        
        html += '</div>'
        return html
    
    def _render_tree(self, node: FileNode, level: int, top_folder: str = "") -> str:
        html = ""
        
        if node.is_folder:
            current_folder = top_folder if top_folder else node.name
            
            for child in node.children:
                if child.is_folder:
                    html += self._render_tree(child, level + 1, current_folder)
                else:
                    html += self._render_file(child, current_folder)
            
            folder_html = f'<div class="folder-header" style="padding:10px 12px; background:#e8e8f0; border-radius:8px; margin-bottom:8px; margin-top:8px; display:flex; align-items:center; gap:10px;">'
            folder_html += f'<input type="checkbox" class="folder-checkbox" data-folder="{current_folder}" style="width:18px; height:18px; cursor:pointer;">'
            folder_html += f'<span style="font-weight:600; color:#374151;">&#128193; {node.name}</span>'
            folder_html += f'<span style="color:#9ca3af; font-size:0.85rem;">({self._count_files(node)} 个文件)</span>'
            folder_html += f'</div>'
            
            if html:
                html = folder_html + f'<div style="padding-left:{level * 20}px;">{html}</div>'
            else:
                html = folder_html
        
        return html
    
    def _render_file(self, node: FileNode, top_folder: str = "") -> str:
        icon = self._get_file_icon(node.extension)
        size_str = self._format_size(node.size)
        html = f'<div class="file-row" style="display:flex; align-items:center; padding:8px 12px; border-radius:8px; margin-bottom:4px; background:#fafafa;">'
        html += f'<input type="checkbox" data-path="{node.path}" data-folder="{top_folder}" class="file-checkbox" style="width:18px; height:18px; cursor:pointer; margin-right:12px;">'
        html += f'<span style="flex:1; display:flex; align-items:center; gap:8px;">'
        html += f'<span style="background:#667eea; color:white; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:600;">{icon}</span>'
        html += f'<span style="font-weight:500;">{node.name}</span>'
        html += f'</span>'
        html += f'<span style="color:#9ca3af; font-size:0.85rem;">{size_str}</span>'
        html += f'</div>'
        return html
    
    def _count_files(self, node: FileNode) -> int:
        if not node.is_folder:
            return 1
        return sum(self._count_files(child) for child in node.children)
    
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
