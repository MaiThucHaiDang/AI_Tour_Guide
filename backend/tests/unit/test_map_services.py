import pytest
import math
import httpx
from unittest.mock import patch, MagicMock, AsyncMock
import networkx as nx

from services.map.osrm_service import OSRMService
from services.map.routing import MapRoutingService
from services.map.tour_service import TourService, HUE_CENTER_LAT, HUE_CENTER_LNG

# --- 4.10: osrm_service.py tests ---

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_osrm_get_route_success_converts_lng_lat_to_lat_lng(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "code": "Ok",
        "routes": [{
            "geometry": {"coordinates": [[107.579, 16.467], [107.580, 16.468]]},
            "legs": [{"steps": []}],
            "distance": 100,
            "duration": 50
        }]
    }
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    res = await OSRMService.get_route(16.467, 107.579, 16.468, 107.580)
    assert res["success"] is True
    # OSRM [lng, lat] -> Leaflet [lat, lng]
    assert res["coordinates"] == [[16.467, 107.579], [16.468, 107.580]]

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_osrm_get_route_non_ok_returns_false(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"code": "NoRoute"}
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    res = await OSRMService.get_route(16.467, 107.579, 16.468, 107.580)
    assert res["success"] is False

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_osrm_get_route_http_error_returns_false(mock_get):
    mock_get.side_effect = httpx.RequestError("Network error")
    res = await OSRMService.get_route(16.467, 107.579, 16.468, 107.580)
    assert res["success"] is False

def test_parse_steps_vi_en():
    steps = [
        {"maneuver": {"type": "turn", "modifier": "left"}, "name": "Le Loi", "distance": 100}
    ]
    vi_instr = OSRMService._parse_steps(steps, "vi")
    assert "rẽ trái" in vi_instr[0]
    
    en_instr = OSRMService._parse_steps(steps, "en")
    assert "turn left" in en_instr[0]
    
    assert OSRMService._parse_steps([], "vi") == []

def test_translate_step_vi_depart_left_right_straight_arrive():
    assert "Bắt đầu di chuyển" in OSRMService._translate_step_vi("depart", "", "Lê Lợi", 150)
    assert "Bạn đã đến nơi" in OSRMService._translate_step_vi("arrive", "", "", 0)
    assert "rẽ trái" in OSRMService._translate_step_vi("turn", "left", "", 50)
    assert "rẽ phải" in OSRMService._translate_step_vi("turn", "right", "", 50)
    assert "đi thẳng" in OSRMService._translate_step_vi("continue", "straight", "", 50)

def test_translate_step_en_depart_left_right_straight_arrive():
    assert "Start moving" in OSRMService._translate_step_en("depart", "", "Le Loi", 150)
    assert "You have arrived" in OSRMService._translate_step_en("arrive", "", "", 0)
    assert "turn left" in OSRMService._translate_step_en("turn", "left", "", 50)
    assert "turn right" in OSRMService._translate_step_en("turn", "right", "", 50)
    assert "go straight" in OSRMService._translate_step_en("continue", "straight", "", 50)

# --- 4.11: routing.py tests ---

@patch("services.map.routing.GRAPH_FILE")
def test_load_graph_missing_file_keeps_empty_graph(mock_graph_file):
    mock_graph_file.exists.return_value = False
    svc = MapRoutingService()
    assert svc.graph.number_of_nodes() == 0

@patch("services.map.routing.GRAPH_FILE")
@patch("builtins.open")
@patch("json.load")
def test_load_graph_valid_json_adds_nodes_edges(mock_json, mock_open, mock_graph_file):
    mock_graph_file.exists.return_value = True
    mock_json.return_value = {
        "nodes": [{"id": "n1", "lat": 1.0, "lng": 1.0}, {"id": "n2", "lat": 2.0, "lng": 2.0}],
        "edges": [{"source": "n1", "target": "n2", "weight": 1.5}]
    }
    svc = MapRoutingService()
    assert svc.graph.number_of_nodes() == 2
    assert svc.graph.number_of_edges() == 1

def test_find_nearest_node_empty_graph_returns_none():
    svc = MapRoutingService()
    svc.nodes_data = {}
    assert svc.find_nearest_node(1.0, 1.0) is None

def test_find_nearest_node_returns_closest():
    svc = MapRoutingService()
    svc.nodes_data = {
        "n1": {"lat": 1.0, "lng": 1.0},
        "n2": {"lat": 10.0, "lng": 10.0}
    }
    assert svc.find_nearest_node(1.1, 1.1) == "n1"

def test_calculate_route_empty_graph_fails():
    svc = MapRoutingService()
    svc.graph.clear()
    res = svc.calculate_route(1.0, 1.0, 2.0, 2.0)
    assert res["success"] is False

