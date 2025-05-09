from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from io import BytesIO
import time
import hmac
import hashlib
import base64
import os

DOWNLOAD_SECRET = os.getenv("DOWNLOAD_SECRET_KEY", "replace-this-secret").encode()

def generate_pdf_receipt(username, email, phone, payment_id, purchases, discount, original_price, final_amount):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(name='SmallGrey', fontSize=9, textColor=colors.grey))
    styles.add(ParagraphStyle(name='SectionTitle', fontSize=12, leading=14, spaceBefore=12, spaceAfter=6, 
                            textColor=colors.HexColor("#333333"), fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name='ValueBold', fontSize=10, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name='Footer', fontSize=8, textColor=colors.grey, alignment=1))
    styles.add(ParagraphStyle(name='header', fontSize=18, leading=22, alignment=0, 
                            textColor=colors.HexColor("#008080"), fontName="Helvetica-Bold"))

    elements = []

    # Header with company branding
    header_data = [
        ["Shyam Practice Paper", "Payment Receipt"],
        ["123 Education Street, New Delhi", f"ID: {payment_id}"]
    ]
    header_table = Table(header_data, colWidths=[350, 150])
    header_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 14),
        ('FONTSIZE', (0, 1), (1, 1), 9),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor("#008080")),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor("#333333")),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('ALIGN', (1, 1), (1, 1), 'RIGHT'),
    ]))
    elements.append(header_table)
    
    # Divider line
    elements.append(Spacer(1, 12))
    elements.append(Table([[ "" ]], colWidths=[510], style=[
        ('LINEABOVE', (0, 0), (0, 0), 1, colors.HexColor("#008080"))
    ]))
    elements.append(Spacer(1, 16))

    # Section: User Info
    elements.append(Paragraph("CUSTOMER INFORMATION", styles['SectionTitle']))
    user_info_data = [
        ["Name:", username],
        ["Email:", email],
        ["Phone:", phone],
        ["Date:", time.strftime('%d %b %Y %H:%M:%S')],
    ]
    user_table = Table(user_info_data, colWidths=[80, 350])
    user_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(user_table)
    elements.append(Spacer(1, 20))

    # Section: Course Details
    elements.append(Paragraph("PURCHASED ITEMS", styles['SectionTitle']))
    data = [["Course Code", "Title", "Price"]]
    for item in purchases:
        code = item.get("course_code", "")
        title = item.get("title", "")
        subtitle = item.get("subtitle", "")
        price = float(item.get("price", 0))

        data.append([code, Paragraph(title, styles['Normal']), f"₹{price:,.2f}"])
        if subtitle:
            data.append(["", Paragraph(f"<font size='9' color='grey'>{subtitle}</font>", styles['Normal']), ""])

    course_table = Table(data, hAlign='LEFT', colWidths=[80, 300, 100])
    course_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#008080")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.white),
    ]))
    elements.append(course_table)
    elements.append(Spacer(1, 20))

    # Section: Payment Summary
    elements.append(Paragraph("PAYMENT SUMMARY", styles['SectionTitle']))
    discount_amount = round(original_price * discount / 100, 2)
    
    payment_data = [
        ["Subtotal", f"₹{original_price:,.2f}"],
        [f"Discount ({discount}%)", f"- ₹{discount_amount:,.2f}"],
        ["", ""],  # Spacer row
        ["Total Amount", f"₹{final_amount:,.2f}"],
    ]
    
    payment_table = Table(payment_data, colWidths=[350, 130])
    payment_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor("#008080")),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor("#008080")),
        ('LINEABOVE', (0, -2), (-1, -2), 0.5, colors.HexColor("#e0e0e0")),
    ]))
    elements.append(payment_table)
    elements.append(Spacer(1, 24))

    # Footer
    footer_text = """
    <para align=center spaceb=3>
    <font size=9 color=#666666>
    Thank you for your purchase!<br/>
    For any questions regarding this receipt, please contact support@shyampracticepaper.com<br/>
    <br/>
    Invoice generated on {date} • © {year} Shyam Practice Paper. All rights reserved.
    </font>
    </para>
    """.format(date=time.strftime('%d %b %Y'), year=time.strftime('%Y'))
    
    elements.append(Paragraph(footer_text, styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer



def generate_download_token(payment_id, expires_in=600):  # 10 mins default
    expiry = int(time.time()) + expires_in
    message = f"{payment_id}:{expiry}".encode()
    signature = hmac.new(DOWNLOAD_SECRET, message, hashlib.sha256).hexdigest()
    token = base64.urlsafe_b64encode(f"{expiry}:{signature}".encode()).decode()
    return token


def verify_download_token(payment_id, token):
    try:
        decoded = base64.urlsafe_b64decode(token).decode()
        expiry_str, received_sig = decoded.split(":")
        expiry = int(expiry_str)
        if time.time() > expiry:
            return False  # expired
        message = f"{payment_id}:{expiry}".encode()
        expected_sig = hmac.new(DOWNLOAD_SECRET, message, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_sig, received_sig)
    except Exception:
        return False
