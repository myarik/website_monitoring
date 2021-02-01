from diagrams import Diagram, Edge
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.queue import Kafka
from diagrams.onprem.container import Docker


with Diagram("Monitoring Application", show=False):
    Docker("Monitoring service") >> Edge(color="black", style="bold") >> Kafka(
        "stream"
    ) >> Edge(color="black", style="bold") >> Docker("Consumer service") >> Edge(
        color="black", style="bold"
    ) >> PostgreSQL(
        "storage"
    )
