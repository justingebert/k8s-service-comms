"""
Generate architecture diagrams for benchmark.
"""

import os

from PIL import Image
from diagrams import Diagram, Cluster, Edge
from diagrams.k8s.compute import Pod
from diagrams.k8s.network import Service
from diagrams.k8s.storage import Volume
from diagrams.custom import Custom

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level to repo root, then into results/architecture
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "results", "architecture")
os.makedirs(OUTPUT_DIR, exist_ok=True)
ICON_PATH = os.path.join(OUTPUT_DIR, "k8s-container-custom.png")

def crop_whitespace(image_path):
    """Remove external whitespace from diagram image without affecting internal layout."""
    img = Image.open(image_path)

    # Convert to RGB if needed
    if img.mode == "RGBA":
        # Create white background
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Convert to numpy for easier processing
    import numpy as np

    img_array = np.array(img)

    # Create a mask where pixels are NOT white (or near-white)
    # Consider pixels with all RGB values > 250 as "white"
    threshold = 250
    non_white = (
        (img_array[:, :, 0] < threshold)
        | (img_array[:, :, 1] < threshold)
        | (img_array[:, :, 2] < threshold)
    )

    # Find the bounding box of non-white pixels
    rows = np.any(non_white, axis=1)
    cols = np.any(non_white, axis=0)

    if rows.any() and cols.any():
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]

        # Crop with a small padding (5 pixels) to avoid cutting too close
        padding = 5
        rmin = max(0, rmin - padding)
        rmax = min(img_array.shape[0], rmax + padding + 1)
        cmin = max(0, cmin - padding)
        cmax = min(img_array.shape[1], cmax + padding + 1)

        # Crop the image
        img_cropped = img.crop((cmin, rmin, cmax, rmax))
        img_cropped.save(image_path)
        print(
            f"  Cropped: {os.path.basename(image_path)} from {img.size} to {img_cropped.size}"
        )
    else:
        print(f"  No cropping needed: {os.path.basename(image_path)}")


graph_attr = {
    "fontsize": "14",
    "pad": "0.5",
    "ratio": "0.5",
    "size": "8,10!"
}

# Network-based architecture
with Diagram(
    #"Network Communication (Inter-Pod)",
    filename=os.path.join(OUTPUT_DIR, "network_arch"),
    show=False,
    direction="LR",
    graph_attr=graph_attr,
):
    with Cluster("Kubernetes Cluster"):
        with Cluster("Sender Pod"):
            sender = Pod("Sender\nContainer")

        svc = Service("Service")

        with Cluster("Receiver Pod"):
            receiver = Pod("Receiver\nContainer")

    sender >> Edge(label="HTTP") >> svc >> Edge(label="Routes") >> receiver
    #sender << Edge(label="") << svc << Edge(label="") << receiver




# Crop external whitespace
crop_whitespace(os.path.join(OUTPUT_DIR, "network_arch.png"))



# File-based architecture
with Diagram(
    #"File Communication (Intra-Pod)",
    filename=os.path.join(OUTPUT_DIR, "file_arch"),
    show=False,
    direction="LR",
    graph_attr=graph_attr,
):
    with Cluster("Kubernetes Cluster"):
        with Cluster("Combined Pod"):
            file_sender = Custom("Sender\nContainer", ICON_PATH)

            volume = Volume("emptyDir")

            file_receiver = Custom("Receiver\nContainer", ICON_PATH)

            file_sender >> Edge(label="Write") >> volume
            volume >> Edge(label="Read") >> file_receiver

# Crop external whitespace
crop_whitespace(os.path.join(OUTPUT_DIR, "file_arch.png"))


panel_attr = {
    "style": "rounded,filled",
    "color": "gray40",
    "fillcolor": "gray95",
    "fontsize": "12",
    "margin": "16"
}

with Diagram(
        filename=os.path.join(OUTPUT_DIR, "architectures"),
        show=False,
        direction="LR",
        graph_attr={
            **graph_attr,
            "nodesep": "0.6",
            "ranksep": "0.8",
            "pad": "0.2"
        },
):
    # --- Panel (a): Network ---
    with Cluster("1) Inter-Pod: Service + HTTP/TCP", graph_attr=panel_attr):
        with Cluster("Sender Pod"):
            sender = Pod("Sender")

        svc = Service("ClusterIP\nService")

        with Cluster("Receiver Pod"):
            receiver = Pod("Receiver")

        sender >> Edge(label="HTTP") >> svc >> Edge(label="Routes") >> receiver

    # --- Panel (b): File ---
    with Cluster("2) Intra-Pod: emptyDir Volume", graph_attr=panel_attr):
        with Cluster("Combined Pod"):
            file_sender = Custom("Sender", ICON_PATH)

            with Cluster("Shared Volume"):
                volume = Volume("emptyDir")

            file_receiver = Custom("Receiver", ICON_PATH)

            file_sender >> Edge(label="Write") >> volume
            volume >> Edge(label="Read") >> file_receiver

crop_whitespace(os.path.join(OUTPUT_DIR, "architectures.png"))

print("✅ Architecture diagrams generated in results/architecture/")
