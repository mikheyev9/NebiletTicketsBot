from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple
from collections import namedtuple

MAX_MESSAGE_LENGTH = 4076
@dataclass
class EventMessage:
    header: str = "📈 **Результаты проверки мероприятий** 📈\n\n"
    body: List[str] = field(default_factory=list)
    notifications: List[str] = field(default_factory=list)
    messages: List[Tuple[str, str]] = field(default_factory=list)

    def add(self, site_info: namedtuple, percentage_with_tickets: float) -> None:
        check_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if percentage_with_tickets > 60:
            icon = "🟢"
            warning_icon = ""
        elif 50 < percentage_with_tickets <= 60:
            icon = "🟡"
            warning_icon = ""
        elif 20 < percentage_with_tickets <= 50:
            icon = "🟠"
            warning_icon = ""
        elif 10 < percentage_with_tickets <= 20:
            icon = "🔴"
            warning_icon = ""
        elif 0 <= percentage_with_tickets <= 10:
            icon = "🔴"
            warning_icon = "⚠️"
        else:
            icon = "🔴"
            warning_icon = "⚠️"

        new_message = (
            f"🔹 Сайт: {site_info.site_name}\n"
            f"   ➖ Всего мероприятий: {site_info.total_events_count}\n"
            f"   ➖ Мероприятий с билетами: {icon} {site_info.events_with_tickets_count} "
            f"({percentage_with_tickets:.2f}%) {warning_icon}\n"
            f"   ➖ Время проверки: {check_time}\n\n"
        )
        self._add_to_messages(site_info.site_name, new_message)

    def add_warning(self, site_name: str,
                    percentage_drop: float,
                    need_return=False):
        check_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        warning_message = (
            f"🚨 **Внимание!** На сайте {site_name} количество мероприятий"
            f" с билетами упало на {percentage_drop:.2f}%. Время проверки: {check_time}.\n"
        )
        self._add_to_notifications(warning_message)
        if need_return:
            return warning_message

    def add_available_ticket(self, site_name: str,
                             percentage_with_tickets: float,
                             need_return=False):
        check_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        available_ticket_message = (
            f"🎉 **Внимание!** На сайте {site_name} появились билеты. "
            f"Текущий процент мероприятий с билетами: {percentage_with_tickets:.2f}%. "
            f"Время проверки: {check_time}.\n"
        )
        self._add_to_notifications(available_ticket_message)
        if need_return:
            return available_ticket_message

    def _add_to_messages(self, site_name: str, new_message: str):
        self.messages.append((site_name, new_message))

    def _add_to_notifications(self, new_message: str):
        if (not self.notifications
                or len(self.notifications[-1]) + len(new_message) > MAX_MESSAGE_LENGTH):
            self.notifications.append(new_message)
        else:
            self.notifications[-1] += new_message

    @property
    def message(self):
        sorted_messages = sorted(self.messages, key=lambda x: x[0])
        sorted_body = [message for _, message in sorted_messages]
        full_message = self.header + "".join(sorted_body)
        if self.notifications:
            full_message += "\n".join(self.notifications)
        return full_message

    @property
    def message_parts(self):
        parts = []
        current_part = self.header
        sorted_messages = sorted(self.messages, key=lambda x: x[0])
        sorted_body = [message for _, message in sorted_messages]
        for section in sorted_body + self.notifications:
            if len(current_part) + len(section) > MAX_MESSAGE_LENGTH:
                parts.append(current_part)
                current_part = section
            else:
                current_part += section
        if current_part:
            parts.append(current_part)
        return parts
