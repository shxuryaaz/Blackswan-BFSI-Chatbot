import os
from datetime import datetime
from typing import Dict, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


class PDFGenerator:
    NBFC_NAME = "Horizon Finance Limited"
    NBFC_TAGLINE = "Your Trusted Financial Partner"
    NBFC_ADDRESS = "Corporate Office: Tower A, Financial District, Mumbai - 400051"
    NBFC_REGISTRATION = "RBI Registration No: N-13.02215"

    def __init__(self, output_dir: str = "generated_letters"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()

    def _create_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name='NBFCHeader',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a365d'),
            alignment=TA_CENTER,
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name='NBFCTagline',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#4a5568'),
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='SanctionTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2d3748'),
            alignment=TA_CENTER,
            spaceBefore=20,
            spaceAfter=20,
            borderWidth=1,
            borderColor=colors.HexColor('#cbd5e0'),
            borderPadding=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='LoanBodyText',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=16,
            alignment=TA_JUSTIFY,
            spaceBefore=8,
            spaceAfter=8
        ))
        
        self.styles.add(ParagraphStyle(
            name='Disclaimer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#718096'),
            alignment=TA_JUSTIFY,
            spaceBefore=20,
            spaceAfter=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#4a5568'),
            alignment=TA_CENTER
        ))

    def generate_sanction_letter(
        self,
        customer_name: str,
        loan_amount: float,
        tenure_months: int,
        interest_rate: float,
        emi: float,
        session_id: str
    ) -> str:
        filename = f"sanction_letter_{session_id[:8]}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=1*inch,
            leftMargin=1*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        story = []
        
        story.append(Paragraph(self.NBFC_NAME, self.styles['NBFCHeader']))
        story.append(Paragraph(self.NBFC_TAGLINE, self.styles['NBFCTagline']))
        
        header_data = [[self.NBFC_ADDRESS], [self.NBFC_REGISTRATION]]
        header_table = Table(header_data, colWidths=[6*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#4a5568')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.3*inch))
        
        line_table = Table([['_' * 80]], colWidths=[6*inch])
        line_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#cbd5e0')),
        ]))
        story.append(line_table)
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph("LOAN SANCTION LETTER", self.styles['SanctionTitle']))
        
        today = datetime.now()
        ref_number = f"HFL/{today.strftime('%Y%m%d')}/{session_id[:8].upper()}"
        
        date_ref_data = [
            [f"Date: {today.strftime('%B %d, %Y')}", f"Ref No: {ref_number}"]
        ]
        date_ref_table = Table(date_ref_data, colWidths=[3*inch, 3*inch])
        date_ref_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        story.append(date_ref_table)
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph(f"Dear <b>{customer_name}</b>,", self.styles['LoanBodyText']))
        story.append(Spacer(1, 0.1*inch))
        
        story.append(Paragraph(
            f"We are pleased to inform you that your application for a Personal Loan has been "
            f"<b>APPROVED</b> by {self.NBFC_NAME}. We appreciate the trust you have placed in us "
            f"and are committed to providing you with the best financial services.",
            self.styles['LoanBodyText']
        ))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph("<b>LOAN DETAILS</b>", self.styles['LoanBodyText']))
        
        total_amount = emi * tenure_months
        total_interest = total_amount - loan_amount
        
        loan_data = [
            ["Loan Amount", f"Rs. {loan_amount:,.2f}"],
            ["Interest Rate (Per Annum)", f"{interest_rate}%"],
            ["Loan Tenure", f"{tenure_months} months"],
            ["Monthly EMI", f"Rs. {emi:,.2f}"],
            ["Total Interest Payable", f"Rs. {total_interest:,.2f}"],
            ["Total Amount Payable", f"Rs. {total_amount:,.2f}"],
        ]
        
        loan_table = Table(loan_data, colWidths=[3*inch, 2.5*inch])
        loan_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2d3748')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ]))
        story.append(loan_table)
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph("<b>TERMS AND CONDITIONS</b>", self.styles['LoanBodyText']))
        
        terms = [
            "This sanction is valid for 30 days from the date of issue.",
            "The loan amount will be disbursed to your registered bank account within 3 business days upon completion of documentation.",
            "EMI payment shall commence from the following month of disbursement.",
            "Prepayment of loan is permitted after 6 EMI payments with applicable charges.",
            "All terms are subject to the detailed loan agreement to be executed.",
        ]
        
        for i, term in enumerate(terms, 1):
            story.append(Paragraph(f"{i}. {term}", self.styles['LoanBodyText']))
        
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph(
            "We look forward to a long-lasting relationship with you. Should you have any queries, "
            "please feel free to contact our customer service team.",
            self.styles['LoanBodyText']
        ))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph("Warm Regards,", self.styles['LoanBodyText']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("<b>Authorized Signatory</b>", self.styles['LoanBodyText']))
        story.append(Paragraph(f"{self.NBFC_NAME}", self.styles['LoanBodyText']))
        
        story.append(Spacer(1, 0.5*inch))
        
        disclaimer_text = (
            "<b>DISCLAIMER:</b> This is a system-generated document and does not require a physical signature. "
            "This sanction letter is subject to verification of documents submitted and credit assessment. "
            f"{self.NBFC_NAME} reserves the right to modify or cancel this sanction if any information "
            "provided is found to be incorrect or incomplete. This document is confidential and intended "
            "only for the addressee. Interest rates and terms are subject to change as per RBI guidelines. "
            "Please read all terms and conditions carefully before signing the loan agreement."
        )
        story.append(Paragraph(disclaimer_text, self.styles['Disclaimer']))
        
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(
            f"Toll-Free: 1800-XXX-XXXX | Email: care@horizonfinance.com | Web: www.horizonfinance.com",
            self.styles['Footer']
        ))
        
        doc.build(story)
        
        return filepath

    def get_download_path(self, session_id: str) -> str:
        filename = f"sanction_letter_{session_id[:8]}.pdf"
        return os.path.join(self.output_dir, filename)
