from datetime import datetime

_TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"
_SEPARATOR = "__"


class PackageNamer:
    def name_for(self, cluster_fqdn: str, collected_at: datetime) -> str:
        return f"{cluster_fqdn}{_SEPARATOR}{collected_at.strftime(_TIMESTAMP_FORMAT)}"
