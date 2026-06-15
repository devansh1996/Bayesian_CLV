#!/usr/bin/env python3
"""
Compile thesis.tex to PDF using Overleaf's API
"""
import requests
import os
import json
from pathlib import Path
import time

def compile_latex_overleaf(tex_file_path, output_pdf_path):
    """
    Compile LaTeX using RestAPI at https://latex.codecogs.com or similar
    For full document, use a different approach
    """
    with open(tex_file_path, 'r', encoding='utf-8') as f:
        latex_content = f.read()
    
    print(f"Compiling {tex_file_path}...")
    
    # Method: Use compile API endpoint
    url = "http://128.30.3.38:9901/compile"
    
    try:
        data = {
            'src': latex_content,
            'rootName': 'thesis'
        }
        
        response = requests.post(url, json=data, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            if 'pdf' in result and result['pdf']:
                os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
                with open(output_pdf_path, 'wb') as f:
                    pdf_data = result['pdf']
                    if isinstance(pdf_data, str):
                        import base64
                        pdf_data = base64.b64decode(pdf_data)
                    f.write(pdf_data)
                print(f"✓ Successfully compiled to: {output_pdf_path}")
                return True
        
        print(f"Trying alternative endpoint...")
        return compile_latex_tectonic(tex_file_path, output_pdf_path)
    
    except Exception as e:
        print(f"Method 1 failed: {e}")
        return compile_latex_tectonic(tex_file_path, output_pdf_path)

def compile_latex_tectonic(tex_file_path, output_pdf_path):
    """
    Use Tectonic online service
    """
    with open(tex_file_path, 'r', encoding='utf-8') as f:
        latex_content = f.read()
    
    print("Trying Tectonic service...")
    
    try:
        # Tectonic has a web interface, try using it
        url = "https://tectonic.hosted.runkit.com"
        files = {'file': ('thesis.tex', latex_content)}
        
        response = requests.post(url, files=files, timeout=120)
        
        if response.status_code == 200 and len(response.content) > 1000:
            os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
            with open(output_pdf_path, 'wb') as f:
                f.write(response.content)
            print(f"✓ Successfully compiled to: {output_pdf_path}")
            return True
    except:
        pass
    
    print("Tectonic service unavailable, trying Docker...")
    return False

if __name__ == "__main__":
    tex_file = Path("texts/thesis.tex")
    output_pdf = Path("texts/thesis.pdf")
    
    if not tex_file.exists():
        print(f"✗ Error: {tex_file} not found")
        exit(1)
    
    success = compile_latex_online(str(tex_file), str(output_pdf))
    
    if success:
        print(f"\nPDF file size: {os.path.getsize(output_pdf) / 1024:.2f} KB")
    else:
        print("Could not compile LaTeX. Please try:")
        print("1. Install MiKTeX from https://miktex.org/download")
        print("2. Use Overleaf: https://www.overleaf.com")
        print("3. Install TeX Live from https://www.tug.org/texlive/")
        exit(1)
