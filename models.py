import sqlite3
from typing import List, Optional, Dict

class Database:
    def __init__(self, db_name: str = 'habitgain.db'):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabla de categorías
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                icono TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de hábitos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habitos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                descripcion_breve TEXT NOT NULL,
                descripcion_completa TEXT NOT NULL,
                por_que_funciona TEXT NOT NULL,
                categoria_id INTEGER NOT NULL,
                icono TEXT NOT NULL,
                frecuencia TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (categoria_id) REFERENCES categorias (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def seed_data(self):
        """Insertar datos iniciales hardcodeados"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Verificar si ya hay datos
        cursor.execute('SELECT COUNT(*) as count FROM categorias')
        if cursor.fetchone()['count'] > 0:
            conn.close()
            return
        
        # Insertar categorías
        categorias = [
            ('Bienestar', '🍃'),
            ('Salud Física', '💪'),
            ('Productividad', '⚡'),
            ('Mindfulness', '🧘')
        ]
        
        cursor.executemany('INSERT INTO categorias (nombre, icono) VALUES (?, ?)', categorias)
        
        # Insertar hábitos
        habitos = [
            # Bienestar (categoria_id = 1)
            (
                'Meditación Diaria',
                'Diaria',
                'Encuentra calma y reduce estrés dedicando tan solo unos minutos al día.',
                'Mejora tu enfoque, claridad mental y estabilidad emocional a largo plazo mediante la práctica diaria de meditación. Estudios demuestran que solo 10 minutos al día pueden reducir significativamente los niveles de cortisol (hormona del estrés).',
                'Basado en ciencia de atención plena, reestructura el cerebro (neuroplasticidad) para mejorar regulación y concentración.',
                1,
                '🧘‍♀️'
            ),
            (
                'Gratitud Nocturna',
                'Diaria',
                'Anota 3 cosas por las que estás agradecido antes de dormir.',
                'La práctica de gratitud nocturna reprograma tu cerebro para enfocarse en aspectos positivos de tu vida. Escribir tres cosas por las que estás agradecido cada noche mejora la calidad del sueño, reduce la ansiedad y aumenta la sensación de bienestar general.',
                'La psicología positiva demuestra que la gratitud activa el sistema de recompensa del cerebro, liberando dopamina y serotonina, mejorando el estado de ánimo.',
                1,
                '📝'
            ),
            (
                'Respiración Consciente',
                'Diaria',
                'Practica 5 minutos de respiración profunda para calmar tu mente.',
                'La respiración consciente es una técnica simple pero poderosa que activa el sistema nervioso parasimpático, reduciendo inmediatamente el estrés y la ansiedad. Solo 5 minutos al día pueden mejorar tu claridad mental y regulación emocional.',
                'La respiración profunda reduce la frecuencia cardíaca y presión arterial, activando la respuesta de relajación del cuerpo.',
                1,
                '🌬️'
            ),
            
            # Salud Física (categoria_id = 2)
            (
                'Caminata de 10 min',
                'Diaria',
                'Da una caminata breve para activar tu cuerpo y mente.',
                'Una caminata de 10 minutos es suficiente para activar tu circulación, mejorar tu estado de ánimo y aumentar tu energía. No necesitas equipo especial ni mucho tiempo, solo salir y moverte. Ideal para romper el sedentarismo y despejar la mente.',
                'El ejercicio aeróbico ligero libera endorfinas (hormonas de la felicidad) y mejora la función cardiovascular, incluso en sesiones cortas.',
                2,
                '🚶'
            ),
            (
                'Beber Agua (8 vasos)',
                '8 vasos',
                'Mantén tu cuerpo hidratado bebiendo agua regularmente.',
                'La hidratación adecuada es fundamental para el funcionamiento óptimo de tu cuerpo y mente. Beber 8 vasos de agua al día mejora la concentración, energía, digestión y salud de la piel. Establece recordatorios para crear este hábito.',
                'El agua representa el 60% del cuerpo humano y es esencial para todas las funciones celulares, desde el transporte de nutrientes hasta la regulación de temperatura.',
                2,
                '💧'
            ),
            (
                'Estiramientos Matutinos',
                'Mañanera',
                'Despierta tu cuerpo con 5 minutos de estiramientos.',
                'Comenzar el día con estiramientos suaves activa tu circulación, mejora tu flexibilidad y prepara tu cuerpo para el día. Reduce la rigidez muscular, previene lesiones y te ayuda a sentirte más despierto y energizado.',
                'Los estiramientos aumentan el flujo sanguíneo a los músculos, mejorando la oxigenación y reduciendo la tensión acumulada durante el sueño.',
                2,
                '🤸'
            ),
            
            # Productividad (categoria_id = 3)
            (
                'Técnica Pomodoro',
                'Diaria',
                'Trabaja en bloques de 25 minutos con descansos de 5 minutos.',
                'La Técnica Pomodoro te ayuda a mantener el foco y evitar el agotamiento mental. Trabajar en intervalos de 25 minutos seguidos de descansos cortos mejora tu productividad, reduce la procrastinación y mantiene tu mente fresca durante todo el día.',
                'Basado en el funcionamiento de la atención humana, que se mantiene óptima en períodos cortos. Los descansos previenen la fatiga cognitiva.',
                3,
                '⏲️'
            ),
            (
                'Planificación Diaria',
                'Mañanera',
                'Define tus 3 prioridades del día cada mañana.',
                'Identificar tus 3 tareas más importantes cada mañana te ayuda a enfocarte en lo que realmente importa. Esta práctica reduce la sensación de estar abrumado, aumenta tu efectividad y te da una sensación de logro al final del día.',
                'El cerebro funciona mejor con objetivos claros y limitados. Priorizar reduce la carga cognitiva y mejora la toma de decisiones.',
                3,
                '📋'
            ),
            (
                'Desconexión Digital',
                'Nocturna',
                'Apaga dispositivos 1 hora antes de dormir.',
                'Desconectarte de pantallas una hora antes de dormir mejora significativamente la calidad de tu sueño. La luz azul de los dispositivos suprime la melatonina, dificultando el descanso. Este hábito te ayudará a dormir mejor y despertar más renovado.',
                'La luz azul inhibe la producción de melatonina, la hormona del sueño. Eliminar esta exposición mejora los ciclos circadianos naturales.',
                3,
                '📵'
            ),
            
            # Mindfulness (categoria_id = 4)
            (
                'Escaneo Corporal',
                'Diaria',
                'Dedica 5 minutos a escanear sensaciones en tu cuerpo.',
                'El escaneo corporal es una práctica de mindfulness que te ayuda a conectar con tu cuerpo y detectar tensiones o incomodidades. Esta técnica reduce el estrés, mejora la conciencia corporal y te ayuda a relajarte profundamente.',
                'La práctica de body scan activa la interocepción (conciencia de sensaciones internas), reduciendo la respuesta de estrés y mejorando la regulación emocional.',
                4,
                '🧘'
            ),
            (
                'Comida Consciente',
                'Diaria',
                'Come al menos una comida sin distracciones, enfocándote en sabores.',
                'Comer conscientemente mejora tu relación con la comida, ayuda a la digestión y te permite disfrutar más de tus alimentos. Eliminar distracciones durante las comidas te ayuda a reconocer señales de saciedad y prevenir el comer en exceso.',
                'El mindful eating mejora la digestión y el reconocimiento de señales de hambre/saciedad, reduciendo patrones de alimentación emocional.',
                4,
                '🍽️'
            ),
            (
                'Observación de Pensamientos',
                'Diaria',
                'Observa tus pensamientos sin juzgarlos durante 5 minutos.',
                'Esta práctica de mindfulness te ayuda a tomar distancia de tus pensamientos y emociones, reconociendo que no eres tus pensamientos. Mejora la claridad mental, reduce la rumiación y aumenta tu capacidad de responder (no reaccionar) ante situaciones difíciles.',
                'La metacognición (pensar sobre el pensamiento) permite desidentificarse de patrones mentales negativos, reduciendo ansiedad y depresión.',
                4,
                '💭'
            )
        ]
        
        cursor.executemany('''
            INSERT INTO habitos 
            (nombre, frecuencia, descripcion_breve, descripcion_completa, por_que_funciona, categoria_id, icono) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', habitos)
        
        conn.commit()
        conn.close()


class Categoria:
    @staticmethod
    def get_all() -> List[Dict]:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM categorias ORDER BY nombre')
        categorias = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return categorias
    
    @staticmethod
    def get_by_id(categoria_id: int) -> Optional[Dict]:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM categorias WHERE id = ?', (categoria_id,))
        categoria = cursor.fetchone()
        conn.close()
        return dict(categoria) if categoria else None


class Habito:
    @staticmethod
    def get_all() -> List[Dict]:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT h.*, c.nombre as categoria_nombre, c.icono as categoria_icono
            FROM habitos h
            JOIN categorias c ON h.categoria_id = c.id
            ORDER BY h.nombre
        ''')
        habitos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return habitos
    
    @staticmethod
    def get_by_id(habito_id: int) -> Optional[Dict]:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT h.*, c.nombre as categoria_nombre, c.icono as categoria_icono
            FROM habitos h
            JOIN categorias c ON h.categoria_id = c.id
            WHERE h.id = ?
        ''', (habito_id,))
        habito = cursor.fetchone()
        conn.close()
        return dict(habito) if habito else None
    
    @staticmethod
    def get_by_categoria(categoria_id: int) -> List[Dict]:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT h.*, c.nombre as categoria_nombre, c.icono as categoria_icono
            FROM habitos h
            JOIN categorias c ON h.categoria_id = c.id
            WHERE h.categoria_id = ?
            ORDER BY h.nombre
        ''', (categoria_id,))
        habitos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return habitos
    
    @staticmethod
    def search(query: str) -> List[Dict]:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        search_term = f'%{query}%'
        cursor.execute('''
            SELECT h.*, c.nombre as categoria_nombre, c.icono as categoria_icono
            FROM habitos h
            JOIN categorias c ON h.categoria_id = c.id
            WHERE h.nombre LIKE ? OR h.descripcion_breve LIKE ?
            ORDER BY h.nombre
        ''', (search_term, search_term))
        habitos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return habitos