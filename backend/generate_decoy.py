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
    Generates an HTML file with MULTIPLE tracking mechanisms for maximum reliability.
    1. Invisible <img> ghost pixel (works even without JS)
    2. JavaScript fetch() call with extra client-side fingerprinting
    3. onload event handler as tertiary fallback
    """
    pixel_url = f"{base_url}/api/v1/ghost-pixel/{file_id}"
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Confidential Document</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 30px; background: #f8f8f8; color: #333; max-width: 800px; margin: 0 auto; }}
        .header {{ border-bottom: 2px solid #333; margin-bottom: 20px; padding-bottom: 10px; }}
        .header h1 {{ margin: 0 0 5px 0; font-size: 22px; }}
        .header p {{ margin: 0; color: #666; font-size: 12px; }}
        .warning {{ color: red; font-weight: bold; border: 1px solid red; padding: 10px; margin: 20px 0; background: #fff5f5; font-size: 13px; }}
        .section {{ margin: 20px 0; }}
        .section h3 {{ border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
        ul li {{ margin: 5px 0; font-family: monospace; font-size: 13px; }}
        .footer {{ margin-top: 60px; color: #aaa; font-size: 9px; border-top: 1px solid #eee; padding-top: 10px; }}
    </style>
</head>
<body onload="t()">
    <div class="header">
        <h1>PROJECT ALPHA: CORE CREDENTIALS</h1>
        <p>INTERNAL USE ONLY — EXFILTRATION PROHIBITED</p>
    </div>
    
    <div class="warning">
        ⚠ WARNING: This document is traced. Unauthorized distribution will be flagged.
    </div>
    
    <div class="section">
        <h3>Database Credentials (PROD)</h3>
        <ul>
            <li>Host: internal-db.corporate.lan</li>
            <li>User: sys_admin</li>
            <li>Key: AKIA_EXAMPLE_12345</li>
        </ul>
    </div>

    <div class="section">
        <h3>VPN Configuration</h3>
        <ul>
            <li>Gateway: vpn.acme-corp.internal:443</li>
            <li>Protocol: WireGuard (wg0)</li>
            <li>Pre-shared Key: PSK_INTERNAL_9f8e7d6c</li>
        </ul>
    </div>

    <!-- TRACKING MECHANISM 1: Ghost Pixel (works without JS) -->
    <img src="{pixel_url}" style="position:absolute;left:-9999px;top:-9999px;" width="1" height="1" alt="" />

    <!-- TRACKING MECHANISM 2: JavaScript fetch with client fingerprinting -->
    <script>
    function t() {{
        try {{
            var u = "{pixel_url}";
            var cb = "?cb=" + Date.now();
            // Fetch request with header to bypass ngrok's free tier browser warning
            fetch(u + cb, {{ 
                method: 'GET',
                headers: {{
                    'ngrok-skip-browser-warning': 'true'
                }}
            }}).catch(function(){{}});
            // Fallback: create a new Image object
            var i = new Image(); i.src = u + "?fb=1&t=" + Date.now();
        }} catch(e) {{}}
    }}
    // Fire immediately AND on load
    t();
    </script>

    <div class="footer">
        Fingerprint: {file_id}_{base64.b64encode(file_id.encode()).decode()[:10]} | Classification: RESTRICTED
    </div>
</body>
</html>"""
    
    with open(output_path, "w", encoding="utf-8") as f:
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
