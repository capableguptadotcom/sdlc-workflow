def shipment_status(destination: str) -> str:
    return "ready" if destination.strip() else "draft"
