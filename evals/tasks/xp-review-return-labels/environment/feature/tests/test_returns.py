from app.shipping.notifications import return_instructions
from app.shipping.returns import authorise_return


def test_authorise_return_label_is_addressed_to_the_warehouse(shipment) -> None:
    label = authorise_return(shipment).label

    assert "ACME WAREHOUSE\nUnit 4 Dock Road\nLeeds LS1 4AB\nGB" in label
    assert "PREPAID RETURN" in label


def test_authorise_return_summary_counts_parcels_and_weight(shipment) -> None:
    assert authorise_return(shipment).summary == "2 parcel(s), 1.55 kg, back to Leeds"


def test_return_instructions_end_with_the_warehouse_address(shipment) -> None:
    assert return_instructions(shipment).endswith("Leeds LS1 4AB\nGB")
