from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field

from rs_collector.analysis.models import StoredAnalysis
from rs_collector.packages.models import StoredPackage


class RetentionPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    max_age_days: int = Field(gt=0)

    def cutoff(self, now: datetime | None = None) -> datetime:
        return (now or datetime.now(UTC)) - timedelta(days=self.max_age_days)

    def package_expired(self, package: StoredPackage, now: datetime | None = None) -> bool:
        if package.metadata.pinned:
            return False
        return package.metadata.collected_at < self.cutoff(now)

    def analysis_expired(self, analysis: StoredAnalysis, now: datetime | None = None) -> bool:
        if analysis.metadata.pinned:
            return False
        return analysis.metadata.analyzed_at < self.cutoff(now)
