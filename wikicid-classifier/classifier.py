"""
Clasificador de empresas usando OpenAI
"""

import os
import json
import time
from typing import Dict, List, Optional
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
        self.model = 'gpt-4o-mini'  # Modelo más económico y rápido
        self.max_retries = int(os.getenv('MAX_RETRIES', 3))
        
        # Definir sectores y casos de uso
        self.sectores = {
            'Sector financiero': [
                'Fraude en tiempo real',
                'Scoring crediticio alternativo',
                'Agente LLM para atención y soporte bancario',
                'Resumen inteligente de expedientes/KYC/auditorías',
                'Agente AML/KYC con razonamiento y acciones',
                'Agente financiero autoservicio (Banca personal)',
                'Predicción de churn',
                'Predicción de red/capacity planning'
            ],
            'Telecomunicaciones': [
                'Agentes de atención y soporte (Whatsapp, voz, apps)',
                'Resumen inteligente de interacciones, tickets y fallas',
                'Agente de postventa multicanal (portabilidad, facturación)',
                'Agente de operaciones de red (diagnóstico, órdenes de trabajo)',
                'Forecasting de demanda',
                'Pricing dinámico/optimización de inventario'
            ],
            'Retail eCommerce': [
                'Product descriptions + enrichment',
                'Atención/venta conversacional en eCommerce',
                'Agentes de operación en tiendas (reabastecimiento, quiebres)',
                'Agente de marketing automatizado (campañas, segmentación, cross-sell)',
                'Diagnóstico por imágenes asistido',
                'Modelos de riesgo de enfermedades'
            ],
            'Salud': [
                'Resumen de expediente clínico',
                'Generación de notas médicas y documentación',
                'Agente administrativo (citas, preautorizaciones, pagos)',
                'Agente de soporte clínico (protocolos, dosificación, guías)'
            ]
        }
        
        self.tipos_ia = [
            'IA tradicional ML clásico',
            'IA Generativa (Gen IA)',
            'IA Agéntica'
        ]
    
    def clasificar_empresa(self, empresa_info: Dict) -> Dict:
        """
        Clasifica una empresa en sectores, tipo de IA y casos de uso
        """
        prompt = self._crear_prompt(empresa_info)
        
        for intento in range(self.max_retries):
            try:
                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Eres un experto en clasificación de empresas de tecnología e inteligencia artificial. Tu tarea es clasificar empresas según su sector de aplicación, tipo de IA que desarrollan, y casos de uso específicos. Responde SOLO con un JSON válido, sin texto adicional."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=1500,
                    response_format={"type": "json_object"}
                )
                
                result = json.loads(response.choices[0].message.content)
                logger.info(f"✓ Empresa clasificada: {empresa_info.get('nombre', 'Desconocida')}")
                
                return result
                
            except json.JSONDecodeError as e:
                logger.warning(f"⚠ Error decodificando JSON (intento {intento + 1}/{self.max_retries}): {e}")
                if intento == self.max_retries - 1:
                    return self._clasificacion_por_defecto()
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"✗ Error en clasificación (intento {intento + 1}/{self.max_retries}): {e}")
                if intento == self.max_retries - 1:
                    return self._clasificacion_por_defecto()
                time.sleep(2)
        
        return self._clasificacion_por_defecto()
    
    def _crear_prompt(self, empresa_info: Dict) -> str:
        """Crea el prompt para la clasificación"""
        
        sectores_str = "\n".join([f"- {sector}: {', '.join(casos)}" 
                                  for sector, casos in self.sectores.items()])
        tipos_ia_str = "\n".join([f"- {tipo}" for tipo in self.tipos_ia])
        
        prompt = f"""
Analiza la siguiente información de una empresa y clasifícala:

**INFORMACIÓN DE LA EMPRESA:**
Nombre: {empresa_info.get('nombre', 'N/A')}
Website: {empresa_info.get('website', 'N/A')}
Título: {empresa_info.get('title', 'N/A')}
Descripción: {empresa_info.get('description', 'N/A')}
Meta descripción: {empresa_info.get('meta_description', 'N/A')}
H1 Tags: {empresa_info.get('h1_tags', 'N/A')}
Keywords: {empresa_info.get('keywords', 'N/A')}
Contenido: {empresa_info.get('text_content', 'N/A')[:500]}

**SECTORES DISPONIBLES Y SUS CASOS DE USO:**
{sectores_str}

**TIPOS DE IA:**
{tipos_ia_str}

Donde:
- IA tradicional ML clásico: Machine Learning clásico, predicción, análisis de datos
- IA Generativa (Gen IA): Generación de contenido, LLMs, ChatGPT-like, síntesis
- IA Agéntica: Agentes autónomos que pueden realizar acciones, tomar decisiones, workflows

**INSTRUCCIONES:**
1. Identifica a qué sector(es) pertenece (puede ser múltiple)
2. Determina el tipo de IA principal
3. Asigna los casos de uso específicos que aplican (pueden ser varios)
4. Proporciona una descripción relevante breve (1-2 líneas)
5. Indica nivel de ajuste (1=perfecto, 2=bueno, 3=aceptable)

Responde ÚNICAMENTE con este JSON (sin markdown, sin ```json):
{{
  "sectores": ["Sector 1", "Sector 2"],
  "tipo_ia": "Tipo de IA principal",
  "casos_uso": {{
    "Sector 1": ["Caso de uso 1", "Caso de uso 2"],
    "Sector 2": ["Caso de uso X"]
  }},
  "descripcion_relevante": "Descripción breve de la empresa y su solución",
  "nivel_ajuste": 1,
  "observaciones": "Observaciones adicionales si las hay"
}}
"""
        return prompt
    
    def _clasificacion_por_defecto(self) -> Dict:
        """Retorna una clasificación por defecto en caso de error"""
        return {
            "sectores": ["No clasificado"],
            "tipo_ia": "Requiere revisión manual",
            "casos_uso": {},
            "descripcion_relevante": "Clasificación automática fallida - requiere revisión manual",
            "nivel_ajuste": 3,
            "observaciones": "Error en clasificación automática"
        }

def test_classifier():
    """Función de prueba"""
    classifier = EmpresaClassifier()
    
    test_empresa = {
        'nombre': '247.ai',
        'website': 'https://www.247.ai',
        'title': '247.ai - AI-Powered Customer Service',
        'description': 'Conversational AI platform for customer service automation using natural language processing and machine learning.',
        'meta_description': 'Transform customer experience with AI chatbots and virtual agents',
        'h1_tags': 'Customer Service AI | Conversational AI Platform',
        'keywords': 'AI, chatbot, customer service, automation',
        'text_content': '247.ai provides artificial intelligence solutions for customer service including chatbots, virtual agents, and conversational AI platforms for enterprises.'
    }
    
    print("\n🧪 Probando clasificador con empresa de prueba...\n")
    resultado = classifier.clasificar_empresa(test_empresa)
    
    print("✅ Resultado de clasificación:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_classifier()
