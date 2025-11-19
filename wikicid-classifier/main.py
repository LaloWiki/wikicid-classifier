"""
Script principal para clasificar empresas de WikiCID usando IA
"""

import os
import json
import time
import pandas as pd
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import logging

from scraper import WebScraper
from classifier import EmpresaClassifier
from excel_generator import ExcelGenerator

# Configurar logging
log_file = f'logs/proceso_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WikiCIDProcessor:
    def __init__(self):
        self.scraper = WebScraper()
        self.classifier = EmpresaClassifier()
        self.cache_file = 'cache/empresas_procesadas.json'
        self.empresas_procesadas = self._cargar_cache()
        
    def _cargar_cache(self):
        """Carga el cache de empresas ya procesadas"""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _guardar_cache(self):
        """Guarda el cache de empresas procesadas"""
        os.makedirs('cache', exist_ok=True)
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.empresas_procesadas, f, ensure_ascii=False, indent=2)
    
    def procesar_empresas(self, input_file: str, limit: int = None):
        """
        Procesa todas las empresas del archivo Excel
        """
        logger.info("=" * 80)
        logger.info("🚀 INICIANDO PROCESAMIENTO DE EMPRESAS WIKICID")
        logger.info("=" * 80)
        
        # Leer Excel
        df = pd.read_excel(input_file)
        logger.info(f"📁 Archivo cargado: {len(df)} empresas encontradas")
        
        # Aplicar límite si se especifica (para pruebas)
        if limit:
            df = df.head(limit)
            logger.info(f"⚠ Modo prueba: procesando solo {limit} empresas")
        
        # Procesar cada empresa
        empresas_clasificadas = []
        errores = []
        
        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Procesando empresas"):
            empresa_id = str(row['ID'])
            nombre = row['Nombre']
            website = row['Website']
            
            logger.info(f"\n{'='*80}")
            logger.info(f"Procesando #{idx + 1}/{len(df)}: {nombre}")
            logger.info(f"{'='*80}")
            
            # Verificar si ya está en cache
            if empresa_id in self.empresas_procesadas:
                logger.info(f"✓ Empresa ya procesada (usando cache)")
                empresas_clasificadas.append(self.empresas_procesadas[empresa_id])
                continue
            
            # Verificar si tiene website
            if pd.isna(website) or not website:
                logger.warning(f"⚠ No tiene website, saltando...")
                errores.append({
                    'id': empresa_id,
                    'nombre': nombre,
                    'error': 'Sin website'
                })
                continue
            
            try:
                # 1. Extraer información del website
                logger.info(f"🌐 Extrayendo información de: {website}")
                info = self.scraper.extract_info(website, nombre)
                
                if not info:
                    logger.warning(f"⚠ No se pudo extraer información del website")
                    errores.append({
                        'id': empresa_id,
                        'nombre': nombre,
                        'error': 'Error al extraer información del website'
                    })
                    continue
                
                # Agregar datos básicos
                info['id'] = empresa_id
                info['nombre'] = nombre
                info['website'] = website
                
                # 2. Clasificar con IA
                logger.info(f"🤖 Clasificando empresa con IA...")
                clasificacion = self.classifier.clasificar_empresa(info)
                
                # 3. Guardar resultado
                empresa_completa = {
                    'id': empresa_id,
                    'nombre': nombre,
                    'website': website,
                    'info': info,
                    'clasificacion': clasificacion
                }
                
                empresas_clasificadas.append(empresa_completa)
                self.empresas_procesadas[empresa_id] = empresa_completa
                
                # Guardar cache cada 10 empresas
                if (idx + 1) % 10 == 0:
                    self._guardar_cache()
                    logger.info(f"💾 Cache guardado ({len(self.empresas_procesadas)} empresas)")
                
                # Pequeña pausa para no saturar APIs
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Error procesando empresa: {e}")
                errores.append({
                    'id': empresa_id,
                    'nombre': nombre,
                    'error': str(e)
                })
                continue
        
        # Guardar cache final
        self._guardar_cache()
        
        # Generar reporte de errores si los hay
        if errores:
            error_file = f'logs/errores_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(errores, f, ensure_ascii=False, indent=2)
            logger.warning(f"⚠ {len(errores)} empresas con errores. Ver: {error_file}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ PROCESAMIENTO COMPLETADO")
        logger.info("=" * 80)
        logger.info(f"✓ Empresas procesadas: {len(empresas_clasificadas)}")
        logger.info(f"✗ Empresas con errores: {len(errores)}")
        logger.info(f"💾 Cache guardado en: {self.cache_file}")
        
        return empresas_clasificadas
    
    def generar_excel_final(self, empresas_clasificadas: list, output_file: str):
        """
        Genera el Excel final con las empresas clasificadas
        """
        logger.info("\n" + "=" * 80)
        logger.info("📊 GENERANDO EXCEL FINAL")
        logger.info("=" * 80)
        
        generator = ExcelGenerator(output_file)
        excel_path = generator.generar_excel(empresas_clasificadas)
        
        logger.info(f"✅ Excel generado exitosamente: {excel_path}")
        return excel_path

def main():
    """Función principal"""
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║         🤖 CLASIFICADOR DE EMPRESAS WIKICID CON IA 🤖         ║
    ║                                                               ║
    ║                   Powered by Groq AI 🚀                       ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Configuración
    input_file = 'input/empresas_wikicid.xlsx'
    output_file = f'output/empresas_clasificadas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    # Preguntar si es modo prueba
    print("\n¿Deseas ejecutar en modo prueba?")
    print("1. Sí - Procesar solo 10 empresas (prueba rápida)")
    print("2. No - Procesar todas las 801 empresas (proceso completo)")
    
    modo = input("\nSelecciona una opción (1 o 2): ").strip()
    
    limit = 10 if modo == "1" else None
    
    if modo == "1":
        print("\n⚡ Modo PRUEBA activado - Se procesarán solo 10 empresas")
    else:
        print("\n🚀 Modo COMPLETO activado - Se procesarán todas las empresas")
        print("⏱ Tiempo estimado: 45-60 minutos")
    
    input("\nPresiona ENTER para comenzar...")
    
    # Crear processor y ejecutar
    processor = WikiCIDProcessor()
    
    # Procesar empresas
    empresas_clasificadas = processor.procesar_empresas(input_file, limit=limit)
    
    # Generar Excel
    excel_path = processor.generar_excel_final(empresas_clasificadas, output_file)
    
    print(f"""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║                    ✅ PROCESO COMPLETADO ✅                    ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    📊 Excel generado: {excel_path}
    💾 Cache guardado para futuras ejecuciones
    📋 Logs disponibles en: logs/
    
    ¡Listo para entregar a tu líder! 🎉
    """)

if __name__ == "__main__":
    main()
