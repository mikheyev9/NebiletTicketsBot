from typing import List, Tuple
from collections import namedtuple

def calculate_percentage(event_result: namedtuple) -> float:
    """
    Вычисляет процент мероприятий с доступными билетами.

    :param event_result: Экземпляр EventResult, содержащий информацию о мероприятии
    :return: Процент мероприятий с билетами
    """
    if event_result.total_events_count > 0:
        return (event_result.events_with_tickets_count / event_result.total_events_count) * 100
    return 0.0

def calculate_average_percentage(previous_results: List[Tuple[int, int]]) -> float:
    """
    Вычисляет средний процент мероприятий с доступными билетами за предыдущие проверки.

    :param previous_results: Список кортежей с данными предыдущих проверок (events_with_tickets_count, total_events_count)
    :return: Средний процент мероприятий с билетами
    """
    previous_percentages = [
        (events_with_tickets_count / total_events_count) * 100
        if total_events_count > 0
        else 0
        for events_with_tickets_count, total_events_count
        in previous_results
    ]
    if previous_percentages:
        return sum(previous_percentages) / len(previous_percentages)
    return 0.0

def calculate_percentage_drop(average_previous_percentage: float,
                              current_percentage: float) -> float:
    """
    Вычисляет падение процента мероприятий с билетами по сравнению со средним значением предыдущих проверок.

    :param average_previous_percentage: Средний процент мероприятий с билетами за предыдущие проверки
    :param current_percentage: Текущий процент мероприятий с билетами
    :return: Разница между средним предыдущим процентом и текущим процентом
    """
    return average_previous_percentage - current_percentage

def were_tickets_available(previous_results: List[Tuple[int, int]]) -> bool:
    """
    Проверяет, были ли билеты доступны на предыдущих проверках.

    :param previous_results: Список кортежей с данными предыдущих проверок (events_with_tickets_count, total_events_count)
    :return: True, если хотя бы на одной из предыдущих проверок были доступны билеты, иначе False
    """
    return any(events_with_tickets_count > 0
               for events_with_tickets_count, total_events_count
               in previous_results)