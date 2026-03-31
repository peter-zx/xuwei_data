import os
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Callable
import tempfile
import zipfile
import shutil


class ConversionResult:
    def __init__(self, success: bool, original_path: str, output_path: str = "", error: str = ""):
        self.success = success
        self.original_path = original_path
        self.output_path = output_path
        self.error = error


class Doc2PdfConverter:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[ConversionResult] = []
    
    def convert_single(self, file_path: str, progress_callback: Optional[Callable] = None) -> ConversionResult:
        path = Path(file_path)
        ext = path.suffix.lower()
        
        try:
            output_path = self.output_dir / f"{path.stem}.pdf"
            
            if ext == '.pdf':
                shutil.copy(file_path, output_path)
                return ConversionResult(True, file_path, str(output_path))
            
            if ext in ['.docx', '.doc']:
                result = self._convert_word(file_path, output_path)
            elif ext in ['.xlsx', '.xls']:
                result = self._convert_excel(file_path, output_path)
            elif ext in ['.pptx', '.ppt']:
                result = self._convert_ppt(file_path, output_path)
            elif ext == '.txt':
                result = self._convert_txt(file_path, output_path)
            else:
                return ConversionResult(False, file_path, error=f"Unsupported format: {ext}")
            
            if progress_callback:
                progress_callback()
            
            return result
            
        except Exception as e:
            return ConversionResult(False, file_path, error=str(e))
    
    def _convert_word(self, input_path: str, output_path: Path) -> ConversionResult:
        try:
            from docx import Document
            doc = Document(input_path)
            
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as f:
                html_content = self._docx_to_html(doc)
                f.write(html_content)
                html_path = f.name
            
            try:
                self._convert_html_to_pdf(html_path, output_path)
                return ConversionResult(True, input_path, str(output_path))
            finally:
                os.unlink(html_path)
        except Exception as e:
            return ConversionResult(False, input_path, error=str(e))
    
    def _docx_to_html(self, doc) -> str:
        html_parts = ['<!DOCTYPE html>', '<html>', '<head>',
                      '<meta charset="utf-8">',
                      '<style>',
                      'body { font-family: SimSun, sans-serif; font-size: 12pt; }',
                      'p { margin: 6pt 0; }',
                      'table { border-collapse: collapse; width: 100%; }',
                      'td, th { border: 1px solid #000; padding: 4pt; }',
                      '</style>', '</head>', '<body>']
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                if para.style.name.startswith('Heading'):
                    level = int(para.style.name[-1]) if para.style.name[-1].isdigit() else 1
                    html_parts.append(f'<h{level}>{text}</h{level}>')
                else:
                    html_parts.append(f'<p>{text}</p>')
        
        for table in doc.tables:
            html_parts.append('<table>')
            for row in table.rows:
                html_parts.append('<tr>')
                for cell in row.cells:
                    html_parts.append(f'<td>{cell.text}</td>')
                html_parts.append('</tr>')
            html_parts.append('</table>')
        
        html_parts.extend(['</body>', '</html>'])
        return '\n'.join(html_parts)
    
    def _convert_excel(self, input_path: str, output_path: Path) -> ConversionResult:
        try:
            from openpyxl import load_workbook
            
            wb = load_workbook(input_path)
            html_parts = ['<!DOCTYPE html>', '<html>', '<head>',
                         '<meta charset="utf-8">',
                         '<style>',
                         'body { font-family: SimSun, sans-serif; }',
                         'table { border-collapse: collapse; width: 100%; }',
                         'td, th { border: 1px solid #000; padding: 4pt; }',
                         'th { background: #f0f0f0; }',
                         '</style>', '</head>', '<body>']
            
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                html_parts.append(f'<h2>{sheet_name}</h2>')
                html_parts.append('<table>')
                
                for row in ws.iter_rows():
                    html_parts.append('<tr>')
                    for cell in row:
                        value = cell.value if cell.value is not None else ''
                        html_parts.append(f'<td>{value}</td>')
                    html_parts.append('</tr>')
                
                html_parts.append('</table>')
            
            html_parts.extend(['</body>', '</html>'])
            
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as f:
                f.write('\n'.join(html_parts))
                html_path = f.name
            
            try:
                self._convert_html_to_pdf(html_path, output_path)
                return ConversionResult(True, input_path, str(output_path))
            finally:
                os.unlink(html_path)
        except Exception as e:
            return ConversionResult(False, input_path, error=str(e))
    
    def _convert_ppt(self, input_path: str, output_path: Path) -> ConversionResult:
        try:
            from pptx import Presentation
            
            prs = Presentation(input_path)
            html_parts = ['<!DOCTYPE html>', '<html>', '<head>',
                         '<meta charset="utf-8">',
                         '<style>',
                         'body { font-family: SimSun, sans-serif; }',
                         '.slide { page-break-after: always; margin-bottom: 20px; }',
                         'h1 { color: #333; }',
                         '</style>', '</head>', '<body>']
            
            for i, slide in enumerate(prs.slides, 1):
                html_parts.append(f'<div class="slide">')
                html_parts.append(f'<h1>Slide {i}</h1>')
                
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        html_parts.append(f'<p>{shape.text}</p>')
                
                html_parts.append('</div>')
            
            html_parts.extend(['</body>', '</html>'])
            
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as f:
                f.write('\n'.join(html_parts))
                html_path = f.name
            
            try:
                self._convert_html_to_pdf(html_path, output_path)
                return ConversionResult(True, input_path, str(output_path))
            finally:
                os.unlink(html_path)
        except Exception as e:
            return ConversionResult(False, input_path, error=str(e))
    
    def _convert_txt(self, input_path: str, output_path: Path) -> ConversionResult:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>body {{ font-family: SimSun; font-size: 12pt; white-space: pre-wrap; }}</style>
</head><body><p>{content}</p></body></html>'''
            
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as f:
                f.write(html)
                html_path = f.name
            
            try:
                self._convert_html_to_pdf(html_path, output_path)
                return ConversionResult(True, input_path, str(output_path))
            finally:
                os.unlink(html_path)
        except Exception as e:
            return ConversionResult(False, input_path, error=str(e))
    
    def _convert_html_to_pdf(self, html_path: str, output_path: Path):
        import pdfkit
        pdfkit.from_file(html_path, str(output_path))
    
    def convert_batch(self, file_paths: List[str], 
                     progress_callback: Optional[Callable[[int, int], None]] = None) -> List[ConversionResult]:
        total = len(file_paths)
        completed = 0
        results = []
        
        for path in file_paths:
            result = self.convert_single(path)
            results.append(result)
            completed += 1
            if progress_callback:
                progress_callback(completed, total)
        
        return results
    
    def create_zip(self, output_zip_path: str) -> str:
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in self.output_dir.glob('*.pdf'):
                zf.write(file_path, file_path.name)
        return output_zip_path
