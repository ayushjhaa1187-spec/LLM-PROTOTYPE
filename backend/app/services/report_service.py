"""Report Service: Generates PDF Compliance and Risk reports."""

from fpdf import FPDF
import datetime

class ComplianceReport(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 16)
        self.cell(0, 10, "Enterprise Compliance & Risk Report", border=False, align="C")
        self.ln(10)
        self.set_font("helvetica", "I", 10)
        self.cell(0, 10, f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", align="C")
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

def generate_compliance_pdf(data: dict):
    """
    Generates a structured PDF from raw agent data.
    Expects keys: query, answer, contract_analysis, compliance_analysis, confidence
    """
    pdf = ComplianceReport()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Summary Section
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(25, 118, 210)
    pdf.cell(0, 10, "Executive Summary")
    pdf.ln(8)
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 7, f"Query: {data.get('query', 'N/A')}")
    pdf.ln(5)
    pdf.multi_cell(0, 7, f"AI Answer: {data.get('answer', 'N/A')}")
    pdf.ln(10)

    # Compliance Radar Section
    comp = data.get("compliance_analysis")
    if comp:
        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(46, 125, 50)
        pdf.cell(0, 10, "Compliance Radar")
        pdf.ln(8)
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 7, f"Compliance Score: {comp.get('compliance_score', 0)}%")
        pdf.ln(7)
        pdf.set_font("helvetica", "I", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(0, 6, f"Rationale: {comp.get('scoring_rationale', 'N/A')}")
        pdf.ln(5)
        
        pdf.set_font("helvetica", "B", 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 7, "Applicable Regulations:")
        pdf.ln(6)
        pdf.set_font("helvetica", "", 10)
        for reg in comp.get("regulations", []):
            pdf.multi_cell(0, 6, f"- {reg.get('name')} ({reg.get('region')}): {reg.get('impact')}")
        pdf.ln(10)

    # Contract Risks Section
    cont = data.get("contract_analysis")
    if cont:
        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(198, 40, 40)
        pdf.cell(0, 10, "Contract Risk Audit")
        pdf.ln(8)
        pdf.set_font("helvetica", "", 11)
        pdf.set_text_color(0, 0, 0)
        
        for risk in cont.get("risks", []):
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(0, 6, f"Level: {risk.get('level', 'N/A').upper()}")
            pdf.ln(5)
            pdf.set_font("helvetica", "I", 10)
            pdf.multi_cell(0, 6, f"Clause: \"{risk.get('clause')}\"")
            pdf.set_font("helvetica", "", 10)
            pdf.multi_cell(0, 6, f"Reason: {risk.get('reason')}")
            pdf.set_text_color(0, 0, 255)
            pdf.multi_cell(0, 6, f"Remediation: {risk.get('remediation')}")
            pdf.set_text_color(0, 0, 0)
            pdf.ln(3)

    return pdf.output()
