import os
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def generate_trackable_pdf(file_id, output_path, base_url):
    """
    Generates a PDF with an invisible tracking pixel (Ghost Pixel).
    """
    c = canvas.Canvas(output_path, pagesize=letter)
    c.setFont("Helvetica", 12)
    
    # Add some realistic content
    c.drawString(100, 750, "CONFIDENTIAL: INTERNAL PROJECT STATUS")
    c.drawString(100, 730, "--------------------------------------")
    c.drawString(100, 710, "Author: Senior System Architect")
    c.drawString(100, 690, f"Document ID: {file_id}")
    c.drawString(100, 670, "Status: FINAL - Internal Distribution Only")
    
    c.drawString(100, 640, "Budget Summary (Q3-Q4):")
    c.drawString(120, 620, "- Research: $450,000")
    c.drawString(120, 600, "- Infrastructure: $1,200,000")
    c.drawString(120, 580, "- Human Capital: $2,100,000")
    
    # Embed the tracking pixel
    pixel_url = f"{base_url}/api/v1/ghost-pixel/{file_id}"
    
    # In PDFs, we can add a 'Launch' action or a simple invisible link
    # For this demo, we'll add a 'Heartbeat' note that acts as a trigger
    c.setFont("Helvetica", 1)
    c.setStrokeColorRGB(1,1,1) # White on white
    c.linkURL(pixel_url, (0, 0, 10, 10), relative=1)
    
    c.setFont("Helvetica", 10)
    c.setStrokeColorRGB(0,0,0)
    c.drawString(100, 500, "[DOCUMENT GEOGRAPHICALLY INSTRUMENTED FOR AUDIT]")
    
    c.save()
    print(f"[*] Trackable PDF generated: {output_path}")

def generate_trackable_html(file_id, output_path, base_url):
    """
    Generates an HTML file with an invisible tracking pixel.
    This is highly reliable for the demo as browsers always load images.
    """
    pixel_url = f"{base_url}/api/v1/ghost-pixel/{file_id}"
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Confidential Document</title>
    <style>
        body {{ font-family: sans-serif; padding: 40px; background: #f4f4f4; color: #333; }}
        .header {{ border-bottom: 2px solid #333; margin-bottom: 20px; }}
        .warning {{ color: red; font-weight: bold; border: 1px solid red; padding: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>PROJECT ALPHA: CORE CREDENTIALS</h1>
        <p>INTERNAL USE ONLY - EXFILTRATION PROHIBITED</p>
    </div>
    
    <div class="warning">
        WARNING: This document is traced. Unauthorized distribution will be flagged.
    </div>
    
    <h3>Database Credentials (PROD)</h3>
    <ul>
        <li>Host: internal-db.corporate.lan</li>
        <li>User: sys_admin</li>
        <li>Key: AKIA_EXAMPLE_12345</li>
    </ul>

    <!-- THE GHOST PIXEL -->
    <img src="{pixel_url}" style="display:none;" width="1" height="1" />
    
    <p style="margin-top: 100px; color: #888; font-size: 10px;">
        Fingerprint: {file_id}_{base64.b64encode(file_id.encode()).decode()[:10]}
    </p>
</body>
</html>"""
    
    with open(output_path, "w") as f:
        f.write(html_content)
    print(f"[*] HTML generated: {output_path}")

def base_64_encode(s):
    return base64.b64encode(s.encode()).decode()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python generate_decoy.py [filename] [base_url]")
        print("Example: python generate_decoy.py payroll_info.html http://your-ngrok-url.io")
        sys.exit(1)
        
    fname = sys.argv[1]
    url = sys.argv[2].rstrip('/')
    fid = fname.split('.')[0]
    
    if fname.endswith('.pdf'):
        generate_trackable_pdf(fid, fname, url)
    elif fname.endswith('.html'):
        generate_trackable_html(fid, fname, url)
    else:
        print("[!] Unsupported format. Use .pdf or .html")
