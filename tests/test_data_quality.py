from dataclasses import replace,FrozenInstanceError
from datetime import timedelta
import pytest
from core.scientific.data_quality import assess_quality,unavailable_quality,SourceError
from tests.test_multi_market_capture import freeze,cycle,rows,T


def test_exact_factual_span_skew_age(tmp_path,monkeypatch):
    freeze(tmp_path,monkeypatch); body=rows(); body[0]['time']-=2000
    c=cycle(tmp_path,monkeypatch,body)
    q=assess_quality(c,as_of=c.completed_at+timedelta(seconds=10))
    assert q.state=='COMPLETE' and q.capture_span_seconds==2
    assert q.member_timestamp_skew_seconds==2 and q.oldest_evidence_age_seconds==3615
    assert q.oldest_available_age_seconds==10 and q.clock_state=='LOCAL_CONTINUITY_ONLY'
    assert q.source_errors==() and q.missing_members==()
    with pytest.raises(FrozenInstanceError): q.state='OTHER'


def test_missing_and_unknown_not_zero(tmp_path,monkeypatch):
    freeze(tmp_path,monkeypatch); body=rows()[1:]; del body[0]['time']
    c=cycle(tmp_path,monkeypatch,body); q=assess_quality(c,as_of=c.completed_at)
    assert q.state=='INCOMPLETE' and len(q.missing_members)==1
    assert q.member_timestamp_skew_seconds is None and q.oldest_evidence_age_seconds is None
    assert q.unknown_timestamp_members==(body[0]['symbol'],)


def test_no_rewrite_of_prior_span(tmp_path,monkeypatch):
    freeze(tmp_path,monkeypatch); c=cycle(tmp_path,monkeypatch)
    c=replace(c,completed_at=c.started_at+timedelta(seconds=82.39547))
    q=assess_quality(c,as_of=c.completed_at)
    assert q.capture_span_seconds==82.39547
    with pytest.raises(ValueError): assess_quality(c,as_of=c.completed_at-timedelta(microseconds=1))


def test_unobserved_error_is_explicit():
    q=unavailable_quality(as_of=T,source_error=SourceError.NETWORK_FAILURE)
    assert q.capture_span_seconds is None and q.clock_state=='UNKNOWN'
    assert q.source_errors==(SourceError.NETWORK_FAILURE,) and len(q.missing_members)==5
    with pytest.raises(TypeError): unavailable_quality(as_of=T,source_error='profitable')
