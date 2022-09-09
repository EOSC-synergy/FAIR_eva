import logging
import sys
from bs4 import BeautifulSoup
from flask_babel import gettext as _l
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus.tables import Table
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from datetime import datetime
from PyPDF2 import PdfFileMerger
from io import BytesIO

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


'''
Define un estilo de párrafo según el color introducido.
'''


def def_style(color):
    style = ParagraphStyle('second_title',
                           fontName="Helvetica",
                           fontSize=14,
                           alignment=1,
                           spaceAfter=10,
                           textColor=color)
    return style


'''
Pasa a formato RGB dado un código de color comenzando por #
'''


def color_to_rgb(color, alpha=None):
    if color.startswith('#'):
        return (*(int(color[i:i + 2], 16) / 255 for i in range(1, 6, 2)), 1 if alpha is None else alpha)
    raise ValueError('invalid color string')


'''
Crea un pdf con el mensaje sobre descargo de responsabilidad y con los logos dados en logos_CSIC.
    logos_CSIC: png con los logos a incluir.
    name_pdf: nombre con el que se guardará el pdf.
    estilos: lista de estilos para los párrafos.
'''


def create_last_page(logos_CSIC, name_pdf, estilos):
    doc_lastpage = SimpleDocTemplate(name_pdf, pagesize=letter,
                                     rightMargin=72, leftMargin=72,
                                     topMargin=72, bottomMargin=18)
    Story_lastpage = []

    Story_lastpage.append(Paragraph('Descargo de responsabilidad:', estilos["JustifyRight12Bold"]))
    Story_lastpage.append(Paragraph('''Los resultados de los tests estan basados en datos y código preeliminar
    que continúa en desarrollo.''', estilos["JustifyRight11"]))
    Story_lastpage.append(Spacer(1, 500))
    logos = Image(logos_CSIC, 7 * inch, 0.7 * inch)
    Story_lastpage.append(logos)
    doc_lastpage.build(Story_lastpage)


def merge_pdf(pdf1, pdf2, name_file):
    # Une los pdfs pdf1 y pdf2 y guarda el resultado en un fichero llamado name_file.
    pdfs = [pdf1, pdf2]
    nombre_archivo_salida = name_file
    fusionador = PdfFileMerger()

    for pdf in pdfs:
        fusionador.append(open(pdf, 'rb'))

    with open(nombre_archivo_salida, 'wb') as salida:
        fusionador.write(salida)


def bar_FAIR(data):
    # Diagrama de barras con el porcentaje de Findable, Accessible, Interoperable y Reusable obtenido.
    drawing = Drawing(500, 200)
    data_barplot = [(data['findable']['result']['points'], data['accessible']['result']['points'],
                     data['interoperable']['result']['points'], data['reusable']['result']['points'])]
    bc = VerticalBarChart()
    bc.valueAxis.labels.fontName = 'Helvetica'
    bc.categoryAxis.labels.fontName = 'Helvetica'
    bc.x = 50
    bc.y = 50
    bc.height = 125
    bc.width = 350
    bc.data = data_barplot
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = 100
    bc.valueAxis.valueStep = 20
    bc.barLabelFormat = '%.2f'
    bc.barLabels.nudge = 7

    # Para fillColor hay que pasar el color como RGB o por su nombre (no vale código empezando por #)
    color_f = colors.Color(color_to_rgb(data['findable']['result']['color'])[0],
                           color_to_rgb(data['findable']['result']['color'])[1],
                           color_to_rgb(data['findable']['result']['color'])[2])

    color_a = colors.Color(color_to_rgb(data['accessible']['result']['color'])[0],
                           color_to_rgb(data['accessible']['result']['color'])[1],
                           color_to_rgb(data['accessible']['result']['color'])[2])

    color_i = colors.Color(color_to_rgb(data['interoperable']['result']['color'])[0],
                           color_to_rgb(data['interoperable']['result']['color'])[1],
                           color_to_rgb(data['interoperable']['result']['color'])[2])

    color_r = colors.Color(color_to_rgb(data['reusable']['result']['color'])[0],
                           color_to_rgb(data['reusable']['result']['color'])[1],
                           color_to_rgb(data['reusable']['result']['color'])[2])
    bc.bars[(0, 0)].fillColor = color_f
    bc.bars[(0, 1)].fillColor = color_a
    bc.bars[(0, 2)].fillColor = color_i
    bc.bars[(0, 3)].fillColor = color_r

    bc.categoryAxis.categoryNames = ['Findable', 'Accessible', 'Interoperable', 'Reusable']
    drawing.add(bc)
    return drawing