def test_calculate_route_same_nearest_node_returns_arrived():
    svc = MapRoutingService()
    svc.nodes_data = {"n1": {"lat": 1.0, "lng": 1.0}}
    svc.graph.add_node("n1")
    res = svc.calculate_route(1.0, 1.0, 1.01, 1.01)
    assert res["success"] is True
    assert "Bạn đã ở vị trí gần" in res["instructions"][0]

def test_calculate_route_shortest_path_success():
    svc = MapRoutingService()
    svc.nodes_data = {
        "n1": {"id": "n1", "lat": 1.0, "lng": 1.0, "name": "A"},
        "n2": {"id": "n2", "lat": 2.0, "lng": 2.0, "name": "B"}
    }
    svc.graph.add_edge("n1", "n2", weight=1.0)
    res = svc.calculate_route(1.0, 1.0, 2.0, 2.0)
    assert res["success"] is True
    assert res["coordinates"] == [[1.0, 1.0], [2.0, 2.0]]

def test_calculate_route_no_path_returns_message():
    svc = MapRoutingService()
    svc.nodes_data = {
        "n1": {"id": "n1", "lat": 1.0, "lng": 1.0},
        "n2": {"id": "n2", "lat": 2.0, "lng": 2.0}
    }
    svc.graph.add_node("n1")
    svc.graph.add_node("n2")
    res = svc.calculate_route(1.0, 1.0, 2.0, 2.0)
    assert res["success"] is False

def test_generate_instructions_empty_and_path():
    svc = MapRoutingService()
    assert svc._generate_instructions([]) == []
    path = [{"name": "A"}, {"name": "B"}]
    instr = svc._generate_instructions(path)
    assert "Bắt đầu" in instr[0]
    assert "Bạn đã đến nơi" in instr[-1]

# --- 4.12: tour_service.py tests ---

def test_haversine_distance_zero_and_known_meter_range():
    dist = TourService.haversine_distance(16.4, 107.5, 16.4, 107.5)
    assert dist == 0.0
    # Approx distance between two 1 deg apart is ~111km, but lets test a small dist
    d2 = TourService.haversine_distance(16.467734, 107.579151, 16.4695, 107.5780)
    assert 200 < d2 < 300

def test_is_far_from_hue_true_for_saigon_false_for_citadel():
    svc = TourService()
    assert svc.is_far_from_hue(HUE_CENTER_LAT, HUE_CENTER_LNG) is False
    assert svc.is_far_from_hue(10.8231, 106.6297) is True

class MockArtifact:
    def __init__(self, art_id, lat, lng, name_vi="A", name_en="A", author="Auth", year=1900, hist_vi="V", hist_en="E"):
        self.art_id = art_id
        self.latitude = lat
        self.longitude = lng
        self.name_vi = name_vi
        self.name_en = name_en
        self.author = author
        self.year = year
        self.history_text_vi = hist_vi
        self.history_text_en = hist_en

class MockRelation:
    def __init__(self, src, tgt, rel_type, weight):
        self.source_artifact_id = src
        self.target_artifact_id = tgt
        self.relation_type = rel_type
        self.weight = weight

class MockSession:
    def __init__(self, results):
        self.results = results
        self.call_count = 0
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        pass
    async def execute(self, stmt):
        class MockResult:
            def __init__(self, r):
                self.r = r
            def scalars(self):
                class MockScalars:
                    def __init__(self, r):
                        self.r = r
                    def all(self):
                        return self.r
                return MockScalars(self.r)
        # return different result per call if results is a list of lists
        if isinstance(self.results, list) and len(self.results) > 0 and isinstance(self.results[0], list):
            res = self.results[self.call_count]
            self.call_count += 1
            return MockResult(res)
        return MockResult(self.results)

@pytest.mark.asyncio
@patch("services.map.tour_service.async_session_factory")
@patch("services.map.tour_service.osrm_service.get_route")
async def test_plan_tour_uses_ngo_mon_when_start_far(mock_osrm, mock_session):
    mock_session.return_value = MockSession([MockArtifact(1, HUE_CENTER_LAT, HUE_CENTER_LNG)])
    mock_osrm.return_value = {"success": True, "coordinates": [[1, 1]], "instructions": [], "distance": 100, "duration": 60}
    
    svc = TourService()
    res = await svc.plan_tour(10.0, 106.0) # far from Hue
    assert res["is_start_far"] is True
    assert res["success"] is True

@pytest.mark.asyncio
@patch("services.map.tour_service.async_session_factory")
async def test_plan_tour_no_artifacts_returns_failure(mock_session):
    mock_session.return_value = MockSession([])
    svc = TourService()
    res = await svc.plan_tour(HUE_CENTER_LAT, HUE_CENTER_LNG)
    assert res["success"] is False

@pytest.mark.asyncio
@patch("services.map.tour_service.async_session_factory")
async def test_plan_tour_filters_missing_coordinates(mock_session):
    mock_session.return_value = MockSession([MockArtifact(1, None, None)])
    svc = TourService()
    res = await svc.plan_tour(HUE_CENTER_LAT, HUE_CENTER_LNG)
    assert res["success"] is False

