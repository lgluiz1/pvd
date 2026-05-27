import io
from decimal import Decimal
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.graphics.shapes import Drawing, Line


def gerar_recibo_pdf(fatura):
    """
    Gera um recibo profissional em PDF para uma fatura paga.
    Retorna um buffer (BytesIO) com o PDF pronto.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    elements = []

    # ─── Estilos customizados ───
    title_style = ParagraphStyle(
        'RecTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=2*mm,
        alignment=TA_LEFT,
    )
    subtitle_style = ParagraphStyle(
        'RecSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=1*mm,
    )
    label_style = ParagraphStyle(
        'RecLabel',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#95a5a6'),
    )
    value_style = ParagraphStyle(
        'RecValue',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#2c3e50'),
        fontName='Helvetica-Bold',
    )
    small_style = ParagraphStyle(
        'RecSmall',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#bdc3c7'),
        alignment=TA_CENTER,
    )

    empresa = fatura.empresa

    # ─── Cabecalho ───
    elements.append(Paragraph('RECIBO DE PAGAMENTO', title_style))
    elements.append(Paragraph(f'N. {str(fatura.id)[:8].upper()}', subtitle_style))
    elements.append(Spacer(1, 4*mm))

    # Linha separadora vermelha (igual ao modelo)
    elements.append(HRFlowable(
        width='100%', thickness=3, color=colors.HexColor('#e74c3c'),
        spaceAfter=6*mm
    ))

    # ─── Dados do Cliente e da Fatura ───
    info_data = [
        [
            Paragraph('<b>Cliente</b>', label_style),
            Paragraph('<b>CNPJ</b>', label_style),
            Paragraph('<b>Data Pagamento</b>', label_style),
        ],
        [
            Paragraph(empresa.nome_fantasia, value_style),
            Paragraph(empresa.cnpj if empresa.cnpj else '-', value_style),
            Paragraph(
                fatura.data_pagamento.strftime('%d/%m/%Y') if fatura.data_pagamento else '-',
                value_style
            ),
        ],
        [
            Paragraph('<b>Referencia</b>', label_style),
            Paragraph('<b>Forma Pagamento</b>', label_style),
            Paragraph('<b>Vencimento</b>', label_style),
        ],
        [
            Paragraph(fatura.descricao, value_style),
            Paragraph(
                fatura.get_forma_pagamento_display() if fatura.forma_pagamento else '-',
                value_style
            ),
            Paragraph(fatura.data_vencimento.strftime('%d/%m/%Y'), value_style),
        ],
    ]

    info_table = Table(info_data, colWidths=[6*cm, 5*cm, 5*cm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8*mm))

    # ─── Tabela de Itens ───
    itens = fatura.itens.all()
    # Cabecalho da tabela
    table_header = [
        Paragraph('<b>Qtd</b>', ParagraphStyle('th', parent=styles['Normal'], fontSize=9, textColor=colors.white, fontName='Helvetica-Bold')),
        Paragraph('<b>Descricao</b>', ParagraphStyle('th', parent=styles['Normal'], fontSize=9, textColor=colors.white, fontName='Helvetica-Bold')),
        Paragraph('<b>Valor Unit.</b>', ParagraphStyle('th', parent=styles['Normal'], fontSize=9, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
        Paragraph('<b>Total</b>', ParagraphStyle('th', parent=styles['Normal'], fontSize=9, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
    ]

    table_data = [table_header]
    subtotal = Decimal('0')

    if itens.exists():
        for i, item in enumerate(itens, 1):
            table_data.append([
                Paragraph(str(1), styles['Normal']),
                Paragraph(item.descricao, styles['Normal']),
                Paragraph(f'R$ {item.valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
                          ParagraphStyle('td_right', parent=styles['Normal'], alignment=TA_RIGHT)),
                Paragraph(f'R$ {item.valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
                          ParagraphStyle('td_right', parent=styles['Normal'], alignment=TA_RIGHT)),
            ])
            subtotal += item.valor
    else:
        # Se nao tem itens detalhados, usa o valor total da fatura
        table_data.append([
            Paragraph('1', styles['Normal']),
            Paragraph(fatura.descricao, styles['Normal']),
            Paragraph(f'R$ {fatura.valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
                      ParagraphStyle('td_right', parent=styles['Normal'], alignment=TA_RIGHT)),
            Paragraph(f'R$ {fatura.valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
                      ParagraphStyle('td_right', parent=styles['Normal'], alignment=TA_RIGHT)),
        ])
        subtotal = fatura.valor

    items_table = Table(table_data, colWidths=[1.5*cm, 8*cm, 3.5*cm, 3.5*cm])
    items_table.setStyle(TableStyle([
        # Cabecalho com fundo vermelho
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#c0392b')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
        # Linhas alternadas
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f9f9f9'), colors.white]),
        # Bordas
        ('LINEBELOW', (0,0), (-1,0), 1, colors.HexColor('#c0392b')),
        ('LINEBELOW', (0,-1), (-1,-1), 1, colors.HexColor('#ddd')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 4*mm))

    # ─── Totais ───
    total_style_right = ParagraphStyle('total_r', parent=styles['Normal'], fontSize=11, alignment=TA_RIGHT)
    total_bold_right = ParagraphStyle('total_br', parent=styles['Normal'], fontSize=14, alignment=TA_RIGHT, fontName='Helvetica-Bold', textColor=colors.HexColor('#2c3e50'))

    totals_data = [
        ['', '', Paragraph('Subtotal', total_style_right),
         Paragraph(f'R$ {subtotal:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'), total_style_right)],
        ['', '', Paragraph('<b>TOTAL</b>', total_bold_right),
         Paragraph(f'<b>R$ {fatura.valor:,.2f}</b>'.replace(',', 'X').replace('.', ',').replace('X', '.'), total_bold_right)],
    ]

    totals_table = Table(totals_data, colWidths=[1.5*cm, 8*cm, 3.5*cm, 3.5*cm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
        ('LINEABOVE', (2,1), (-1,1), 2, colors.HexColor('#2c3e50')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 15*mm))

    # ─── Rodape ───
    elements.append(HRFlowable(
        width='100%', thickness=0.5, color=colors.HexColor('#ddd'),
        spaceAfter=4*mm
    ))
    elements.append(Paragraph(
        'Este e um recibo gerado automaticamente pelo sistema PDV Cloud.',
        small_style
    ))
    elements.append(Paragraph(
        f'Emitido em {fatura.updated_at.strftime("%d/%m/%Y %H:%M")} | Luiz Gustavo Tech',
        small_style
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