def bar_rda(data_principle):
    # Diagrama de barras con el porcentaje que se verifica de cada apartado de cada principio FAIR.
    # data_principle peude ser: data_findable, data_accessible, data_interoperable o data_reusable.
    drawing = Drawing(500, 200)
    data_barplot = []
    for key in list(data_principle.keys())[:-1]:
        data_barplot.append(data_principle[key]['score']['earned'])
    data_barplot = [tuple(data_barplot)]

    bc = VerticalBarChart()
    bc.valueAxis.labels.fontName = 'Helvetica'
    bc.categoryAxis.labels.fontName = 'Helvetica'
    bc.x = 50
    bc.y = 50
    bc.height = 125
    bc.width = 400
    bc.data = data_barplot
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = 100
    bc.valueAxis.valueStep = 20
    bc.barLabelFormat = '%.2f'
    bc.barLabels.nudge = 7

    # Para fillColor hay que pasar el color como RGB o por su nombre (no vale código empezando por #
    for i, key in enumerate(list(data_principle.keys())[:-1]):
        bc.bars[(0, i)].fillColor = colors.Color(color_to_rgb(data_principle[key]['color'])[0],
                                                 color_to_rgb(data_principle[key]['color'])[1],
                                                 color_to_rgb(data_principle[key]['color'])[2])

    bc.categoryAxis.categoryNames = list(data_principle.keys())[:-1]
    bc.categoryAxis.labels.boxAnchor = 'ne'
    bc.categoryAxis.labels.dx = 8
    bc.categoryAxis.labels.dy = 2
    bc.categoryAxis.labels.angle = 45
    drawing.add(bc)
    return drawing


def indicator_table(data):
    level = "Optional"
    if data['score']['weight'] == 3:
        level = "Essential"
    elif data['score']['weight'] == 2:
        level = "Recommendable"

    if data['points'] == 100:
        table = [(_l('Indicator Level'), Paragraph(level)),
                 (_l('Indicator Assesment'),
                  Paragraph(_l("%s.indicator" % data['name']))),
                 (_l('Technical Implementation'), Paragraph(_l("%s.technical" % data['name']))),
                 (_l('Technical feedback'), Paragraph(data['msg'][:500]))]
    else:
        st = BeautifulSoup(_l("%s.tips" % data['name']))
        tips = st.get_text()
        table = [(_l('Indicator Level'), Paragraph(level)),
                 (_l('Indicator Assesment'),
                  Paragraph(_l("%s.indicator" % data['name']))),
                 (_l('Technical Implementation'), Paragraph(_l("%s.technical" % data['name']))),
                 (_l('Technical feedback'), Paragraph(data['msg'][:350])),
                 (_l('Tips'), Paragraph(tips))]
    return table


def add_group_indicators(Story, data_indicators, name, estilos):
    Story.append(Paragraph(name, estilos["second_title"]))
    Story.append(Paragraph(str(data_indicators['result']['points']) + '%',
                 def_style(color=data_indicators['result']['color'])))

    for k in data_indicators:
        if k != 'result':
            print(k)
            Story.append(Paragraph(_l(data_indicators[k]['name']), estilos["centerBold"]))
            Story.append(Paragraph(str(data_indicators[k]['score']['earned']) + '%',
                         def_style(color=data_indicators[k]['color'])))
            Story.append(Table(indicator_table(data_indicators[k]), style=[('GRID', (0, 0), (-1, -1), 1, colors.grey),
                         ('BACKGROUND', (0, 2), (1, 2),
                         data_indicators[k]['color'])]))
            Story.append(Spacer(1, 20))
    Story.append(bar_rda(data_indicators))
    return Story