@pytest.mark.asyncio
@patch("services.map.tour_service.async_session_factory")
@patch("services.map.tour_service.osrm_service.get_route")
async def test_plan_tour_respects_max_places(mock_osrm, mock_session):
    artifacts = [
        MockArtifact(1, HUE_CENTER_LAT + 0.001, HUE_CENTER_LNG),
        MockArtifact(2, HUE_CENTER_LAT + 0.002, HUE_CENTER_LNG),
        MockArtifact(3, HUE_CENTER_LAT + 0.003, HUE_CENTER_LNG),
    ]
    mock_session.return_value = MockSession(artifacts)
    mock_osrm.return_value = {"success": True, "coordinates": [], "instructions": [], "distance": 0, "duration": 0}
    
    svc = TourService()
    res = await svc.plan_tour(HUE_CENTER_LAT, HUE_CENTER_LNG, max_places=2)
    assert res["success"] is True
    assert len(res["route"]) == 2

@pytest.mark.asyncio
@patch("services.map.tour_service.async_session_factory")
@patch("services.map.tour_service.osrm_service.get_route")
async def test_plan_tour_allows_first_stop_even_when_budget_short(mock_osrm, mock_session):
    artifacts = [MockArtifact(1, HUE_CENTER_LAT + 0.001, HUE_CENTER_LNG)]
    mock_session.return_value = MockSession(artifacts)
    mock_osrm.return_value = {"success": True, "coordinates": [], "instructions": [], "distance": 0, "duration": 0}
    
    svc = TourService()
    res = await svc.plan_tour(HUE_CENTER_LAT, HUE_CENTER_LNG, max_duration=1) # 1 minute
    assert res["success"] is True
    assert len(res["route"]) == 1

@pytest.mark.asyncio
@patch("services.map.tour_service.async_session_factory")
@patch("services.map.tour_service.osrm_service.get_route")
async def test_plan_tour_osrm_failure_uses_straight_line_fallback(mock_osrm, mock_session):
    artifacts = [MockArtifact(1, HUE_CENTER_LAT + 0.001, HUE_CENTER_LNG)]
    mock_session.return_value = MockSession(artifacts)
    mock_osrm.return_value = {"success": False} # OSRM fails
    
    svc = TourService()
    res = await svc.plan_tour(HUE_CENTER_LAT, HUE_CENTER_LNG)
    assert res["success"] is True
    assert len(res["coordinates"]) > 0
    assert any("thẳng" in instr for instr in res["instructions"])

@pytest.mark.asyncio
@patch("services.map.tour_service.async_session_factory")
async def test_next_suggestion_empty_db_returns_empty(mock_session):
    mock_session.return_value = MockSession([])
    svc = TourService()
    res = await svc.get_next_suggestion(1, [])
    assert res == []

@pytest.mark.asyncio
@patch("services.map.tour_service.async_session_factory")
async def test_next_suggestion_excludes_current_and_visited(mock_session):
    artifacts = [
        MockArtifact(1, 16.4, 107.5),
        MockArtifact(2, 16.41, 107.51),
        MockArtifact(3, 16.42, 107.52)
    ]
    # First call for artifacts, second for relations
    mock_session.return_value = MockSession([artifacts, []])
    svc = TourService()
    res = await svc.get_next_suggestion(1, [2])
    assert len(res) == 1
    assert res[0]["id"] == 3

@pytest.mark.asyncio
@patch("services.map.tour_service.async_session_factory")
async def test_next_suggestion_relation_boost_affects_order(mock_session):
    artifacts = [
        MockArtifact(1, 16.4, 107.5),
        MockArtifact(2, 16.41, 107.51), # Closer
        MockArtifact(3, 16.43, 107.53)  # Further
    ]
    relations = [
        MockRelation(1, 3, "LOCATED_NEAR", 1.0) # Boost 3
    ]
    mock_session.return_value = MockSession([artifacts, relations])
    svc = TourService()
    res = await svc.get_next_suggestion(1, [])
    assert len(res) == 2
    # 3 should have higher score due to boost
    assert res[0]["id"] == 3

@pytest.mark.asyncio
@patch("services.map.tour_service.async_session_factory")
async def test_next_suggestion_returns_top_three_with_reason(mock_session):
    artifacts = [MockArtifact(1, 16.4, 107.5)] + [MockArtifact(i, 16.4 + i*0.01, 107.5) for i in range(2, 7)]
    relations = [MockRelation(1, 2, "SAME_AUTHOR", 1.0)]
    mock_session.return_value = MockSession([artifacts, relations])
    
    svc = TourService()
    res = await svc.get_next_suggestion(1, [])
    assert len(res) == 3
    assert "reason" in res[0]
