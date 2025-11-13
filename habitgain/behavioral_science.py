"""
HU-17: Behavioral Science Module
Sistema de mensajes motivacionales y refuerzos conductuales
"""
import random
from typing import Dict, Any
from datetime import date, timedelta


class MotivationalMessages:
    """
    Generador de mensajes motivacionales basados en ciencia conductual.
    Los mensajes se adaptan al rendimiento y estado del usuario.
    """

    # Mensajes para nuevos usuarios o usuarios empezando
    WELCOME_MESSAGES = [
        {
            "icon": "🌱",
            "title": "¡Bienvenido a tu viaje!",
            "text": "Formar un hábito es un maratón, no un sprint. ¡Cada día cuenta!",
            "subtext": "Los primeros días son los más importantes."
        },
        {
            "icon": "🎯",
            "title": "Pequeños pasos, grandes logros",
            "text": "No subestimes el poder de la consistencia diaria.",
            "subtext": "Un 1% mejor cada día = 37x mejor en un año."
        },
        {
            "icon": "💪",
            "title": "Tu cerebro aprende con repetición",
            "text": "Cada vez que completas un hábito, refuerzas las conexiones neuronales.",
            "subtext": "La neuroplasticidad está de tu lado."
        },
        {
            "icon": "⭐",
            "title": "Empieza hoy, no mañana",
            "text": "El mejor momento para plantar un árbol fue hace 20 años. El segundo mejor momento es ahora.",
            "subtext": "Tu yo del futuro te lo agradecerá."
        }
    ]

    # Mensajes para usuarios con racha activa (2-6 días)
    BUILDING_MESSAGES = [
        {
            "icon": "🔥",
            "title": "¡Tu racha está creciendo!",
            "text": "Estás construyendo momentum. ¡No rompas la cadena!",
            "subtext": "Cada día que mantienes la racha, más fácil se vuelve."
        },
        {
            "icon": "🚀",
            "title": "Vas por buen camino",
            "text": "Los estudios muestran que después de 21 días, un comportamiento se vuelve automático.",
            "subtext": "Sigue adelante, cada día suma."
        },
        {
            "icon": "💎",
            "title": "La constancia es tu superpoder",
            "text": "No es lo que hacemos de vez en cuando, es lo que hacemos consistentemente lo que moldea nuestras vidas.",
            "subtext": "Tu disciplina está pagando dividendos."
        },
        {
            "icon": "⚡",
            "title": "El poder de la repetición",
            "text": "Tu cerebro está creando nuevos caminos neuronales con cada repetición.",
            "subtext": "Estás reprogramando tus hábitos automáticos."
        }
    ]

    # Mensajes para usuarios con racha fuerte (7+ días)
    STRONG_MESSAGES = [
        {
            "icon": "🏆",
            "title": "¡Eres imparable!",
            "text": "Tu racha es impresionante. Estás en el 10% superior de usuarios comprometidos.",
            "subtext": "La excelencia es un hábito, y tú lo estás dominando."
        },
        {
            "icon": "👑",
            "title": "Maestría en progreso",
            "text": "Has convertido la disciplina en tu segunda naturaleza.",
            "subtext": "Los hábitos fuertes crean personas excepcionales."
        },
        {
            "icon": "🎖️",
            "title": "Nivel experto desbloqueado",
            "text": "Tu compromiso es inspirador. Sigue siendo un ejemplo de constancia.",
            "subtext": "El éxito es la suma de pequeños esfuerzos repetidos día tras día."
        },
        {
            "icon": "⚡",
            "title": "Momentum imparable",
            "text": "Has demostrado que la transformación real viene de la acción consistente.",
            "subtext": "No te detengas ahora, estás en tu mejor momento."
        }
    ]

    # Mensajes para usuarios que no han completado hábitos recientemente
    ENCOURAGEMENT_MESSAGES = [
        {
            "icon": "🌤️",
            "title": "Un nuevo comienzo",
            "text": "Cada día es una oportunidad para volver a empezar. ¡Hoy es tu día!",
            "subtext": "El fracaso es solo una oportunidad para comenzar de nuevo con más inteligencia."
        },
        {
            "icon": "💫",
            "title": "No te rindas",
            "text": "Los campeones no se hacen en los gimnasios. Se hacen con algo profundo: voluntad.",
            "subtext": "Tu próximo intento podría ser el que lo cambie todo."
        },
        {
            "icon": "🎯",
            "title": "Enfócate en hoy",
            "text": "No te preocupes por la racha perdida. Lo importante es lo que haces hoy.",
            "subtext": "Cada momento es una nueva oportunidad."
        },
        {
            "icon": "🌈",
            "title": "El progreso no es lineal",
            "text": "Los retrocesos son parte del proceso. Lo que importa es que sigas avanzando.",
            "subtext": "La resiliencia es más importante que la perfección."
        }
    ]

    # Mensajes para días específicos (fin de semana, etc.)
    WEEKEND_MESSAGES = [
        {
            "icon": "🎉",
            "title": "¡Fin de semana productivo!",
            "text": "Los fines de semana son perfectos para reforzar tus hábitos sin la presión del trabajo.",
            "subtext": "Aprovecha este tiempo para ti."
        }
    ]

    # Mensajes de logro especial
    MILESTONE_MESSAGES = {
        7: {
            "icon": "🎊",
            "title": "¡Primera semana completada!",
            "text": "Has mantenido tu racha por 7 días. ¡Esto es solo el comienzo!",
            "subtext": "La primera semana es la más difícil. ¡Lo lograste!"
        },
        21: {
            "icon": "🏅",
            "title": "¡21 días de constancia!",
            "text": "Según la ciencia, has dado un paso importante hacia convertir esto en un hábito automático.",
            "subtext": "Tu cerebro está cambiando. ¡Sigue así!"
        },
        30: {
            "icon": "🌟",
            "title": "¡Un mes completo!",
            "text": "Has demostrado un compromiso extraordinario. ¡Estás en el camino correcto!",
            "subtext": "Solo el 8% de las personas llegan aquí."
        },
        66: {
            "icon": "💪",
            "title": "¡Hábito automático!",
            "text": "Estudios muestran que 66 días es el promedio para automatizar un hábito. ¡Lo lograste!",
            "subtext": "Ahora es parte de quién eres."
        },
        100: {
            "icon": "🚀",
            "title": "¡LEYENDA: 100 días!",
            "text": "Has alcanzado un nivel élite de constancia. ¡Eres una inspiración!",
            "subtext": "Tu disciplina es inquebrantable."
        }
    }

    @staticmethod
    def get_message_for_user(stats: Dict[str, Any]) -> Dict[str, str]:
        """
        Obtiene un mensaje personalizado basado en las estadísticas del usuario.

        Args:
            stats: {
                "max_streak": int - racha más alta del usuario
                "total_habits": int - total de hábitos activos
                "completed_today": int - hábitos completados hoy
                "days_active": int - días con al menos un hábito completado en los últimos 7 días
                "is_weekend": bool - si es fin de semana
            }

        Returns:
            Dict con el mensaje motivacional (icon, title, text, subtext)
        """
        max_streak = stats.get("max_streak", 0)
        completed_today = stats.get("completed_today", 0)
        total_habits = stats.get("total_habits", 0)
        days_active = stats.get("days_active", 0)
        is_weekend = stats.get("is_weekend", False)

        # Mensajes especiales para hitos (milestones)
        if max_streak in MotivationalMessages.MILESTONE_MESSAGES:
            return MotivationalMessages.MILESTONE_MESSAGES[max_streak]

        # Fin de semana y usuario activo
        if is_weekend and days_active >= 5:
            return random.choice(MotivationalMessages.WEEKEND_MESSAGES)

        # Usuario nuevo o sin racha
        if max_streak == 0 or total_habits == 0:
            return random.choice(MotivationalMessages.WELCOME_MESSAGES)

        # Usuario con racha fuerte
        if max_streak >= 7:
            return random.choice(MotivationalMessages.STRONG_MESSAGES)

        # Usuario construyendo racha
        if max_streak >= 2:
            return random.choice(MotivationalMessages.BUILDING_MESSAGES)

        # Usuario que necesita ánimo
        if days_active <= 2:
            return random.choice(MotivationalMessages.ENCOURAGEMENT_MESSAGES)

        # Default: mensaje de bienvenida
        return random.choice(MotivationalMessages.WELCOME_MESSAGES)


def calculate_user_motivation_stats(user_email: str, habits: list, completed_today_ids: set, days_completed: int) -> Dict[str, Any]:
    """
    Calcula estadísticas para el sistema de mensajes motivacionales.

    Args:
        user_email: email del usuario
        habits: lista de hábitos activos
        completed_today_ids: set de IDs de hábitos completados hoy
        days_completed: días con al menos un hábito completado en los últimos 7 días

    Returns:
        Dict con estadísticas para generar mensajes
    """
    from .models import Completion

    # Calcular racha máxima entre todos los hábitos
    max_streak = 0
    for habit in habits:
        streak = Completion.get_current_streak(habit["id"], user_email)
        if streak > max_streak:
            max_streak = streak

    # Detectar si es fin de semana
    today = date.today()
    is_weekend = today.weekday() >= 5  # 5 = Sábado, 6 = Domingo

    return {
        "max_streak": max_streak,
        "total_habits": len(habits),
        "completed_today": len(completed_today_ids),
        "days_active": days_completed,
        "is_weekend": is_weekend
    }
