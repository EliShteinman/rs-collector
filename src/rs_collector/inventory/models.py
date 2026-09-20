import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_HOSTNAME_PATTERN = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)(\.(?!-)[a-z0-9-]{1,63}(?<!-))*$")


class Hostname(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: str = Field(min_length=1, max_length=253)

    @model_validator(mode="before")
    @classmethod
    def _accept_plain_string(cls, data: object) -> object:
        if isinstance(data, str):
            return {"value": data}
        return data

    @field_validator("value")
    @classmethod
    def _normalized(cls, value: str) -> str:
        normalized = value.strip().rstrip(".").lower()
        if not _HOSTNAME_PATTERN.match(normalized):
            raise ValueError(f"'{value}' is not a valid hostname")
        return normalized

    def __str__(self) -> str:
        return self.value


class Cluster(BaseModel):
    model_config = ConfigDict(frozen=True)

    fqdn: Hostname
    nodes: tuple[Hostname, ...] = Field(default=())
    environment: str = Field(default="")

    @model_validator(mode="after")
    def _without_duplicate_nodes(self) -> Cluster:
        names = [node.value for node in self.nodes]
        if len(names) != len(set(names)):
            raise ValueError(f"cluster {self.fqdn} lists a node twice")
        return self

    @property
    def name(self) -> str:
        return self.fqdn.value

    def hosts_in_connection_order(self) -> tuple[Hostname, ...]:
        return (self.fqdn, *self.nodes)

    def with_environment(self, environment: str) -> Cluster:
        return self.model_copy(update={"environment": environment})


class Environment(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    clusters: tuple[Cluster, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _without_duplicate_clusters(self) -> Environment:
        names = [cluster.name for cluster in self.clusters]
        if len(names) != len(set(names)):
            raise ValueError(f"environment {self.name} lists a cluster twice")
        return self


class Inventory(BaseModel):
    model_config = ConfigDict(frozen=True)

    environments: tuple[Environment, ...] = Field(default=())

    @model_validator(mode="after")
    def _without_duplicate_environments(self) -> Inventory:
        names = [environment.name for environment in self.environments]
        if len(names) != len(set(names)):
            raise ValueError("an environment is declared twice")
        return self

    @property
    def clusters(self) -> tuple[Cluster, ...]:
        return tuple(
            cluster for environment in self.environments for cluster in environment.clusters
        )

    def environment_names(self) -> tuple[str, ...]:
        return tuple(environment.name for environment in self.environments)

    def environment(self, name: str) -> Environment | None:
        for environment in self.environments:
            if environment.name == name:
                return environment
        return None

    def cluster(self, fqdn: str) -> Cluster | None:
        for cluster in self.clusters:
            if cluster.name == fqdn.lower():
                return cluster
        return None

    def is_empty(self) -> bool:
        return not self.environments
