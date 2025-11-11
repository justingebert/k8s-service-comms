"""
Generate architecture diagrams for benchmark.
"""
from diagrams import Diagram, Cluster, Edge
from diagrams.k8s.compute import Pod
from diagrams.k8s.network import Service
from diagrams.k8s.storage import Volume
from diagrams.onprem.network import Internet
import os

os.makedirs("../results/architecture", exist_ok=True)

# Network-based architecture
with Diagram("Network Communication (Inter-Pod)",
             filename="../results/architecture/network_arch",
             show=False,
             direction="LR"):
    with Cluster("Kubernetes Cluster"):
        with Cluster("Sender Pod"):
            sender = Pod("Sender\nContainer")

        svc = Service("Network\nService")

        with Cluster("Receiver Pod"):
            receiver = Pod("Receiver\nContainer")

    sender >> Edge(label="GTTP") >> svc >> Edge(label="Load Balance") >> receiver

# File-based architecture
with Diagram("File Communication (Intra-Pod)",
             filename="../results/architecture/file_arch",
             show=False,
             direction="TB"):
    with Cluster("Kubernetes Cluster"):
        with Cluster("Combined Pod"):
            with Cluster("Shared Volume"):
                volume = Volume()

            sender = Pod("Sender\nContainer")
            receiver = Pod("Receiver\nContainer")

            sender >> Edge(label="Write") >> volume
            volume >> Edge(label="Read") >> receiver

print("✅ Architecture diagrams generated in results/architecture/")
