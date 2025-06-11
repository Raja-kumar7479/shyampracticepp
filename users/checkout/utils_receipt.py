from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas 
from io import BytesIO
import time
import hmac
import hashlib
import base64
import os

DOWNLOAD_SECRET = os.getenv("DOWNLOAD_SECRET_KEY", "replace-this-secret").encode()

def generate_pdf_receipt(username, email, phone, payment_id, purchases, discount,
                         original_price, final_amount, payment_mode, status):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(name='SmallGrey', fontSize=9, textColor=colors.grey))
    styles.add(ParagraphStyle(name='SectionTitle', fontSize=12, leading=14, spaceBefore=12, spaceAfter=6,
                              textColor=colors.HexColor("#333333"), fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name='ValueBold', fontSize=10, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name='Footer', fontSize=8, textColor=colors.grey, alignment=1))
    styles.add(ParagraphStyle(name='Header', fontSize=18, leading=22, alignment=0,
                              textColor=colors.HexColor("#008080"), fontName="Helvetica-Bold"))

    elements = []

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

    elements.append(Spacer(1, 12))
    elements.append(Table([[ "" ]], colWidths=[510], style=[
        ('LINEABOVE', (0, 0), (0, 0), 1, colors.HexColor("#008080"))
    ]))
    elements.append(Spacer(1, 16))

    elements.append(Paragraph("CUSTOMER & PAYMENT DETAILS", styles['SectionTitle']))
    user_info_data = [
        ["Name:", username, "Payment Status:", Paragraph(f'<b>{status}</b>', styles['Normal'])],
        ["Email:", email, "Payment Method:", payment_mode.title()],
        ["Phone:", phone, "Payment Date:", time.strftime('%d %b %Y %H:%M:%S')],
    ]
    user_table = Table(user_info_data, colWidths=[50, 260, 100, 100])
    user_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(user_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("PURCHASED ITEMS", styles['SectionTitle']))
    data = [["Course Code", "Title", "Price (INR)"]]
    for item in purchases:
        code = item.get("course_code", "")
        title = item.get("title", "")
        subtitle = item.get("subtitle", "")
        price = float(item.get("price", 0))

        data.append([code, Paragraph(title, styles['Normal']), f"INR {price:,.2f}"])
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

    elements.append(Paragraph("PAYMENT SUMMARY", styles['SectionTitle']))
    discount_amount = round(original_price * discount / 100, 2)

    payment_data = [
        ["Subtotal", f"INR {original_price:,.2f}"],
        [f"Discount ({discount}%)", f"- INR {discount_amount:,.2f}"],
        ["", ""],
        ["Total Amount", f"INR {final_amount:,.2f}"],
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

    footer_text = f"""
    <para align=center spaceb=3>
    <font size=9 color=#666666>
    Thank you for your purchase!<br/>
    For any questions regarding this receipt, please contact support@shyampracticepaper.com<br/><br/>
    Invoice generated on {time.strftime('%d %b %Y')} • © {time.strftime('%Y')} Shyam Practice Paper. All rights reserved.
    </font>
    </para>
    """
    elements.append(Paragraph(footer_text, styles['Normal']))

    def add_paid_stamp(canvas_obj, doc_obj):
        if status.lower() == 'paid':
            canvas_obj.saveState()
            
            hex_color = "#7CAFAF"
            r = int(hex_color[1:3], 16) / 255.0
            g = int(hex_color[3:5], 16) / 255.0
            b = int(hex_color[5:7], 16) / 255.0
            
            canvas_obj.setFillColor(colors.Color(r, g, b, alpha=0.2)) 
            canvas_obj.setStrokeColor(colors.HexColor("#008080"))
            canvas_obj.setLineWidth(3)

            radius = 60
            center_x = A4[0] / 2
            center_y = A4[1] / 2

            # Draw circle
            canvas_obj.circle(center_x, center_y, radius, fill=1, stroke=1)

            # Add 'PAID' text
            canvas_obj.setFillColor(colors.HexColor("#008080")) # Teal color
            canvas_obj.setFont("Helvetica-Bold", 48) # Large and bold font
            canvas_obj.drawCentredString(center_x, center_y - 20, "PAID") # Adjust Y for centering

            canvas_obj.restoreState()

    doc.build(elements, onFirstPage=add_paid_stamp, onLaterPages=add_paid_stamp)
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
