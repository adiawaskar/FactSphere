# 04_graph_builder.py
from neo4j import GraphDatabase
import dateparser
from typing import Dict, List
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, CONSOLE

class Neo4jGraph:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def clear_database(self):
        """Deletes all nodes and relationships from the graph."""
        with self.driver.session() as session:
            session.execute_write(self._clear_db_query)
    
    @staticmethod
    def _clear_db_query(tx):
        """Cypher query to detach and delete all nodes."""
        query = "MATCH (n) DETACH DELETE n"
        tx.run(query)
        
    def _normalize_date(self, event: Dict) -> str:
        """Normalizes date using explicit_date or falls back to inferred_date."""
        date_str = event.get('explicit_date')
        if date_str:
            # Use dateparser to handle various formats like "November 24, 2023"
            parsed_date = dateparser.parse(date_str)
            if parsed_date:
                return parsed_date.strftime('%Y-%m-%d')
        
        # Fallback to the article's publication date
        return event.get('inferred_date')

    def add_event(self, event: Dict):
        """Adds a single event to the Neo4j graph."""
        normalized_date = self._normalize_date(event)
        if not normalized_date:
            return # Skip events without a usable date

        with self.driver.session() as session:
            # session.write_transaction(self._create_event_nodes, event, normalized_date)
            session.execute_write(self._create_event_nodes, event, normalized_date)
    
    @staticmethod
    def _create_event_nodes(tx, event, normalized_date):
        query = """
        // Create the main Event node
        MERGE (e:Event {title: $title, date: $date})
        SET e.description = $description, e.url = $source_url

        // Create or merge Date node and link to Event
        MERGE (d:Date {value: $date})
        MERGE (e)-[:HAPPENED_ON]->(d)

        // Create or merge Location node and link to Event
        WITH e
        MERGE (l:Location {name: $location})
        MERGE (e)-[:OCCURRED_AT]->(l)

        // Unwind actors and create/merge Actor nodes and relationships
        WITH e
        UNWIND $actors AS actor_name
        MERGE (a:Actor {name: actor_name})
        MERGE (a)-[:PARTICIPATED_IN]->(e)
        """
        tx.run(query, 
               title=event['event_title'],
               description=event['description'],
               date=normalized_date,
               source_url=event['source_url'],
               # This will use 'Unknown' if event.get('location') is None or the key is missing.
               location=event.get('location') or 'Unknown', 
               actors=event.get('actors', [])
        )

    def add_temporal_relationships(self):
        """Finds events in chronological order and links them with [:BEFORE]."""
        CONSOLE.print("\n[yellow]🔗 Building temporal relationships in Neo4j...[/yellow]")
        with self.driver.session() as session:
            # session.write_transaction(self._create_before_links)
            session.execute_write(self._create_before_links)

    @staticmethod
    def _create_before_links(tx):
        query = """
        // Get all events sorted by date
        MATCH (e:Event)
        WITH e ORDER BY e.date ASC
        // Collect them into a list
        WITH collect(e) AS events
        // Iterate through pairs of consecutive events
        UNWIND range(0, size(events) - 2) AS i
        WITH events[i] AS e1, events[i+1] AS e2
        // Create a :BEFORE relationship
        MERGE (e1)-[:BEFORE]->(e2)
        """
        tx.run(query)

    def get_sorted_events(self) -> List[Dict]:
        """Queries the graph to get all events, sorted chronologically."""
        with self.driver.session() as session:
            # result = session.read_transaction(self._get_all_events_query)
            result = session.execute_read(self._get_all_events_query)
            return result

    @staticmethod
    def _get_all_events_query(tx) -> List[Dict]:
        query = """
        MATCH (e:Event)
        RETURN e.title AS title, e.description AS description, e.date AS date
        ORDER BY e.date ASC
        """
        records = tx.run(query)
        return [record.data() for record in records]