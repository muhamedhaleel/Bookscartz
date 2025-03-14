from io import BytesIO
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

def render_to_pdf(template_src, context_dict={}):
    buffer = BytesIO()
    
    # Create the PDF object using ReportLab with A4 size
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Initialize story for elements
    elements = []
    
    # Custom styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        name='SubTitle',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2C3639')
    ))
    styles.add(ParagraphStyle(
        name='RightAlign',
        parent=styles['Normal'],
        alignment=TA_RIGHT
    ))
    
    # Add header
    elements.append(Paragraph("BOOKSCARTZ BOOKSTORE", styles['CustomTitle']))
    elements.append(Paragraph("INVOICE", styles['SubTitle']))
    elements.append(Spacer(1, 20))
    
    # Add order details in a table
    order = context_dict.get('order')
    order_info = [
        ['Order Number:', f'#{order.id}'],
        ['Date:', order.created_at.strftime('%B %d, %Y')],
        ['Payment Method:', order.payment_method]
    ]
    order_table = Table(order_info, colWidths=[100, 300])
    order_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(order_table)
    elements.append(Spacer(1, 20))
    
    # Add billing address
    elements.append(Paragraph("BILL TO", styles['Heading3']))
    address = order.billing_address
    address_info = [
        [address.full_name],
        [address.address_line1],
        [address.address_line2] if address.address_line2 else [''],
        [f"{address.city}, {address.state} - {address.pincode}"],
        [f"Phone: {address.phone}"]
    ]
    address_table = Table(address_info, colWidths=[400])
    address_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(address_table)
    elements.append(Spacer(1, 20))
    
    # Create table for order items with improved styling
    data = [['Product Details', 'Quantity', 'Price', 'Total']]
    for item in order.items.all():
        data.append([
            Paragraph(item.product.name, styles['Normal']),
            str(item.quantity),
            f"{item.price}",
            f"{item.total_price}"
        ])
    
    # Simple table style without background colors
    table_style = TableStyle([
        # Header style
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        
        # Content style
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Product name left aligned
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Other columns center aligned
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        
        # Grid style
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.black),  # Thicker line below header
    ])
    
    # Create the table with calculated widths
    table = Table(data, colWidths=[250, 75, 100, 100])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Simple summary table style
    summary_data = []
    summary_data.append(['Subtotal:', f"{order.subtotal}"])
    if order.total_discount > 0:
        summary_data.append(['Discount:', f"{order.total_discount}"])
    shipping = "Free" if order.subtotal >= 999 else "50"
    summary_data.append(['Shipping:', shipping])
    summary_data.append(['Total:', f"{order.total_amount}"])
    
    summary_table = Table(summary_data, colWidths=[100, 100])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -2), 10),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
    ]))
    
    # Create a table to align the summary table to the right
    wrapper = Table([[summary_table]], colWidths=[525])
    wrapper.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
    ]))
    elements.append(wrapper)
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF from buffer and return it
    pdf = buffer.getvalue()
    buffer.close()
    return pdf 