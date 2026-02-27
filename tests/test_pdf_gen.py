import sys
import os
import time

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.honeypot import HoneypotSession, PDFReportHandler

def test_pdf_generation():
    print("Initializing test session...")
    session = HoneypotSession()
    
    # Run some demo commands to populate history
    commands = ["whoami", "ls -la /etc", "cat /etc/passwd", "sudo su", "nmap -sV 10.0.0.1"]
    for cmd in commands:
        session.process_command(cmd)
    
    print("Generating report data...")
    report = session.generate_report("192.168.1.100")
    
    print("Generating PDF...")
    try:
        pdf_handler = PDFReportHandler()
        pdf_bytes = pdf_handler.generate(report)
        
        output_path = os.path.join("backend", "test_hacker_report.pdf")
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        
        print(f"Success! PDF generated at: {output_path}")
        print(f"File size: {len(pdf_bytes)} bytes")
    except Exception as e:
        print(f"FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_generation()
