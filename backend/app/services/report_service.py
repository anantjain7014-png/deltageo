import io
import time
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from PIL import Image

from backend.app.schemas.detection import DetectedCluster, DetectionMetrics

class ReportService:
    """
    Reporting and GIS Vector Export Service.
    Generates GeoJSON features and PDF analytical reports from AI detections.
    """

    @staticmethod
    def generate_geojson(
        clusters: List[DetectedCluster], 
        metrics: DetectionMetrics,
        image_shape: tuple[int, int] = (256, 256)
    ) -> Dict[str, Any]:
        """
        Converts detected human activity clusters to a standard GeoJSON FeatureCollection.
        Coordinates are normalized to [0..100] spatial units or projected bounding boxes.
        """
        features = []
        for cluster in clusters:
            min_x, min_y, max_x, max_y = cluster.bbox
            
            # Create polygon ring
            coordinates = [[
                [min_x, min_y],
                [max_x, min_y],
                [max_x, max_y],
                [min_x, max_y],
                [min_x, min_y]
            ]]

            feature = {
                "type": "Feature",
                "id": cluster.id,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": coordinates
                },
                "properties": {
                    "cluster_id": cluster.id,
                    "category": cluster.category,
                    "confidence": cluster.confidence,
                    "area_sq_meters": cluster.area_sq_meters,
                    "area_hectares": cluster.area_hectares,
                    "severity": cluster.severity,
                    "centroid": cluster.centroid,
                    "sensor": metrics.sensor_type
                }
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "metadata": {
                "title": "Anthropogenic Change Detection Vector Map",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "sensor": metrics.sensor_type,
                "total_change_area_sq_m": metrics.total_change_area_sq_meters,
                "total_clusters": metrics.total_clusters,
                "dominant_activity": metrics.dominant_activity
            },
            "features": features
        }

    @staticmethod
    def generate_pdf_report(
        metrics: DetectionMetrics,
        clusters: List[DetectedCluster],
        t1_bytes: bytes,
        t2_bytes: bytes,
        overlay_bytes: bytes
    ) -> bytes:
        """
        Generates a comprehensive PDF audit report with summary telemetry and detection tables.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter, 
            rightMargin=36, 
            leftMargin=36, 
            topMargin=36, 
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0f172a")
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=colors.HexColor("#64748b")
        )
        section_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=10,
            spaceAfter=6
        )

        story = []

        # 1. Header & Metadata
        story.append(Paragraph("SATELLITE CHANGE DETECTION AUDIT REPORT", title_style))
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph(f"Problem Statement: Anthropogenic Activity Change Monitoring | Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}", subtitle_style))
        story.append(Spacer(1, 0.2 * inch))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=12))

        # 2. Executive Summary Metrics Table
        story.append(Paragraph("Executive Summary & Telemetry", section_style))
        summary_data = [
            [
                Paragraph("<b>Sensor Platform:</b>", styles['Normal']),
                Paragraph(str(metrics.sensor_type), styles['Normal']),
                Paragraph("<b>Total Area Analyzed:</b>", styles['Normal']),
                Paragraph(f"{metrics.total_image_area_sq_meters:,.0f} m²", styles['Normal'])
            ],
            [
                Paragraph("<b>Anthropogenic Change:</b>", styles['Normal']),
                Paragraph(f"<b>{metrics.total_change_area_sq_meters:,.1f} m²</b> ({metrics.total_change_area_hectares:.3f} ha)", styles['Normal']),
                Paragraph("<b>Change Percentage:</b>", styles['Normal']),
                Paragraph(f"<b>{metrics.change_percentage:.2f}%</b>", styles['Normal'])
            ],
            [
                Paragraph("<b>Dominant Activity:</b>", styles['Normal']),
                Paragraph(f"{metrics.dominant_activity}", styles['Normal']),
                Paragraph("<b>Detected Clusters:</b>", styles['Normal']),
                Paragraph(f"{metrics.total_clusters} Zones", styles['Normal'])
            ]
        ]
        summary_table = Table(summary_data, colWidths=[130, 140, 130, 140])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 12))

        # 3. Class Distribution Breakdown
        story.append(Paragraph("Human Activity Classification Breakdown", section_style))
        dist_data = [["Activity Category", "Detected Area (m²)", "Percentage of Change"]]
        total_chg = max(1e-5, metrics.total_change_area_sq_meters)
        for cat, area in metrics.class_distribution.items():
            pct = (area / total_chg) * 100.0 if total_chg > 0 else 0.0
            dist_data.append([cat, f"{area:,.1f} m²", f"{pct:.1f}%"])

        dist_table = Table(dist_data, colWidths=[240, 150, 150])
        dist_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(dist_table)
        story.append(Spacer(1, 14))

        # 4. Top Detected Clusters Table
        story.append(Paragraph("Detected Change Zones & Threat Evaluation", section_style))
        cluster_rows = [["ID", "Category", "Confidence", "Area (m²)", "Severity"]]
        for cl in clusters[:10]: # Top 10 clusters
            cluster_rows.append([
                f"#{cl.id}",
                cl.category,
                f"{cl.confidence * 100:.1f}%",
                f"{cl.area_sq_meters:,.1f}",
                cl.severity
            ])

        if len(clusters) == 0:
            cluster_rows.append(["-", "No Anthropogenic Change Detected", "-", "0", "NONE"])

        cl_table = Table(cluster_rows, colWidths=[40, 220, 90, 100, 90])
        cl_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 0), (3, -1), 'RIGHT'),
            ('ALIGN', (4, 0), (4, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(cl_table)

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
