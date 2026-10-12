"""
Agenda fictícia do RPA: horários fixos todo dia (ex.: 08:00, 12:00, 18:00),
configuráveis pela variável SIMULATOR_SCHEDULE.
"""

from datetime import date, datetime, time, timedelta

from app.core.config import get_settings


def schedule_times() -> list[time]:
    times = []
    for item in get_settings().simulator_schedule.split(","):
        hour, minute = item.strip().split(":")
        times.append(time(int(hour), int(minute)))
    return sorted(times)


def scheduled_slots(day: date) -> list[datetime]:
    """Horários agendados de um dia, no fuso local."""
    return [datetime.combine(day, t).astimezone() for t in schedule_times()]


def upcoming_slots(now: datetime, count: int = 2) -> list[datetime]:
    slots: list[datetime] = []
    day = now.date()
    while len(slots) < count:
        slots += [slot for slot in scheduled_slots(day) if slot > now]
        day += timedelta(days=1)
    return slots[:count]


def slot_name(slot: datetime) -> str:
    return f"Captura agendada {slot:%Hh%M}".replace("h00", "h")
