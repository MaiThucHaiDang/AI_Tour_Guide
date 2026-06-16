"""Map Routing Service using NetworkX."""

import json
import math
import logging
from pathlib import Path
import networkx as nx
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# The path to the graph JSON file
GRAPH_FILE = Path(__file__).resolve().parents[2] / "data" / "map_graph.json"

class MapRoutingService:
    def __init__(self):
        self.graph = nx.Graph()
        self.nodes_data = {}
        self._load_graph()

    def _load_graph(self):
        """Loads the map graph from JSON."""
        if not GRAPH_FILE.exists():
            logger.warning(f"Graph file {GRAPH_FILE} not found. Routing will fail.")
            return

        try:
            with open(GRAPH_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for node in data.get("nodes", []):
                self.graph.add_node(node["id"], **node)
                self.nodes_data[node["id"]] = node
            
            for edge in data.get("edges", []):
                self.graph.add_edge(edge["source"], edge["target"], weight=edge.get("weight", 1.0))
                
            logger.info(f"Loaded Map Graph: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges.")
        except Exception as e:
            logger.error(f"Failed to load map graph: {e}")

    def find_nearest_node(self, lat: float, lng: float) -> str | None:
        """Finds the nearest node in the graph to the given coordinates."""
        if not self.nodes_data:
            return None
            
        nearest_node = None
        min_dist = float('inf')
        
        for node_id, data in self.nodes_data.items():
            n_lat = data.get("lat")
            n_lng = data.get("lng")
            if n_lat is None or n_lng is None:
                continue
                
            # Simple Euclidean distance is sufficient for small distances
            dist = math.hypot(lat - n_lat, lng - n_lng)
            if dist < min_dist:
                min_dist = dist
                nearest_node = node_id
                
        return nearest_node

    def calculate_route(self, start_lat: float, start_lng: float, end_lat: float, end_lng: float) -> Dict[str, Any]:
        """Calculates the shortest path and generates directions."""
        if not self.graph.nodes:
            return {"success": False, "message": "Graph not loaded."}
            
        start_node = self.find_nearest_node(start_lat, start_lng)
        end_node = self.find_nearest_node(end_lat, end_lng)
        
        if not start_node or not end_node:
            return {"success": False, "message": "Could not locate nearby points on the map."}
            
        if start_node == end_node:
            return {
                "success": True, 
                "path_nodes": [self.nodes_data[start_node]],
                "coordinates": [[self.nodes_data[start_node]["lat"], self.nodes_data[start_node]["lng"]]],
                "instructions": ["Bạn đã ở vị trí gần với điểm đến."]
            }
            
        try:
            # Dijkstra algorithm
            path = nx.shortest_path(self.graph, source=start_node, target=end_node, weight="weight")
            
            # Extract coordinates and data
            path_nodes = [self.nodes_data[n] for n in path]
            coordinates = [[n["lat"], n["lng"]] for n in path_nodes]
            
            # Generate simple instructions
            instructions = self._generate_instructions(path_nodes)
            
            return {
                "success": True,
                "path_nodes": path_nodes,
                "coordinates": coordinates,
                "instructions": instructions
            }
        except nx.NetworkXNoPath:
            return {"success": False, "message": "Không tìm thấy đường đi đến điểm đến."}
        except Exception as e:
            logger.error(f"Routing error: {e}")
            return {"success": False, "message": "Lỗi khi tính toán đường đi."}

    def _generate_instructions(self, path_nodes: List[Dict]) -> List[str]:
        """Generates simple turn-by-turn text instructions."""
        instructions = []
        if not path_nodes:
            return instructions
            
        instructions.append("Bắt đầu di chuyển.")
        for i in range(1, len(path_nodes)):
            prev = path_nodes[i - 1].get("name", f"điểm {i}")
            target = path_nodes[i].get("name", f"điểm {i + 1}")
            instructions.append(f"Đi từ {prev} đến {target}.")

        instructions.append("Bạn đã đến nơi.")
        return instructions

# Singleton instance
routing_service = MapRoutingService()
