import pytest

from rs_collector.analysis.options import AnalysisDepth
from rs_collector.exceptions.web import BadRequestError
from rs_collector.web.http import Request
from rs_collector.web.requests import AnalyzeRequest, CollectRequest

pytestmark = pytest.mark.unit


def test_a_cluster_is_read_from_the_form() -> None:
    assert CollectRequest.parse({"cluster": "c1.example.com"}).cluster == "c1.example.com"


def test_a_missing_cluster_is_refused() -> None:
    with pytest.raises(BadRequestError):
        CollectRequest.parse({})


def test_the_default_analysis_adds_no_flags() -> None:
    asked = AnalyzeRequest.parse({"package": "p1", "depth": "default"})

    assert asked.options().flags == ()


def test_a_blank_database_means_every_database() -> None:
    asked = AnalyzeRequest.parse({"package": "p1", "bdb": "  "})

    assert asked.bdb_id is None


def test_a_database_number_becomes_a_flag() -> None:
    asked = AnalyzeRequest.parse({"package": "p1", "bdb": "5"})

    assert asked.options().flags == ("--bdb", "5")


def test_a_checked_mask_box_becomes_a_flag() -> None:
    asked = AnalyzeRequest.parse({"package": "p1", "mask": "yes"})

    assert "--mask" in asked.options().flags


def test_the_depth_is_read_from_the_form() -> None:
    asked = AnalyzeRequest.parse({"package": "p1", "depth": "max"})

    assert asked.depth is AnalysisDepth.MAX


def test_an_unknown_depth_is_refused() -> None:
    with pytest.raises(BadRequestError):
        AnalyzeRequest.parse({"package": "p1", "depth": "deepest"})


def test_a_reverse_proxy_prefix_is_used_for_links() -> None:
    request = Request.parse("GET", "/", headers={"X-Forwarded-Prefix": "/rsc/"})

    assert request.url("/collect") == "/rsc/collect"