def create_pdf(data, name_pdf_report, logo_FAIR, logos_CSIC):

    report_buffer = BytesIO()
    doc = SimpleDocTemplate(report_buffer, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    Story = []
    # Se incluye la fecha actual y el logo FAIR.
    today = datetime.now()
    date = today.strftime("%b %d %Y %H:%M:%S")
    imagen = Image(logo_FAIR, 2 * inch, 1 * inch)
    Story.append(imagen)

    # Se definen estilos para los párrafos
    estilos = getSampleStyleSheet()
    estilos.add(ParagraphStyle(name='JustifyLeft', alignment=2, fontSize=10, spaceAfter=10, fontName="Helvetica"))
    estilos.add(ParagraphStyle(name='JustifyRight', alignment=0, fontSize=10, spaceAfter=10, fontName="Helvetica"))
    estilos.add(ParagraphStyle(name='JustifyRight11', alignment=0, fontSize=11, spaceAfter=10, fontName="Helvetica"))
    estilos.add(ParagraphStyle(name='JustifyRight12BoldSpace', alignment=0, fontSize=12, spaceAfter=10, fontName="Helvetica-Bold"))
    estilos.add(ParagraphStyle(name='JustifyRight12Bold', alignment=0, fontSize=12, spaceAfter=2, fontName="Helvetica-Bold"))
    estilos.add(ParagraphStyle(name='JustifyRight14', alignment=0, fontSize=14, spaceAfter=10, fontName="Helvetica"))
    estilos.add(ParagraphStyle(name='center', alignment=1, fontSize=10, spaceAfter=10, fontName="Helvetica"))
    estilos.add(ParagraphStyle(name='centerBold', alignment=1, fontSize=11, spaceAfter=10, fontName="Helvetica-Bold"))
    estilos.add(ParagraphStyle(name='centerBoldBox', alignment=1, fontSize=11, spaceAfter=10,
                               fontName="Helvetica-Bold", borderWidth=1, borderColor=colors.grey))

    style = getSampleStyleSheet()
    estilos.add(ParagraphStyle('main_title',
                               fontName="Helvetica-Bold",
                               fontSize=18,
                               parent=style['Heading2'],
                               alignment=1,
                               spaceAfter=10))

    estilos.add(ParagraphStyle('second_title',
                               fontName="Helvetica",
                               fontSize=16,
                               parent=style['Heading2'],
                               alignment=1,
                               spaceAfter=10))

    # Se incluye título y descripción:
    Story.append(Paragraph('FAIR EVA', estilos["main_title"]))
    Story.append(Paragraph('DIGITAL.CSIC', estilos["main_title"]))

    Story.append(Paragraph(date, estilos["JustifyRight12BoldSpace"]))

    url_fair = 'https://www.rd-alliance.org/system/files/FAIR%20Data%20Maturity%20Model_%20specification%20and%20guidelines_v0.90.pdf'
    desc_url_fair = 'RDA FAIR Data Maturity Indicators'
    direccion = '<link href="' + url_fair + '">' + desc_url_fair + '</link>'

    Story.append(Paragraph('DESCRIPCIÓN:', estilos["JustifyRight12Bold"]))
    descripcion = '''FAIR EVA es un servicio web que mide el grado de alineación de los
    objetos digitales (principalmente datos de investigación) disponibles en el repositorio institucional
    DIGITAL.CSIC con los Principios FAIR.''' + ' Se basa en los ' + direccion + ''' y presta especial atención a
    características de repositorios institucionales.'''
    Story.append(Paragraph(descripcion, estilos["JustifyRight11"]))

    Story.append(Paragraph('Principios FAIR', estilos["second_title"]))

    # Gráfico de barras con el porcentaje que se cumple de cada principio FAIR:
    Story.append(bar_FAIR(data))

    # Se añaden las tablas y los gráficos de barras correspondientes a cada principio:
    # FINDABLE:

    Story = add_group_indicators(Story, data['findable'], 'FINDABLE', estilos)
    Story = add_group_indicators(Story, data['accessible'], 'ACCESSIBLE', estilos)
    Story = add_group_indicators(Story, data['interoperable'], 'INTEROPERABLE', estilos)
    Story = add_group_indicators(Story, data['reusable'], 'REUSABLE', estilos)
    logging.debug("StringIO")

    doc.build(Story)  # Se crea el pdf po el reporte

    # Se crea la páfina finial:
    logging.debug("LastPage")
    # name_pdf_last_page = "temp_last_page.pdf"
    # create_last_page(logos_CSIC, name_pdf_last_page, estilos)

    # Se unen los pdfs con el reporte y se añade la página final. Se guarda como un nuevo pdf:
    logging.debug("merge")
    # merge_pdf(name_doc, name_pdf_last_page, name_pdf_report)
    # Se eliminan los dos pdf auxiliares (el que incluye el reporte y el que tiene la página final):
    # remove(name_doc)
    # remove(name_pdf_last_page)

    logging.debug("pdf_output")
    pdf_out = report_buffer.getvalue()
    report_buffer.close()

    return pdf_out
