"""
Generador de Excel con empresas clasificadas por sector
"""

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
import logging
from typing import List, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ExcelGenerator:
    def __init__(self, output_path: str):
        self.output_path = output_path
        
        # Colores para headers
        self.header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        self.header_font = Font(bold=True, color="FFFFFF", size=11)
        
        # Sectores disponibles
        self.sectores = [
            'Sector financiero',
            'Telecomunicaciones',
            'Retail eCommerce',
            'Salud'
        ]
    
    def generar_excel(self, empresas_clasificadas: List[Dict]):
        """
        Genera el Excel con pestañas por sector
        """
        logger.info("📊 Generando Excel con empresas clasificadas...")
        
        # Crear un writer de Excel
        with pd.ExcelWriter(self.output_path, engine='openpyxl') as writer:
            
            # Generar una pestaña por sector
            for sector in self.sectores:
                df_sector = self._crear_dataframe_sector(empresas_clasificadas, sector)
                
                if not df_sector.empty:
                    # Escribir al Excel
                    sheet_name = self._get_sheet_name(sector)
                    df_sector.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Aplicar formato
                    self._aplicar_formato(writer.book[sheet_name])
                    
                    logger.info(f"✓ Pestaña '{sheet_name}' creada con {len(df_sector)} empresas")
            
            # Crear pestaña de resumen
            df_resumen = self._crear_resumen(empresas_clasificadas)
            df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
            self._aplicar_formato(writer.book['Resumen'])
            
            logger.info("✓ Pestaña 'Resumen' creada")
        
        logger.info(f"✅ Excel generado exitosamente: {self.output_path}")
        return self.output_path
    
    def _crear_dataframe_sector(self, empresas: List[Dict], sector: str) -> pd.DataFrame:
        """
        Crea un DataFrame con las empresas de un sector específico
        """
        filas = []
        
        for empresa in empresas:
            clasificacion = empresa.get('clasificacion', {})
            sectores = clasificacion.get('sectores', [])
            
            # Si la empresa pertenece a este sector
            if sector in sectores:
                casos_uso_sector = clasificacion.get('casos_uso', {}).get(sector, [])
                
                # Crear una fila por cada caso de uso
                if casos_uso_sector:
                    for i, caso_uso in enumerate(casos_uso_sector, 1):
                        fila = {
                            'TIPO DE IA': clasificacion.get('tipo_ia', ''),
                            'Casos de uso/ Vertical': caso_uso,
                            'Empresa wikicid': empresa.get('nombre', ''),
                            'Descripcion relevante': clasificacion.get('descripcion_relevante', '') if i == 1 else '',
                            'Nivel de ajuste': clasificacion.get('nivel_ajuste', '') if i == 1 else '',
                            'Observaciones': clasificacion.get('observaciones', '') if i == 1 else ''
                        }
                        filas.append(fila)
                else:
                    # Si no tiene casos de uso específicos, crear una fila genérica
                    fila = {
                        'TIPO DE IA': clasificacion.get('tipo_ia', ''),
                        'Casos de uso/ Vertical': 'General',
                        'Empresa wikicid': empresa.get('nombre', ''),
                        'Descripcion relevante': clasificacion.get('descripcion_relevante', ''),
                        'Nivel de ajuste': clasificacion.get('nivel_ajuste', ''),
                        'Observaciones': clasificacion.get('observaciones', '')
                    }
                    filas.append(fila)
        
        df = pd.DataFrame(filas)
        
        # Ordenar por tipo de IA y luego por caso de uso
        if not df.empty:
            df = df.sort_values(['TIPO DE IA', 'Casos de uso/ Vertical'])
        
        return df
    
    def _crear_resumen(self, empresas: List[Dict]) -> pd.DataFrame:
        """
        Crea un DataFrame de resumen con estadísticas
        """
        resumen_data = {
            'Total de empresas procesadas': len(empresas),
            'Empresas clasificadas exitosamente': len([e for e in empresas if e.get('clasificacion')]),
            'Empresas sin clasificar': len([e for e in empresas if not e.get('clasificacion')]),
        }
        
        # Contar por sector
        for sector in self.sectores:
            count = sum(1 for e in empresas 
                       if sector in e.get('clasificacion', {}).get('sectores', []))
            resumen_data[f'Empresas en {sector}'] = count
        
        # Contar por tipo de IA
        tipos_ia = {}
        for empresa in empresas:
            tipo = empresa.get('clasificacion', {}).get('tipo_ia', 'Sin clasificar')
            tipos_ia[tipo] = tipos_ia.get(tipo, 0) + 1
        
        for tipo, count in tipos_ia.items():
            resumen_data[f'Empresas con {tipo}'] = count
        
        # Convertir a DataFrame
        df = pd.DataFrame([
            {'Métrica': k, 'Valor': v} 
            for k, v in resumen_data.items()
        ])
        
        return df
    
    def _get_sheet_name(self, sector: str) -> str:
        """
        Convierte el nombre del sector a un nombre válido de hoja
        """
        nombres = {
            'Sector financiero': 'Sector financiero',
            'Telecomunicaciones': 'Telecomunicaciones',
            'Retail eCommerce': 'Retail eCommerce',
            'Salud': 'Salud'
        }
        return nombres.get(sector, sector[:31])  # Excel limita a 31 caracteres
    
    def _aplicar_formato(self, worksheet):
        """
        Aplica formato a una hoja de Excel
        """
        # Formatear encabezados
        for cell in worksheet[1]:
            cell.fill = self.header_fill
            cell.font = self.header_font
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        
        # Ajustar anchos de columna
        column_widths = {
            'A': 25,  # TIPO DE IA
            'B': 50,  # Casos de uso
            'C': 30,  # Empresa
            'D': 60,  # Descripción
            'E': 15,  # Nivel
            'F': 40   # Observaciones
        }
        
        for col, width in column_widths.items():
            worksheet.column_dimensions[col].width = width
        
        # Congelar primera fila
        worksheet.freeze_panes = 'A2'

def test_excel_generator():
    """Función de prueba"""
    # Datos de prueba
    empresas_test = [
        {
            'nombre': '247.ai',
            'website': 'https://www.247.ai',
            'clasificacion': {
                'sectores': ['Telecomunicaciones', 'Sector financiero'],
                'tipo_ia': 'IA Generativa (Gen IA)',
                'casos_uso': {
                    'Telecomunicaciones': ['Agentes de atención y soporte (Whatsapp, voz, apps)'],
                    'Sector financiero': ['Agente LLM para atención y soporte bancario']
                },
                'descripcion_relevante': 'Plataforma de IA conversacional para servicio al cliente',
                'nivel_ajuste': 1,
                'observaciones': 'Solución enterprise probada'
            }
        }
    ]
    
    generator = ExcelGenerator('/home/claude/wikicid-classifier/output/test_output.xlsx')
    generator.generar_excel(empresas_test)
    print("✅ Excel de prueba generado")

if __name__ == "__main__":
    test_excel_generator()