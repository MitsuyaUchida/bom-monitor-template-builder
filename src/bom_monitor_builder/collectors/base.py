from abc import ABC, abstractmethod

from bom_monitor_builder.models.discovery import EventLogInfo, ServiceInfo


class Collector(ABC):
    @abstractmethod
    def collect_services(self) -> list[ServiceInfo]:
        raise NotImplementedError

    @abstractmethod
    def collect_event_logs(self) -> list[EventLogInfo]:
        raise NotImplementedError
