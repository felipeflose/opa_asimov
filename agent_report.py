import os
from datetime import datetime
from html import escape as html_escape

class ReportAgent:
    def __init__(self, export_dirs):
        if isinstance(export_dirs, str): export_dirs = [export_dirs]
        self.export_dirs = export_dirs
        for d in self.export_dirs:
            os.makedirs(d, exist_ok=True)

    def generate_html_report(self, subject, content):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Resumo_{subject[:30].replace(' ', '_')}_{timestamp}.html"
        
        safe_subject = html_escape(subject)
        content_html = html_escape(content).replace('\n', '<br>')
        html = f"""
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <title>{safe_subject}</title>
            <style>
                body {{ font-family: sans-serif; background: #0f172a; color: #f1f5f9; padding: 50px; line-height: 1.6; }}
                .container {{ max-width: 800px; margin: 0 auto; background: rgba(30, 41, 59, 0.7); padding: 40px; border-radius: 20px; }}
                h1 {{ color: #38bdf8; font-size: 2.5rem; }}
                .content {{ font-size: 1.1rem; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{safe_subject}</h1>
                <div class="content">{content_html}</div>
                <hr>
                <p style="font-size: 0.8rem; color: #64748b;">Gerado pelo ReportAgent • {datetime.now().strftime("%d/%m/%Y")}</p>
            </div>
        </body>
        </html>
        """
        for d in self.export_dirs:
            filepath = os.path.join(d, filename)
            with open(filepath, "w", encoding="utf-8") as f: f.write(html)
        
        return os.path.join(self.export_dirs[0], filename)
