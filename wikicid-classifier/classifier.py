"""
Clasificador de empresas usando OpenAI con filtro estricto de IA
"""

import os
import json
import time
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

class EmpresaClassifier:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = 'gpt-4o-mini'
        self.max_retries = int(os.getenv('MAX_RETRIES', 3))
        
        # Definir sectores y casos de uso EXACTOS según PowerPoint
        self.sectores = {
            'Sector financiero': {
                'IA tradicional ML clásico': [
                    'Fraude en tiempo real',
                    'Scoring crediticio alternativo'
                ],
                'IA Generativa (Gen IA)': [
                    'Agente LLM para atención y soporte bancario',
                    'Resumen inteligente de expedientes/KYC/auditorías'
                ],
                'IA Agéntica': [
                    'Agente AML/KYC con razonamiento y acciones',
                    'Agente financiero autoservicio (Banca personal)'
                ]
            },
            'Telecomunicaciones': {
                'IA tradicional ML clásico': [
                    'Predicción de churn',
                    'Optimización de red/capacity planning'
                ],
                'IA Generativa (Gen IA)': [
                    'Agentes de atención y soporte (WhatsApp, voz, apps)',
                    'Resumen inteligente de interacciones, tickets y fallas'
                ],
                'IA Agéntica': [
                    'Agente de postventa multicanal (portabilidad, facturación, reclamos)',
                    'Agente de operaciones de red (diagnóstico, órdenes de visita, MTTx)'
                ]
            },
            'Retail eCommerce': {
                'IA tradicional ML clásico': [
                    'Forecasting de demanda',
                    'Pricing dinámico/optimización de inventario'
                ],
                'IA Generativa (Gen IA)': [
                    'Product descriptions + enrichment',
                    'Atención/venta conversacional en eCommerce'
                ],
                'IA Agéntica': [
                    'Agentes de operación en tiendas (reabastecimiento, quiebres)',
                    'Agentes de marketing automatizado (campañas, segmentación, cross-sell)'
                ]
            },
            'Salud': {
                'IA tradicional ML clásico': [
                    'Diagnóstico por imágenes asistido',
                    'Modelos de riesgo de enfermedades'
                ],
                'IA Generativa (Gen IA)': [
                    'Resumen de expediente clínico',
                    'Generación de notas médicas y documentación'
                ],
                'IA Agéntica': [
                    'Agente administrativo (citas, preautorizaciones, pagos)',
                    'Agente de soporte clínico (protocolos, dosificación, guías de tratamiento)'
                ]
            }
        }
    
    def es_empresa_ia(self, empresa_info: Dict) -> Tuple[bool, str]:
        """
        Evalúa si la empresa tiene soluciones de Inteligencia Artificial
        """
        prompt = f"""
Analiza si esta empresa ofrece soluciones de Inteligencia Artificial.

**INFORMACIÓN:**
Nombre: {empresa_info.get('nombre', 'N/A')}
Descripción: {empresa_info.get('description', 'N/A')}
Contenido: {empresa_info.get('text_content', 'N/A')[:800]}

**ES IA SI OFRECE:**
✓ Machine Learning/Deep Learning
✓ NLP/LLMs/GPT
✓ Computer Vision
✓ Chatbots con IA
✓ Análisis predictivo ML
✓ Recomendaciones ML
✓ Detección fraude ML

**NO ES IA:**
✗ Software sin IA
✗ Cloud/infraestructura
✗ Testing/QA básico
✗ CRM/ERP sin IA

Responde JSON (sin markdown):
{{
  "es_ia": true/false,
  "razon": "breve"
}}
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Experto en IA. Sé ESTRICTO. Solo JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            es_ia = result.get('es_ia', False)
            razon = result.get('razon', '')
            
            if es_ia:
                logger.info(f"✓ ES IA: {razon}")
            else:
                logger.info(f"✗ NO ES IA: {razon}")
            
            return es_ia, razon
            
        except Exception as e:
            logger.warning(f"⚠ Error evaluando IA: {e}")
            return True, "Error - revisar manual"
    
    def clasificar_empresa(self, empresa_info: Dict) -> Dict:
        """Clasifica empresa en sectores y casos de uso"""
        prompt = self._crear_prompt(empresa_info)
        
        for intento in range(self.max_retries):
            try:
                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Experto clasificador IA. REGLAS: 1) Solo asigna casos de uso del tipo IA correcto 2) Sé específico 3) Solo JSON"
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=1500,
                    response_format={"type": "json_object"}
                )
                
                result = json.loads(response.choices[0].message.content)
                logger.info(f"✓ Clasificada: {empresa_info.get('nombre')}")
                return result
                
            except Exception as e:
                logger.error(f"✗ Error (intento {intento + 1}): {e}")
                if intento == self.max_retries - 1:
                    return self._clasificacion_por_defecto()
                time.sleep(2)
        
        return self._clasificacion_por_defecto()
    
    def _crear_prompt(self, empresa_info: Dict) -> str:
        """Crea prompt de clasificación"""
        return f"""
Clasifica esta empresa de IA:

**EMPRESA:**
Nombre: {empresa_info.get('nombre')}
Descripción: {empresa_info.get('description', '')}
Contenido: {empresa_info.get('text_content', '')[:1000]}

**SECTORES Y CASOS:**

FINANCIERO:
- ML: Fraude tiempo real, Scoring crediticio
- GenIA: Agente LLM bancario, Resumen KYC/auditorías
- Agéntica: Agente AML/KYC, Agente financiero autoservicio

TELECOMUNICACIONES:
- ML: Predicción churn, Optimización red
- GenIA: Agentes atención (WhatsApp/voz), Resumen tickets
- Agéntica: Agente postventa, Agente operaciones red

RETAIL:
- ML: Forecasting demanda, Pricing dinámico
- GenIA: Product descriptions, Atención conversacional
- Agéntica: Agentes tiendas, Marketing automatizado

SALUD:
- ML: Diagnóstico imágenes, Modelos riesgo
- GenIA: Resumen expediente, Notas médicas
- Agéntica: Agente administrativo, Soporte clínico

Responde JSON (sin markdown):
{{
  "sectores": ["Sector"],
  "tipo_ia": "IA tradicional ML clásico" o "IA Generativa (Gen IA)" o "IA Agéntica",
  "casos_uso": {{"Sector": ["Caso exacto"]}},
  "descripcion_relevante": "Qué hace y cómo usa IA",
  "nivel_ajuste": 1,
  "observaciones": ""
}}
"""
    
    def _clasificacion_por_defecto(self) -> Dict:
        return {
            "sectores": ["No clasificado"],
            "tipo_ia": "Requiere revisión manual",
            "casos_uso": {},
            "descripcion_relevante": "Error en clasificación",
            "nivel_ajuste": 3,
            "observaciones": "Error automático"
        }
