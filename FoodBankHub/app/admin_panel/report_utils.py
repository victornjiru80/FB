"""
Shared PDF branding utilities for FoodBankHub reports.

Provides consistent header, table styling, summary sections, and page numbering
across all exported PDF reports.

Table width: Use make_full_width_table() for all data tables so they automatically
use the full landscape A4 content width (no unused left/right space). Pass
col_weights for relative column widths, or None for equal columns.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    HRFlowable, PageBreak
)
from reportlab.platypus.doctemplate import BaseDocTemplate
from io import BytesIO
import datetime
from django.http import HttpResponse


# ── Brand colours ──────────────────────────────────────────────────
BRAND_DARK_BLUE = colors.HexColor("#1F4E78")
BRAND_GREEN = colors.HexColor("#059669")
BRAND_LIGHT_BLUE = colors.HexColor("#E8F0FE")
BRAND_LIGHT_GRAY = colors.HexColor("#F3F4F6")
BRAND_MEDIUM_GRAY = colors.HexColor("#6B7280")
BRAND_WHITE = colors.white
BRAND_BLACK = colors.black

# Default PDF margins (points)
DEFAULT_LEFT_MARGIN_PT = 12
DEFAULT_RIGHT_MARGIN_PT = 12
DEFAULT_TOP_MARGIN_PT = 20
DEFAULT_BOTTOM_MARGIN_PT = 30

# Backward-compatible aggregate horizontal margin
_DEFAULT_LEFT_RIGHT_MARGIN_PT = DEFAULT_LEFT_MARGIN_PT + DEFAULT_RIGHT_MARGIN_PT
LANDSCAPE_A4_CONTENT_WIDTH_PT = landscape(A4)[0] - _DEFAULT_LEFT_RIGHT_MARGIN_PT


# ── Reusable paragraph styles ─────────────────────────────────────
def get_report_styles():
    """Return a dict of named ParagraphStyles used across all reports."""
    styles = getSampleStyleSheet()

    brand_title = ParagraphStyle(
        'BrandTitle',
        parent=styles['Heading1'],
        fontSize=22,
        leading=26,
        spaceAfter=2,
        alignment=TA_CENTER,
        textColor=BRAND_DARK_BLUE,
        fontName='Helvetica-Bold',
    )

    tagline = ParagraphStyle(
        'Tagline',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        spaceAfter=8,
        alignment=TA_CENTER,
        textColor=BRAND_MEDIUM_GRAY,
        fontName='Helvetica-Oblique',
    )

    report_title = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading2'],
        fontSize=15,
        leading=18,
        spaceAfter=6,
        alignment=TA_CENTER,
        textColor=BRAND_DARK_BLUE,
        fontName='Helvetica-Bold',
    )

    meta_style = ParagraphStyle(
        'Meta',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        spaceAfter=4,
        alignment=TA_LEFT,
        textColor=BRAND_BLACK,
    )

    wrap_style = ParagraphStyle(
        'CellWrap',
        fontSize=7.5,
        leading=9.5,
        alignment=TA_LEFT,
    )

    wrap_center = ParagraphStyle(
        'CellWrapCenter',
        fontSize=7.5,
        leading=9.5,
        alignment=TA_CENTER,
    )

    summary_heading = ParagraphStyle(
        'SummaryHeading',
        parent=styles['Heading3'],
        fontSize=11,
        leading=14,
        spaceBefore=10,
        spaceAfter=4,
        textColor=BRAND_DARK_BLUE,
        fontName='Helvetica-Bold',
    )

    summary_item = ParagraphStyle(
        'SummaryItem',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
    )

    return {
        'brand_title': brand_title,
        'tagline': tagline,
        'report_title': report_title,
        'meta': meta_style,
        'wrap': wrap_style,
        'wrap_center': wrap_center,
        'summary_heading': summary_heading,
        'summary_item': summary_item,
        'normal': styles['Normal'],
    }


# ── Header builder ─────────────────────────────────────────────────
def build_report_header(elements, report_title, generated_for, total_records,
                        active_filters=None, styles_dict=None):
    """
    Append the branded header block to *elements*.

    Parameters
    ----------
    elements : list
        The flowable list being built for the PDF document.
    report_title : str
        e.g. "My Requests Report"
    generated_for : str
        Recipient / user display name.
    total_records : int
    active_filters : dict | None
        {display_label: value} for any non-default filters.
    styles_dict : dict | None
        If None, ``get_report_styles()`` is called.
    """
    if styles_dict is None:
        styles_dict = get_report_styles()

    # Brand name
    elements.append(Paragraph("FOODBANKHUB", styles_dict['brand_title']))
    elements.append(Paragraph("Connecting Donors to Communities", styles_dict['tagline']))

    # Horizontal rule
    elements.append(HRFlowable(
        width="100%", thickness=1.5, color=BRAND_DARK_BLUE,
        spaceAfter=10, spaceBefore=4,
    ))

    # Report title
    elements.append(Paragraph(report_title, styles_dict['report_title']))
    elements.append(Spacer(1, 4))

    # Metadata block
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    meta_lines = [
        f"<b>Generated for:</b> {generated_for}",
        f"<b>Generated on:</b> {now_str}",
        f"<b>Total Records:</b> {total_records}",
    ]

    if active_filters:
        filter_parts = [f"{k}: {v}" for k, v in active_filters.items() if v]
        if filter_parts:
            meta_lines.append(f"<b>Active Filters:</b> {', '.join(filter_parts)}")

    elements.append(Paragraph("<br/>".join(meta_lines), styles_dict['meta']))
    elements.append(Spacer(1, 8))

    # Second rule before the table
    elements.append(HRFlowable(
        width="100%", thickness=0.75, color=BRAND_MEDIUM_GRAY,
        spaceAfter=10, spaceBefore=2,
    ))


# ── Table style builder ───────────────────────────────────────────
def get_branded_table_style(row_count):
    """
    Return a ``TableStyle`` with the FoodBankHub branded look.

    - Dark-blue header row with white text
    - Alternating light-blue / white data rows
    - Thin grey grid
    """
    style_commands = [
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_DARK_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), BRAND_WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
        ('TOPPADDING', (0, 0), (-1, 0), 7),

        # Data rows defaults
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7.5),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),

        # Grid
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
        ('LINEBELOW', (0, 0), (-1, 0), 1.2, BRAND_DARK_BLUE),
    ]

    # Alternating row colours
    for i in range(1, row_count):
        bg = BRAND_LIGHT_BLUE if i % 2 == 0 else BRAND_WHITE
        style_commands.append(('BACKGROUND', (0, i), (-1, i), bg))

    return TableStyle(style_commands)


# ── Full-width table helper ──────────────────────────────────────
def make_full_width_table(
    data,
    repeat_rows=0,
    col_weights=None,
    pagesize=None,
    left_margin=None,
    right_margin=None,
):
    """
    Build a ReportLab Table that uses the full content width for the target page size.

    Column widths are computed so the table fills the page (no unused left/right
    space). Use this for all data tables in PDF reports so they auto-adjust.

    Parameters
    ----------
    data : list of lists
        Table data (e.g. [header_row, ...data_rows]).
    repeat_rows : int
        Number of top rows to repeat on each page (e.g. 1 for header).
    col_weights : list of float, optional
        Relative width of each column (same length as number of columns).
        If None, all columns get equal width.
    pagesize : tuple, optional
        ReportLab page size tuple (width, height). Defaults to landscape(A4).

    Returns
    -------
    Table
    """
    if not data:
        return Table(data)
    ncols = len(data[0])
    if col_weights is None:
        col_weights = [1.0] * ncols
    if pagesize is None:
        pagesize = landscape(A4)
    if left_margin is None:
        left_margin = DEFAULT_LEFT_MARGIN_PT
    if right_margin is None:
        right_margin = DEFAULT_RIGHT_MARGIN_PT
    content_width = pagesize[0] - (left_margin + right_margin)
    total = sum(col_weights)
    col_widths = [(w / total) * content_width for w in col_weights]
    return Table(data, colWidths=col_widths, repeatRows=repeat_rows)


# ── Summary builder ────────────────────────────────────────────────
def build_report_summary(elements, summary_items, styles_dict=None):
    """
    Append a summary section to *elements*.

    Parameters
    ----------
    summary_items : list of (label, value)
        e.g. [("Total Requests", 42), ("Pending", 5), ...]
    """
    if styles_dict is None:
        styles_dict = get_report_styles()

    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(
        width="100%", thickness=0.75, color=BRAND_MEDIUM_GRAY,
        spaceAfter=6, spaceBefore=4,
    ))
    elements.append(Paragraph("Summary", styles_dict['summary_heading']))

    # Build a small two-column table for the summary
    data = [[Paragraph(f"<b>{label}:</b>", styles_dict['summary_item']),
             Paragraph(str(value), styles_dict['summary_item'])]
            for label, value in summary_items]

    if data:
        t = Table(data, colWidths=[1.8 * inch, 1.2 * inch], hAlign='LEFT')
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(t)


# ── Page-number footer callback ────────────────────────────────────
def _footer_callback(canvas, doc):
    """Draw page number and brand on every page."""
    canvas.saveState()

    page_width = doc.pagesize[0]
    y = 14

    # Left: brand
    canvas.setFont('Helvetica-Oblique', 7)
    canvas.setFillColor(BRAND_MEDIUM_GRAY)
    canvas.drawString(doc.leftMargin, y, "FoodBankHub Reports")

    # Right: page number
    canvas.drawRightString(
        page_width - doc.rightMargin, y,
        f"Page {canvas.getPageNumber()}"
    )

    canvas.restoreState()


# ── Document builder helper ────────────────────────────────────────
def build_pdf_document(
    elements,
    filename_prefix,
    user_display_name,
    pagesize=None,
    left_margin=DEFAULT_LEFT_MARGIN_PT,
    right_margin=DEFAULT_RIGHT_MARGIN_PT,
    top_margin=DEFAULT_TOP_MARGIN_PT,
    bottom_margin=DEFAULT_BOTTOM_MARGIN_PT,
):
    """
    Build and return a Django ``HttpResponse`` containing the PDF.

    Parameters
    ----------
    elements : list
        Fully constructed list of ReportLab flowables.
    filename_prefix : str
        e.g. "my_requests" – timestamp is appended automatically.
    user_display_name : str
        Used in the filename.

    Returns
    -------
    HttpResponse
    """
    buffer = BytesIO()
    if pagesize is None:
        pagesize = landscape(A4)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=pagesize,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
    )

    doc.build(elements, onFirstPage=_footer_callback, onLaterPages=_footer_callback)
    buffer.seek(0)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = user_display_name.replace(' ', '_')[:30]
    filename = f"{safe_name}_{filename_prefix}_{timestamp}.pdf"

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ── Utility: collect active filters for display ────────────────────
def collect_active_filters(request, filter_keys):
    """
    Given a Django *request* and a list of GET-parameter names,
    return a dict of {display_label: value} for non-default filters.

    ``filter_keys`` is a list of (param_name, display_label) tuples.
    """
    active = {}
    for param, label in filter_keys:
        val = request.GET.get(param, '').strip()
        if val and val != 'all':
            active[label] = val
    return active
