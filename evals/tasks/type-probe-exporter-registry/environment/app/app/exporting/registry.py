from app.exporting.exporter import Exporter


class UnknownFormatError(LookupError):
    pass


class ExporterRegistry:
    def __init__(self) -> None:
        self._by_format: dict[str, Exporter] = {}

    def register(self, format_name: str, exporter: Exporter) -> None:
        self._by_format[format_name] = exporter

    def get(self, format_name: str) -> Exporter:
        try:
            return self._by_format[format_name]
        except KeyError:
            raise UnknownFormatError(format_name) from None

    def formats(self) -> list[str]:
        return sorted(self._by_format)
